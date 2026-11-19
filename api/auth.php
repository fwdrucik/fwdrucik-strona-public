<?php
declare(strict_types=1);

/**
 * Konta użytkowników.
 *
 *   GET  /api/auth.php?akcja=ja            — kto jest zalogowany (+ token CSRF)
 *   POST /api/auth.php?akcja=rejestracja   — nick, email, haslo
 *   POST /api/auth.php?akcja=logowanie     — login (nick lub e-mail), haslo
 *   POST /api/auth.php?akcja=wylogowanie
 */

require_once __DIR__ . '/_lib.php';
require_once __DIR__ . '/_poczta.php';
require_once __DIR__ . '/_captcha.php';

/**
 * Dokłada kolumny potwierdzenia adresu e-mail, jeśli ich jeszcze nie ma.
 *
 * MySQL nie zna `ADD COLUMN IF NOT EXISTS`, więc obecność kolumny sprawdzamy
 * w information_schema. Dzięki temu serwis nie wymaga ręcznej migracji
 * w phpMyAdmin — tak samo jak przy pozostałych tabelach dokładanych później.
 */
function fw_zapewnij_kolumny_potwierdzenia(): void
{
    static $gotowe = false;
    if ($gotowe) {
        return;
    }
    $pdo = fw_baza();
    $tabela = fw_tabela('uzytkownicy');
    $st = $pdo->prepare('SELECT COLUMN_NAME FROM information_schema.COLUMNS'
        . ' WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?');
    $st->execute([$tabela]);
    $kolumny = array_column($st->fetchAll(), 'COLUMN_NAME');

    $doDodania = [];
    if (!in_array('email_potwierdzony', $kolumny, true)) {
        $doDodania[] = 'ADD COLUMN email_potwierdzony TINYINT NOT NULL DEFAULT 0';
    }
    if (!in_array('token_email', $kolumny, true)) {
        $doDodania[] = 'ADD COLUMN token_email CHAR(64) NULL';
    }
    if (!in_array('token_email_wygasa', $kolumny, true)) {
        $doDodania[] = 'ADD COLUMN token_email_wygasa DATETIME NULL';
    }
    if ($doDodania) {
        $pdo->exec('ALTER TABLE ' . $tabela . ' ' . implode(', ', $doDodania));
        // Konta zalozone przed wprowadzeniem potwierdzania traktujemy jako
        // potwierdzone — inaczej wszyscy dotychczasowi uzytkownicy zostaliby
        // z dnia na dzien odciec od komentarzy i forum.
        $pdo->exec('UPDATE ' . $tabela . ' SET email_potwierdzony = 1'
            . ' WHERE email_potwierdzony = 0 AND token_email IS NULL');
    }
    $gotowe = true;
}

/** Wysyła wiadomość z linkiem potwierdzającym i zapisuje token. */
function fw_wyslij_potwierdzenie(int $id, string $email, string $nick): bool
{
    $token = bin2hex(random_bytes(32));
    fw_baza()->prepare('UPDATE ' . fw_tabela('uzytkownicy')
        . ' SET token_email = ?, token_email_wygasa = ? WHERE id = ?')
        ->execute([hash('sha256', $token), date('Y-m-d H:i:s', time() + 172800), $id]);

    $link = 'https://fwdrucik.pl/konto/?potwierdz=' . $token;
    return fw_wyslij_mail(
        $email,
        'Potwierdź adres e-mail — F.W. DRUCIK',
        "Cześć $nick,\n\n"
        . "dziękujemy za założenie konta w serwisie F.W. DRUCIK.\n"
        . "Potwierdź swój adres e-mail, klikając w link poniżej:\n\n"
        . "$link\n\n"
        . "Link jest ważny przez 48 godzin. Jeśli to nie Ty zakładałeś konto,\n"
        . "po prostu zignoruj tę wiadomość — konto bez potwierdzenia nic nie robi.\n\n"
        . "F.W. DRUCIK, Domosław 13A, 06-120 Winnica\ntel. 601 726 924"
    );
}

$akcja = fw_akcja();

