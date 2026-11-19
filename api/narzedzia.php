<?php
declare(strict_types=1);

/**
 * Notatnik i kalendarz zalogowanego użytkownika.
 *
 *   GET  /api/narzedzia.php?akcja=notatki
 *   POST /api/narzedzia.php?akcja=notatka-zapisz   — id?, tytul, tresc
 *   POST /api/narzedzia.php?akcja=notatka-usun     — id
 *   GET  /api/narzedzia.php?akcja=kalendarz&od=RRRR-MM-DD&do=RRRR-MM-DD
 *   POST /api/narzedzia.php?akcja=wydarzenie-zapisz — id?, dzien, godzina?, tytul, opis?
 *   POST /api/narzedzia.php?akcja=wydarzenie-usun   — id
 *
 * Wszystko wymaga zalogowania i każdy widzi wyłącznie własne wpisy — filtr po
 * `wlasciciel_id` siedzi w każdym zapytaniu, także w UPDATE i DELETE, więc
 * podanie cudzego identyfikatora nic nie daje.
 */

require_once __DIR__ . '/_lib.php';

/**
 * Zakłada tabele notatnika i kalendarza przy pierwszym użyciu.
 *
 * Hosting nie daje shella ani MySQL z zewnątrz, a schemat wgrywa się ręcznie
 * przez phpMyAdmin. Te dwie tabele dochodzą później niż reszta, więc — tak jak
 * tabela wpisów — tworzą się same. Zapytania są idempotentne i wołane dopiero
 * po sprawdzeniu sesji.
 */
function fw_zapewnij_tabele_narzedzi(): void
{
    static $gotowe = false;
    if ($gotowe) {
        return;
    }
    $pdo = fw_baza();
    $pdo->exec(
        'CREATE TABLE IF NOT EXISTS ' . fw_tabela('notatki') . ' ('
        . ' id            INT UNSIGNED NOT NULL AUTO_INCREMENT,'
        . ' wlasciciel_id INT UNSIGNED NOT NULL,'
        . ' tytul         VARCHAR(160)  NOT NULL,'
        . ' tresc         MEDIUMTEXT    NOT NULL,'
        . ' utworzona     DATETIME      NOT NULL,'
        . ' zmieniona     DATETIME      NOT NULL,'
        . ' PRIMARY KEY (id),'
        . ' KEY idx_wlasciciel (wlasciciel_id, zmieniona)'
        . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
    );
    $pdo->exec(
        'CREATE TABLE IF NOT EXISTS ' . fw_tabela('kalendarz') . ' ('
        . ' id            INT UNSIGNED NOT NULL AUTO_INCREMENT,'
        . ' wlasciciel_id INT UNSIGNED NOT NULL,'
        . ' dzien         DATE          NOT NULL,'
        . ' godzina       TIME          NULL,'
        . ' tytul         VARCHAR(160)  NOT NULL,'
        . ' opis          TEXT          NOT NULL,'
        . ' utworzone     DATETIME      NOT NULL,'
        . ' PRIMARY KEY (id),'
        . ' KEY idx_wlasciciel (wlasciciel_id, dzien)'
        . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
    );
    $gotowe = true;
}

/** Data w formacie RRRR-MM-DD albo błąd — bez zgadywania, co użytkownik miał na myśli. */
function fw_dzien(string $wartosc, string $etykieta): string
{
    $wartosc = trim($wartosc);
    $d = DateTimeImmutable::createFromFormat('!Y-m-d', $wartosc);
    if ($d === false || $d->format('Y-m-d') !== $wartosc) {
        fw_blad(400, $etykieta . ' musi mieć format RRRR-MM-DD.');
    }
    return $wartosc;
}

/** Godzina GG:MM albo pusta wartość dla wydarzenia całodniowego. */
function fw_godzina(string $wartosc): ?string
{
    $wartosc = trim($wartosc);
    if ($wartosc === '') {
        return null;
    }
    if (!preg_match('/^([01]\d|2[0-3]):([0-5]\d)$/', $wartosc)) {
        fw_blad(400, 'Godzina musi mieć format GG:MM.');
    }
    return $wartosc . ':00';
}

$akcja = fw_akcja();
$pdo = fw_baza();

// ------------------------------------------------------------------ notatnik

if ($akcja === 'notatki') {
    $u = fw_wymagaj_logowania();
    fw_zapewnij_tabele_narzedzi();

    $st = $pdo->prepare('SELECT id, tytul, tresc, utworzona, zmieniona'
        . ' FROM ' . fw_tabela('notatki')
        . ' WHERE wlasciciel_id = ? ORDER BY zmieniona DESC LIMIT 500');
    $st->execute([$u['id']]);

    fw_odpowiedz([
        'ok'      => true,
        'notatki' => array_map(static fn(array $n): array => [
            'id'        => (int) $n['id'],
            'tytul'     => $n['tytul'],
            'tresc'     => $n['tresc'],
            'utworzona' => $n['utworzona'],
            'zmieniona' => $n['zmieniona'],
        ], $st->fetchAll()),
    ]);
}

