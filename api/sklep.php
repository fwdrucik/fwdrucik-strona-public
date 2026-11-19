<?php
declare(strict_types=1);

// Bledy do dziennika, nigdy na ekran.
//
// PO CO: `display_errors` wlaczone na produkcji wysyla klientowi sciezki na
// dysku, fragmenty zapytan SQL i nazwy tabel razem z trescia bledu. To jest
// gotowa mapa dla kogos, kto szuka sposobu na wejscie. Do diagnozy sluzy log
// serwera, ktory widzi tylko wlasciciel.
ini_set('display_errors', '0');
ini_set('log_errors', '1');
error_reporting(E_ALL);

/**
 * Sklep: katalog produktów, koszyk po stronie serwera i zamówienia.
 *
 * Publiczne:
 *   GET  ?akcja=produkty[&kategoria=]      — lista opublikowanych
 *   GET  ?akcja=produkt&slug=...           — jeden produkt
 *
 * Zalogowany:
 *   GET  ?akcja=profil                     — dane do wysyłki
 *   POST ?akcja=profil-zapisz              — zapis danych do wysyłki
 *   POST ?akcja=zamow                      — złożenie zamówienia
 *   GET  ?akcja=moje-zamowienia
 *
 * Administrator:
 *   GET  ?akcja=admin-produkty             — wszystkie, także szkice i ukryte
 *   POST ?akcja=produkt-zapisz             — dodanie albo edycja
 *   POST ?akcja=produkt-status             — publikacja / ukrycie / szkic
 *   POST ?akcja=produkt-usun
 *   POST ?akcja=obraz-wgraj                — multipart, jedno zdjęcie
 *   POST ?akcja=plik-wgraj                 — multipart, wideo / GIF / model 3D / szkic
 *   POST ?akcja=plik-usun                  — usuwa plik produktu
 *   POST ?akcja=obraz-usun
 *   GET  ?akcja=admin-zamowienia
 *   POST ?akcja=zamowienie-status
 *
 * Ceny trzymamy w groszach jako liczby całkowite. Kwota w formacie
 * zmiennoprzecinkowym prędzej czy później gubi grosz na zaokrągleniu,
 * a przy rachunkach to jest błąd, którego nikt nie chce tłumaczyć klientowi.
 */

require_once __DIR__ . '/_lib.php';
require_once __DIR__ . '/_sklep.php';
require_once __DIR__ . '/_poczta.php';
require_once __DIR__ . '/_pliki_produktu.php';

/** Slug produktu z nazwy, gdy administrator nie poda własnego. */
function fw_slug_produktu(string $nazwa): string
{
    $s = fw_slug_tytulu($nazwa);
    return $s !== '' ? mb_substr($s, 0, 180, 'UTF-8') : 'produkt';
}

/** Kwota w groszach z pola tekstowego: "129", "129,90", "129.90". */
function fw_grosze(string $wartosc, string $etykieta = 'Cena'): int
{
    $w = trim(str_replace([' ', "\u{00A0}", ','], ['', '', '.'], $wartosc));
    if ($w === '') {
        return 0;
    }
    if (!preg_match('/^\d+(\.\d{1,2})?$/', $w)) {
        fw_blad(422, $etykieta . ': podaj kwotę w złotych, np. 129,90.');
    }
    return (int) round(((float) $w) * 100);
}

$akcja = fw_akcja();
$pdo = fw_baza();

// USUNIETE: koncowka `napraw-media`.
//
// Byl to jednorazowy skrypt naprawczy, ktory przypisywal zdjecia do jednego
// produktu — ale zostal w kodzie jako akcja PUBLICZNA, bez logowania, bez CSRF
// i bez limitu. Kazdy z internetu mogl ja wywolac, a ona kasowala i wstawiala
// wiersze w tabeli obrazow. Robote, do ktorej sluzyla, dawno wykonano.

// ------------------------------------------------------------------ katalog

if ($akcja === 'produkty' || $akcja === 'admin-produkty') {
    $adminowe = $akcja === 'admin-produkty';
    if ($adminowe) {
        fw_wymagaj_admina_lub_tokenu(false);
    }
    fw_zapewnij_tabele_sklepu();

    $warunki = $adminowe ? [] : ['status = "opublikowany"'];
    $parametry = [];
    $kategoria = trim((string) ($_GET['kategoria'] ?? ''));
    if ($kategoria !== '' && $kategoria !== 'all') {
        $warunki[] = 'kategoria = ?';
        $parametry[] = $kategoria;
    }

    $sql = 'SELECT * FROM ' . fw_tabela('produkty')
        . ($warunki ? ' WHERE ' . implode(' AND ', $warunki) : '')
        . ' ORDER BY pozycja ASC, id DESC LIMIT 500';
    $st = $pdo->prepare($sql);
    $st->execute($parametry);
    $wiersze = $st->fetchAll();

    $idki = array_map(static fn($p) => (int) $p['id'], $wiersze);
    $obrazy = fw_obrazy_dla($idki);

    // Pliki dodatkowe doklejamy tylko dla panelu — publiczna lista produktow
    // ich nie potrzebuje, a kazdy zbedny wiersz to zapytanie wiecej.
    $plikiWg = [];
    if ($adminowe) {
        try {
            fw_zapewnij_tabele_plikow($pdo);
            $plikiWg = fw_pliki_dla($idki);
        } catch (Throwable $e) {
            $plikiWg = [];
        }
    }

    fw_odpowiedz([
        'ok' => true,
        'produkty' => array_map(
            static function (array $p) use ($obrazy, $plikiWg, $adminowe): array {
                $wynik = fw_produkt_publiczny($p, $obrazy[(int) $p['id']] ?? [], $adminowe);
                if ($adminowe) {
                    $wynik['pliki'] = $plikiWg[(int) $p['id']] ?? [];
                    $wynik += fw_produkt_dodatki_admina($p);
                }
                return $wynik;
            },
            $wiersze
        ),
    ]);
}

if ($akcja === 'produkt') {
    fw_zapewnij_tabele_sklepu();
    $slug = trim((string) ($_GET['slug'] ?? ''));
    $ja = fw_uzytkownik();
    $adminowe = $ja !== null && $ja['rola'] === 'admin';

    $st = $pdo->prepare('SELECT * FROM ' . fw_tabela('produkty')
        . ' WHERE slug = ?' . ($adminowe ? '' : ' AND status = "opublikowany"'));
    $st->execute([$slug]);
    $p = $st->fetch();
    if (!$p) {
        fw_blad(404, 'Nie ma takiego produktu.');
    }
    $obrazy = fw_obrazy_dla([(int) $p['id']]);
    $wynik = fw_produkt_publiczny($p, $obrazy[(int) $p['id']] ?? [], $adminowe);
    if ($adminowe) {
        $wynik += fw_produkt_dodatki_admina($p);
    }
    fw_odpowiedz(['ok' => true, 'produkt' => $wynik]);
}

// ------------------------------------------------------- zarządzanie (admin)

