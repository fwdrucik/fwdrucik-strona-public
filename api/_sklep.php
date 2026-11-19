<?php
declare(strict_types=1);
require_once __DIR__ . '/_sklep_security.php';

/**
 * Wspólna warstwa sklepu: tabele, stałe i odczyt katalogu.
 *
 * Korzystają z niej dwa miejsca: końcówka `api/sklep.php` (obsługa panelu
 * i zamówień) oraz strony `sklep/index.php` i `sklep/produkt.php` renderowane
 * po stronie serwera. Bez tego pliku definicje dostawy, statusów i odczytu
 * produktów istniałyby w dwóch kopiach, które prędzej czy później by się
 * rozjechały.
 */

if (basename((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === '_sklep.php') {
    http_response_code(404);
    exit;
}

const FW_STATUSY_PRODUKTU = ['szkic', 'opublikowany', 'ukryty'];
const FW_STATUSY_ZAMOWIENIA = ['nowe', 'oplacone', 'w_realizacji', 'wyslane', 'zakonczone', 'anulowane'];

// Dostawa. Kwoty w groszach — do zmiany w jednym miejscu.
const FW_DOSTAWA = [
    'odbior'    => ['nazwa' => 'Odbiór osobisty w warsztacie (Domosław 13A)', 'cena_gr' => 0],
    'kurier'    => ['nazwa' => 'Kurier', 'cena_gr' => 2500],
    'paczkomat' => ['nazwa' => 'Paczkomat InPost', 'cena_gr' => 1699],
];

/**
 * Sposoby zapłaty dostępne dla klienta.
 *
 * BLIK, Google Pay i karta wymagają umowy z operatorem płatności i kluczy
 * w konfiguracji serwera. Dopóki ich nie ma, lista zawiera wyłącznie sposoby,
 * które działają bez pośrednika — patrz api/PLATNOSCI.md.
 */
function fw_platnosci(): array
{
    $cfg = fw_konfiguracja();
    $lista = [
        'przelew'       => 'Przelew tradycyjny na konto',
        'przy_odbiorze' => 'Gotówka lub karta przy odbiorze w warsztacie',
    ];
    if (!empty($cfg['p24_merchant_id']) || !empty($cfg['payu_pos_id']) || !empty($cfg['tpay_id'])) {
        $lista = ['online' => 'Płatność online — BLIK, Google Pay, karta'] + $lista;
    }
    return $lista;
}

const FW_KATALOG_OBRAZOW = __DIR__ . '/../assets/sklep';
const FW_MAX_OBRAZ_B = 6291456; // 6 MB
/**
 * Adres bazowy serwisu WWW (wykorzystuje stałą FW_SITE, jeśli została zdefiniowana).
 */
function fw_adres_strony(): string
{
    return defined('FW_SITE') ? FW_SITE : 'https://fwdrucik.pl';
}

/**
 * Bezwzględny adres bazowy katalogu ze zdjęciami sklepu lub pełny adres pliku (dla zewnętrznych API, np. Allegro).
 */
function fw_adres_zdjec(string $plik = ''): string
{
    $prefiks = fw_adres_strony() . '/assets/sklep/';
    return $plik !== '' ? $prefiks . ltrim($plik, '/') : $prefiks;
}

/**
 * Czy sklep jest otwarty dla wszystkich.
 *
 * Na czas budowy katalogu sklep widzi wyłącznie administrator; pozostali
 * dostają stronę z informacją o przebudowie. Przełącznik siedzi w konfiguracji
 * serwera (`sklep_otwarty`), żeby otwarcie sklepu nie wymagało wdrożenia kodu.
 */
function fw_sklep_otwarty(): bool
{
    return !empty(fw_konfiguracja()['sklep_otwarty']);
}

/** Czy bieżący użytkownik może oglądać sklep mimo przebudowy. */
function fw_sklep_dostepny_dla_mnie(): bool
{
    if (fw_sklep_otwarty()) {
        return true;
    }
    $u = fw_uzytkownik();
    return $u !== null && $u['rola'] === 'admin';
}

function fw_zapewnij_tabele_sklepu(): void
{
    static $gotowe = false;
    if ($gotowe) {
        return;
    }
    $pdo = fw_baza();

    $pdo->exec(
        'CREATE TABLE IF NOT EXISTS ' . fw_tabela('produkty') . ' ('
        . ' id            INT UNSIGNED NOT NULL AUTO_INCREMENT,'
        . ' slug          VARCHAR(190) NOT NULL,'
        . ' nazwa         VARCHAR(190) NOT NULL,'
        . ' kategoria     VARCHAR(40)  NOT NULL DEFAULT "inne",'
        . ' opis_krotki   VARCHAR(400) NOT NULL DEFAULT "",'
        . ' opis          MEDIUMTEXT   NOT NULL,'
        . ' cena_gr       INT UNSIGNED NOT NULL DEFAULT 0,'
        . ' cena_promo_gr INT UNSIGNED NULL,'
        // NULL w `stan` znaczy "wykonywane na zamowienie" — inaczej niz 0,
        // ktore znaczy "chwilowo nie ma".
        . ' stan          INT          NULL,'
        . ' waga_g        INT UNSIGNED NOT NULL DEFAULT 0,'
        . ' jednostka     VARCHAR(20)  NOT NULL DEFAULT "szt.",'
        . ' czas_realizacji VARCHAR(80) NOT NULL DEFAULT "",'
        . ' status        ENUM("szkic","opublikowany","ukryty") NOT NULL DEFAULT "szkic",'
        . ' pozycja       INT          NOT NULL DEFAULT 100,'
        . ' utworzony     DATETIME     NOT NULL,'
        . ' zmieniony     DATETIME     NOT NULL,'
        . ' allegro_id    VARCHAR(40)  NULL,'
        . ' allegro_url   VARCHAR(255) NULL,'
        . ' allegro_kategoria VARCHAR(60) NULL,'
        . ' allegro_cena_gr INT UNSIGNED NULL,'
        . ' allegro_status ENUM("brak","kolejka","szkic","wystaw","aktywna","zakonczona","blad") NOT NULL DEFAULT "brak",'
        . ' allegro_blad   TEXT NULL,'
        . ' allegro_parametry MEDIUMTEXT NULL,'
        . ' PRIMARY KEY (id),'
        . ' UNIQUE KEY uniq_slug (slug),'
        . ' KEY idx_lista (status, pozycja, id)'
        . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
    );

    $pdo->exec(
        'CREATE TABLE IF NOT EXISTS ' . fw_tabela('produkty_obrazy') . ' ('
        . ' id         INT UNSIGNED NOT NULL AUTO_INCREMENT,'
        . ' produkt_id INT UNSIGNED NOT NULL,'
        . ' plik       VARCHAR(190) NOT NULL,'
        . ' alt        VARCHAR(190) NOT NULL DEFAULT "",'
        . ' szerokosc  INT UNSIGNED NOT NULL DEFAULT 0,'
        . ' wysokosc   INT UNSIGNED NOT NULL DEFAULT 0,'
        . ' pozycja    INT          NOT NULL DEFAULT 100,'
        . ' PRIMARY KEY (id),'
        . ' KEY idx_produkt (produkt_id, pozycja),'
        . ' CONSTRAINT fk_obraz_produkt FOREIGN KEY (produkt_id)'
        . '   REFERENCES ' . fw_tabela('produkty') . ' (id) ON DELETE CASCADE'
        . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
    );

    $pdo->exec(
        'CREATE TABLE IF NOT EXISTS ' . fw_tabela('adresy') . ' ('
        . ' uzytkownik_id INT UNSIGNED NOT NULL,'
        . ' imie          VARCHAR(80)  NOT NULL DEFAULT "",'
        . ' nazwisko      VARCHAR(80)  NOT NULL DEFAULT "",'
        . ' telefon       VARCHAR(30)  NOT NULL DEFAULT "",'
        . ' ulica         VARCHAR(120) NOT NULL DEFAULT "",'
        . ' nr_domu       VARCHAR(20)  NOT NULL DEFAULT "",'
        . ' nr_lokalu     VARCHAR(20)  NOT NULL DEFAULT "",'
        . ' kod           VARCHAR(10)  NOT NULL DEFAULT "",'
        . ' miasto        VARCHAR(90)  NOT NULL DEFAULT "",'
        . ' firma         VARCHAR(160) NOT NULL DEFAULT "",'
        . ' nip           VARCHAR(20)  NOT NULL DEFAULT "",'
        . ' zmieniony     DATETIME     NOT NULL,'
        . ' PRIMARY KEY (uzytkownik_id),'
        . ' CONSTRAINT fk_adres_uzytkownik FOREIGN KEY (uzytkownik_id)'
        . '   REFERENCES ' . fw_tabela('uzytkownicy') . ' (id) ON DELETE CASCADE'
        . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
    );

    $pdo->exec(
        'CREATE TABLE IF NOT EXISTS ' . fw_tabela('zamowienia') . ' ('
        . ' id             INT UNSIGNED NOT NULL AUTO_INCREMENT,'
        . ' numer          VARCHAR(24)  NOT NULL,'
        . ' uzytkownik_id  INT UNSIGNED NOT NULL,'
        . ' email          VARCHAR(190) NOT NULL,'
        . ' status         ENUM("nowe","oplacone","w_realizacji","wyslane","zakonczone","anulowane")'
        . '                NOT NULL DEFAULT "nowe",'
        . ' towar_gr       INT UNSIGNED NOT NULL DEFAULT 0,'
        . ' dostawa_gr     INT UNSIGNED NOT NULL DEFAULT 0,'
        . ' suma_gr        INT UNSIGNED NOT NULL DEFAULT 0,'
        . ' sposob_dostawy VARCHAR(24)  NOT NULL,'
        . ' sposob_platnosci VARCHAR(24) NOT NULL,'
        . ' adres          TEXT         NOT NULL,'
        . ' uwagi          TEXT         NOT NULL,'
        . ' utworzone      DATETIME     NOT NULL,'
        . ' PRIMARY KEY (id),'
        . ' UNIQUE KEY uniq_numer (numer),'
        . ' KEY idx_uzytkownik (uzytkownik_id, utworzone),'
        . ' KEY idx_status (status, utworzone)'
        . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
    );

    $pdo->exec(
        'CREATE TABLE IF NOT EXISTS ' . fw_tabela('zamowienia_pozycje') . ' ('
        . ' id            INT UNSIGNED NOT NULL AUTO_INCREMENT,'
        . ' zamowienie_id INT UNSIGNED NOT NULL,'
        . ' produkt_id    INT UNSIGNED NULL,'
        // Nazwe i cene zapisujemy w chwili zamowienia. Pozniejsza zmiana ceny
        // w katalogu nie moze zmieniac tego, co klient faktycznie zamowil.
        . ' nazwa         VARCHAR(190) NOT NULL,'
        . ' cena_gr       INT UNSIGNED NOT NULL,'
        . ' ilosc         INT UNSIGNED NOT NULL DEFAULT 1,'
        . ' PRIMARY KEY (id),'
        . ' KEY idx_zamowienie (zamowienie_id),'
        . ' CONSTRAINT fk_pozycja_zamowienie FOREIGN KEY (zamowienie_id)'
        . '   REFERENCES ' . fw_tabela('zamowienia') . ' (id) ON DELETE CASCADE'
        . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
    );

    fw_zapewnij_kolumny_allegro();
    $gotowe = true;
}

/**
 * Automatyczna migracja: sprawdza i dokłada kolumny Allegro do tabeli produktów.
 */
function fw_zapewnij_kolumny_allegro(): void
{
    static $gotowe = false;
    if ($gotowe) {
        return;
    }
    try {
        $pdo = fw_baza();
        $tabela = fw_tabela('produkty');
        // Jedno zapytanie do information_schema zamiast dwoch — nazwy kolumn
        // i typ allegro_status od razu w tym samym wierszu.
        $st = $pdo->prepare('SELECT COLUMN_NAME, COLUMN_TYPE FROM information_schema.COLUMNS'
            . ' WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?');
        $st->execute([$tabela]);
        $kolumny = [];
        $typAllegroStatus = '';
        foreach ($st->fetchAll() as $wiersz) {
            $nazwa = strtolower((string) ($wiersz['COLUMN_NAME'] ?? $wiersz['column_name'] ?? ''));
            if ($nazwa === '') {
                continue;
            }
            $kolumny[] = $nazwa;
            if ($nazwa === 'allegro_status') {
                $typAllegroStatus = (string) ($wiersz['COLUMN_TYPE'] ?? $wiersz['column_type'] ?? '');
            }
        }

        $doDodania = [];
        if (!in_array('allegro_id', $kolumny, true)) {
            $doDodania[] = 'ADD COLUMN allegro_id VARCHAR(40) NULL';
        }
        if (!in_array('allegro_url', $kolumny, true)) {
            $doDodania[] = 'ADD COLUMN allegro_url VARCHAR(255) NULL';
        }
        if (!in_array('allegro_kategoria', $kolumny, true)) {
            $doDodania[] = 'ADD COLUMN allegro_kategoria VARCHAR(60) NULL';
        }
        if (!in_array('allegro_cena_gr', $kolumny, true)) {
            $doDodania[] = 'ADD COLUMN allegro_cena_gr INT UNSIGNED NULL';
        }
        if (!in_array('allegro_status', $kolumny, true)) {
            $doDodania[] = 'ADD COLUMN allegro_status ENUM("brak","kolejka","szkic","wystaw","aktywna","zakonczona","blad") NOT NULL DEFAULT "brak"';
        }
        if (!in_array('allegro_parametry', $kolumny, true)) {
            $doDodania[] = 'ADD COLUMN allegro_parametry MEDIUMTEXT NULL';
        }
        if (!in_array('allegro_blad', $kolumny, true)) {
            $doDodania[] = 'ADD COLUMN allegro_blad TEXT NULL';
        }
        if ($doDodania) {
            $pdo->exec('ALTER TABLE ' . $tabela . ' ' . implode(', ', $doDodania));
        }
        // Rozszerzenie ENUM dla istniejących baz — osobny ALTER, tylko gdy
        // jeszcze go nie ma (idempotentne bez ALTER na każdym żądaniu).
        if (!str_contains($typAllegroStatus, 'kolejka')) {
            $pdo->exec('ALTER TABLE ' . $tabela . ' MODIFY COLUMN allegro_status'
                . ' ENUM("brak","kolejka","szkic","wystaw","aktywna","zakonczona","blad") NOT NULL DEFAULT "brak"');
        }
    } catch (\Throwable $e) {
        error_log('Ostrzeżenie fw_zapewnij_kolumny_allegro: ' . $e->getMessage());
    }
    $gotowe = true;
}

/** Dozwolone statusy kolejki/publikacji Allegro. */
function fw_statusy_allegro(): array
{
    return ['brak', 'kolejka', 'szkic', 'wystaw', 'aktywna', 'zakonczona', 'blad'];
}

/**
 * Przekształca ustandaryzowane sekcje opisu Allegro (standard JSON)
 * na estetyczny, semantyczny HTML zgodny ze stylem warsztatowym fwdrucik.pl.
 */
function fw_parsuj_sekcje_allegro(array $sekcje, ?array $parametry = null, string $tytul = ''): string
{
    $html = '<div class="opis-allegro-kontener">';
    foreach ($sekcje as $sekcja) {
        $items = $sekcja['items'] ?? [];
        if (!is_array($items) || empty($items)) {
            continue;
        }
        $html .= '<div class="opis-allegro-sekcja">';
        foreach ($items as $item) {
            $typ = strtoupper((string) ($item['type'] ?? ''));
            if ($typ === 'TEXT') {
                $tresc = (string) ($item['content'] ?? '');
                $czysta = fw_sklep_opis_html($tresc);
                $html .= '<div class="opis-allegro-tekst">' . $czysta . '</div>';
            } elseif ($typ === 'IMAGE') {
                $url = filter_var((string) ($item['url'] ?? ''), FILTER_VALIDATE_URL);
                if ($url) {
                    $altText = !empty($tytul)
                        ? htmlspecialchars($tytul . ' — detal wykonania warsztatowego F.W. DRUCIK', ENT_QUOTES, 'UTF-8')
                        : 'Rękodzieło i obróbka warsztatowa F.W. DRUCIK — oferta Allegro';
                    $html .= '<div class="opis-allegro-foto"><img src="' . htmlspecialchars($url, ENT_QUOTES, 'UTF-8') . '" alt="' . $altText . '" loading="lazy" /></div>';
                }
            }
        }
        $html .= '</div>';
    }

    if (!empty($parametry) && is_array($parametry)) {
        $html .= '<div class="opis-allegro-parametry">';
        $html .= '<h4 class="allegro-parametry-tytul">Parametry wyrobu z oferty:</h4>';
        $html .= '<table class="allegro-tabela-spec">';
        foreach ($parametry as $nazwa => $wartosc) {
            if (is_scalar($wartosc) && trim((string) $wartosc) !== '') {
                $html .= '<tr><th>' . htmlspecialchars((string) $nazwa, ENT_QUOTES, 'UTF-8') . '</th>';
                $html .= '<td>' . htmlspecialchars((string) $wartosc, ENT_QUOTES, 'UTF-8') . '</td></tr>';
            }
        }
        $html .= '</table>';
        $html .= '</div>';
    }

    $html .= '</div>';
    return $html;
}

/**
 * Nagłówek User-Agent wymagany przez integrację oraz REST API Allegro.
 */
const FW_ALLEGRO_USER_AGENT = 'FWDRUCIK_SKLEP/3.0 (+https://github.com/fwdrucik/FWDrucikSklep#readme)';

/**
 * Pobiera dane aukcji z publicznej strony Allegro lub API.
 * Ekstrahuje tytuł (max 75 zn.), cenę, opis, zdjęcia i ID oferty.
 */
function fw_pobierz_dane_aukcji_allegro(string $url, ?callable $resolve = null, ?callable $fetch = null): ?array
{
    $url = trim($url);
    $options = fw_allegro_import_options($url, $resolve);
    if ($options === null) {
        return null;
    }
    $allegroId = '';
    if (preg_match('/(?:oferta\/[^\/]+-)?(\d{8,15})/i', $url, $m)) {
        $allegroId = $m[1];
    }

    if ($fetch !== null) {
        [$kod, $html] = $fetch($options);
    } else {
        $ch = curl_init();
        $html = '';
        $options[CURLOPT_WRITEFUNCTION] = static function ($handle, string $chunk) use (&$html): int {
            if (strlen($html) + strlen($chunk) > 4194304) { return 0; }
            $html .= $chunk;
            return strlen($chunk);
        };
        curl_setopt_array($ch, $options);
        $ok = curl_exec($ch);
        $kod = $ok === false ? 0 : curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
    }

    if (!$html || $kod !== 200) {
        return null;
    }

    $nazwa = '';
    $cenaGr = 0;
    $opis = '';
    $zdjecia = [];

    if (preg_match('/<script\s+type=["\']application\/ld\+json["\']>(.*?)<\/script>/is', $html, $m)) {
        $ld = json_decode($m[1], true);
        if (is_array($ld)) {
            $nazwa = (string) ($ld['name'] ?? '');
            if (!empty($ld['description'])) {
                $opis = (string) $ld['description'];
            }
            if (!empty($ld['image'])) {
                $zdjecia = is_array($ld['image']) ? $ld['image'] : [$ld['image']];
            }
            if (!empty($ld['offers']['price'])) {
                $cenaGr = (int) round(((float) $ld['offers']['price']) * 100);
            }
        }
    }

    if ($nazwa === '' && preg_match('/<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']/i', $html, $m)) {
        $nazwa = html_entity_decode($m[1], ENT_QUOTES | ENT_HTML5, 'UTF-8');
    }
    if ($opis === '' && preg_match('/<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']/i', $html, $m)) {
        $opis = html_entity_decode($m[1], ENT_QUOTES | ENT_HTML5, 'UTF-8');
    }
    if (empty($zdjecia) && preg_match('/<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']/i', $html, $m)) {
        $zdjecia[] = $m[1];
    }
    if ($cenaGr === 0 && preg_match('/<meta\s+property=["\']product:price:amount["\']\s+content=["\']([^"\']+)["\']/i', $html, $m)) {
        $cenaGr = (int) round(((float) $m[1]) * 100);
    }

    if ($nazwa === '') {
        return null;
    }

    $nazwa = preg_replace('/(?:\s*-\s*Stan:.*|\s*\|\s*Allegro.*)$/iu', '', $nazwa);
    $zakazane = ['/\bHIT\b/iu', '/\bOKAZJA\b/iu', '/\bNOWOŚĆ\b/iu', '/\bNOWOSC\b/iu',
                 '/\bWYPRZEDAŻ\b/iu', '/\bWYPRZEDAZ\b/iu', '/\bPOLECAM\b/iu',
                 '/\bSUPER\b/iu', '/\bCENA\b/iu', '/!+/'];
    $nazwa = preg_replace($zakazane, '', $nazwa);
    $nazwa = preg_replace('/\s{2,}/', ' ', $nazwa);
    $nazwa = trim($nazwa, " -–—:,;!.");
    if (mb_strlen($nazwa, 'UTF-8') > 75) {
        $ciete = mb_substr($nazwa, 0, 75, 'UTF-8');
        $spacja = mb_strrpos($ciete, ' ', 0, 'UTF-8');
        $nazwa = ($spacja !== false && $spacja > 40) ? mb_substr($ciete, 0, $spacja, 'UTF-8') : $ciete;
    }
    $nazwa = trim($nazwa);

    return [
        'allegro_url' => $url,
        'allegro_id'  => $allegroId,
        'nazwa'       => $nazwa,
        'cena_gr'     => $cenaGr,
        'opis'        => $opis,
        'opis_krotki' => mb_substr(strip_tags($opis), 0, 350, 'UTF-8'),
        'zdjecia'     => $zdjecia,
        'kategoria'   => 'inne',
    ];
}

/**
 * Produkt razem ze zdjęciami — wspólny kształt dla wszystkich odpowiedzi.
 *
 * `$pelneAllegro` odsłania allegro_id/allegro_url niezależnie od statusu —
 * tylko dla panelu admina/agenta (kontrakt pkt 4). Domyślnie (publiczny widok
 * i strony HTML sklepu) te dwa pola wychodzą wyłącznie gdy oferta jest
 * faktycznie aktywna — inaczej link „Kup na Allegro” prowadziłby do szkicu,
 * którego nikt jeszcze nie widzi na Allegro.
 */
function fw_produkt_publiczny(array $p, array $obrazy, bool $pelneAllegro = false): array
{
    $aktywna = ($p['allegro_status'] ?? null) === 'aktywna';
    $odslon = $pelneAllegro || $aktywna;
    $statusAllegroRaw = !empty($p['allegro_status']) ? (string) $p['allegro_status'] : 'brak';
    $allegroStatusPubliczny = $pelneAllegro
        ? $statusAllegroRaw
        : ($statusAllegroRaw === 'aktywna' ? 'aktywna' : 'brak');

    return [
        'id'              => (int) $p['id'],
        'slug'            => $p['slug'],
        'nazwa'           => $p['nazwa'],
        'kategoria'       => $p['kategoria'],
        'opis_krotki'     => $p['opis_krotki'],
        'opis'            => $p['opis'],
        'cena_gr'         => (int) $p['cena_gr'],
        'cena_promo_gr'   => $p['cena_promo_gr'] === null ? null : (int) $p['cena_promo_gr'],
        'stan'            => $p['stan'] === null ? null : (int) $p['stan'],
        'waga_g'          => (int) $p['waga_g'],
        'jednostka'       => $p['jednostka'],
        'czas_realizacji' => $p['czas_realizacji'],
        'status'          => $p['status'],
        'pozycja'         => (int) $p['pozycja'],
        'url'             => '/sklep/' . $p['slug'] . '/',
        'obrazy'          => $obrazy,
        'allegro_id'      => ($odslon && !empty($p['allegro_id'])) ? (string) $p['allegro_id'] : null,
        'allegro_url'     => $odslon ? fw_allegro_url(isset($p['allegro_url']) ? (string) $p['allegro_url'] : null) : null,
        'allegro_kategoria' => !empty($p['allegro_kategoria']) ? (string) $p['allegro_kategoria'] : null,
        'allegro_cena_gr' => isset($p['allegro_cena_gr']) && $p['allegro_cena_gr'] !== null ? (int) $p['allegro_cena_gr'] : null,
        'allegro_status'  => $allegroStatusPubliczny,
    ];
}

/**
 * Pola produktu widoczne wylacznie dla admina/agenta (panel, aplikacja telefonu).
 *
 * `allegro_parametry` to surowe id/wartosci parametrow kategorii Allegro,
 * a `allegro_blad` bywa tresc bledu z Allegro API (moze zawierac nazwy
 * parametrow czy fragmenty configu) — zaden z dwoch nie powinien wyciekac
 * do anonimowego `akcja=produkt`/`akcja=produkty`.
 */
function fw_produkt_dodatki_admina(array $p): array
{
    return [
        'allegro_parametry' => !empty($p['allegro_parametry']) ? (string) $p['allegro_parametry'] : null,
        'allegro_blad'      => $p['allegro_blad'] ?? null,
    ];
}

/** Zdjęcia pogrupowane po produktach — jedno zapytanie zamiast N. */
function fw_obrazy_dla(array $idki): array
{
    if (!$idki) {
        return [];
    }
    $znaki = implode(',', array_fill(0, count($idki), '?'));
    $wynik = [];
    try {
        $st = fw_baza()->prepare('SELECT id, produkt_id, plik, alt, szerokosc, wysokosc'
            . ' FROM ' . fw_tabela('produkty_obrazy')
            . ' WHERE produkt_id IN (' . $znaki . ') ORDER BY id ASC');
        $st->execute($idki);
        foreach ($st->fetchAll() as $o) {
            $pid = (int) $o['produkt_id'];
            if (!isset($wynik[$pid])) {
                $wynik[$pid] = [];
            }
            $plik = (string) $o['plik'];
            if (preg_match('#^https?://#i', $plik)) {
                $prefiksZdjec = fw_adres_zdjec();
                if (strpos($plik, $prefiksZdjec) === 0) {
                    $src = substr($plik, strlen(fw_adres_strony()));
                } else {
                    $src = $plik;
                }
            } elseif (strpos($plik, '/') === 0) {
                $src = $plik;
            } else {
                $src = '/assets/sklep/' . $plik;
            }
            $wynik[$pid][] = [
                'id'        => (int) $o['id'],
                'src'       => $src,
                'alt'       => $o['alt'],
                'szerokosc' => (int) $o['szerokosc'],
                'wysokosc'  => (int) $o['wysokosc'],
            ];
        }
    } catch (Throwable $e) {}

    // Dołączamy animacje (GIF) z tabeli produktów_pliki jako obrazy o priorytecie pozycja=0,
    // jeśli istnieją — dzięki temu na liście produktów od razu wyświetla się ruchomy GIF.
    try {
        $stPliki = fw_baza()->prepare('SELECT id, produkt_id, plik, opis, rodzaj'
            . ' FROM ' . fw_tabela('produkty_pliki')
            . ' WHERE produkt_id IN (' . $znaki . ') AND rodzaj = "animacja"'
            . ' ORDER BY id ASC');
        $stPliki->execute($idki);
        foreach ($stPliki->fetchAll() as $pf) {
            $pid = (int) $pf['produkt_id'];
            if (!isset($wynik[$pid])) {
                $wynik[$pid] = [];
            }
            array_unshift($wynik[$pid], [
                // MINUS NIE JEST OZDOBNIKIEM. To jest identyfikator z INNEJ
                // tabeli (produkty_pliki), a obie numeracje zaczynaja sie od 1 —
                // animacja nr 1 i zdjecie nr 1 trafialy do jednej listy z tym
                // samym kluczem. Aplikacja na telefonie wywalala sie wtedy
                // natychmiast przy wejsciu w edycje produktu:
                // „Key 1 was already used" z LazyRow.
                //
                // Ujemna liczba daje osobna przestrzen bez zmiany ksztaltu
                // odpowiedzi i od razu mowi klientowi, ze to nie jest zwykle
                // zdjecie: usuwa sie je przez plik-usun, nie obraz-usun.
                'id'        => -1 * (int) $pf['id'],
                'src'       => '/assets/sklep/' . $pf['plik'],
                'alt'       => (string) $pf['opis'],
                'szerokosc' => 0,
                'wysokosc'  => 0,
            ]);
        }
    } catch (Throwable $e) {}
    return $wynik;
}

/**
 * Dokłada kolumny, których nie było w pierwszej wersji tabeli zamówień.
 *
 * Tak samo jak przy potwierdzaniu e-maila w `auth.php`: sprawdzamy
 * `information_schema` i dokładamy brakujące, żeby nikt nie musiał wchodzić
 * do phpMyAdmina po wgraniu nowej wersji sklepu.
 */
function fw_zapewnij_kolumny_zamowien(): void
{
    static $gotowe = false;
    if ($gotowe) {
        return;
    }
    $pdo = fw_baza();
    $tabela = fw_tabela('zamowienia');
    $st = $pdo->prepare('SELECT COLUMN_NAME FROM information_schema.COLUMNS'
        . ' WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?');
    $st->execute([$tabela]);
    $kolumny = array_column($st->fetchAll(), 'COLUMN_NAME');

    $doDodania = [];
    if (!in_array('przesylka', $kolumny, true)) {
        // Numer listu przewozowego. Pierwsza rzecz, o ktora pyta klient,
        // gdy zamowienie zmieni status na „wyslane".
        $doDodania[] = 'ADD COLUMN przesylka VARCHAR(64) NOT NULL DEFAULT ""';
    }
    if (!in_array('zgoda', $kolumny, true)) {
        // KIEDY klient zaakceptowal regulamin i pouczenie o odstapieniu.
        // Sam „haczyk" w formularzu nie jest dowodem — dowodem jest zapis
        // po stronie sklepu, razem z zamowieniem.
        $doDodania[] = 'ADD COLUMN zgoda DATETIME NULL';
    }
    if (!in_array('gosc', $kolumny, true)) {
        // Zamowienie zlozone bez konta. `uzytkownik_id` jest wtedy zerem,
        // ale zero to tez „brak danych", wiec trzymamy to wprost.
        $doDodania[] = 'ADD COLUMN gosc TINYINT NOT NULL DEFAULT 0';
    }
    if ($doDodania) {
        $pdo->exec('ALTER TABLE ' . $tabela . ' ' . implode(', ', $doDodania));
    }
    $gotowe = true;
}

/**
 * Rysunek kategorii dla produktu bez zdjęcia.
 *
 * Celowo ilustracja, a nie zdjęcie z banku: zdjęcie sugerowałoby konkretny
 * egzemplarz, a przy wyrobach ręcznych każdy wygląda inaczej. Rysunek mówi
 * "taka robota", nie "ta sztuka" — i nikogo nie wprowadza w błąd.
 */
function fw_ilustracja_kategorii(string $kategoria): string
{
    $mapa = [
        'zywica'    => 'kat-zywica',
        'druk3d'    => 'kat-druk3d',
        'spawanie'  => 'kat-spawanie',
        'cnc'       => 'kat-cnc',
    ];
    return $mapa[$kategoria] ?? 'kat-inne';
}

/** Cena obowiązująca: promocyjna, jeśli ustawiona. */
function fw_cena_obowiazujaca(array $p): int
{
    return $p['cena_promo_gr'] !== null ? (int) $p['cena_promo_gr'] : (int) $p['cena_gr'];
}

/**
 * Dane dostawy do schema.org — koszt i czas, tak jak je widzi klient.
 *
 * Google wyświetla je obok ceny w wynikach wyszukiwania. Bierzemy najtańszą
 * płatną wysyłkę (paczkomat), bo odbiór osobisty za 0 zł nie dotyczy nikogo,
 * kto szuka produktu przez wyszukiwarkę i mieszka poza gminą.
 *
 * Wyroby na zamówienie (`stan === null`) mają dłuższy czas przygotowania —
 * podanie tu 1–2 dni byłoby obietnicą, której warsztat nie dotrzyma.
 */
function fw_dostawa_ld(array $p): array
{
    $naZamowienie = ($p['stan'] ?? null) === null;
    $cena = min(FW_DOSTAWA['kurier']['cena_gr'], FW_DOSTAWA['paczkomat']['cena_gr']);
    return [
        '@type' => 'OfferShippingDetails',
        'shippingRate' => [
            '@type' => 'MonetaryAmount',
            'value' => number_format($cena / 100, 2, '.', ''),
            'currency' => 'PLN',
        ],
        'shippingDestination' => [
            '@type' => 'DefinedRegion',
            'addressCountry' => 'PL',
        ],
        'deliveryTime' => [
            '@type' => 'ShippingDeliveryTime',
            'handlingTime' => [
                '@type' => 'QuantitativeValue',
                'minValue' => $naZamowienie ? 7 : 1,
                'maxValue' => $naZamowienie ? 35 : 3,
                'unitCode' => 'DAY',
            ],
            'transitTime' => [
                '@type' => 'QuantitativeValue',
                'minValue' => 1, 'maxValue' => 3, 'unitCode' => 'DAY',
            ],
        ],
    ];
}

/**
 * Zasady zwrotu do schema.org.
 *
 * Uwaga prawna: prawo odstąpienia od umowy w 14 dni NIE obejmuje rzeczy
 * wykonanych według specyfikacji klienta (art. 38 pkt 3 ustawy o prawach
 * konsumenta) — a takie są wszystkie wyroby z `stan === null`. Zadeklarowanie
 * tam zwrotów byłoby nieprawdą wobec klienta i błędem w danych dla Google.
 */
function fw_zwroty_ld(array $p): array
{
    if (($p['stan'] ?? null) === null) {
        return [
            '@type' => 'MerchantReturnPolicy',
            'applicableCountry' => 'PL',
            'returnPolicyCategory' => 'https://schema.org/MerchantReturnNotPermitted',
        ];
    }
    return [
        '@type' => 'MerchantReturnPolicy',
        'applicableCountry' => 'PL',
        'returnPolicyCategory' => 'https://schema.org/MerchantReturnFiniteReturnWindow',
        'merchantReturnDays' => 14,
        'returnMethod' => 'https://schema.org/ReturnByMail',
        'returnFees' => 'https://schema.org/ReturnShippingFees',
        'merchantReturnLink' => fw_adres_strony() . '/odstapienie/',
    ];
}

/**
 * Inne wyroby do pokazania pod produktem.
 *
 * Najpierw z tej samej kategorii — ktoś, kto ogląda deskę z żywicy, prędzej
 * kupi drugą deskę niż stelaż spawany. Gdy kategoria ma za mało pozycji,
 * dobieramy resztę z całego katalogu, żeby miejsce nie zostało puste.
 */
function fw_produkty_powiazane(int $pomijId, string $kategoria, int $ile = 3): array
{
    fw_zapewnij_tabele_sklepu();
    $st = fw_baza()->prepare('SELECT * FROM ' . fw_tabela('produkty')
        . ' WHERE status = "opublikowany" AND id <> ?'
        . ' ORDER BY (kategoria = ?) DESC, pozycja ASC, id DESC LIMIT ?');
    $st->bindValue(1, $pomijId, PDO::PARAM_INT);
    $st->bindValue(2, $kategoria, PDO::PARAM_STR);
    $st->bindValue(3, $ile, PDO::PARAM_INT);
    $st->execute();
    $wiersze = $st->fetchAll();
    $obrazy = fw_obrazy_dla(array_map(static fn($p) => (int) $p['id'], $wiersze));
    return array_map(
        static fn(array $p): array => fw_produkt_publiczny($p, $obrazy[(int) $p['id']] ?? []),
        $wiersze
    );
}

/** Opublikowane produkty do wyświetlenia na stronie sklepu. */
function fw_produkty_publiczne(string $kategoria = ''): array
{
    fw_zapewnij_tabele_sklepu();
    $warunki = ['status = "opublikowany"'];
    $parametry = [];
    if ($kategoria !== '' && $kategoria !== 'all') {
        $warunki[] = 'kategoria = ?';
        $parametry[] = $kategoria;
    }
    $st = fw_baza()->prepare('SELECT * FROM ' . fw_tabela('produkty')
        . ' WHERE ' . implode(' AND ', $warunki)
        . ' ORDER BY pozycja ASC, id DESC LIMIT 500');
    $st->execute($parametry);
    $wiersze = $st->fetchAll();
    $obrazy = fw_obrazy_dla(array_map(static fn($p) => (int) $p['id'], $wiersze));
    return array_map(
        static fn(array $p): array => fw_produkt_publiczny($p, $obrazy[(int) $p['id']] ?? []),
        $wiersze
    );
}