if ($akcja === 'notatka-zapisz') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    $u = fw_wymagaj_logowania();
    fw_limit('notatka', 120, 3600);
    fw_zapewnij_tabele_narzedzi();

    $id = (int) (fw_wejscie()['id'] ?? 0);
    $tytul = fw_tekst(fw_pole('tytul'), 'Tytuł notatki', 1, 160);
    $tresc = fw_tekst(fw_pole('tresc'), 'Treść notatki', 0, 60000);
    $teraz = fw_teraz();

    if ($id > 0) {
        // Filtr po właścicielu także tutaj: cudze id po prostu nic nie zmieni.
        $st = $pdo->prepare('UPDATE ' . fw_tabela('notatki')
            . ' SET tytul = ?, tresc = ?, zmieniona = ?'
            . ' WHERE id = ? AND wlasciciel_id = ?');
        $st->execute([$tytul, $tresc, $teraz, $id, $u['id']]);
        if ($st->rowCount() === 0) {
            // Brak zmian oznacza albo cudzą notatkę, albo zapis identycznej
            // treści. Rozróżniamy to jednym zapytaniem, żeby nie kłamać
            // komunikatem o powodzeniu tam, gdzie nic się nie zapisało.
            $czy = $pdo->prepare('SELECT 1 FROM ' . fw_tabela('notatki')
                . ' WHERE id = ? AND wlasciciel_id = ?');
            $czy->execute([$id, $u['id']]);
            if ($czy->fetchColumn() === false) {
                fw_blad(404, 'Nie ma takiej notatki.');
            }
        }
    } else {
        $pdo->prepare('INSERT INTO ' . fw_tabela('notatki')
            . ' (wlasciciel_id, tytul, tresc, utworzona, zmieniona) VALUES (?, ?, ?, ?, ?)')
            ->execute([$u['id'], $tytul, $tresc, $teraz, $teraz]);
        $id = (int) $pdo->lastInsertId();
    }

    fw_odpowiedz(['ok' => true, 'id' => $id, 'zmieniona' => $teraz]);
}

if ($akcja === 'notatka-usun') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    $u = fw_wymagaj_logowania();
    fw_zapewnij_tabele_narzedzi();

    $id = fw_id('id');
    $st = $pdo->prepare('DELETE FROM ' . fw_tabela('notatki')
        . ' WHERE id = ? AND wlasciciel_id = ?');
    $st->execute([$id, $u['id']]);
    if ($st->rowCount() === 0) {
        fw_blad(404, 'Nie ma takiej notatki.');
    }

    fw_odpowiedz(['ok' => true]);
}

// ----------------------------------------------------------------- kalendarz

if ($akcja === 'kalendarz') {
    $u = fw_wymagaj_logowania();
    fw_zapewnij_tabele_narzedzi();

    $od = fw_dzien((string) ($_GET['od'] ?? ''), 'Początek zakresu');
    $do = fw_dzien((string) ($_GET['do'] ?? ''), 'Koniec zakresu');
    if ($od > $do) {
        fw_blad(400, 'Początek zakresu jest późniejszy niż koniec.');
    }

    $st = $pdo->prepare('SELECT id, dzien, godzina, tytul, opis'
        . ' FROM ' . fw_tabela('kalendarz')
        . ' WHERE wlasciciel_id = ? AND dzien BETWEEN ? AND ?'
        . ' ORDER BY dzien ASC, godzina IS NULL DESC, godzina ASC LIMIT 1000');
    $st->execute([$u['id'], $od, $do]);

    fw_odpowiedz([
        'ok'         => true,
        'wydarzenia' => array_map(static fn(array $w): array => [
            'id'      => (int) $w['id'],
            'dzien'   => $w['dzien'],
            'godzina' => $w['godzina'] === null ? '' : substr((string) $w['godzina'], 0, 5),
            'tytul'   => $w['tytul'],
            'opis'    => $w['opis'],
        ], $st->fetchAll()),
    ]);
}

if ($akcja === 'wydarzenie-zapisz') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    $u = fw_wymagaj_logowania();
    fw_limit('wydarzenie', 120, 3600);
    fw_zapewnij_tabele_narzedzi();

    $id = (int) (fw_wejscie()['id'] ?? 0);
    $dzien = fw_dzien(fw_pole('dzien'), 'Data wydarzenia');
    $godzina = fw_godzina(fw_pole('godzina'));
    $tytul = fw_tekst(fw_pole('tytul'), 'Tytuł wydarzenia', 1, 160);
    $opis = fw_tekst(fw_pole('opis'), 'Opis wydarzenia', 0, 4000);

    if ($id > 0) {
        $st = $pdo->prepare('UPDATE ' . fw_tabela('kalendarz')
            . ' SET dzien = ?, godzina = ?, tytul = ?, opis = ?'
            . ' WHERE id = ? AND wlasciciel_id = ?');
        $st->execute([$dzien, $godzina, $tytul, $opis, $id, $u['id']]);
        $czy = $pdo->prepare('SELECT 1 FROM ' . fw_tabela('kalendarz')
            . ' WHERE id = ? AND wlasciciel_id = ?');
        $czy->execute([$id, $u['id']]);
        if ($czy->fetchColumn() === false) {
            fw_blad(404, 'Nie ma takiego wydarzenia.');
        }
    } else {
        $pdo->prepare('INSERT INTO ' . fw_tabela('kalendarz')
            . ' (wlasciciel_id, dzien, godzina, tytul, opis, utworzone) VALUES (?, ?, ?, ?, ?, ?)')
            ->execute([$u['id'], $dzien, $godzina, $tytul, $opis, fw_teraz()]);
        $id = (int) $pdo->lastInsertId();
    }

    fw_odpowiedz(['ok' => true, 'id' => $id]);
}

if ($akcja === 'wydarzenie-usun') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    $u = fw_wymagaj_logowania();
    fw_zapewnij_tabele_narzedzi();

    $id = fw_id('id');
    $st = $pdo->prepare('DELETE FROM ' . fw_tabela('kalendarz')
        . ' WHERE id = ? AND wlasciciel_id = ?');
    $st->execute([$id, $u['id']]);
    if ($st->rowCount() === 0) {
        fw_blad(404, 'Nie ma takiego wydarzenia.');
    }

    fw_odpowiedz(['ok' => true]);
}

fw_blad(404, 'Nieznana akcja.');