if ($akcja === 'produkt-zapisz' || $akcja === 'admin-produkt-zapisz') {
    fw_wymagaj_post();
    $autoryzacja = fw_wymagaj_admina_lub_tokenu(true);
    $jestSesjaAdmina = $autoryzacja['typ'] === 'admin';
    fw_zapewnij_tabele_sklepu();

    $we = fw_wejscie();
    $id = (int) ($we['id'] ?? 0);
    $nazwa = fw_tekst(fw_pole('nazwa'), 'Nazwa produktu', 2, 190);
    $slug = trim(fw_pole('slug')) !== '' ? fw_slug_produktu(fw_pole('slug')) : fw_slug_produktu($nazwa);
    $kategoria = fw_tekst(fw_pole('kategoria'), 'Kategoria', 1, 40);
    $opisKrotki = fw_tekst(fw_pole('opis_krotki'), 'Krótki opis', 0, 400);
    $opis = fw_tekst(fw_pole('opis'), 'Opis', 0, 60000);
    $cena = fw_grosze(fw_pole('cena'), 'Cena');
    $promo = trim(fw_pole('cena_promo')) === '' ? null : fw_grosze(fw_pole('cena_promo'), 'Cena promocyjna');
    $stan = trim(fw_pole('stan')) === '' ? null : max(0, (int) fw_pole('stan'));
    $waga = max(0, (int) fw_pole('waga_g'));
    $jednostka = fw_tekst(fw_pole('jednostka') ?: 'szt.', 'Jednostka', 1, 20);
    $czas = fw_tekst(fw_pole('czas_realizacji'), 'Czas realizacji', 0, 80);
    $status = fw_pole('status') ?: 'szkic';
    if (!in_array($status, FW_STATUSY_PRODUKTU, true)) {
        fw_blad(422, 'Nieznany status produktu.');
    }
    if ($promo !== null && $promo >= $cena) {
        fw_blad(422, 'Cena promocyjna musi być niższa od zwykłej.');
    }
    $pozycja = (int) (fw_pole('pozycja') ?: 100);
    $teraz = fw_teraz();

    // Pola Allegro — allegro_id/url/kategoria/blad NALEŻĄ do serwera (kontrakt
    // pkt 1): je ustawiają wyłącznie allegro-wynik/allegro-wystaw, klient tu
    // ich nie zapisuje. allegro_status klient smie zazadac wylacznie
    // "kolejka", i tylko gdy obecny status to "brak" albo "blad" (retry) —
    // kazda inna wartosc od klienta zostaje bez zmian (kontrakt pkt 2).
    // allegro_cena_gr i allegro_parametry klient nadal moze ustawiac.
    $allegroCena = trim((string) ($we['allegro_cena'] ?? '')) !== '' ? fw_grosze((string) $we['allegro_cena'], 'Cena Allegro') : null;
    $allegroParametry = isset($we['allegro_parametry'])
        ? (is_array($we['allegro_parametry']) ? json_encode($we['allegro_parametry'], JSON_UNESCAPED_UNICODE) : (string) $we['allegro_parametry'])
        : null;

    // Slug musi byc unikalny — przy kolizji doklejamy licznik, zamiast
    // odrzucac zapis i kazac administratorowi zgadywac, co jest zajete.
    $bazowy = $slug;
    for ($i = 2; $i < 50; $i++) {
        $czy = $pdo->prepare('SELECT id FROM ' . fw_tabela('produkty') . ' WHERE slug = ? AND id <> ?');
        $czy->execute([$slug, $id]);
        if ($czy->fetchColumn() === false) {
            break;
        }
        $slug = $bazowy . '-' . $i;
    }

    // id>0 musi juz istniec — inaczej 404, nigdy wskrzeszenie usunietego
    // produktu przez INSERT (kontrakt pkt 3). Tylko id=0 wstawia nowy.
    $biezacy = null;
    if ($id > 0) {
        $czy = $pdo->prepare('SELECT * FROM ' . fw_tabela('produkty') . ' WHERE id = ?');
        $czy->execute([$id]);
        $biezacy = $czy->fetch() ?: null;
        if ($biezacy === null) {
            fw_blad(404, 'Nie ma takiego produktu.');
        }
    }

    $allegroStatusObecny = $biezacy !== null ? (string) ($biezacy['allegro_status'] ?? 'brak') : 'brak';
    // Serwer wlasnymi rekami — allegro_id/url/kategoria z biezacego wiersza,
    // niezalezne od tego, co przyslal klient (kontrakt pkt 1).
    $allegroId = $biezacy !== null ? ($biezacy['allegro_id'] ?? null) : null;
    $allegroUrl = $biezacy !== null ? ($biezacy['allegro_url'] ?? null) : null;
    $allegroKategoria = $biezacy !== null ? ($biezacy['allegro_kategoria'] ?? null) : null;
    $allegroStatus = $allegroStatusObecny;

    // Jedyny wyjatek: admin (nie agent) w panelu recznie podlacza/zmienia
    // istniejaca aukcje albo ja odlacza — sygnalizuje to explicit flaga,
    // ktorej apka telefonu nigdy nie wysyla.
    $recznePolaczenie = $jestSesjaAdmina && !empty($we['allegro_reczne_polaczenie']);
    if ($recznePolaczenie) {
        $allegroUrlWe = trim((string) ($we['allegro_url'] ?? ''));
        if ($allegroUrlWe === '') {
            $allegroId = null;
            $allegroUrl = null;
            $allegroStatus = 'brak';
        } else {
            $allegroUrlWe = fw_allegro_url($allegroUrlWe);
            if ($allegroUrlWe === null) {
                fw_blad(422, 'Podaj publiczny link HTTPS do Allegro lub Allegro Lokalnie.');
            }
            $allegroIdWe = trim((string) ($we['allegro_id'] ?? ''));
            if ($allegroIdWe !== '' && !preg_match('/^\d+$/', $allegroIdWe)) {
                fw_blad(422, 'Identyfikator aukcji Allegro to same cyfry.');
            }
            if ($allegroIdWe === '' && preg_match('/(?:oferta\/[^\/]+-)?(\d{8,15})/i', $allegroUrlWe, $m)) {
                $allegroIdWe = $m[1];
            }
            $allegroUrl = $allegroUrlWe;
            $allegroId = $allegroIdWe !== '' ? $allegroIdWe : null;
            $allegroStatus = 'aktywna';
        }
    } else {
        // Bez recznego polaczenia klient smie zazadac wylacznie "kolejka",
        // i tylko gdy obecny status to "brak" albo "blad" (retry) — kazda
        // inna wartosc od klienta zostaje bez zmian (kontrakt pkt 2).
        $allegroStatusZadanie = trim((string) ($we['allegro_status'] ?? ''));
        if ($allegroStatusZadanie === 'kolejka' && in_array($allegroStatusObecny, ['brak', 'blad'], true)) {
            $allegroStatus = 'kolejka';
        }
    }

    if ($biezacy !== null) {
        $st = $pdo->prepare('UPDATE ' . fw_tabela('produkty') . ' SET'
            . ' slug = ?, nazwa = ?, kategoria = ?, opis_krotki = ?, opis = ?, cena_gr = ?,'
            . ' cena_promo_gr = ?, stan = ?, waga_g = ?, jednostka = ?, czas_realizacji = ?,'
            . ' status = ?, pozycja = ?, zmieniony = ?,'
            . ' allegro_id = ?, allegro_url = ?, allegro_kategoria = ?, allegro_cena_gr = ?,'
            . ' allegro_status = ?, allegro_parametry = ?'
            . ' WHERE id = ?');
        $st->execute([$slug, $nazwa, $kategoria, $opisKrotki, $opis, $cena, $promo, $stan,
            $waga, $jednostka, $czas, $status, $pozycja, $teraz,
            $allegroId, $allegroUrl, $allegroKategoria, $allegroCena, $allegroStatus, $allegroParametry,
            $id]);
    } else {
        $pdo->prepare('INSERT INTO ' . fw_tabela('produkty')
            . ' (slug, nazwa, kategoria, opis_krotki, opis, cena_gr, cena_promo_gr, stan, waga_g,'
            . '  jednostka, czas_realizacji, status, pozycja, utworzony, zmieniony,'
            . '  allegro_id, allegro_url, allegro_kategoria, allegro_cena_gr, allegro_status, allegro_parametry)'
            . ' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
            ->execute([$slug, $nazwa, $kategoria, $opisKrotki, $opis, $cena, $promo, $stan, $waga,
                $jednostka, $czas, $status, $pozycja, $teraz, $teraz,
                $allegroId, $allegroUrl, $allegroKategoria, $allegroCena, $allegroStatus, $allegroParametry]);
        $id = (int) $pdo->lastInsertId();
    }

    fw_odpowiedz(['ok' => true, 'id' => $id, 'slug' => $slug, 'url' => '/sklep/' . $slug . '/']);
}

// -------------------------------------------------- synchronizacja z Allegro

if ($akcja === 'allegro-synchronizuj-aukcje') {
    fw_wymagaj_post();
    fw_wymagaj_admina_lub_tokenu(true);

    try {
        fw_zapewnij_tabele_sklepu();
        $wejscie = fw_wejscie();

        $allegroId = trim((string) ($wejscie['allegro_id'] ?? fw_pole('allegro_id')));
        $allegroUrl = trim((string) ($wejscie['allegro_url'] ?? fw_pole('allegro_url')));
        if ($allegroUrl === '' && $allegroId !== '') {
            $allegroUrl = 'https://allegro.pl/oferta/' . $allegroId;
        }
        if (fw_allegro_url($allegroUrl) === null) {
            fw_blad(422, 'Wymagany jest poprawny adres URL aukcji Allegro.');
        }

        if ($allegroId === '' && preg_match('/(?:oferta\/[^\/]+-)?(\d{8,15})/i', $allegroUrl, $m)) {
            $allegroId = $m[1];
        }

        $nazwa = trim((string) ($wejscie['nazwa'] ?? fw_pole('nazwa')));
        if ($nazwa === '') {
            fw_blad(422, 'Wymagana jest nazwa (tytuł aukcji).');
        }
        // Limit 75 znaków tytułu Allegro
        $nazwa = mb_substr($nazwa, 0, 75, 'UTF-8');

        $kategoria = trim((string) ($wejscie['kategoria'] ?? fw_pole('kategoria', 'inne')));
        if ($kategoria === '') {
            $kategoria = 'inne';
        }
        $allegroKategoria = trim((string) ($wejscie['allegro_kategoria'] ?? fw_pole('allegro_kategoria', $kategoria)));
        if ($allegroKategoria === '') {
            $allegroKategoria = $kategoria;
        }

        $cenaStr = trim((string) ($wejscie['cena'] ?? fw_pole('cena')));
        if ($cenaStr !== '') {
            $cenaGr = fw_grosze($cenaStr, 'Cena');
        } elseif (isset($wejscie['cena_gr'])) {
            $cenaGr = (int) $wejscie['cena_gr'];
        } else {
            $cenaGr = 0;
        }
        if ($cenaGr < 1) {
            fw_blad(422, 'Cena musi być większa od zera.');
        }

        $sekcje = $wejscie['sekcje_allegro'] ?? ($wejscie['sections'] ?? null);
        $parametry = $wejscie['parametry'] ?? ($wejscie['parameters'] ?? null);
        if (!is_array($parametry)) {
            $parametry = [];
        }
        $allegroParametry = json_encode($parametry, JSON_UNESCAPED_UNICODE);

        $opis = trim((string) ($wejscie['opis'] ?? fw_pole('opis')));
        if (is_array($sekcje) && !empty($sekcje)) {
            $opisZeSekcji = fw_parsuj_sekcje_allegro($sekcje, $parametry, $nazwa);
            $opis = $opis !== '' ? ($opis . "\n\n" . $opisZeSekcji) : $opisZeSekcji;
        }

        $opisKrotki = trim((string) ($wejscie['opis_krotki'] ?? fw_pole('opis_krotki')));
        if ($opisKrotki === '') {
            $opisKrotki = mb_substr(strip_tags($opis), 0, 350, 'UTF-8');
        }

        $wagaG = (int) ($wejscie['waga_g'] ?? fw_pole('waga_g', '0'));
        $czasRealizacji = trim((string) ($wejscie['czas_realizacji'] ?? fw_pole('czas_realizacji', '1-2 dni robocze')));
        $stan = isset($wejscie['stan']) ? (int) $wejscie['stan'] : 1;
        $jednostka = trim((string) ($wejscie['jednostka'] ?? fw_pole('jednostka', 'szt.')));
        $allegroStatus = trim((string) ($wejscie['allegro_status'] ?? fw_pole('allegro_status', 'aktywna')));
        if (!in_array($allegroStatus, fw_statusy_allegro(), true)) {
            $allegroStatus = 'aktywna';
        }
        $status = 'opublikowany';
        $pozycja = (int) ($wejscie['pozycja'] ?? fw_pole('pozycja', '10'));
        $teraz = fw_teraz();

        // Szukamy istniejącego produktu: po ID, allegro_id, allegro_url lub nazwie
        $istniejacy = null;
        $wejscieId = isset($wejscie['id']) ? (int) $wejscie['id'] : (int) fw_pole('id', '0');
        if ($wejscieId > 0) {
            $stIst = $pdo->prepare('SELECT id, slug FROM ' . fw_tabela('produkty') . ' WHERE id = ? LIMIT 1');
            $stIst->execute([$wejscieId]);
            $istniejacy = $stIst->fetch();
        }
        if (!$istniejacy && $allegroId !== '') {
            $stIst = $pdo->prepare('SELECT id, slug FROM ' . fw_tabela('produkty') . ' WHERE allegro_id = ? LIMIT 1');
            $stIst->execute([$allegroId]);
            $istniejacy = $stIst->fetch();
        }
        if (!$istniejacy && $allegroUrl !== '') {
            $stIst = $pdo->prepare('SELECT id, slug FROM ' . fw_tabela('produkty') . ' WHERE allegro_url = ? LIMIT 1');
            $stIst->execute([$allegroUrl]);
            $istniejacy = $stIst->fetch();
        }
        if (!$istniejacy) {
            $stIst = $pdo->prepare('SELECT id, slug FROM ' . fw_tabela('produkty') . ' WHERE nazwa = ? LIMIT 1');
            $stIst->execute([$nazwa]);
            $istniejacy = $stIst->fetch();
        }

        if ($istniejacy) {
            $id = (int) $istniejacy['id'];
            $slug = (string) $istniejacy['slug'];
            $stUp = $pdo->prepare('UPDATE ' . fw_tabela('produkty') . ' SET'
                . ' nazwa = ?, kategoria = ?, opis_krotki = ?, opis = ?, cena_gr = ?,'
                . ' stan = ?, waga_g = ?, jednostka = ?, czas_realizacji = ?, status = ?,'
                . ' allegro_id = ?, allegro_url = ?, allegro_kategoria = ?, allegro_cena_gr = ?, allegro_status = ?, allegro_parametry = ?,'
                . ' zmieniony = ? WHERE id = ?');
            $stUp->execute([
                $nazwa, $kategoria, $opisKrotki, $opis, $cenaGr,
                $stan, $wagaG, $jednostka, $czasRealizacji, $status,
                $allegroId, $allegroUrl, $allegroKategoria, $cenaGr, $allegroStatus, $allegroParametry,
                $teraz, $id
            ]);
        } else {
            $bazowySlug = fw_slug_produktu($nazwa);
            if ($bazowySlug === '') {
                $bazowySlug = 'produkt-' . ($allegroId !== '' ? $allegroId : time());
            }
            $slug = $bazowySlug;
            for ($i = 2; $i < 100; $i++) {
                $czy = $pdo->prepare('SELECT 1 FROM ' . fw_tabela('produkty') . ' WHERE slug = ?');
                $czy->execute([$slug]);
                if ($czy->fetchColumn() === false) {
                    break;
                }
                $slug = $bazowySlug . '-' . $i;
            }

            $stIns = $pdo->prepare('INSERT INTO ' . fw_tabela('produkty')
                . ' (slug, nazwa, kategoria, opis_krotki, opis, cena_gr, cena_promo_gr, stan, waga_g,'
                . '  jednostka, czas_realizacji, status, pozycja, utworzony, zmieniony,'
                . '  allegro_id, allegro_url, allegro_kategoria, allegro_cena_gr, allegro_status, allegro_parametry)'
                . ' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)');
            $stIns->execute([
                $slug, $nazwa, $kategoria, $opisKrotki, $opis, $cenaGr, null, $stan, $wagaG,
                $jednostka, $czasRealizacji, $status, $pozycja, $teraz, $teraz,
                $allegroId, $allegroUrl, $allegroKategoria, $cenaGr, $allegroStatus, $allegroParametry
            ]);
            $id = (int) $pdo->lastInsertId();
        }

        $zdjecia = $wejscie['zdjecia'] ?? ($wejscie['images'] ?? []);
        if (is_array($zdjecia) && !empty($zdjecia)) {
            $stObrazyIstniejace = $pdo->prepare('SELECT plik FROM ' . fw_tabela('produkty_obrazy') . ' WHERE produkt_id = ?');
            $stObrazyIstniejace->execute([$id]);
            $istniejacePliki = $stObrazyIstniejace->fetchAll(PDO::FETCH_COLUMN);

            $pozycjaZdj = 100;
            $stInsObraz = $pdo->prepare('INSERT INTO ' . fw_tabela('produkty_obrazy')
                . ' (produkt_id, plik, alt, szerokosc, wysokosc, pozycja) VALUES (?,?,?,?,?,?)');
            foreach ($zdjecia as $zUrl) {
                if (is_string($zUrl) && filter_var($zUrl, FILTER_VALIDATE_URL) && !in_array($zUrl, $istniejacePliki, true)) {
                    $stInsObraz->execute([$id, $zUrl, $nazwa, 1200, 900, $pozycjaZdj]);
                    $pozycjaZdj += 10;
                }
            }
        }

        $salesCenterUrl = $allegroId !== '' ? ('https://salescenter.allegro.pl/offer-management/offers/' . rawurlencode($allegroId) . '/edit') : null;
        fw_odpowiedz([
            'ok'          => true,
            'id'          => $id,
            'slug'        => $slug,
            'url'         => '/sklep/' . $slug . '/',
            'allegro_url' => $allegroUrl,
            'allegro_id'  => $allegroId,
            'sales_center_url' => $salesCenterUrl,
            'allegro_status' => $allegroStatus,
            'komunikat'   => 'Aukcja Allegro została pomyślnie powiązana ze sklepem fwdrucik.pl',
        ]);
    } catch (\Throwable $e) {
        fw_blad(500, 'Błąd zapisu aukcji Allegro: ' . $e->getMessage());
    }
}

if ($akcja === 'allegro-import-z-linku') {
    fw_wymagaj_post();
    fw_wymagaj_admina_lub_tokenu(true);

    try {
        $url = fw_pole('url');
        if (fw_allegro_url($url) === null) {
            fw_blad(422, 'Podaj prawidłowy adres URL aukcji Allegro.');
        }

        $dane = fw_pobierz_dane_aukcji_allegro($url);
        if (!$dane) {
            fw_blad(422, 'Nie udało się pobrać danych z podanego linku Allegro. Upewnij się, że aukcja istnieje i jest publicznie dostępna.');
        }

        fw_zapewnij_tabele_sklepu();
        $allegroUrl = $dane['allegro_url'];
        $allegroId = $dane['allegro_id'];
        $nazwa = $dane['nazwa'];
        $cenaGr = $dane['cena_gr'];
        $opis = $dane['opis'];
        $opisKrotki = $dane['opis_krotki'];
        $kategoria = 'inne';
        $stan = 1;
        $wagaG = 0;
        $jednostka = 'szt.';
        $czasRealizacji = '1-2 dni robocze';
        $allegroStatus = 'aktywna';
        $status = 'opublikowany';
        $pozycja = 10;
        $teraz = fw_teraz();

        $stIstniejacy = $pdo->prepare('SELECT id, slug FROM ' . fw_tabela('produkty')
            . ' WHERE (allegro_id IS NOT NULL AND allegro_id <> "" AND allegro_id = ?) OR allegro_url = ? LIMIT 1');
        $stIstniejacy->execute([$allegroId, $allegroUrl]);
        $istniejacy = $stIstniejacy->fetch();

        if ($istniejacy) {
            $id = (int) $istniejacy['id'];
            $slug = (string) $istniejacy['slug'];
            $stUp = $pdo->prepare('UPDATE ' . fw_tabela('produkty') . ' SET'
                . ' nazwa = ?, opis_krotki = ?, opis = ?, cena_gr = ?,'
                . ' allegro_id = ?, allegro_url = ?, allegro_cena_gr = ?, allegro_status = ?,'
                . ' zmieniony = ? WHERE id = ?');
            $stUp->execute([$nazwa, $opisKrotki, $opis, $cenaGr, $allegroId, $allegroUrl, $cenaGr, $allegroStatus, $teraz, $id]);
        } else {
            $bazowySlug = fw_slug_produktu($nazwa);
            if ($bazowySlug === '') {
                $bazowySlug = 'produkt-' . ($allegroId !== '' ? $allegroId : time());
            }
            $slug = $bazowySlug;
            for ($i = 2; $i < 100; $i++) {
                $czy = $pdo->prepare('SELECT 1 FROM ' . fw_tabela('produkty') . ' WHERE slug = ?');
                $czy->execute([$slug]);
                if ($czy->fetchColumn() === false) {
                    break;
                }
                $slug = $bazowySlug . '-' . $i;
            }

            $stIns = $pdo->prepare('INSERT INTO ' . fw_tabela('produkty')
                . ' (slug, nazwa, kategoria, opis_krotki, opis, cena_gr, cena_promo_gr, stan, waga_g,'
                . '  jednostka, czas_realizacji, status, pozycja, utworzony, zmieniony,'
                . '  allegro_id, allegro_url, allegro_kategoria, allegro_cena_gr, allegro_status)'
                . ' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)');
            $stIns->execute([
                $slug, $nazwa, $kategoria, $opisKrotki, $opis, $cenaGr, null, $stan, $wagaG,
                $jednostka, $czasRealizacji, $status, $pozycja, $teraz, $teraz,
                $allegroId, $allegroUrl, $kategoria, $cenaGr, $allegroStatus
            ]);
            $id = (int) $pdo->lastInsertId();
        }

        if (!empty($dane['zdjecia'])) {
            $stObrazyIstniejace = $pdo->prepare('SELECT plik FROM ' . fw_tabela('produkty_obrazy') . ' WHERE produkt_id = ?');
            $stObrazyIstniejace->execute([$id]);
            $istniejacePliki = $stObrazyIstniejace->fetchAll(PDO::FETCH_COLUMN);

            $pozycjaZdj = 100;
            $stInsObraz = $pdo->prepare('INSERT INTO ' . fw_tabela('produkty_obrazy')
                . ' (produkt_id, plik, alt, szerokosc, wysokosc, pozycja) VALUES (?,?,?,?,?,?)');
            foreach ($dane['zdjecia'] as $zUrl) {
                if (is_string($zUrl) && filter_var($zUrl, FILTER_VALIDATE_URL) && !in_array($zUrl, $istniejacePliki, true)) {
                    $stInsObraz->execute([$id, $zUrl, $nazwa, 1200, 900, $pozycjaZdj]);
                    $pozycjaZdj += 10;
                }
            }
        }

        fw_odpowiedz([
            'ok'          => true,
            'id'          => $id,
            'slug'        => $slug,
            'url'         => '/sklep/' . $slug . '/',
            'allegro_url' => $allegroUrl,
            'allegro_id'  => $allegroId,
            'komunikat'   => 'Aukcja Allegro została pomyślnie zaimportowana i opublikowana.',
        ]);
    } catch (\Throwable $e) {
        fw_blad(500, 'Błąd importu aukcji Allegro: ' . $e->getMessage());
    }
}

if ($akcja === 'allegro-kolejka') {
    fw_wymagaj_tokenu_agenta();
    fw_zapewnij_tabele_sklepu();
    fw_zapewnij_tabele_plikow($pdo);
    $st = $pdo->query('SELECT id, nazwa, opis, cena_gr, stan, allegro_id, allegro_kategoria, allegro_cena_gr,'
        . ' allegro_status, allegro_parametry FROM ' . fw_tabela('produkty')
        . ' WHERE allegro_status IN ("kolejka","wystaw") ORDER BY zmieniony ASC LIMIT 10');
    $wynik = [];
    foreach ($st->fetchAll(PDO::FETCH_ASSOC) as $p) {
        $pl = $pdo->prepare('SELECT plik FROM ' . fw_tabela('produkty_pliki')
            . ' WHERE produkt_id = ? AND rodzaj = "allegro" ORDER BY pozycja ASC, id ASC LIMIT 16');
        $pl->execute([$p['id']]);
        $p['id'] = (int) $p['id'];
        $p['cena_gr'] = (int) $p['cena_gr'];
        $p['allegro_parametry'] = !empty($p['allegro_parametry']) ? (json_decode((string) $p['allegro_parametry'], true) ?: new stdClass()) : new stdClass();
        $p['zdjecia_allegro'] = array_map(static fn($f) => fw_adres_zdjec((string) $f), $pl->fetchAll(PDO::FETCH_COLUMN));
        $wynik[] = $p;
    }
    fw_odpowiedz(['ok' => true, 'produkty' => $wynik]);
}

if ($akcja === 'allegro-wynik') {
    fw_wymagaj_post();
    fw_wymagaj_tokenu_agenta();
    fw_zapewnij_tabele_sklepu();
    $we = json_decode((string) file_get_contents('php://input'), true) ?: [];
    $id = (int) ($we['id'] ?? 0);
    $status = (string) ($we['allegro_status'] ?? '');
    if ($id < 1 || !in_array($status, ['szkic', 'aktywna', 'blad'], true)) {
        fw_blad(422, 'Nieprawidłowy wynik kolejki Allegro.');
    }
    // Rzutowanie na string/null przed strict_types — agent moglby przyslac
    // np. liczbe albo tablice i wywrocic TypeError w fw_allegro_url.
    $allegroIdWe = isset($we['allegro_id']) && is_scalar($we['allegro_id']) ? (string) $we['allegro_id'] : null;
    $allegroUrlWe = isset($we['allegro_url']) && is_scalar($we['allegro_url']) ? (string) $we['allegro_url'] : null;
    $allegroKategoriaWe = isset($we['allegro_kategoria']) && is_scalar($we['allegro_kategoria']) ? (string) $we['allegro_kategoria'] : null;
    $st = $pdo->prepare('UPDATE ' . fw_tabela('produkty') . ' SET allegro_status = ?,'
        . ' allegro_id = COALESCE(?, allegro_id), allegro_url = COALESCE(?, allegro_url),'
        . ' allegro_kategoria = COALESCE(?, allegro_kategoria), allegro_blad = ? WHERE id = ?'
        . ' AND allegro_status IN ("kolejka","wystaw")');
    $st->execute([$status, $allegroIdWe, fw_allegro_url($allegroUrlWe),
        $allegroKategoriaWe,
        $status === 'aktywna' ? null : (isset($we['allegro_blad']) ? mb_substr((string) $we['allegro_blad'], 0, 2000) : null),
        $id]);
    if ($st->rowCount() !== 1) {
        // UPDATE bez faktycznej zmiany wartosci tez daje rowCount 0 w MySQL —
        // rozroznij "wiersz nie istnieje/zly status" od "nic sie nie zmienilo".
        $czy = $pdo->prepare('SELECT 1 FROM ' . fw_tabela('produkty') . ' WHERE id = ? AND allegro_status = ?');
        $czy->execute([$id, $status]);
        if ($czy->fetchColumn() === false) {
            fw_blad(409, 'Produkt nie czeka w kolejce Allegro.');
        }
    }
    fw_odpowiedz(['ok' => true]);
}

if ($akcja === 'allegro-wystaw') {
    fw_wymagaj_post();
    fw_wymagaj_admina_lub_tokenu(true);
    fw_zapewnij_tabele_sklepu();
    $id = fw_id('id');
    $st = $pdo->prepare('UPDATE ' . fw_tabela('produkty') . ' SET allegro_status = "wystaw", allegro_blad = NULL'
        . ' WHERE id = ? AND allegro_status = "szkic"');
    $st->execute([$id]);
    if ($st->rowCount() !== 1) {
        fw_blad(409, 'Wystawić można tylko gotowy szkic Allegro.');
    }
    fw_odpowiedz(['ok' => true]);
}

// -------------------------------------------------- Szkice i kategorie Allegro

if ($akcja === 'allegro-szkice') {
    $u = fw_uzytkownik();
    $jestAdmin = ($u !== null && ($u['rola'] ?? '') === 'admin');
    $oczekiwany = (string) (fw_konfiguracja()['agent_token'] ?? '');
    $podany = (string) ($_SERVER['HTTP_X_AGENT_TOKEN'] ?? ($_SERVER['HTTP_X_FW_TOKEN'] ?? fw_pole('token')));
    $jestAgent = ($oczekiwany !== '' && hash_equals($oczekiwany, $podany));

    fw_zapewnij_tabele_sklepu();
    $pdo = fw_baza();
    $warunek = ($jestAdmin || $jestAgent)
        ? 'allegro_id IS NOT NULL AND allegro_id <> ""'
        : 'allegro_id IS NOT NULL AND allegro_id <> "" AND status = "opublikowany"';
    $st = $pdo->query('SELECT id, slug, nazwa, kategoria, opis_krotki, opis, cena_gr, stan,'
        . ' allegro_id, allegro_url, allegro_kategoria, allegro_cena_gr, allegro_status, allegro_parametry, zmieniony'
        . ' FROM ' . fw_tabela('produkty')
        . ' WHERE ' . $warunek
        . ' ORDER BY id DESC');
    $szkice = $st->fetchAll();
    $idki = array_map(static fn($p) => (int) $p['id'], $szkice);
    $obrazy = !empty($idki) ? fw_obrazy_dla($idki) : [];
    $pelny = $jestAdmin || $jestAgent;
    foreach ($szkice as &$s) {
        $s['id'] = (int) $s['id'];
        $s['cena_gr'] = (int) $s['cena_gr'];
        $s['allegro_cena_gr'] = (int) ($s['allegro_cena_gr'] ?? $s['cena_gr']);
        $s['obrazy'] = $obrazy[$s['id']] ?? [];
        $s['url'] = '/sklep/' . $s['slug'] . '/';
        // sales_center_url/parametry/allegro_parametry to zaplecze admina —
        // dla anonima nie moga wyciekac (kontrakt pkt 4).
        if ($pelny) {
            $s['sales_center_url'] = !empty($s['allegro_id']) ? ('https://salescenter.allegro.pl/offer-management/offers/' . rawurlencode((string) $s['allegro_id']) . '/edit') : null;
            $s['parametry'] = !empty($s['allegro_parametry']) ? (json_decode((string) $s['allegro_parametry'], true) ?: []) : [];
        } else {
            unset($s['allegro_parametry']);
        }
    }
    unset($s);
    fw_odpowiedz([
        'ok'      => true,
        'szkice'  => $szkice,
        'lacznie' => count($szkice),
        'admin'   => ($jestAdmin || $jestAgent)
    ]);
}

if ($akcja === 'allegro-kategorie') {
    $kategorie = [
        [
            'id' => '110888',
            'nazwa' => 'Patery (Dom i Ogród -> Zastawa stołowa)',
            'parametry_wymagane' => ['Stan', 'Marka', 'Średnica (cm)', 'Kod producenta'],
            'domyslne' => ['Stan' => 'Nowy', 'Marka' => 'F.W. DRUCIK / bez marki', 'Kod producenta' => 'FWD-PAT-01']
        ],
        [
            'id' => '254294',
            'nazwa' => 'Świeczniki (Dom i Ogród -> Dekoracje)',
            'parametry_wymagane' => ['Stan', 'Rodzaj (na tealighty)', 'Marka', 'Wysokość (cm)', 'Kod producenta'],
            'domyslne' => ['Stan' => 'Nowy', 'Rodzaj' => 'na tealighty', 'Marka' => 'F.W. DRUCIK / bez marki', 'Wysokość' => '5', 'Kod producenta' => 'FWD-LOTOS-01']
        ],
        [
            'id' => '54089',
            'nazwa' => 'Stoliki i ławy (Meble -> Salon)',
            'parametry_wymagane' => ['Stan', 'Typ (stolik kawowy)', 'Kształt blatu', 'Marka', 'Kolor mebla', 'Wymiary (Gł/Szer/Wys)', 'Kod producenta'],
            'domyslne' => ['Stan' => 'Nowy', 'Typ' => 'stolik kawowy', 'Marka' => 'F.W. DRUCIK / bez marki', 'Kolor mebla' => 'dąb naturalny', 'Kod producenta' => 'FWD-STOLIK-01']
        ],
        [
            'id' => '15557',
            'nazwa' => 'Breloki i gadżety (Galanteria i dodatki)',
            'parametry_wymagane' => ['Stan', 'Marka', 'Kolor', 'Materiał dominujący', 'Kod producenta'],
            'domyslne' => ['Stan' => 'Nowy', 'Marka' => 'F.W. DRUCIK / bez marki', 'Kolor' => 'wielokolorowy / złoty', 'Materiał dominujący' => 'metal / żywica', 'Kod producenta' => 'FWD-BRELOK-01']
        ],
        [
            'id' => '26069',
            'nazwa' => 'Talerze, deski i podstawki dekoracyjne',
            'parametry_wymagane' => ['Stan', 'Marka', 'Średnica / Wymiary', 'Kod producenta'],
            'domyslne' => ['Stan' => 'Nowy', 'Marka' => 'F.W. DRUCIK / bez marki', 'Kod producenta' => 'FWD-DESKA-01']
        ]
    ];
    fw_odpowiedz(['ok' => true, 'kategorie' => $kategorie]);
}

if ($akcja === 'produkt-status') {
    fw_wymagaj_post();
    fw_wymagaj_admina_lub_tokenu(true);
    fw_zapewnij_tabele_sklepu();

    $id = fw_id('id');
    $status = fw_pole('status');
    if (!in_array($status, FW_STATUSY_PRODUKTU, true)) {
        fw_blad(422, 'Nieznany status produktu.');
    }
    $st = $pdo->prepare('UPDATE ' . fw_tabela('produkty')
        . ' SET status = ?, zmieniony = ? WHERE id = ?');
    $st->execute([$status, fw_teraz(), $id]);
    if ($st->rowCount() === 0) {
        $czy = $pdo->prepare('SELECT 1 FROM ' . fw_tabela('produkty') . ' WHERE id = ?');
        $czy->execute([$id]);
        if ($czy->fetchColumn() === false) {
            fw_blad(404, 'Nie ma takiego produktu.');
        }
    }
    fw_odpowiedz(['ok' => true, 'status' => $status]);
}

if ($akcja === 'produkt-usun') {
    fw_wymagaj_post();
    fw_wymagaj_admina_lub_tokenu(true);
    fw_zapewnij_tabele_sklepu();

    $id = fw_id('id');
    // Pliki zdjec kasujemy razem z wpisem — inaczej katalog rosnie w nieskonczonosc.
    $st = $pdo->prepare('SELECT plik FROM ' . fw_tabela('produkty_obrazy') . ' WHERE produkt_id = ?');
    $st->execute([$id]);
    foreach ($st->fetchAll() as $o) {
        $sciezka = FW_KATALOG_OBRAZOW . '/' . basename((string) $o['plik']);
        if (is_file($sciezka)) {
            @unlink($sciezka);
        }
    }
    $st = $pdo->prepare('DELETE FROM ' . fw_tabela('produkty') . ' WHERE id = ?');
    $st->execute([$id]);
    if ($st->rowCount() === 0) {
        fw_blad(404, 'Nie ma takiego produktu.');
    }
    fw_odpowiedz(['ok' => true]);
}

// ----------------------------------------------------------------- zdjęcia

if ($akcja === 'obraz-przypisz') {
    fw_wymagaj_post();
    fw_wymagaj_admina_lub_tokenu(true);
    fw_zapewnij_tabele_sklepu();

    $produktId = (int) (fw_pole('produkt_id') ?: 0);
    if ($produktId < 1) {
        fw_blad(422, 'Brak identyfikatora produktu.');
    }
    $czy = $pdo->prepare('SELECT 1 FROM ' . fw_tabela('produkty') . ' WHERE id = ?');
    $czy->execute([$produktId]);
    if ($czy->fetchColumn() === false) {
        fw_blad(404, 'Nie ma takiego produktu.');
    }

    $plik = basename(trim((string) fw_pole('plik')));
    if ($plik === '') {
        fw_blad(422, 'Brak nazwy pliku.');
    }
    $sciezka = FW_KATALOG_OBRAZOW . '/' . $plik;
    if (!is_file($sciezka)) {
        fw_blad(404, 'Plik nie istnieje w katalogu assets/sklep: ' . $plik);
    }
    $info = @getimagesize($sciezka);
    $szerokosc = $info ? (int) $info[0] : 1200;
    $wysokosc = $info ? (int) $info[1] : 900;
    $alt = fw_tekst(fw_pole('alt'), 'Alt', 0, 190);
    $pozycja = (int) (fw_pole('pozycja') ?: 10);

    $pdo->prepare('INSERT INTO ' . fw_tabela('produkty_obrazy')
        . ' (produkt_id, plik, alt, szerokosc, wysokosc, pozycja) VALUES (?,?,?,?,?,?)')
        ->execute([$produktId, $plik, $alt, $szerokosc, $wysokosc, $pozycja]);

    fw_odpowiedz([
        'ok' => true,
        'obraz' => [
            'id'        => (int) $pdo->lastInsertId(),
            'src'       => '/assets/sklep/' . $plik,
            'alt'       => $alt,
            'szerokosc' => $szerokosc,
            'wysokosc'  => $wysokosc,
        ],
    ], 201);
}

if ($akcja === 'obraz-wgraj') {
    fw_wymagaj_post();
    fw_wymagaj_admina_lub_tokenu(true);
    fw_zapewnij_tabele_sklepu();

    $produktId = (int) ($_POST['produkt_id'] ?? 0);
    if ($produktId < 1) {
        fw_blad(422, 'Brak identyfikatora produktu.');
    }
    $czy = $pdo->prepare('SELECT 1 FROM ' . fw_tabela('produkty') . ' WHERE id = ?');
    $czy->execute([$produktId]);
    if ($czy->fetchColumn() === false) {
        fw_blad(404, 'Nie ma takiego produktu.');
    }

    fw_wymagaj_uploadu('plik', FW_MAX_OBRAZ_B);
    if ($_FILES['plik']['size'] > FW_MAX_OBRAZ_B) {
        fw_blad(422, 'Zdjęcie jest za duże. Maksimum to 6 MB.');
    }

    // Typ pliku bierzemy z jego zawartosci, nie z nazwy ani z naglowka
    // przegladarki — obie te rzeczy podaje klient i obie mozna sfalszowac.
    $info = @getimagesize($_FILES['plik']['tmp_name']);
    $dozwolone = [IMAGETYPE_JPEG => 'jpg', IMAGETYPE_PNG => 'png', IMAGETYPE_WEBP => 'webp', IMAGETYPE_GIF => 'gif'];
    if ($info === false || !isset($dozwolone[$info[2]])) {
        fw_blad(422, 'Dozwolone formaty zdjęć: JPG, PNG, WEBP, GIF.');
    }
    $rozszerzenie = $dozwolone[$info[2]];

    if (!is_dir(FW_KATALOG_OBRAZOW) && !@mkdir(FW_KATALOG_OBRAZOW, 0755, true)) {
        fw_blad(500, 'Nie mogę utworzyć katalogu na zdjęcia.');
    }
    $nazwaPliku = $produktId . '-' . bin2hex(random_bytes(6)) . '.' . $rozszerzenie;
    $cel = FW_KATALOG_OBRAZOW . '/' . $nazwaPliku;
    if (!move_uploaded_file($_FILES['plik']['tmp_name'], $cel)) {
        fw_blad(500, 'Nie udało się zapisać zdjęcia na serwerze.');
    }
    @chmod($cel, 0644);

    // Logo w prawym dolnym rogu — wypalone w pikselach, nie doklejone stylem.
    // Nieudane naniesienie NIE przerywa wgrywania: zdjęcie bez znaku jest
    // lepsze niż odrzucone zdjęcie.
    require_once __DIR__ . '/_znak_wodny.php';
    if (fw_nanies_znak_wodny($cel, $info[2])) {
        // Znak zmienia rozmiar pliku, a przy JPEG także wymiary zaokrąglone
        // przez ponowny zapis — czytamy je jeszcze raz, żeby baza zgadzała się
        // z tym, co naprawdę leży na dysku.
        $poZnaku = @getimagesize($cel);
        if ($poZnaku !== false) {
            $info = $poZnaku;
        }
    }

    $alt = trim((string) ($_POST['alt'] ?? ''));
    $pozycja = (int) ($_POST['pozycja'] ?? 100);
    $pdo->prepare('INSERT INTO ' . fw_tabela('produkty_obrazy')
        . ' (produkt_id, plik, alt, szerokosc, wysokosc, pozycja) VALUES (?,?,?,?,?,?)')
        ->execute([$produktId, $nazwaPliku, mb_substr($alt, 0, 190, 'UTF-8'),
            (int) $info[0], (int) $info[1], $pozycja]);

    fw_odpowiedz([
        'ok' => true,
        'obraz' => [
            'id'        => (int) $pdo->lastInsertId(),
            'src'       => '/assets/sklep/' . $nazwaPliku,
            'alt'       => $alt,
            'szerokosc' => (int) $info[0],
            'wysokosc'  => (int) $info[1],
        ],
    ], 201);
}

if ($akcja === 'plik-wgraj') {
    fw_wymagaj_post();
    fw_wymagaj_admina_lub_tokenu(true);
    fw_zapewnij_tabele_sklepu();
    fw_zapewnij_tabele_plikow($pdo);

    $produktId = (int) ($_POST['produkt_id'] ?? 0);
    if ($produktId < 1) {
        fw_blad(422, 'Brak identyfikatora produktu.');
    }
    $czy = $pdo->prepare('SELECT 1 FROM ' . fw_tabela('produkty') . ' WHERE id = ?');
    $czy->execute([$produktId]);
    if ($czy->fetchColumn() === false) {
        fw_blad(404, 'Nie ma takiego produktu.');
    }

    fw_wymagaj_uploadu('plik', FW_MAX_PLIK_B);

    if ($_FILES['plik']['size'] > FW_MAX_PLIK_B) {
        fw_blad(422, 'Plik przekracza limit ' . (FW_MAX_PLIK_B / 1048576) . ' MB.');
    }

    $rozszerzenie = strtolower(pathinfo((string) $_FILES['plik']['name'], PATHINFO_EXTENSION));
    $opis = ($_POST['rodzaj'] ?? '') === 'allegro'
        ? fw_rozpoznaj_zdjecie_allegro($_FILES['plik']['tmp_name'])
        : fw_rozpoznaj_plik($_FILES['plik']['tmp_name'], $rozszerzenie);
    if ($opis === null) {
        fw_blad(422, 'Nieobsługiwany albo uszkodzony plik. Przyjmujemy wideo (MP4, WEBM, MOV, AVI), '
            . 'animacje (GIF), modele 3D (STL, OBJ, 3MF, STEP) oraz szkice (PDF, DXF, GCODE).');
    }

    $limit = fw_limit_dla_rodzaju($opis['rodzaj']);
    if ($_FILES['plik']['size'] > $limit) {
        fw_blad(422, 'Plik jest za duży. Maksimum to ' . (int) ($limit / 1048576) . ' MB.');
    }

    if (!is_dir(FW_KATALOG_PLIKOW) && !@mkdir(FW_KATALOG_PLIKOW, 0755, true)) {
        fw_blad(500, 'Nie mogę utworzyć katalogu na pliki produktów.');
    }

    $nazwaPliku = $produktId . '-' . bin2hex(random_bytes(6)) . '.' . $opis['rozszerzenie'];
    $cel = FW_KATALOG_PLIKOW . '/' . $nazwaPliku;
    if (!move_uploaded_file($_FILES['plik']['tmp_name'], $cel)) {
        fw_blad(500, 'Nie udało się zapisać pliku na serwerze.');
    }
    @chmod($cel, 0644);

    $podpis = fw_tekst(fw_pole('opis'), 'Opis pliku', 0, 190);
    $pozycja = (int) (fw_pole('pozycja') ?: 100);

    $pdo->prepare('INSERT INTO ' . fw_tabela('produkty_pliki')
        . ' (produkt_id, plik, rodzaj, mime, opis, rozmiar_b, pozycja) VALUES (?,?,?,?,?,?,?)')
        ->execute([$produktId, $nazwaPliku, $opis['rodzaj'], $opis['mime'], $podpis, (int) $_FILES['plik']['size'], $pozycja]);

    fw_odpowiedz([
        'ok'   => true,
        'plik' => [
            'id'      => (int) $pdo->lastInsertId(),
            'src'     => '/assets/sklep/' . $nazwaPliku,
            'rodzaj'  => $opis['rodzaj'],
            'mime'    => $opis['mime'],
            'opis'    => $podpis,
            'rozmiar' => (int) $_FILES['plik']['size'],
        ],
    ], 201);
}

if ($akcja === 'plik-usun') {
    fw_wymagaj_post();
    fw_wymagaj_admina_lub_tokenu(true);
    fw_zapewnij_tabele_plikow($pdo);

    $id = fw_id('id');
    $st = $pdo->prepare('SELECT plik FROM ' . fw_tabela('produkty_pliki') . ' WHERE id = ?');
    $st->execute([$id]);
    $plik = $st->fetchColumn();
    if ($plik === false) {
        fw_blad(404, 'Nie ma takiego pliku.');
    }
    $pdo->prepare('DELETE FROM ' . fw_tabela('produkty_pliki') . ' WHERE id = ?')->execute([$id]);
    @unlink(FW_KATALOG_PLIKOW . '/' . $plik);

    fw_odpowiedz(['ok' => true]);
}

if ($akcja === 'obraz-usun') {
    fw_wymagaj_post();
    fw_wymagaj_admina_lub_tokenu(true);
    fw_zapewnij_tabele_sklepu();

    $id = fw_id('id');
    $st = $pdo->prepare('SELECT plik FROM ' . fw_tabela('produkty_obrazy') . ' WHERE id = ?');
    $st->execute([$id]);
    $plik = $st->fetchColumn();
    if ($plik === false) {
        fw_blad(404, 'Nie ma takiego zdjęcia.');
    }
    $sciezka = FW_KATALOG_OBRAZOW . '/' . basename((string) $plik);
    if (is_file($sciezka)) {
        @unlink($sciezka);
    }
    $pdo->prepare('DELETE FROM ' . fw_tabela('produkty_obrazy') . ' WHERE id = ?')->execute([$id]);
    fw_odpowiedz(['ok' => true]);
}

// ------------------------------------------------------------------- profil

if ($akcja === 'profil') {
    $u = fw_wymagaj_logowania();
    fw_zapewnij_tabele_sklepu();
    $st = $pdo->prepare('SELECT * FROM ' . fw_tabela('adresy') . ' WHERE uzytkownik_id = ?');
    $st->execute([$u['id']]);
    $a = $st->fetch() ?: [];
    unset($a['uzytkownik_id'], $a['zmieniony']);
    fw_odpowiedz(['ok' => true, 'adres' => $a, 'email' => $u['email']]);
}

if ($akcja === 'profil-zapisz') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    $u = fw_wymagaj_logowania();
    fw_limit('profil', 60, 3600);
    fw_zapewnij_tabele_sklepu();

    $pola = [
        'imie'     => fw_tekst(fw_pole('imie'), 'Imię', 0, 80),
        'nazwisko' => fw_tekst(fw_pole('nazwisko'), 'Nazwisko', 0, 80),
        'telefon'  => fw_tekst(fw_pole('telefon'), 'Telefon', 0, 30),
        'ulica'    => fw_tekst(fw_pole('ulica'), 'Ulica', 0, 120),
        'nr_domu'  => fw_tekst(fw_pole('nr_domu'), 'Numer domu', 0, 20),
        'nr_lokalu' => fw_tekst(fw_pole('nr_lokalu'), 'Numer lokalu', 0, 20),
        'kod'      => fw_tekst(fw_pole('kod'), 'Kod pocztowy', 0, 10),
        'miasto'   => fw_tekst(fw_pole('miasto'), 'Miejscowość', 0, 90),
        'firma'    => fw_tekst(fw_pole('firma'), 'Firma', 0, 160),
        'nip'      => fw_tekst(fw_pole('nip'), 'NIP', 0, 20),
    ];
    if ($pola['kod'] !== '' && !preg_match('/^\d{2}-\d{3}$/', $pola['kod'])) {
        fw_blad(422, 'Kod pocztowy w formacie 00-000.');
    }

    $kolumny = array_keys($pola);
    $wartosci = array_values($pola);
    $pdo->prepare('INSERT INTO ' . fw_tabela('adresy')
        . ' (uzytkownik_id, ' . implode(', ', $kolumny) . ', zmieniony)'
        . ' VALUES (?' . str_repeat(',?', count($kolumny)) . ',?)'
        . ' ON DUPLICATE KEY UPDATE '
        . implode(', ', array_map(static fn($k) => "$k = VALUES($k)", $kolumny))
        . ', zmieniony = VALUES(zmieniony)')
        ->execute(array_merge([$u['id']], $wartosci, [fw_teraz()]));

    fw_odpowiedz(['ok' => true]);
}

