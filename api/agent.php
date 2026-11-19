<?php
declare(strict_types=1);

/**
 * API Agenta Administratora Forum — fwdrucik.pl.
 *
 * Dostęp wyłącznie z poprawnym nagłówkiem X-Agent-Token lub dla zalogowanego admina:
 *   GET  /api/agent.php?akcja=status             — statystyki, stan wątków bazowych
 *   GET  /api/agent.php?akcja=nieodpowiedziane   — wątki czekające na odpowiedź eksperta
 *   GET  /api/agent.php?akcja=kolejka            — wpisy oczekujące na moderację
 *   POST /api/agent.php?akcja=zaloz-watek        — kategoria, tytul, tresc (jako Admin)
 *   POST /api/agent.php?akcja=odpowiedz          — watek_id, tresc (jako Admin)
 *   POST /api/agent.php?akcja=moderuj            — typ (watek/odpowiedz), id, decyzja (zatwierdz/odrzuc)
 */

require_once __DIR__ . '/_lib.php';

// ----------------------------------------------------------- Uwierzytelnienie
$cfg = fw_konfiguracja();
$wymagany_token = (string) ($cfg['agent_token'] ?? '');
$naglowek_token = (string) ($_SERVER['HTTP_X_AGENT_TOKEN'] ?? '');

$autoryzowany = false;

// 1. Sprawdzenie tokenu agenta (jeśli skonfigurowany)
if ($wymagany_token !== '' && $naglowek_token !== '' && hash_equals($wymagany_token, $naglowek_token)) {
    $autoryzowany = true;
}

// 2. Sprawdzenie sesji admina jako alternatywy
if (!$autoryzowany) {
    $uzytkownik = fw_uzytkownik();
    if ($uzytkownik !== null && ($uzytkownik['rola'] === 'admin')) {
        $autoryzowany = true;
    }
}

// 3. Tryb lokalny deweloperski (jeśli wywołano z localhost / CLI)
$klient_ip = fw_ip();
if (!$autoryzowany && in_array($klient_ip, ['127.0.0.1', '::1'], true) && $wymagany_token === '') {
    $autoryzowany = true;
}

if (!$autoryzowany) {
    fw_blad(401, 'Brak autoryzacji agenta. Wymagany poprawny nagłówek X-Agent-Token lub sesja administratora.');
}

$akcja = fw_akcja();
$pdo = fw_baza();

/**
 * Zwraca ID konta administratora. Tworzy dedykowane konto Admin AI, jeśli brak.
 */
function fw_id_konta_admina(PDO $pdo): int
{
    // 1. Dedykowany nick Admin AI
    $st = $pdo->prepare('SELECT id FROM ' . fw_tabela('uzytkownicy') . ' WHERE nick = ? LIMIT 1');
    $st->execute(['Admin AI - F.W. DRUCIK']);
    $id = $st->fetchColumn();
    if ($id) {
        return (int) $id;
    }

    // 2. Konto główne fwdrucik@gmail.com
    $st = $pdo->prepare('SELECT id FROM ' . fw_tabela('uzytkownicy') . ' WHERE email = ? LIMIT 1');
    $st->execute(['fwdrucik@gmail.com']);
    $id = $st->fetchColumn();
    if ($id) {
        $pdo->prepare('UPDATE ' . fw_tabela('uzytkownicy') . ' SET rola = "admin", zaufany = 1 WHERE id = ?')
            ->execute([$id]);
        return (int) $id;
    }

    // 3. Jakikolwiek admin w bazie
    $st = $pdo->query('SELECT id FROM ' . fw_tabela('uzytkownicy') . ' WHERE rola = "admin" ORDER BY id ASC LIMIT 1');
    $id = $st->fetchColumn();
    if ($id) {
        return (int) $id;
    }

    // 4. Utworzenie nowego konta Administratora AI
    $losowe_haslo = bin2hex(random_bytes(24));
    $haslo_hash = password_hash($losowe_haslo, PASSWORD_DEFAULT);
    $teraz = fw_teraz();

    $st = $pdo->prepare('INSERT INTO ' . fw_tabela('uzytkownicy')
        . ' (nick, email, haslo_hash, rola, zaufany, utworzony)'
        . ' VALUES (?, ?, ?, "admin", 1, ?)');
    $st->execute(['Admin AI - F.W. DRUCIK', 'fwdrucik@gmail.com', $haslo_hash, $teraz]);
    return (int) $pdo->lastInsertId();
}