// ------------------------------------------------------------------------ ja
if ($akcja === 'ja') {
    $u = fw_uzytkownik();
    fw_odpowiedz([
        'ok'         => true,
        'uzytkownik' => $u === null ? null : fw_publiczny_uzytkownik($u),
        'csrf'       => fw_token_csrf(),
    ]);
}

// ---------------------------------------------------------------- rejestracja
if ($akcja === 'rejestracja') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    fw_limit('rejestracja', 5, 3600);

    // Pole-pułapka: wypełniają je wyłącznie boty, człowiek go nie widzi.
    if (fw_pole('firma') !== '') {
        fw_blad(422, 'Formularz odrzucony.');
    }

    // Kod z obrazka sprawdzamy przed czymkolwiek innym — zanim policzymy skrót
    // hasła i zanim odpytamy bazę o zajęty nick.
    fw_captcha_sprawdz(fw_pole('captcha_id'), fw_pole('captcha'));
    fw_zapewnij_kolumny_potwierdzenia();

    $nick  = fw_tekst(fw_pole('nick'), 'Nick', 3, 40);
    $email = mb_strtolower(fw_pole('email'), 'UTF-8');
    $haslo = fw_pole('haslo');

    if (!preg_match('/^[\p{L}\p{N}_. -]{3,40}$/u', $nick)) {
        fw_blad(422, 'Nick może zawierać tylko litery, cyfry, spację, kropkę, myślnik i podkreślenie.');
    }
    if (!filter_var($email, FILTER_VALIDATE_EMAIL) || mb_strlen($email) > 190) {
        fw_blad(422, 'Podaj poprawny adres e-mail.');
    }
    // 10 znaków to więcej niż typowe 8 — hasła do forum bywają wielokrotnie użyte.
    fw_tekst($haslo, 'Hasło', 10, 200);

    $pdo = fw_baza();
    $st = $pdo->prepare('SELECT email, nick FROM ' . fw_tabela('uzytkownicy')
        . ' WHERE email = ? OR nick = ? LIMIT 1');
    $st->execute([$email, $nick]);
    if ($istnieje = $st->fetch()) {
        fw_blad(409, $istnieje['email'] === $email
            ? 'Konto z tym adresem e-mail już istnieje.'
            : 'Ten nick jest już zajęty.');
    }

    $st = $pdo->prepare('INSERT INTO ' . fw_tabela('uzytkownicy')
        . ' (nick, email, haslo_hash, rola, zaufany, utworzony) VALUES (?, ?, ?, "user", 0, ?)');
    $st->execute([$nick, $email, password_hash($haslo, PASSWORD_DEFAULT), fw_teraz()]);

    $id = (int) $pdo->lastInsertId();
    fw_zaloz_sesje($id);
    $wyslano = fw_wyslij_potwierdzenie($id, $email, $nick);

    fw_odpowiedz([
        'ok'         => true,
        'uzytkownik' => ['id' => $id, 'nick' => $nick, 'rola' => 'user', 'zaufany' => false],
        'csrf'       => fw_token_csrf(),
        'komunikat'  => $wyslano
            ? 'Konto założone. Na podany adres wysłaliśmy wiadomość z linkiem potwierdzającym — kliknij go, żeby móc zamawiać w sklepie.'
            : 'Konto założone, ale nie udało się wysłać wiadomości potwierdzającej. Napisz na fwdrucik@gmail.com, potwierdzimy adres ręcznie.',
    ], 201);
}

// -------------------------------------------------- potwierdzenie adresu
if ($akcja === 'potwierdz-email') {
    fw_zapewnij_kolumny_potwierdzenia();
    $token = (string) ($_GET['token'] ?? fw_pole('token'));
    if (!preg_match('/^[a-f0-9]{64}$/', $token)) {
        fw_blad(422, 'Niepoprawny link potwierdzający.');
    }
    $pdo = fw_baza();
    $st = $pdo->prepare('SELECT id FROM ' . fw_tabela('uzytkownicy')
        . ' WHERE token_email = ? AND token_email_wygasa >= ?');
    $st->execute([hash('sha256', $token), fw_teraz()]);
    $id = $st->fetchColumn();
    if ($id === false) {
        fw_blad(410, 'Link potwierdzający wygasł albo został już użyty. Poproś o nowy.');
    }
    $pdo->prepare('UPDATE ' . fw_tabela('uzytkownicy')
        . ' SET email_potwierdzony = 1, token_email = NULL, token_email_wygasa = NULL WHERE id = ?')
        ->execute([$id]);

    fw_odpowiedz(['ok' => true, 'komunikat' => 'Adres e-mail potwierdzony. Możesz już zamawiać w sklepie.']);
}