// --------------------------------------------------------------- zamówienia

if ($akcja === 'zamow') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();

    // ZAMOWIENIE BEZ KONTA.
    //
    // Wczesniej kupic mogl wylacznie ktos zalogowany i z potwierdzonym adresem —
    // czyli klient z ulicy musial zalozyc konto, znalezc maila z linkiem, kliknac
    // i dopiero wtedy zaplacic. Kazdy z tych krokow to miejsce, w ktorym czlowiek
    // zamyka karte. Teraz konto jest opcja, nie warunkiem.
    //
    // Konto nadal ma sens i nadal jest wygodniejsze: adres wpisany raz, historia
    // zamowien w jednym miejscu. Ale to ma byc zacheta, a nie bramka.
    $u = fw_uzytkownik();
    fw_limit('zamowienie', 10, 3600);
    fw_zapewnij_tabele_sklepu();
    fw_zapewnij_kolumny_zamowien();

    if ($u !== null && (int) ($u['email_potwierdzony'] ?? 1) === 0) {
        fw_blad(403, 'Najpierw potwierdź adres e-mail — wysłaliśmy na niego wiadomość z linkiem.');
    }

    $we = fw_wejscie();
    $koszyk = $we['koszyk'] ?? [];
    if (!is_array($koszyk) || !$koszyk) {
        fw_blad(422, 'Koszyk jest pusty.');
    }
    $dostawa = fw_pole('dostawa');
    if (!isset(FW_DOSTAWA[$dostawa])) {
        fw_blad(422, 'Nieznany sposób dostawy.');
    }
    $platnosc = fw_pole('platnosc');
    if (!isset(fw_platnosci()[$platnosc])) {
        fw_blad(422, 'Nieznany sposób zapłaty.');
    }
    if ($platnosc === 'przy_odbiorze' && $dostawa !== 'odbior') {
        fw_blad(422, 'Zapłata przy odbiorze jest możliwa tylko przy odbiorze osobistym.');
    }

    // Zgoda na regulamin i pouczenie o odstapieniu.
    //
    // Haczyk w formularzu z atrybutem `required` blokuje wyslanie w przegladarce
    // i tyle — nie jest ani dowodem, ani przeszkoda dla czegokolwiek, co pomija
    // formularz. Sprawdzamy ja tutaj i zapisujemy razem z zamowieniem, bo przy
    // sporze liczy sie zapis po stronie sklepu, a nie stan pola w cudzej
    // przegladarce.
    $zgoda = $we['zgoda'] ?? false;
    if ($zgoda !== true && $zgoda !== 'true' && $zgoda !== 1 && $zgoda !== '1') {
        fw_blad(422, 'Zaznacz zgodę na regulamin i pouczenie o odstąpieniu.');
    }

    // Ceny bierzemy z bazy, nigdy z koszyka przegladarki. Klient przysyla
    // wylacznie identyfikatory i ilosci — reszta to dane, ktore kontrolujemy.
    $idki = [];
    foreach ($koszyk as $poz) {
        $pid = (int) ($poz['id'] ?? 0);
        if ($pid > 0) {
            $idki[$pid] = max(1, min(99, (int) ($poz['ilosc'] ?? 1)));
        }
    }
    if (!$idki) {
        fw_blad(422, 'Koszyk jest pusty.');
    }
    $znaki = implode(',', array_fill(0, count($idki), '?'));
    $st = $pdo->prepare('SELECT id, nazwa, cena_gr, cena_promo_gr, stan FROM ' . fw_tabela('produkty')
        . ' WHERE id IN (' . $znaki . ') AND status = "opublikowany"');
    $st->execute(array_keys($idki));
    $produkty = $st->fetchAll();
    if (count($produkty) !== count($idki)) {
        fw_blad(422, 'Któryś z produktów przestał być dostępny. Odśwież koszyk.');
    }

    $towar = 0;
    $pozycje = [];
    foreach ($produkty as $p) {
        $pid = (int) $p['id'];
        $ilosc = $idki[$pid];
        if ($p['stan'] !== null && (int) $p['stan'] < $ilosc) {
            fw_blad(422, 'Produkt „' . $p['nazwa'] . '" nie jest dostępny w takiej ilości.');
        }
        $cena = $p['cena_promo_gr'] !== null ? (int) $p['cena_promo_gr'] : (int) $p['cena_gr'];
        $towar += $cena * $ilosc;
        $pozycje[] = [
            'id' => $pid, 'nazwa' => $p['nazwa'], 'cena_gr' => $cena,
            'ilosc' => $ilosc, 'ma_stan' => $p['stan'] !== null,
        ];
    }

    // Adres: zalogowany bierze swoj z konta, gosc podaje w formularzu.
    if ($u !== null) {
        $st = $pdo->prepare('SELECT * FROM ' . fw_tabela('adresy') . ' WHERE uzytkownik_id = ?');
        $st->execute([$u['id']]);
        $adres = $st->fetch() ?: [];
        $email = (string) $u['email'];
    } else {
        $email = mb_strtolower(trim((string) fw_pole('email')), 'UTF-8');
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            fw_blad(422, 'Podaj poprawny adres e-mail — na niego wyślemy potwierdzenie.');
        }
        $adres = [
            'imie'     => fw_tekst(fw_pole('imie'), 'Imię', 0, 60),
            'nazwisko' => fw_tekst(fw_pole('nazwisko'), 'Nazwisko', 0, 60),
            'telefon'  => fw_tekst(fw_pole('telefon'), 'Telefon', 0, 30),
            'ulica'    => fw_tekst(fw_pole('ulica'), 'Ulica i numer', 0, 120),
            'kod'      => fw_tekst(fw_pole('kod'), 'Kod pocztowy', 0, 12),
            'miasto'   => fw_tekst(fw_pole('miasto'), 'Miejscowość', 0, 80),
            'firma'    => fw_tekst(fw_pole('firma'), 'Firma', 0, 120),
            'nip'      => fw_tekst(fw_pole('nip'), 'NIP', 0, 20),
        ];
    }

    // Przy odbiorze osobistym adres nie jest potrzebny, ale kontakt juz tak —
    // inaczej nie ma jak powiedziec, ze wyrob czeka.
    $wymagane = $dostawa !== 'odbior'
        ? ['imie', 'nazwisko', 'telefon', 'ulica', 'kod', 'miasto']
        : ['imie', 'telefon'];
    foreach ($wymagane as $pole) {
        if (trim((string) ($adres[$pole] ?? '')) === '') {
            fw_blad(422, $u !== null
                ? 'Uzupełnij dane do wysyłki w zakładce „Moje dane".'
                : 'Uzupełnij dane do wysyłki w formularzu zamówienia.');
        }
    }

    $dostawaGr = FW_DOSTAWA[$dostawa]['cena_gr'];
    $numer = date('Ymd') . '-' . strtoupper(bin2hex(random_bytes(3)));

    $pdo->beginTransaction();
    try {
        $pdo->prepare('INSERT INTO ' . fw_tabela('zamowienia')
            . ' (numer, uzytkownik_id, email, status, towar_gr, dostawa_gr, suma_gr,'
            . '  sposob_dostawy, sposob_platnosci, adres, uwagi, utworzone, zgoda, gosc)'
            . ' VALUES (?,?,?,"nowe",?,?,?,?,?,?,?,?,?,?)')
            ->execute([$numer, $u !== null ? (int) $u['id'] : 0, $email,
                $towar, $dostawaGr, $towar + $dostawaGr,
                $dostawa, $platnosc, json_encode($adres, JSON_UNESCAPED_UNICODE),
                mb_substr(fw_pole('uwagi'), 0, 2000, 'UTF-8'), fw_teraz(),
                fw_teraz(), $u !== null ? 0 : 1]);
        $zid = (int) $pdo->lastInsertId();

        $wstaw = $pdo->prepare('INSERT INTO ' . fw_tabela('zamowienia_pozycje')
            . ' (zamowienie_id, produkt_id, nazwa, cena_gr, ilosc) VALUES (?,?,?,?,?)');
        foreach ($pozycje as $poz) {
            $wstaw->execute([$zid, $poz['id'], $poz['nazwa'], $poz['cena_gr'], $poz['ilosc']]);
            if ($poz['ma_stan']) {
                $pdo->prepare('UPDATE ' . fw_tabela('produkty')
                    . ' SET stan = GREATEST(0, stan - ?) WHERE id = ? AND stan IS NOT NULL')
                    ->execute([$poz['ilosc'], $poz['id']]);
            }
        }
        $pdo->commit();
    } catch (Throwable $e) {
        $pdo->rollBack();
        fw_blad(500, 'Nie udało się zapisać zamówienia. Spróbuj ponownie.');
    }

    fw_powiadom_o_zamowieniu($numer, $email, $towar + $dostawaGr, $pozycje, $platnosc, $dostawa);

    fw_odpowiedz([
        'ok' => true,
        'numer' => $numer,
        'suma_gr' => $towar + $dostawaGr,
        'platnosc' => fw_platnosci()[$platnosc],
        'komunikat' => ($platnosc === 'przelew'
            ? 'Zamówienie przyjęte. Dane do przelewu wysłaliśmy na Twój adres e-mail.'
            : 'Zamówienie przyjęte. Zapłacisz przy odbiorze w warsztacie.')
            . ($u === null
                ? ' Numer zamówienia zapisz sobie — bez konta to jedyny sposób,'
                  . ' żeby o nie zapytać.'
                : ''),
    ], 201);
}