// ----------------------------------------------------------------- STATUS FORUM
if ($akcja === 'status') {
    $st = $pdo->query('SELECT kategoria, COUNT(*) AS ile FROM ' . fw_tabela('watki')
        . ' WHERE status = "opublikowany" GROUP BY kategoria');
    $kategorie = [];
    foreach ($st->fetchAll() as $row) {
        $kategorie[$row['kategoria']] = (int) $row['ile'];
    }

    $bazowe = ['regulamin', 'witam', 'faq', 'poczekalnia', 'general', 'instrukcje', 'ksiazkiserwisowe'];
    $obecne_bazowe = [];
    $st = $pdo->query('SELECT id, kategoria, tytul FROM ' . fw_tabela('watki')
        . ' WHERE status = "opublikowany" AND kategoria IN ("' . implode('","', $bazowe) . '")');
    foreach ($st->fetchAll() as $row) {
        $obecne_bazowe[$row['kategoria']] = [
            'id'    => (int) $row['id'],
            'tytul' => $row['tytul'],
        ];
    }

    $st = $pdo->query('SELECT COUNT(*) FROM ' . fw_tabela('watki') . ' WHERE status = "oczekuje"');
    $watki_oczekujace = (int) $st->fetchColumn();

    $st = $pdo->query('SELECT COUNT(*) FROM ' . fw_tabela('odpowiedzi') . ' WHERE status = "oczekuje"');
    $odpowiedzi_oczekujace = (int) $st->fetchColumn();

    $st = $pdo->query('SELECT COUNT(*) FROM ' . fw_tabela('watki') . ' WHERE status = "opublikowany"');
    $watki_lacznie = (int) $st->fetchColumn();

    $st = $pdo->query('SELECT COUNT(*) FROM ' . fw_tabela('odpowiedzi') . ' WHERE status = "opublikowany"');
    $odpowiedzi_lacznie = (int) $st->fetchColumn();

    fw_odpowiedz([
        'ok' => true,
        'forum' => [
            'watki_opublikowane'     => $watki_lacznie,
            'odpowiedzi_opublikowane'=> $odpowiedzi_lacznie,
            'kategorie'              => $kategorie,
            'watki_bazowe'           => $obecne_bazowe,
            'brakujace_bazowe'       => array_values(array_diff($bazowe, array_keys($obecne_bazowe))),
            'kolejka_oczekuje'       => [
                'watki'      => $watki_oczekujace,
                'odpowiedzi' => $odpowiedzi_oczekujace,
                'suma'       => $watki_oczekujace + $odpowiedzi_oczekujace,
            ]
        ]
    ]);
}

// ----------------------------------------------------- WĄTKI BEZ ODPOWIEDZI
if ($akcja === 'nieodpowiedziane') {
    $admin_id = fw_id_konta_admina($pdo);

    $sql = 'SELECT w.id, w.kategoria, w.tytul, w.tresc, w.utworzony, a.nick AS autor,'
         . ' (SELECT COUNT(*) FROM ' . fw_tabela('odpowiedzi') . ' o WHERE o.watek_id = w.id AND o.status = "opublikowany") AS liczba_odp,'
         . ' (SELECT COUNT(*) FROM ' . fw_tabela('odpowiedzi') . ' o WHERE o.watek_id = w.id AND o.autor_id = ? AND o.status = "opublikowany") AS odp_admina'
         . ' FROM ' . fw_tabela('watki') . ' w'
         . ' JOIN ' . fw_tabela('uzytkownicy') . ' a ON a.id = w.autor_id'
         . ' WHERE w.status = "opublikowany"'
         . '   AND w.autor_id != ?'
         . ' HAVING odp_admina = 0'
         . ' ORDER BY w.utworzony ASC LIMIT 25';

    $st = $pdo->prepare($sql);
    $st->execute([$admin_id, $admin_id]);

    $wyniki = array_map(static fn(array $r): array => [
        'id'          => (int) $r['id'],
        'kategoria'   => $r['kategoria'],
        'tytul'       => $r['tytul'],
        'tresc'       => $r['tresc'],
        'autor'       => $r['autor'],
        'liczba_odp'  => (int) $r['liczba_odp'],
        'data'        => $r['utworzony'],
    ], $st->fetchAll());

    fw_odpowiedz(['ok' => true, 'watki' => $wyniki]);
}

// ------------------------------------------------------- KOLEJKA MODERACYJNA
if ($akcja === 'kolejka') {
    $pozycje = [];

    $st = $pdo->query('SELECT w.id, w.tytul, w.tresc, w.kategoria, w.utworzony, a.nick AS autor, a.email'
        . ' FROM ' . fw_tabela('watki') . ' w'
        . ' JOIN ' . fw_tabela('uzytkownicy') . ' a ON a.id = w.autor_id'
        . ' WHERE w.status = "oczekuje" ORDER BY w.utworzony ASC LIMIT 50');
    foreach ($st->fetchAll() as $w) {
        $pozycje[] = [
            'typ'       => 'watek',
            'id'        => (int) $w['id'],
            'kategoria' => $w['kategoria'],
            'tytul'     => $w['tytul'],
            'tresc'     => $w['tresc'],
            'autor'     => $w['autor'],
            'email'     => $w['email'],
            'data'      => $w['utworzony'],
        ];
    }

    $st = $pdo->query('SELECT o.id, o.watek_id, o.tresc, o.utworzona, a.nick AS autor, a.email, w.tytul AS watek_tytul'
        . ' FROM ' . fw_tabela('odpowiedzi') . ' o'
        . ' JOIN ' . fw_tabela('uzytkownicy') . ' a ON a.id = o.autor_id'
        . ' JOIN ' . fw_tabela('watki') . ' w ON w.id = o.watek_id'
        . ' WHERE o.status = "oczekuje" ORDER BY o.utworzona ASC LIMIT 50');
    foreach ($st->fetchAll() as $o) {
        $pozycje[] = [
            'typ'         => 'odpowiedz',
            'id'          => (int) $o['id'],
            'watek_id'    => (int) $o['watek_id'],
            'watek_tytul' => $o['watek_tytul'],
            'tresc'       => $o['tresc'],
            'autor'       => $o['autor'],
            'email'       => $o['email'],
            'data'        => $o['utworzona'],
        ];
    }

    fw_odpowiedz(['ok' => true, 'kolejka' => $pozycje]);
}

