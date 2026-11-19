<?php
declare(strict_types=1);

/**
 * Forum dyskusyjne.
 *
 *   GET  /api/forum.php?akcja=watki&kategoria=elektro
 *   GET  /api/forum.php?akcja=watek&id=12
 *   POST /api/forum.php?akcja=nowy-watek   — kategoria, tytul, tresc
 *   POST /api/forum.php?akcja=odpowiedz    — watek_id, tresc
 *
 * Widoczne są wyłącznie treści o statusie "opublikowany"; autor dodatkowo
 * widzi własne wpisy czekające w kolejce, żeby wiedział, że nic nie zginęło.
 */

require_once __DIR__ . '/_lib.php';

$akcja = fw_akcja();
$pdo = fw_baza();
$u = fw_uzytkownik();
// 0 dla gościa — żaden wiersz nie ma autor_id = 0, więc warunek "albo mój wpis"
// po prostu nic nie dołoży.
$moje_id = $u === null ? 0 : $u['id'];

// ------------------------------------------------------------------- lista
if ($akcja === 'watki') {
    $kategoria = (string) ($_GET['kategoria'] ?? 'all');
    $warunki = ['(w.status = "opublikowany" OR w.autor_id = ?)'];
    $parametry = [$moje_id];

    if ($kategoria !== 'all' && $kategoria !== '') {
        $warunki[] = 'w.kategoria = ?';
        $parametry[] = fw_kategoria($kategoria);
    }

    $sql = 'SELECT w.id, w.kategoria, w.tytul, w.status, w.wyswietlenia,'
         . ' w.utworzony, w.ostatnia_aktywnosc, a.nick AS autor, a.id AS autor_id,'
         . ' (SELECT COUNT(*) FROM ' . fw_tabela('odpowiedzi') . ' o'
         . '   WHERE o.watek_id = w.id AND o.status = "opublikowany") AS odpowiedzi'
         . ' FROM ' . fw_tabela('watki') . ' w'
         . ' JOIN ' . fw_tabela('uzytkownicy') . ' a ON a.id = w.autor_id'
         . ' WHERE ' . implode(' AND ', $warunki)
         . ' ORDER BY w.ostatnia_aktywnosc DESC LIMIT 100';

    $st = $pdo->prepare($sql);
    $st->execute($parametry);

    $watki = array_map(static fn(array $w): array => [
        'id'           => (int) $w['id'],
        'kategoria'    => $w['kategoria'],
        'tytul'        => $w['tytul'],
        'autor'        => $w['autor'],
        'autor_id' => (int)$w['autor_id'],
        'status'       => $w['status'],
        'odpowiedzi'   => (int) $w['odpowiedzi'],
        'wyswietlenia' => (int) $w['wyswietlenia'],
        'data'         => $w['utworzony'],
        'aktywnosc'    => $w['ostatnia_aktywnosc'],
    ], $st->fetchAll());

    fw_odpowiedz(['ok' => true, 'watki' => $watki]);
}

