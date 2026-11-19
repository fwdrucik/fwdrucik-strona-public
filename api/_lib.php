<?php
declare(strict_types=1);

/**
 * Wspólna warstwa API fwdrucik.pl — połączenie z bazą, sesje, CSRF, limit tempa.
 *
 * Każda końcówka zaczyna się od `require_once __DIR__ . '/_lib.php';`.
 * Plik nie wypisuje nic sam z siebie — całe wyjście idzie przez odpowiedz().
 */

// Nazwa pliku zaczyna się od podkreślenia i jest blokowana w .htaccess,
// ale gdyby ktoś obszedł blokadę, bezpośrednie wejście nic nie zwróci.
if (basename((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === '_lib.php') {
    http_response_code(404);
    exit;
}

// Błędy PHP nigdy nie lecą do przeglądarki — zepsułyby JSON i zdradziły ścieżki.
ini_set('display_errors', '0');
error_reporting(E_ALL);

const FW_SESJA_COOKIE = 'fw_sesja';
const FW_CSRF_COOKIE  = 'fw_csrf';
const FW_SESJA_DNI    = 30;

// --------------------------------------------------------------- konfiguracja

/**
 * Konfiguracja leży POZA katalogiem serwowanym przez WWW
 * (public_html/autoinstalator/fw-konfiguracja.php), bo domena wskazuje
 * na public_html/autoinstalator/joomla. Wariant obok API jest awaryjny —
 * wtedy chroni go tylko reguła w api/.htaccess.
 */
function fw_konfiguracja(): array
{
    static $cfg = null;
    if ($cfg !== null) {
        return $cfg;
    }
    foreach ([__DIR__ . '/../../fw-konfiguracja.php', __DIR__ . '/konfiguracja.php'] as $sciezka) {
        if (is_file($sciezka)) {
            $cfg = require $sciezka;
            if (!is_array($cfg)) {
                fw_blad(500, 'Plik konfiguracyjny nie zwraca tablicy.');
            }
            return $cfg;
        }
    }
    fw_blad(500, 'Brak pliku konfiguracyjnego API.');
}

function fw_baza(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }
    $c = fw_konfiguracja();
    $dsn = sprintf(
        'mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4',
        $c['db_host'] ?? 'localhost',
        (int) ($c['db_port'] ?? 3306),
        $c['db_nazwa'] ?? ''
    );
    try {
        $pdo = new PDO($dsn, (string) ($c['db_uzytkownik'] ?? ''), (string) ($c['db_haslo'] ?? ''), [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            // Prawdziwe zapytania parametryzowane po stronie MySQL, bez emulacji.
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]);
    } catch (PDOException $e) {
        error_log('FW API — połączenie z bazą: ' . $e->getMessage());
        fw_blad(500, 'Baza danych jest chwilowo niedostępna.');
    }
    return $pdo;
}

/** Prefiks tabel — pozwala postawić API obok innej instalacji w tej samej bazie. */
function fw_tabela(string $nazwa): string
{
    $prefiks = (string) (fw_konfiguracja()['prefiks'] ?? 'fw_');
    if (!preg_match('/^[a-z0-9_]{0,16}$/', $prefiks)) {
        fw_blad(500, 'Niepoprawny prefiks tabel w konfiguracji.');
    }
    return $prefiks . $nazwa;
}

/**
 * Zakłada tabelę wpisów blogowych, jeśli jej jeszcze nie ma.
 *
 * Hosting nie daje shella ani MySQL z zewnątrz — schemat wgrywa się przez
 * phpMyAdmin, ręcznie. Ta tabela dochodzi później niż reszta, więc zamiast
 * wymagać kolejnej ręcznej operacji, tworzy się sama przy pierwszym użyciu.
 * Zapytanie jest idempotentne, a wołają je wyłącznie miejsca uwierzytelnione:
 * panel administratora i agent z własnym tokenem.
 */
function fw_zapewnij_tabele_wpisow(): void
{
    static $gotowe = false;
    if ($gotowe) {
        return;
    }
    fw_baza()->exec(
        'CREATE TABLE IF NOT EXISTS ' . fw_tabela('wpisy') . ' ('
        . ' id             INT UNSIGNED NOT NULL AUTO_INCREMENT,'
        . ' slug           VARCHAR(190) NOT NULL,'
        . ' tytul          VARCHAR(255) NOT NULL,'
        // `lead` to słowo zarezerwowane w MySQL 8 (funkcja okna LEAD), więc
        // wszędzie musi chodzić w odwrotnych apostrofach — bez nich zapytanie
        // wywala się na błędzie składni, a końcówka zwraca puste HTTP 500.
        . ' `lead`         TEXT         NOT NULL,'
        . ' url            VARCHAR(255) NOT NULL,'
        . ' status         ENUM("oczekuje","opublikowany","odrzucony") NOT NULL DEFAULT "oczekuje",'
        . ' utworzony      DATETIME     NOT NULL,'
        . ' rozstrzygniety DATETIME     NULL,'
        . ' rozstrzygnal   INT UNSIGNED NULL,'
        . ' run_url        VARCHAR(255) NULL,'
        . ' PRIMARY KEY (id),'
        . ' UNIQUE KEY idx_slug (slug),'
        . ' KEY idx_kolejka (status, utworzony)'
        . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
    );

    // CREATE TABLE IF NOT EXISTS nie rusza tabeli, ktora juz istnieje, wiec
    // kolumny dokladane pozniej trzeba dolozyc osobno. Kolejnosc jest wazna:
    // najpierw pytamy o kolumne, potem ALTER — inaczej kazde zadanie probowaloby
    // zmienic schemat i lapalo wyjatek na produkcji.
    $ma = fw_baza()->query('SHOW COLUMNS FROM ' . fw_tabela('wpisy') . " LIKE 'notatka'");
    if ($ma->fetch() === false) {
        fw_baza()->exec('ALTER TABLE ' . fw_tabela('wpisy') . ' ADD COLUMN notatka TEXT NULL');
    }

    $gotowe = true;
}

// ------------------------------------------------------------------ odpowiedzi

function fw_odpowiedz(array $dane, int $kod = 200): never
{
    http_response_code($kod);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($dane, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function fw_blad(int $kod, string $komunikat): never
{
    fw_odpowiedz(['ok' => false, 'blad' => $komunikat], $kod);
}

// ------------------------------------------------------------------- wejście

/** Treść żądania: JSON albo zwykły formularz. Zawsze tablica. */
function fw_wejscie(): array
{
    static $dane = null;
    if ($dane !== null) {
        return $dane;
    }
    $typ = (string) ($_SERVER['CONTENT_TYPE'] ?? '');
    if (stripos($typ, 'application/json') !== false) {
        $surowe = file_get_contents('php://input') ?: '';
        $rozkodowane = json_decode($surowe, true);
        $dane = is_array($rozkodowane) ? $rozkodowane : [];
    } else {
        $dane = $_POST;
    }
    return $dane;
}

function fw_pole(string $nazwa, string $domyslne = ''): string
{
    $v = fw_wejscie()[$nazwa] ?? $domyslne;
    if (!is_scalar($v)) {
        return $domyslne;
    }
    // Znaki sterujące (poza tabulatorem i nową linią) nie mają tu czego szukać.
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', (string) $v) ?? '';
    return trim($v);
}

function fw_akcja(): string
{
    $a = $_GET['akcja'] ?? fw_wejscie()['akcja'] ?? '';
    return is_string($a) ? $a : '';
}

function fw_metoda(): string
{
    return strtoupper((string) ($_SERVER['REQUEST_METHOD'] ?? 'GET'));
}

function fw_wymagaj_post(): void
{
    if (fw_metoda() !== 'POST') {
        fw_blad(405, 'Ta operacja wymaga metody POST.');
    }
}

function fw_ip(): string
{
    $ip = (string) ($_SERVER['REMOTE_ADDR'] ?? '0.0.0.0');
    return substr($ip, 0, 45);
}

function fw_teraz(): string
{
    return (new DateTimeImmutable('now'))->format('Y-m-d H:i:s');
}

// ----------------------------------------------------------- ciasteczka, CSRF

function fw_ustaw_cookie(string $nazwa, string $wartosc, int $wygasa, bool $httponly): void
{
    setcookie($nazwa, $wartosc, [
        'expires'  => $wygasa,
        'path'     => '/',
        'secure'   => true,   // serwis chodzi wyłącznie po HTTPS (wymuszone w .htaccess)
        'httponly' => $httponly,
        'samesite' => 'Lax',
    ]);
}

/**
 * Ochrona CSRF metodą podwójnego wysłania: token siedzi w zwykłym ciasteczku
 * i musi zostać powtórzony w nagłówku X-FW-CSRF. Obca strona nie odczyta
 * ciasteczka z fwdrucik.pl, więc nagłówka nie podrobi.
 */
function fw_token_csrf(): string
{
    $token = (string) ($_COOKIE[FW_CSRF_COOKIE] ?? '');
    if (!preg_match('/^[a-f0-9]{64}$/', $token)) {
        $token = bin2hex(random_bytes(32));
        fw_ustaw_cookie(FW_CSRF_COOKIE, $token, time() + 86400 * FW_SESJA_DNI, false);
    }
    return $token;
}

function fw_sprawdz_csrf(): void
{
    $z_ciastka = (string) ($_COOKIE[FW_CSRF_COOKIE] ?? '');
    $z_naglowka = (string) ($_SERVER['HTTP_X_FW_CSRF'] ?? '');
    if ($z_ciastka === '' || $z_naglowka === '' || !hash_equals($z_ciastka, $z_naglowka)) {
        fw_blad(403, 'Sesja wygasła lub żądanie przyszło z obcej strony. Odśwież stronę.');
    }
}

// -------------------------------------------------------------------- sesje

function fw_zaloz_sesje(int $uzytkownik_id): void
{
    $token = bin2hex(random_bytes(32));
    $wygasa = (new DateTimeImmutable('+' . FW_SESJA_DNI . ' days'))->format('Y-m-d H:i:s');
    $sql = 'INSERT INTO ' . fw_tabela('sesje')
         . ' (token_hash, uzytkownik_id, utworzona, wygasa, ip, przegladarka)'
         . ' VALUES (?, ?, ?, ?, ?, ?)';
    fw_baza()->prepare($sql)->execute([
        hash('sha256', $token),
        $uzytkownik_id,
        fw_teraz(),
        $wygasa,
        fw_ip(),
        substr((string) ($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 255),
    ]);
    fw_ustaw_cookie(FW_SESJA_COOKIE, $token, time() + 86400 * FW_SESJA_DNI, true);
    fw_token_csrf();
}

function fw_zamknij_sesje(): void
{
    $token = (string) ($_COOKIE[FW_SESJA_COOKIE] ?? '');
    if ($token !== '') {
        $sql = 'DELETE FROM ' . fw_tabela('sesje') . ' WHERE token_hash = ?';
        fw_baza()->prepare($sql)->execute([hash('sha256', $token)]);
    }
    fw_ustaw_cookie(FW_SESJA_COOKIE, '', time() - 3600, true);
}

/** Zwraca zalogowanego użytkownika albo null. Wynik liczony raz na żądanie. */
function fw_uzytkownik(): ?array
{
    static $u = false;
    if ($u !== false) {
        return $u;
    }
    $u = null;
    $token = (string) ($_COOKIE[FW_SESJA_COOKIE] ?? '');
    if (preg_match('/^[a-f0-9]{64}$/', $token)) {
        $sql = 'SELECT u.id, u.nick, u.email, u.rola, u.zaufany, u.zablokowany'
             . ' FROM ' . fw_tabela('sesje') . ' s'
             . ' JOIN ' . fw_tabela('uzytkownicy') . ' u ON u.id = s.uzytkownik_id'
             . ' WHERE s.token_hash = ? AND s.wygasa > NOW()';
        $st = fw_baza()->prepare($sql);
        $st->execute([hash('sha256', $token)]);
        $wiersz = $st->fetch();
        if ($wiersz && (int) $wiersz['zablokowany'] === 0) {
            $wiersz['id'] = (int) $wiersz['id'];
            $wiersz['zaufany'] = (int) $wiersz['zaufany'] === 1;
            $u = $wiersz;
        }
    }
    return $u;
}

function fw_wymagaj_logowania(): array
{
    $u = fw_uzytkownik();
    if ($u === null) {
        fw_blad(401, 'Zaloguj się, aby wykonać tę operację.');
    }
    return $u;
}

function fw_wymagaj_admina(): array
{
    $u = fw_wymagaj_logowania();
    if ($u['rola'] !== 'admin') {
        fw_blad(403, 'Ta sekcja jest dostępna wyłącznie dla administratora.');
    }
    return $u;
}

/**
 * Wymaga uprawnień administratora (sesja webowa) LUB poprawnego tokenu agenta
 * przekazanego w nagłówku (X-Agent-Token, X-FW-Token) albo polu 'token'.
 *
 * @param bool $wymagajCsrf Jeśli sesja webowa admina i metoda POST, weryfikuje CSRF.
 * @return array ['typ' => 'admin'|'agent', 'uzytkownik' => ?array]
 */
function fw_wymagaj_admina_lub_tokenu(bool $wymagajCsrf = true): array
{
    $u = fw_uzytkownik();
    if ($u !== null && ($u['rola'] ?? '') === 'admin') {
        if ($wymagajCsrf && fw_metoda() === 'POST') {
            fw_sprawdz_csrf();
        }
        return ['typ' => 'admin', 'uzytkownik' => $u];
    }

    $oczekiwany = (string) (fw_konfiguracja()['agent_token'] ?? '');
    $podany = (string) ($_SERVER['HTTP_X_AGENT_TOKEN'] ?? ($_SERVER['HTTP_X_FW_TOKEN'] ?? fw_pole('token')));
    if ($oczekiwany !== '' && hash_equals($oczekiwany, $podany)) {
        return ['typ' => 'agent', 'uzytkownik' => null];
    }

    fw_blad(403, 'Wymagane uprawnienia administratora lub poprawny token autoryzacyjny.');
}

/** Wymaga poprawnego tokenu agenta (X-Agent-Token) — bez furtki sesji admina. */
function fw_wymagaj_tokenu_agenta(): void
{
    $oczekiwany = (string) (fw_konfiguracja()['agent_token'] ?? '');
    $podany = (string) ($_SERVER['HTTP_X_AGENT_TOKEN'] ?? '');
    if ($oczekiwany === '' || !hash_equals($oczekiwany, $podany)) {
        fw_blad(403, 'Brak dostępu.');
    }
}


/** Status, z jakim ma powstać nowa treść danego użytkownika. */
function fw_status_dla(array $u): string
{
    return ($u['rola'] === 'admin' || $u['zaufany']) ? 'opublikowany' : 'oczekuje';
}

// --------------------------------------------------------------- limit tempa

/**
 * Prosty licznik zdarzeń per IP w oknie czasowym. Zapisuje bieżącą próbę,
 * więc trzeba go wywołać dokładnie raz na obsługiwane żądanie.
 */
function fw_limit(string $akcja, int $ile, int $sekund): void
{
    $pdo = fw_baza();
    $tab = fw_tabela('limity');

    // Sprzątanie starych śladów — bez tego tabela rosłaby w nieskończoność.
    if (random_int(1, 50) === 1) {
        $pdo->exec('DELETE FROM ' . $tab . ' WHERE kiedy < (NOW() - INTERVAL 1 DAY)');
    }

    // $sekund jest liczbą całkowitą podawaną w kodzie, nigdy przez użytkownika —
    // wstawiona wprost, bo MySQL nie przyjmuje parametru w wyrażeniu INTERVAL.
    $sekund = max(1, $sekund);
    $st = $pdo->prepare(
        'SELECT COUNT(*) FROM ' . $tab
        . ' WHERE ip = ? AND akcja = ? AND kiedy > (NOW() - INTERVAL ' . $sekund . ' SECOND)'
    );
    $st->execute([fw_ip(), $akcja]);
    if ((int) $st->fetchColumn() >= $ile) {
        fw_blad(429, 'Za dużo prób w krótkim czasie. Spróbuj ponownie za kilka minut.');
    }

    $pdo->prepare('INSERT INTO ' . $tab . ' (ip, akcja, kiedy) VALUES (?, ?, ?)')
        ->execute([fw_ip(), $akcja, fw_teraz()]);
}

// ---------------------------------------------------------------- walidacja

/** Sprawdza długość tekstu w znakach (nie bajtach) i zwraca go bez zmian. */
function fw_tekst(string $wartosc, string $etykieta, int $min, int $max): string
{
    $dl = mb_strlen($wartosc, 'UTF-8');
    if ($dl < $min) {
        fw_blad(422, sprintf('%s: wymagane co najmniej %d znaków.', $etykieta, $min));
    }
    if ($dl > $max) {
        fw_blad(422, sprintf('%s: dopuszczalne maksymalnie %d znaków.', $etykieta, $max));
    }
    return $wartosc;
}

/** Wartosc php.ini w skrocie ("8M", "1G") na bajty. 0/"" = bez limitu. */
function fw_ini_bajty(string $ini): int
{
    $ini = trim($ini);
    if ($ini === '') {
        return 0;
    }
    $mnoznik = ['k' => 1024, 'm' => 1048576, 'g' => 1073741824][strtolower(substr($ini, -1))] ?? 1;
    return (int) $ini * $mnoznik;
}

/**
 * Sprawdza, czy upload pod $pole przeszedl, zanim zaczniemy go czytac.
 *
 * Gdy plik przekroczy `post_max_size`, PHP nie wypelnia w ogole $_FILES ani
 * $_POST — bez tego sprawdzenia lecialby mylacy "brak identyfikatora
 * produktu" zamiast prawdziwej przyczyny (za duzy plik).
 */
function fw_wymagaj_uploadu(string $pole, int $limitB): void
{
    $limitIni = min(array_filter([fw_ini_bajty(ini_get('upload_max_filesize') ?: ''),
        fw_ini_bajty(ini_get('post_max_size') ?: '')]) ?: [$limitB]);
    $efektywny = max(1, min($limitB, $limitIni));

    if (!isset($_FILES[$pole]) && empty($_POST) && (int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > 0) {
        fw_blad(422, 'Plik przekracza limit serwera (' . (int) ($efektywny / 1048576) . ' MB).');
    }
    $blad = $_FILES[$pole]['error'] ?? UPLOAD_ERR_NO_FILE;
    if ($blad === UPLOAD_ERR_INI_SIZE || $blad === UPLOAD_ERR_FORM_SIZE) {
        fw_blad(422, 'Plik przekracza limit serwera (' . (int) ($efektywny / 1048576) . ' MB).');
    }
    if ($blad !== UPLOAD_ERR_OK) {
        fw_blad(422, 'Nie udało się odebrać pliku. Sprawdź jego rozmiar.');
    }
}

function fw_id(string $nazwa): int
{
    $v = $_GET[$nazwa] ?? fw_wejscie()[$nazwa] ?? 0;
    $id = filter_var($v, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
    if ($id === false) {
        fw_blad(422, 'Brak poprawnego identyfikatora.');
    }
    return $id;
}

/** Kategorie forum — kafelki i działy na /forum/. */
function fw_kategoria(string $wartosc): string
{
    $dozwolone = [
        'regulamin',
        'witam',
        'faq',
        'poczekalnia',
        'general',
        'instrukcje',
        'ksiazkiserwisowe',
        'elektro',
        'spawanie',
        'klimatyzacja'
    ];
    if (!in_array($wartosc, $dozwolone, true)) {
        fw_blad(422, 'Nieznana kategoria wątku.');
    }
    return $wartosc;
}

/**
 * Wersja tytulu nadajaca sie do adresu — bez znakow diakrytycznych,
 * same male litery i myslniki. Uzywaja jej strona watku i mapa forum,
 * wiec musi dawac ten sam wynik w obu miejscach.
 */
function fw_slug_tytulu(string $tytul): string
{
    $z = ['ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż'];
    $na = ['a', 'c', 'e', 'l', 'n', 'o', 's', 'z', 'z'];
    $s = str_replace($z, $na, mb_strtolower($tytul, 'UTF-8'));
    $s = preg_replace('/[^a-z0-9]+/', '-', $s) ?? '';
    return trim($s, '-');
}

/** Slug wpisu blogowego z adresu /blog/<slug>/. */
function fw_slug(string $wartosc): string
{
    if (!preg_match('/^[a-z0-9]([a-z0-9-]{1,118})[a-z0-9]$/', $wartosc)) {
        fw_blad(422, 'Niepoprawny identyfikator wpisu.');
    }
    return $wartosc;
}

/** Publiczna postać użytkownika — bez e-maila i bez skrótu hasła. */
function fw_publiczny_uzytkownik(array $u): array
{
    return [
        'id'      => (int) $u['id'],
        'nick'    => $u['nick'],
        'rola'    => $u['rola'],
        'zaufany' => (bool) $u['zaufany'],
        // Front musi wiedziec, czy pokazac prosbe o potwierdzenie adresu.
        // Kolumna dochodzi pozniej niz reszta tabeli, wiec moze jej nie byc —
        // brak kolumny traktujemy jak konto sprzed wprowadzenia potwierdzania.
        'email_potwierdzony' => (bool) ($u['email_potwierdzony'] ?? 1),
    ];
}
