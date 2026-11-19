<?php
declare(strict_types=1);

/**
 * Komentarze pod wpisami blogowymi.
 *
 *   GET  /api/komentarze.php?akcja=lista&slug=regeneracja-alternatorow-pultusk
 *   POST /api/komentarze.php?akcja=dodaj   — slug, tresc
 */

require_once __DIR__ . '/_spolecznosc.php';

$akcja = fw_akcja();
$pdo = fw_baza();

if ($akcja === 'lista') {
    $slug = fw_slug((string) ($_GET['slug'] ?? ''));
    $ja = fw_uzytkownik();
    $moje_id = $ja === null ? 0 : $ja['id'];

    $st = $pdo->prepare('SELECT k.id, k.autor_id, k.tresc, k.status, k.utworzony, a.nick AS autor'
        . ' FROM ' . fw_tabela('komentarze') . ' k'
        . ' JOIN ' . fw_tabela('uzytkownicy') . ' a ON a.id = k.autor_id'
        . ' WHERE k.slug = ? AND (k.status = "opublikowany" OR k.autor_id = ?)'
        . ' ORDER BY k.utworzony ASC LIMIT 300');
    $st->execute([$slug, $moje_id]);

    $rows = $st->fetchAll();
    $replies=[];
    if (fw_spolecznosc_gotowa()) {
        $rs=$pdo->prepare('SELECT f.tresc_id,f.tresc FROM ' . fw_tabela('odpowiedzi_firmy') . ' f JOIN ' . fw_tabela('komentarze') . ' k ON k.id=f.tresc_id WHERE f.typ="komentarz" AND k.slug=? AND k.status="opublikowany"');
        $rs->execute([$slug]); $replies=$rs->fetchAll(PDO::FETCH_KEY_PAIR);
    }
    fw_odpowiedz([
        'ok'         => true,
        'komentarze' => array_map(static fn(array $k): array => [
            'id'     => (int) $k['id'],
            'tresc'  => $k['tresc'],
            'autor'  => $k['autor'],
            'odpowiedz' => $replies[$k['id']] ?? null,
            'poziom' => fw_spolecznosc_gotowa() ? fw_profil_aktywnosci((int)$k['autor_id'])['poziom'] : null,
            'status' => $k['status'],
            'data'   => $k['utworzony'],
        ], $rows),
    ]);
}

if ($akcja === 'dodaj') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    $u = fw_wymagaj_logowania();
    fw_limit('komentarz', 20, 3600);

    $slug = fw_slug(fw_pole('slug'));
    $tresc = fw_tekst(fw_pole('tresc'), 'Treść komentarza', 5, 3000);
    $status = fw_status_dla($u);

    $pdo->prepare('INSERT INTO ' . fw_tabela('komentarze')
        . ' (slug, autor_id, tresc, status, utworzony) VALUES (?, ?, ?, ?, ?)')
        ->execute([$slug, $u['id'], $tresc, $status, fw_teraz()]);

    fw_odpowiedz([
        'ok'        => true,
        'id'        => (int) $pdo->lastInsertId(),
        'status'    => $status,
        'komunikat' => $status === 'opublikowany'
            ? 'Komentarz dodany.'
            : 'Komentarz czeka na zatwierdzenie przez moderatora.',
    ], 201);
}

fw_blad(404, 'Nieznana akcja.');