if ($akcja === 'wyslij-potwierdzenie') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    $u = fw_wymagaj_logowania();
    fw_limit('potwierdzenie', 5, 3600);
    fw_zapewnij_kolumny_potwierdzenia();

    if ((int) ($u['email_potwierdzony'] ?? 0) === 1) {
        fw_odpowiedz(['ok' => true, 'komunikat' => 'Ten adres jest już potwierdzony.']);
    }
    $wyslano = fw_wyslij_potwierdzenie((int) $u['id'], (string) $u['email'], (string) $u['nick']);
    fw_odpowiedz([
        'ok' => true,
        'komunikat' => $wyslano
            ? 'Wysłaliśmy nową wiadomość z linkiem potwierdzającym.'
            : 'Nie udało się wysłać wiadomości. Napisz na fwdrucik@gmail.com.',
    ]);
}

// ------------------------------------------------------------------ logowanie
if ($akcja === 'logowanie') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    fw_limit('logowanie', 10, 900);

    $login = fw_pole('login') !== '' ? fw_pole('login') : fw_pole('email');
    $haslo = fw_pole('haslo');
    if ($login === '' || $haslo === '') {
        fw_blad(422, 'Podaj login i hasło.');
    }

    $st = fw_baza()->prepare('SELECT id, nick, rola, zaufany, zablokowany, haslo_hash'
        . ' FROM ' . fw_tabela('uzytkownicy')
        . ' WHERE email = ? OR nick = ? LIMIT 1');
    $st->execute([mb_strtolower($login, 'UTF-8'), $login]);
    $u = $st->fetch();

    // Hasło weryfikowane także dla nieistniejącego konta — inaczej czas odpowiedzi
    // zdradzałby, które adresy są zarejestrowane.
    // Poprawny formatem, ale nieosiągalny skrót — password_verify wykona pełną
    // pracę i odpadnie, zamiast wrócić natychmiast.
    $hash = $u['haslo_hash'] ?? '$2y$12$usesomesillystringfore7hnbRJHxXVLeakoG8K30M1p1DR.4PS';
    if (!password_verify($haslo, $hash) || !$u) {
        fw_blad(401, 'Niepoprawny login lub hasło.');
    }
    if ((int) $u['zablokowany'] === 1) {
        fw_blad(403, 'To konto zostało zablokowane.');
    }

    // Przeliczenie skrótu, jeśli PHP podniosło domyślny algorytm.
    if (password_needs_rehash($hash, PASSWORD_DEFAULT)) {
        fw_baza()->prepare('UPDATE ' . fw_tabela('uzytkownicy') . ' SET haslo_hash = ? WHERE id = ?')
            ->execute([password_hash($haslo, PASSWORD_DEFAULT), (int) $u['id']]);
    }

    fw_baza()->prepare('UPDATE ' . fw_tabela('uzytkownicy') . ' SET ostatnie_logowanie = ? WHERE id = ?')
        ->execute([fw_teraz(), (int) $u['id']]);

    fw_zaloz_sesje((int) $u['id']);
    fw_odpowiedz([
        'ok'         => true,
        'uzytkownik' => fw_publiczny_uzytkownik($u),
        'csrf'       => fw_token_csrf(),
    ]);
}

// --------------------------------------------------------------- wylogowanie
if ($akcja === 'wylogowanie') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    fw_zamknij_sesje();
    fw_odpowiedz(['ok' => true]);
}

fw_blad(404, 'Nieznana akcja.');