if ($akcja === 'moje-zamowienia') {
    $u = fw_wymagaj_logowania();
    fw_zapewnij_tabele_sklepu();
    fw_zapewnij_kolumny_zamowien();
    $st = $pdo->prepare('SELECT id, numer, status, suma_gr, sposob_dostawy, sposob_platnosci,'
        . ' przesylka, utworzone'
        . ' FROM ' . fw_tabela('zamowienia')
        . ' WHERE uzytkownik_id = ? AND uzytkownik_id > 0 ORDER BY utworzone DESC LIMIT 100');
    $st->execute([$u['id']]);
    $zamowienia = $st->fetchAll();

    foreach ($zamowienia as &$z) {
        $poz = $pdo->prepare('SELECT nazwa, cena_gr, ilosc FROM ' . fw_tabela('zamowienia_pozycje')
            . ' WHERE zamowienie_id = ?');
        $poz->execute([(int) $z['id']]);
        $z['pozycje'] = $poz->fetchAll();
        unset($z['id']);
    }
    unset($z);

    fw_odpowiedz(['ok' => true, 'zamowienia' => $zamowienia]);
}

if ($akcja === 'admin-zamowienia') {
    fw_wymagaj_admina();
    fw_zapewnij_tabele_sklepu();
    fw_zapewnij_kolumny_zamowien();
    // LEFT JOIN, NIE JOIN. Zwykly JOIN gubil kazde zamowienie zlozone bez konta
    // (uzytkownik_id = 0) — czyli od chwili wpuszczenia gosci najwazniejsze
    // zamowienia znikalyby z panelu, a sprzedawca dowiadywalby sie o nich
    // wylacznie z maila. Zamiast nicku pokazujemy wtedy „gość".
    $st = $pdo->query('SELECT z.*, COALESCE(u.nick, "gość") AS nick FROM '
        . fw_tabela('zamowienia') . ' z'
        . ' LEFT JOIN ' . fw_tabela('uzytkownicy') . ' u ON u.id = z.uzytkownik_id'
        . ' ORDER BY z.utworzone DESC LIMIT 200');
    $zamowienia = $st->fetchAll();
    foreach ($zamowienia as &$z) {
        $poz = $pdo->prepare('SELECT nazwa, cena_gr, ilosc FROM ' . fw_tabela('zamowienia_pozycje')
            . ' WHERE zamowienie_id = ?');
        $poz->execute([(int) $z['id']]);
        $z['pozycje'] = $poz->fetchAll();
        $z['adres'] = json_decode((string) $z['adres'], true) ?: [];
    }
    unset($z);
    fw_odpowiedz(['ok' => true, 'zamowienia' => $zamowienia]);
}