// ---------------------------------------------------- ZAŁÓŻ WĄTEK JAKO ADMIN
if ($akcja === 'zaloz-watek') {
    fw_wymagaj_post();
    $admin_id = fw_id_konta_admina($pdo);

    $kategoria = fw_kategoria(fw_pole('kategoria'));
    $tytul = fw_tekst(fw_pole('tytul'), 'Tytuł wątku', 5, 160);
    $tresc = fw_tekst(fw_pole('tresc'), 'Treść wątku', 10, 30000);
    $teraz = fw_teraz();

    $st = $pdo->prepare('INSERT INTO ' . fw_tabela('watki')
        . ' (kategoria, tytul, tresc, autor_id, status, utworzony, ostatnia_aktywnosc)'
        . ' VALUES (?, ?, ?, ?, "opublikowany", ?, ?)');
    $st->execute([$kategoria, $tytul, $tresc, $admin_id, $teraz, $teraz]);
    $nowe_id = (int) $pdo->lastInsertId();

    fw_odpowiedz([
        'ok'        => true,
        'id'        => $nowe_id,
        'kategoria' => $kategoria,
        'tytul'     => $tytul,
        'komunikat' => 'Oficjalny wątek administratora został opublikowany.'
    ], 201);
}

// -------------------------------------------------- ODPOWIEDŹ JAKO ADMIN
if ($akcja === 'odpowiedz') {
    fw_wymagaj_post();
    $admin_id = fw_id_konta_admina($pdo);

    $watek_id = fw_id('watek_id');
    $tresc = fw_tekst(fw_pole('tresc'), 'Treść odpowiedzi', 5, 30000);
    $teraz = fw_teraz();

    $st = $pdo->prepare('SELECT id, tytul FROM ' . fw_tabela('watki') . ' WHERE id = ?');
    $st->execute([$watek_id]);
    $watek = $st->fetch();
    if (!$watek) {
        fw_blad(404, 'Wątek o podanym ID nie istnieje.');
    }

    $pdo->prepare('INSERT INTO ' . fw_tabela('odpowiedzi')
        . ' (watek_id, autor_id, tresc, status, utworzona) VALUES (?, ?, ?, "opublikowany", ?)')
        ->execute([$watek_id, $admin_id, $tresc, $teraz]);
    $odp_id = (int) $pdo->lastInsertId();

    $pdo->prepare('UPDATE ' . fw_tabela('watki') . ' SET ostatnia_aktywnosc = ? WHERE id = ?')
        ->execute([$teraz, $watek_id]);

    fw_odpowiedz([
        'ok'        => true,
        'id'        => $odp_id,
        'watek_id'  => $watek_id,
        'komunikat' => 'Odpowiedź administratora została opublikowana.'
    ], 201);
}

// --------------------------------------------------------- AUTO-MODERACJA
if ($akcja === 'moderuj') {
    fw_wymagaj_post();

    $typ = fw_pole('typ');
    $id = fw_id('id');
    $decyzja = fw_pole('decyzja');

    if (!in_array($typ, ['watek', 'odpowiedz'], true)) {
        fw_blad(422, 'Niepoprawny typ treści.');
    }
    if (!in_array($decyzja, ['zatwierdz', 'odrzuc'], true)) {
        fw_blad(422, 'Niepoprawna decyzja moderacyjna.');
    }

    $nowy_status = $decyzja === 'zatwierdz' ? 'opublikowany' : 'odrzucony';
    $tabela = fw_tabela($typ === 'watek' ? 'watki' : 'odpowiedzi');

    $st = $pdo->prepare('SELECT autor_id FROM ' . $tabela . ' WHERE id = ?');
    $st->execute([$id]);
    $autor_id = (int) $st->fetchColumn();

    if ($autor_id <= 0) {
        fw_blad(404, 'Nie znaleziono wpisu do moderacji.');
    }

    $pdo->prepare('UPDATE ' . $tabela . ' SET status = ? WHERE id = ?')
        ->execute([$nowy_status, $id]);

    if ($decyzja === 'zatwierdz') {
        $pdo->prepare('UPDATE ' . fw_tabela('uzytkownicy') . ' SET zaufany = 1 WHERE id = ?')
            ->execute([$autor_id]);
    }

    fw_odpowiedz([
        'ok'          => true,
        'typ'         => $typ,
        'id'          => $id,
        'nowy_status' => $nowy_status,
        'komunikat'   => 'Zaktualizowano status pozycji.'
    ]);
}

fw_blad(404, 'Nieznana akcja API Agenta.');
