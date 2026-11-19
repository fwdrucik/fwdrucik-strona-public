<?php
declare(strict_types=1);

/**
 * Wysyłka wiadomości e-mail z serwisu.
 *
 * Dwie drogi, w tej kolejności:
 *   1. SMTP, jeśli w konfiguracji są dane skrzynki (`smtp_host` i reszta).
 *      Wiadomość wychodzi wtedy z uwierzytelnionego konta i znacznie rzadziej
 *      ląduje w spamie.
 *   2. Funkcja mail() z PHP jako rozwiązanie zapasowe.
 *
 * Każda nieudana wysyłka jest zapisywana do pliku `poczta-bledy.log` obok
 * konfiguracji. Cicha porażka przy potwierdzaniu adresu e-mail oznaczałaby
 * użytkownika, który nigdy nie dokończy rejestracji i nie wie dlaczego.
 */

if (basename((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === '_poczta.php') {
    http_response_code(404);
    exit;
}

const FW_NADAWCA_DOMYSLNY = 'fwdrucik@gmail.com';
const FW_NADAWCA_NAZWA = 'F.W. DRUCIK';

function fw_log_poczty(string $tekst): void
{
    $plik = __DIR__ . '/../../poczta-bledy.log';
    @file_put_contents($plik, '[' . date('c') . '] ' . $tekst . "\n", FILE_APPEND | LOCK_EX);
}

/**
 * Nagłówek adresu z zakodowaną nazwą.
 *
 * Polskie znaki w nazwie nadawcy muszą być zakodowane w MIME, inaczej część
 * serwerów odrzuca wiadomość albo wyświetla krzaki.
 */
function fw_adres_naglowek(string $email, string $nazwa): string
{
    return $nazwa === ''
        ? $email
        : '=?UTF-8?B?' . base64_encode($nazwa) . '?= <' . $email . '>';
}

/** Rozmowa z serwerem SMTP — jedna komenda, sprawdzenie kodu odpowiedzi. */
function fw_smtp_komenda($gniazdo, string $komenda, array $oczekiwane): bool
{
    if ($komenda !== '') {
        fwrite($gniazdo, $komenda . "\r\n");
    }
    $odpowiedz = '';
    while (($linia = fgets($gniazdo, 515)) !== false) {
        $odpowiedz .= $linia;
        // Ostatnia linia odpowiedzi SMTP ma spację po kodzie, kolejne — myślnik.
        if (strlen($linia) < 4 || $linia[3] === ' ') {
            break;
        }
    }
    $kod = (int) substr(trim($odpowiedz), 0, 3);
    if (!in_array($kod, $oczekiwane, true)) {
        fw_log_poczty('SMTP: ' . substr($komenda, 0, 30) . ' -> ' . trim($odpowiedz));
        return false;
    }
    return true;
}

function fw_wyslij_smtp(array $cfg, string $do, string $temat, string $tresc): bool
{
    $host = (string) $cfg['smtp_host'];
    $port = (int) ($cfg['smtp_port'] ?? 587);
    $uzytkownik = (string) ($cfg['smtp_uzytkownik'] ?? '');
    $haslo = (string) ($cfg['smtp_haslo'] ?? '');
    $nadawca = (string) ($cfg['smtp_nadawca'] ?? $uzytkownik ?: FW_NADAWCA_DOMYSLNY);
    $szyfrowanie = (string) ($cfg['smtp_szyfrowanie'] ?? 'tls');

    $adres = ($szyfrowanie === 'ssl' ? 'ssl://' : '') . $host . ':' . $port;
    $gniazdo = @stream_socket_client($adres, $errno, $errstr, 15);
    if (!$gniazdo) {
        fw_log_poczty("SMTP: brak polaczenia z $adres ($errno $errstr)");
        return false;
    }
    stream_set_timeout($gniazdo, 15);

    $ok = fw_smtp_komenda($gniazdo, '', [220])
        && fw_smtp_komenda($gniazdo, 'EHLO fwdrucik.pl', [250]);

    if ($ok && $szyfrowanie === 'tls') {
        $ok = fw_smtp_komenda($gniazdo, 'STARTTLS', [220])
            && @stream_socket_enable_crypto($gniazdo, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)
            && fw_smtp_komenda($gniazdo, 'EHLO fwdrucik.pl', [250]);
    }
    if ($ok && $uzytkownik !== '') {
        $ok = fw_smtp_komenda($gniazdo, 'AUTH LOGIN', [334])
            && fw_smtp_komenda($gniazdo, base64_encode($uzytkownik), [334])
            && fw_smtp_komenda($gniazdo, base64_encode($haslo), [235]);
    }
    if ($ok) {
        $naglowki = "From: " . fw_adres_naglowek($nadawca, FW_NADAWCA_NAZWA) . "\r\n"
            . "To: <$do>\r\n"
            . "Subject: =?UTF-8?B?" . base64_encode($temat) . "?=\r\n"
            . "MIME-Version: 1.0\r\n"
            . "Content-Type: text/plain; charset=UTF-8\r\n"
            . "Content-Transfer-Encoding: 8bit\r\n"
            . "Date: " . date('r') . "\r\n";
        // Kropka na poczatku linii konczy wiadomosc w protokole SMTP —
        // trzeba ja podwoic, inaczej tresc urwie sie w polowie.
        $cialo = preg_replace('/^\./m', '..', $tresc);
        $ok = fw_smtp_komenda($gniazdo, 'MAIL FROM:<' . $nadawca . '>', [250])
            && fw_smtp_komenda($gniazdo, 'RCPT TO:<' . $do . '>', [250, 251])
            && fw_smtp_komenda($gniazdo, 'DATA', [354])
            && fw_smtp_komenda($gniazdo, $naglowki . "\r\n" . $cialo . "\r\n.", [250]);
    }
    @fw_smtp_komenda($gniazdo, 'QUIT', [221, 250]);
    fclose($gniazdo);
    return $ok;
}

/** Wysyła wiadomość tekstową. Zwraca false, gdy obie drogi zawiodły. */
function fw_wyslij_mail(string $do, string $temat, string $tresc): bool
{
    if (!filter_var($do, FILTER_VALIDATE_EMAIL)) {
        fw_log_poczty('Niepoprawny adres odbiorcy: ' . $do);
        return false;
    }
    $cfg = fw_konfiguracja();

    if (!empty($cfg['smtp_host'])) {
        if (fw_wyslij_smtp($cfg, $do, $temat, $tresc)) {
            return true;
        }
        fw_log_poczty('SMTP nie zadzialal, probuje mail() dla ' . $do);
    }

    $nadawca = (string) ($cfg['smtp_nadawca'] ?? FW_NADAWCA_DOMYSLNY);
    $naglowki = 'From: ' . fw_adres_naglowek($nadawca, FW_NADAWCA_NAZWA) . "\r\n"
        . "MIME-Version: 1.0\r\n"
        . "Content-Type: text/plain; charset=UTF-8\r\n";
    $wyslano = @mail($do, '=?UTF-8?B?' . base64_encode($temat) . '?=', $tresc, $naglowki);
    if (!$wyslano) {
        fw_log_poczty('mail() zwrocilo false dla ' . $do . ' — temat: ' . $temat);
    }
    return $wyslano;
}

/** Kwota w groszach jako tekst „129,90 zł". */
function fw_zlote(int $grosze): string
{
    return number_format($grosze / 100, 2, ',', ' ') . ' zł';
}

/**
 * Powiadomienie o nowym zamówieniu: potwierdzenie dla klienta i kopia
 * dla warsztatu. Kopia jest ważniejsza — bez niej zamówienie leżałoby
 * w bazie, dopóki ktoś nie zajrzy do panelu.
 */
/**
 * Wiadomość do klienta po zmianie statusu zamówienia.
 *
 * PO CO: dotąd status zmieniał się wyłącznie w bazie i w aplikacji sprzedawcy.
 * Klient, który zapłacił przelewem, nie miał skąd wiedzieć, że paczka poszła —
 * dzwonił albo czekał. Jedna wiadomość załatwia obie te sytuacje.
 *
 * Wysyłamy TYLKO przy stanach, które coś znaczą dla kupującego. „Nowe" zna
 * z potwierdzenia zamówienia, a „w realizacji" bez daty nie niesie treści.
 */
function fw_powiadom_o_statusie(
    string $numer,
    string $email,
    string $status,
    string $przesylka = ''
): void {
    $zdania = [
        'oplacone'   => 'Zapłata dotarła — bierzemy się do roboty.',
        'wyslane'    => 'Zamówienie wyszło z warsztatu.',
        'zakonczone' => 'Zamówienie zakończone. Dziękujemy!',
        'anulowane'  => 'Zamówienie zostało anulowane. Jeśli to pomyłka, odpisz na tę wiadomość.',
    ];
    if (!isset($zdania[$status]) || trim($email) === '') {
        return;
    }

    $tresc = "Zamówienie $numer — " . $zdania[$status] . "\n\n";
    if ($status === 'wyslane' && trim($przesylka) !== '') {
        $tresc .= "Numer przesyłki: $przesylka\n"
            . "Śledzenie: sprawdzisz go na stronie przewoźnika.\n\n";
    }
    $tresc .= "Pytania: 601 726 924\n\nF.W. DRUCIK, Domosław 13A, 06-120 Winnica";

    fw_wyslij_mail($email, "Zamówienie $numer — " . $zdania[$status], $tresc);
}

function fw_powiadom_o_zamowieniu(
    string $numer,
    string $email,
    int $sumaGr,
    array $pozycje,
    string $platnosc,
    string $dostawa
): void {
    $cfg = fw_konfiguracja();
    $linie = [];
    foreach ($pozycje as $p) {
        $linie[] = sprintf('  %s x%d — %s', $p['nazwa'], $p['ilosc'], fw_zlote($p['cena_gr'] * $p['ilosc']));
    }
    $spis = implode("\n", $linie);

    $dlaKlienta = "Dziękujemy za zamówienie w F.W. DRUCIK.\n\n"
        . "Numer zamówienia: $numer\n"
        . "Zamówione pozycje:\n$spis\n\n"
        . 'Razem do zapłaty: ' . fw_zlote($sumaGr) . "\n"
        . 'Sposób dostawy: ' . (FW_DOSTAWA[$dostawa]['nazwa'] ?? $dostawa) . "\n"
        . 'Sposób zapłaty: ' . (fw_platnosci()[$platnosc] ?? $platnosc) . "\n\n";

    if ($platnosc === 'przelew') {
        $konto = (string) ($cfg['numer_konta'] ?? '');
        $dlaKlienta .= $konto !== ''
            ? "Dane do przelewu:\n  Odbiorca: F.W. DRUCIK, Domosław 13A, 06-120 Winnica\n"
              . "  Numer konta: $konto\n  Tytuł przelewu: $numer\n\n"
            : "Dane do przelewu prześlemy osobną wiadomością.\n\n";
    }

    $dlaKlienta .= "Status zamówienia sprawdzisz po zalogowaniu na https://fwdrucik.pl/konto/\n"
        . "Pytania: 601 726 924\n\nF.W. DRUCIK, Domosław 13A, 06-120 Winnica";

    fw_wyslij_mail($email, "Zamówienie $numer — F.W. DRUCIK", $dlaKlienta);

    $doWarsztatu = (string) ($cfg['email_zamowien'] ?? FW_NADAWCA_DOMYSLNY);
    fw_wyslij_mail(
        $doWarsztatu,
        "NOWE ZAMÓWIENIE $numer (" . fw_zlote($sumaGr) . ')',
        "Nowe zamówienie w sklepie.\n\nNumer: $numer\nKlient: $email\n"
        . "Pozycje:\n$spis\n\nRazem: " . fw_zlote($sumaGr) . "\n"
        . 'Dostawa: ' . (FW_DOSTAWA[$dostawa]['nazwa'] ?? $dostawa) . "\n"
        . 'Zapłata: ' . (fw_platnosci()[$platnosc] ?? $platnosc) . "\n\n"
        . "Szczegóły: https://fwdrucik.pl/admin/\n"
    );
}