if ($akcja === 'zamowienie-status') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    fw_wymagaj_admina();
    fw_zapewnij_tabele_sklepu();

    fw_zapewnij_kolumny_zamowien();

    $id = fw_id('id');
    $status = fw_pole('status');
    if (!in_array($status, FW_STATUSY_ZAMOWIENIA, true)) {
        fw_blad(422, 'Nieznany status zamówienia.');
    }
    $przesylka = fw_tekst(fw_pole('przesylka'), 'Numer przesyłki', 0, 64);

    $st = $pdo->prepare('SELECT numer, email, status, przesylka FROM '
        . fw_tabela('zamowienia') . ' WHERE id = ?');
    $st->execute([$id]);
    $zam = $st->fetch();
    if (!$zam) {
        fw_blad(404, 'Nie ma takiego zamówienia.');
    }
    $poprzedni = (string) $zam['status'];
    $numerPrzesylki = $przesylka !== '' ? $przesylka : (string) $zam['przesylka'];

    $pdo->prepare('UPDATE ' . fw_tabela('zamowienia')
        . ' SET status = ?, przesylka = ? WHERE id = ?')
        ->execute([$status, $numerPrzesylki, $id]);

    // ANULOWANIE ODDAJE TOWAR NA STAN.
    //
    // Stan schodzi w chwili zlozenia zamowienia — takze przy przelewie, ktory
    // moze nigdy nie przyjsc. Bez tego zwrotu kazde porzucone zamowienie
    // zabieralo sztuke z magazynu na stale, a sklep pokazywal „brak" przy
    // wyrobie lezacym na polce. Warunek na poprzedni status jest po to, zeby
    // dwa klikniecia „anulowane" nie oddaly towaru dwa razy.
    if ($status === 'anulowane' && $poprzedni !== 'anulowane') {
        $poz = $pdo->prepare('SELECT produkt_id, ilosc FROM '
            . fw_tabela('zamowienia_pozycje') . ' WHERE zamowienie_id = ?');
        $poz->execute([$id]);
        $oddaj = $pdo->prepare('UPDATE ' . fw_tabela('produkty')
            . ' SET stan = stan + ? WHERE id = ? AND stan IS NOT NULL');
        foreach ($poz->fetchAll() as $pozycja) {
            $oddaj->execute([(int) $pozycja['ilosc'], (int) $pozycja['produkt_id']]);
        }
    }

    // Klient dowiaduje sie o zmianie tylko wtedy, gdy naprawde sie zmienila.
    if ($status !== $poprzedni) {
        fw_powiadom_o_statusie((string) $zam['numer'], (string) $zam['email'],
            $status, $numerPrzesylki);
    }

    fw_odpowiedz(['ok' => true, 'status' => $status, 'przesylka' => $numerPrzesylki]);
}

if ($akcja === 'ustawienia') {
    // Dane potrzebne stronom koszyka i zamowienia: sposoby dostawy i zaplaty
    // w jednym miejscu, zeby nie powtarzac ich w JavaScripcie.
    fw_odpowiedz([
        'ok' => true,
        'dostawa' => FW_DOSTAWA,
        'platnosci' => fw_platnosci(),
    ]);
}

fw_blad(404, 'Nieznana akcja.');