// ------------------------------------------------------------ pojedynczy wątek
if ($akcja === 'watek') {
    $id = fw_id('id');

    $st = $pdo->prepare('SELECT w.id, w.kategoria, w.tytul, w.tresc, w.status,'
        . ' w.wyswietlenia, w.utworzony, a.nick AS autor, a.id AS autor_id'
        . ' FROM ' . fw_tabela('watki') . ' w'
        . ' JOIN ' . fw_tabela('uzytkownicy') . ' a ON a.id = w.autor_id'
        . ' WHERE w.id = ? AND (w.status = "opublikowany" OR w.autor_id = ?)');
    $st->execute([$id, $moje_id]);
    $watek = $st->fetch();
    if (!$watek) {
        fw_blad(404, 'Nie ma takiego wątku.');
    }

    // Licznik odsłon podbijany tylko dla opublikowanych — podglądy autora
    // nie mają zawyżać statystyki.
    if ($watek['status'] === 'opublikowany') {
        $pdo->prepare('UPDATE ' . fw_tabela('watki')
            . ' SET wyswietlenia = wyswietlenia + 1 WHERE id = ?')->execute([$id]);
        $watek['wyswietlenia'] = (int) $watek['wyswietlenia'] + 1;
    }

    $st = $pdo->prepare('SELECT o.id, o.tresc, o.status, o.utworzona, a.nick AS autor, a.id AS autor_id'
        . ' FROM ' . fw_tabela('odpowiedzi') . ' o'
        . ' JOIN ' . fw_tabela('uzytkownicy') . ' a ON a.id = o.autor_id'
        . ' WHERE o.watek_id = ? AND (o.status = "opublikowany" OR o.autor_id = ?)'
        . ' ORDER BY o.utworzona ASC LIMIT 500');
    $st->execute([$id, $moje_id]);

    fw_odpowiedz([
        'ok'    => true,
        'watek' => [
            'id'           => (int) $watek['id'],
            'kategoria'    => $watek['kategoria'],
            'tytul'        => $watek['tytul'],
            'tresc'        => $watek['tresc'],
            'autor'        => $watek['autor'],
            'autor_id' => (int)$watek['autor_id'],
            'status'       => $watek['status'],
            'wyswietlenia' => (int) $watek['wyswietlenia'],
            'data'         => $watek['utworzony'],
        ],
        'odpowiedzi' => array_map(static fn(array $o): array => [
            'id'     => (int) $o['id'],
            'tresc'  => $o['tresc'],
            'autor'  => $o['autor'],
            'autor_id' => (int)$o['autor_id'],
            'status' => $o['status'],
            'data'   => $o['utworzona'],
        ], $st->fetchAll()),
    ]);
}

// ---------------------------------------------------------------- nowy wątek
if ($akcja === 'nowy-watek') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    $u = fw_wymagaj_logowania();
    fw_limit('watek', 5, 3600);

    $kategoria = fw_kategoria(fw_pole('kategoria'));
    $tytul = fw_tekst(fw_pole('tytul'), 'Tytuł wątku', 10, 160);
    $tresc = fw_tekst(fw_pole('tresc'), 'Treść wątku', 20, 8000);
    $status = fw_status_dla($u);
    $teraz = fw_teraz();

    $st = $pdo->prepare('INSERT INTO ' . fw_tabela('watki')
        . ' (kategoria, tytul, tresc, autor_id, status, utworzony, ostatnia_aktywnosc)'
        . ' VALUES (?, ?, ?, ?, ?, ?, ?)');
    $st->execute([$kategoria, $tytul, $tresc, $u['id'], $status, $teraz, $teraz]);

    fw_odpowiedz([
        'ok'        => true,
        'id'        => (int) $pdo->lastInsertId(),
        'status'    => $status,
        'komunikat' => $status === 'opublikowany'
            ? 'Wątek opublikowany.'
            : 'Wątek trafił do zatwierdzenia — pokaże się po sprawdzeniu przez moderatora.',
    ], 201);
}

// ----------------------------------------------------------------- odpowiedź
if ($akcja === 'odpowiedz') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    $u = fw_wymagaj_logowania();
    fw_limit('odpowiedz', 20, 3600);

    $watek_id = fw_id('watek_id');
    $tresc = fw_tekst(fw_pole('tresc'), 'Treść odpowiedzi', 5, 8000);

    $st = $pdo->prepare('SELECT id FROM ' . fw_tabela('watki')
        . ' WHERE id = ? AND status = "opublikowany"');
    $st->execute([$watek_id]);
    if (!$st->fetch()) {
        fw_blad(404, 'Nie ma takiego wątku albo czeka on jeszcze na zatwierdzenie.');
    }

    $status = fw_status_dla($u);
    $pdo->prepare('INSERT INTO ' . fw_tabela('odpowiedzi')
        . ' (watek_id, autor_id, tresc, status, utworzona) VALUES (?, ?, ?, ?, ?)')
        ->execute([$watek_id, $u['id'], $tresc, $status, fw_teraz()]);

    if ($status === 'opublikowany') {
        $pdo->prepare('UPDATE ' . fw_tabela('watki') . ' SET ostatnia_aktywnosc = ? WHERE id = ?')
            ->execute([fw_teraz(), $watek_id]);
    }

    fw_odpowiedz([
        'ok'        => true,
        'id'        => (int) $pdo->lastInsertId(),
        'status'    => $status,
        'komunikat' => $status === 'opublikowany'
            ? 'Odpowiedź dodana.'
            : 'Odpowiedź czeka na zatwierdzenie przez moderatora.',
    ], 201);
}

fw_blad(404, 'Nieznana akcja.');
