<?php
declare(strict_types=1);

/**
 * Moderacja — wyłącznie dla konta z rolą "admin".
 *
 *   GET  /api/moderacja.php?akcja=kolejka        — treści czekające na decyzję
 *   GET  /api/moderacja.php?akcja=uzytkownicy    — lista kont
 *   POST /api/moderacja.php?akcja=zatwierdz      — typ, id
 *   POST /api/moderacja.php?akcja=odrzuc         — typ, id
 *   POST /api/moderacja.php?akcja=usun           — typ, id
 *   POST /api/moderacja.php?akcja=blokuj         — id, zablokowany (0/1)
 *   GET  /api/moderacja.php?akcja=tresci         — wszystkie treści danego typu
 *   POST /api/moderacja.php?akcja=edytuj|ukryj|przywroc — patrz sekcja niżej
 *
 * "typ" to jedno z: watek, odpowiedz, komentarz, wpis.
 *
 * Wpisy blogowe agenta chodzą osobną ścieżką: decyzja zapisuje status
 * w tabeli wpisów i odpala workflow w repozytorium (repository_dispatch),
 * bo publikacja wymaga przebudowania statycznego serwisu. Ukrycie
 * i usunięcie opublikowanego wpisu idą tą samą drogą (po slugu).
 */

require_once __DIR__ . '/_spolecznosc.php';

fw_wymagaj_admina_lub_tokenu(false);

$akcja = fw_akcja();
$pdo = fw_baza();

/** Mapa typ treści -> tabela i kolumna z datą. Nic spoza niej nie trafia do SQL. */
const FW_TYPY = [
    'watek'     => ['tabela' => 'watki',      'data' => 'utworzony'],
    'odpowiedz' => ['tabela' => 'odpowiedzi', 'data' => 'utworzona'],
    'komentarz' => ['tabela' => 'komentarze', 'data' => 'utworzony'],
];

function fw_typ(): array
{
    $typ = fw_pole('typ');
    if (!isset(FW_TYPY[$typ])) {
        fw_blad(422, 'Nieznany typ treści.');
    }
    return [$typ, fw_tabela(FW_TYPY[$typ]['tabela'])];
}

// ----------------------------------------------------------------- kolejka
if ($akcja === 'kolejka') {
    $pozycje = [];

    $st = $pdo->query('SELECT w.id, w.tytul, w.tresc, w.kategoria, w.utworzony, a.nick AS autor'
        . ' FROM ' . fw_tabela('watki') . ' w'
        . ' JOIN ' . fw_tabela('uzytkownicy') . ' a ON a.id = w.autor_id'
        . ' WHERE w.status = "oczekuje" ORDER BY w.utworzony ASC LIMIT 200');
    foreach ($st->fetchAll() as $w) {
        $pozycje[] = [
            'typ'       => 'watek',
            'id'        => (int) $w['id'],
            'naglowek'  => $w['tytul'],
            'tresc'     => $w['tresc'],
            'kontekst'  => 'Forum / ' . $w['kategoria'],
            'autor'     => $w['autor'],
            'data'      => $w['utworzony'],
        ];
    }

    $st = $pdo->query('SELECT o.id, o.tresc, o.utworzona, a.nick AS autor, w.tytul'
        . ' FROM ' . fw_tabela('odpowiedzi') . ' o'
        . ' JOIN ' . fw_tabela('uzytkownicy') . ' a ON a.id = o.autor_id'
        . ' JOIN ' . fw_tabela('watki') . ' w ON w.id = o.watek_id'
        . ' WHERE o.status = "oczekuje" ORDER BY o.utworzona ASC LIMIT 200');
    foreach ($st->fetchAll() as $o) {
        $pozycje[] = [
            'typ'      => 'odpowiedz',
            'id'       => (int) $o['id'],
            'naglowek' => 'Odpowiedź w wątku: ' . $o['tytul'],
            'tresc'    => $o['tresc'],
            'kontekst' => 'Forum',
            'autor'    => $o['autor'],
            'data'     => $o['utworzona'],
        ];
    }

    $st = $pdo->query('SELECT k.id, k.tresc, k.slug, k.utworzony, a.nick AS autor'
        . ' FROM ' . fw_tabela('komentarze') . ' k'
        . ' JOIN ' . fw_tabela('uzytkownicy') . ' a ON a.id = k.autor_id'
        . ' WHERE k.status = "oczekuje" ORDER BY k.utworzony ASC LIMIT 200');
    foreach ($st->fetchAll() as $k) {
        $pozycje[] = [
            'typ'      => 'komentarz',
            'id'       => (int) $k['id'],
            'naglowek' => 'Komentarz pod wpisem',
            'tresc'    => $k['tresc'],
            'kontekst' => '/blog/' . $k['slug'] . '/',
            'autor'    => $k['autor'],
            'data'     => $k['utworzony'],
        ];
    }

    // Wpisy agenta. Leżą już na serwerze jako szkice (noindex, poza /blog/
    // i sitemapą), więc "kontekst" jest zarazem linkiem do podglądu.
    fw_zapewnij_tabele_wpisow();
    $st = $pdo->query('SELECT id, slug, tytul, `lead`, url, utworzony, run_url, notatka'
        . ' FROM ' . fw_tabela('wpisy')
        . ' WHERE status = "oczekuje" ORDER BY utworzony ASC LIMIT 200');
    foreach ($st->fetchAll() as $w) {
        $pozycje[] = [
            'typ'      => 'wpis',
            'id'       => (int) $w['id'],
            'naglowek' => $w['tytul'],
            'tresc'    => $w['lead'],
            'kontekst' => $w['url'],
            'podglad'  => $w['url'],
            'run_url'  => $w['run_url'],
            'autor'    => 'agent bloga',
            'data'     => $w['utworzony'],
            // Notatka agenta kontroli: czemu wpis wciąż czeka mimo progu kolejki.
            'notatka'  => $w['notatka'],
        ];
    }

    usort($pozycje, static fn(array $a, array $b): int => strcmp($a['data'], $b['data']));
    fw_odpowiedz(['ok' => true, 'kolejka' => $pozycje, 'ile' => count($pozycje)]);
}

// ------------------------------------------------------------- użytkownicy
if ($akcja === 'uzytkownicy') {
    $st = $pdo->query('SELECT id, nick, email, rola, zaufany, zablokowany, utworzony,'
        . ' ostatnie_logowanie FROM ' . fw_tabela('uzytkownicy')
        . ' ORDER BY utworzony DESC LIMIT 500');

    fw_odpowiedz([
        'ok'          => true,
        'uzytkownicy' => array_map(static fn(array $u): array => [
            'id'          => (int) $u['id'],
            'nick'        => $u['nick'],
            'email'       => $u['email'],
            'rola'        => $u['rola'],
            'zaufany'     => (int) $u['zaufany'] === 1,
            'zablokowany' => (int) $u['zablokowany'] === 1,
            'utworzony'   => $u['utworzony'],
            'logowanie'   => $u['ostatnie_logowanie'],
        ], $st->fetchAll()),
    ]);
}

// ------------------------------------------------------- decyzje o treściach
/**
 * Odpala workflow w repozytorium przez repository_dispatch.
 *
 * Zwraca komunikat o wyniku zamiast przerywać żądanie: decyzja admina jest
 * już zapisana w bazie, więc awaria GitHuba nie może jej cofnąć. Wpis
 * zostaje wtedy w stanie "zaakceptowany, ale jeszcze nieopublikowany",
 * co widać w panelu i da się ponowić.
 */
function fw_dispatch_github(string $zdarzenie, array $payload): string
{
    $cfg = fw_konfiguracja();
    $token = (string) ($cfg['github_token'] ?? '');
    $repo  = (string) ($cfg['github_repo'] ?? '');
    if ($token === '' || $repo === '') {
        return 'Brak tokenu GitHuba w konfiguracji — publikacja nie ruszyła.';
    }

    $ch = curl_init('https://api.github.com/repos/' . $repo . '/dispatches');
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 15,
        CURLOPT_HTTPHEADER     => [
            'Accept: application/vnd.github+json',
            'Authorization: Bearer ' . $token,
            'X-GitHub-Api-Version: 2022-11-28',
            'Content-Type: application/json',
            'User-Agent: fwdrucik-panel',
        ],
        CURLOPT_POSTFIELDS => json_encode(
            ['event_type' => $zdarzenie, 'client_payload' => $payload],
            JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE
        ),
    ]);
    $odp = curl_exec($ch);
    $kod = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    $blad = curl_error($ch);
    curl_close($ch);

    if ($odp === false) {
        return 'Nie udało się połączyć z GitHubem: ' . $blad;
    }
    if ($kod !== 204) {
        return 'GitHub odrzucił żądanie (HTTP ' . $kod . ').';
    }
    return '';
}

// ------------------------------------------------------- decyzja o wpisie
if (in_array($akcja, ['zatwierdz', 'odrzuc'], true) && fw_pole('typ') === 'wpis') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    $admin = fw_wymagaj_admina();
    $id = fw_id('id');

    fw_zapewnij_tabele_wpisow();

    $tabela = fw_tabela('wpisy');
    $st = $pdo->prepare('SELECT slug, status FROM ' . $tabela . ' WHERE id = ?');
    $st->execute([$id]);
    $wpis = $st->fetch();
    if ($wpis === false) {
        fw_blad(404, 'Nie ma takiego wpisu.');
    }

    $nowy = $akcja === 'zatwierdz' ? 'opublikowany' : 'odrzucony';
    $pdo->prepare('UPDATE ' . $tabela . ' SET status = ?, rozstrzygniety = ?, rozstrzygnal = ?'
        . ' WHERE id = ?')->execute([$nowy, fw_teraz(), (int) $admin['id'], $id]);

    $problem = fw_dispatch_github(
        $akcja === 'zatwierdz' ? 'publikuj-wpis' : 'odrzuc-wpis',
        ['slug' => $wpis['slug']]
    );

    fw_odpowiedz([
        'ok'        => true,
        'ostrzezenie' => $problem !== '' ? $problem : null,
        'komunikat' => $problem !== ''
            ? ($akcja === 'zatwierdz' ? 'Wpis zaakceptowany, ale publikacja nie ruszyła.'
                                      : 'Wpis odrzucony, ale sprzątanie nie ruszyło.')
            : ($akcja === 'zatwierdz' ? 'Wpis zaakceptowany — publikacja w toku, potrwa około minuty.'
                                      : 'Wpis odrzucony — znika z serwera w ciągu minuty.'),
    ]);
}

// Usunięcie wpisu bloga obsługuje sekcja zarządzania treściami niżej.
if (in_array($akcja, ['zatwierdz', 'odrzuc', 'usun'], true) && fw_pole('typ') !== 'wpis') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    [$typ, $tabela] = fw_typ();
    $id = fw_id('id');

    if ($akcja === 'usun') {
        $pdo->beginTransaction();
        $st = $pdo->prepare('DELETE FROM ' . $tabela . ' WHERE id = ?');
        $st->execute([$id]);
        if ($st->rowCount() === 0) {
            $pdo->rollBack();
            fw_blad(404, 'Nie ma takiej treści.');
        }
        if ($typ === 'komentarz' && fw_spolecznosc_gotowa()) {
            $pdo->prepare('DELETE FROM ' . fw_tabela('odpowiedzi_firmy') . ' WHERE typ="komentarz" AND tresc_id=?')->execute([$id]);
            fw_spolecznosc_audyt((int)(fw_uzytkownik()['id']??0),$typ,$id,'usun');
        }
        $pdo->commit();
        fw_odpowiedz(['ok' => true, 'komunikat' => 'Treść usunięta.']);
    }

    $nowy = $akcja === 'zatwierdz' ? 'opublikowany' : 'odrzucony';
    $st = $pdo->prepare('SELECT autor_id FROM ' . $tabela . ' WHERE id = ?');
    $st->execute([$id]);
    $autor_id = $st->fetchColumn();
    if ($autor_id === false) {
        fw_blad(404, 'Nie ma takiej treści.');
    }

    $pdo->prepare('UPDATE ' . $tabela . ' SET status = ? WHERE id = ?')->execute([$nowy, $id]);

    if ($akcja === 'zatwierdz') {
        // Autor przeszedł pierwszą weryfikację — kolejne wpisy publikuje bez kolejki.
        $pdo->prepare('UPDATE ' . fw_tabela('uzytkownicy') . ' SET zaufany = 1 WHERE id = ?')
            ->execute([(int) $autor_id]);

        if ($typ === 'odpowiedz') {
            $pdo->prepare('UPDATE ' . fw_tabela('watki') . ' w'
                . ' JOIN ' . fw_tabela('odpowiedzi') . ' o ON o.watek_id = w.id'
                . ' SET w.ostatnia_aktywnosc = o.utworzona WHERE o.id = ?')->execute([$id]);
        }
    }

    fw_odpowiedz([
        'ok'        => true,
        'komunikat' => $akcja === 'zatwierdz' ? 'Treść opublikowana.' : 'Treść odrzucona.',
    ]);
}

// ------------------------------------------ zarządzanie opublikowanymi treściami
/**
 *   GET  ?akcja=tresci&typ=watek|odpowiedz|komentarz|wpis[&szukaj=]
 *   POST ?akcja=edytuj    — typ, id, tresc[, tytul dla wątku]
 *   POST ?akcja=ukryj     — typ, id (wpis: slug) — treść niewidoczna publicznie
 *   POST ?akcja=przywroc  — typ, id (wpis: slug)
 *   POST ?akcja=usun      — typ=wpis, slug (pozostałe typy obsługuje blok niżej)
 *
 * Ukrycie na forum to status "odrzucony": autor dalej widzi swój wpis
 * (forum.php pokazuje mu własne treści), świat nie. Przywrócenie ustawia
 * "opublikowany" bez nadawania autorowi zaufania — to nie jest moderacja
 * nowej treści, tylko cofnięcie decyzji admina.
 */
if ($akcja === 'tresci') {
    $typ = (string) ($_GET['typ'] ?? 'watek');
    $szukaj = trim((string) ($_GET['szukaj'] ?? ''));

    if ($typ === 'wpis') {
        // Spis generuje build.py — serwer nie ma pages.py ani src/.
        $spis = is_file(__DIR__ . '/_blog.php') ? require __DIR__ . '/_blog.php' : [];
        $repo = (string) (fw_konfiguracja()['github_repo'] ?? '');
        $pozycje = [];
        foreach (is_array($spis) ? $spis : [] as $w) {
            if ($szukaj !== '' && mb_stripos($w['tytul'] . ' ' . $w['slug'], $szukaj) === false) {
                continue;
            }
            $pozycje[] = [
                'id'       => $w['slug'],
                'naglowek' => $w['tytul'],
                'tresc'    => '',
                'status'   => $w['ukryty'] ? 'ukryty' : 'opublikowany',
                'link'     => '/blog/' . $w['slug'] . '/',
                // Treść wpisu żyje w repozytorium — edycja w edytorze GitHuba,
                // potem workflow "Wysyłka na serwer".
                'edycja'   => $repo !== '' ? 'https://github.com/' . $repo . '/edit/main/src/' . $w['src'] : null,
            ];
        }
        fw_odpowiedz(['ok' => true, 'typ' => $typ, 'pozycje' => $pozycje]);
    }

    $u = fw_tabela('uzytkownicy');
    $w = fw_tabela('watki');
    $sql = match ($typ) {
        'watek' => 'SELECT t.id, t.tytul AS naglowek, t.tresc, t.status, t.utworzony AS data,'
            . ' a.nick AS autor, t.id AS watek_id, t.tytul AS watek_tytul, NULL AS slug'
            . ' FROM ' . $w . ' t JOIN ' . $u . ' a ON a.id = t.autor_id',
        'odpowiedz' => 'SELECT t.id, w.tytul AS naglowek, t.tresc, t.status, t.utworzona AS data,'
            . ' a.nick AS autor, w.id AS watek_id, w.tytul AS watek_tytul, NULL AS slug'
            . ' FROM ' . fw_tabela('odpowiedzi') . ' t JOIN ' . $u . ' a ON a.id = t.autor_id'
            . ' JOIN ' . $w . ' w ON w.id = t.watek_id',
        'komentarz' => 'SELECT t.id, t.slug AS naglowek, t.tresc, t.status, t.utworzony AS data,'
            . ' a.nick AS autor, NULL AS watek_id, NULL AS watek_tytul, t.slug'
            . ' FROM ' . fw_tabela('komentarze') . ' t JOIN ' . $u . ' a ON a.id = t.autor_id',
        default => fw_blad(422, 'Nieznany typ treści.'),
    };
    $parametry = [];
    if ($szukaj !== '') {
        $sql .= ' WHERE t.tresc LIKE ?';
        $parametry[] = '%' . addcslashes($szukaj, '%_\\') . '%';
    }
    $st = $pdo->prepare($sql . ' ORDER BY data DESC LIMIT 200');
    $st->execute($parametry);

    fw_odpowiedz(['ok' => true, 'typ' => $typ, 'pozycje' => array_map(static fn(array $r): array => [
        'id'          => (int) $r['id'],
        'naglowek'    => $r['naglowek'],
        'tresc'       => $r['tresc'],
        'status'      => $r['status'] === 'odrzucony' ? 'ukryty' : $r['status'],
        'autor'       => $r['autor'],
        'data'        => $r['data'],
        'watek_id'    => $r['watek_id'] !== null ? (int) $r['watek_id'] : null,
        'watek_tytul' => $r['watek_tytul'],
        'link'        => $r['slug'] !== null ? '/blog/' . $r['slug'] . '/' : null,
    ], $st->fetchAll())]);
}

if ($akcja === 'edytuj') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    [$typ, $tabela] = fw_typ();
    $id = fw_id('id');

    $czy = $pdo->prepare('SELECT 1 FROM ' . $tabela . ' WHERE id = ?');
    $czy->execute([$id]);
    if ($czy->fetchColumn() === false) {
        fw_blad(404, 'Nie ma takiej treści.');
    }

    // Te same limity co przy dodawaniu (forum.php, komentarze.php).
    $tresc = match ($typ) {
        'watek'     => fw_tekst(fw_pole('tresc'), 'Treść wątku', 20, 8000),
        'odpowiedz' => fw_tekst(fw_pole('tresc'), 'Treść odpowiedzi', 5, 8000),
        'komentarz' => fw_tekst(fw_pole('tresc'), 'Treść komentarza', 5, 3000),
    };
    if ($typ === 'watek') {
        $tytul = fw_tekst(fw_pole('tytul'), 'Tytuł wątku', 10, 160);
        $pdo->prepare('UPDATE ' . $tabela . ' SET tytul = ?, tresc = ? WHERE id = ?')
            ->execute([$tytul, $tresc, $id]);
    } else {
        $pdo->prepare('UPDATE ' . $tabela . ' SET tresc = ? WHERE id = ?')->execute([$tresc, $id]);
    }
    fw_odpowiedz(['ok' => true, 'komunikat' => 'Zmiany zapisane.']);
}

if (in_array($akcja, ['ukryj', 'przywroc', 'usun'], true) && fw_pole('typ') === 'wpis') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    $slug = fw_slug(fw_pole('slug'));

    // Wpis bloga to pliki w repozytorium — zmianę robi workflow
    // "Decyzja o wpisie" (przebudowa + wysyłka), tak jak przy akceptacji.
    $zdarzenie = ['ukryj' => 'ukryj-wpis', 'przywroc' => 'publikuj-wpis', 'usun' => 'odrzuc-wpis'][$akcja];
    $problem = fw_dispatch_github($zdarzenie, ['slug' => $slug]);

    // Rekord agenta (jeśli jest) idzie za decyzją — inaczej sprzątający
    // przebieg dopublikuj.py przywróciłby ukryty wpis jako "opublikowany".
    fw_zapewnij_tabele_wpisow();
    $pdo->prepare('UPDATE ' . fw_tabela('wpisy') . ' SET status = ? WHERE slug = ?')
        ->execute([$akcja === 'przywroc' ? 'opublikowany' : 'odrzucony', $slug]);

    fw_odpowiedz([
        'ok'          => true,
        'ostrzezenie' => $problem !== '' ? $problem : null,
        'komunikat'   => $problem !== ''
            ? 'Zmiana nie ruszyła na serwerze.'
            : 'Zlecone — wpis zmieni się na stronie w ciągu minuty–dwóch.',
    ]);
}

if (in_array($akcja, ['ukryj', 'przywroc'], true)) {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    [, $tabela] = fw_typ();
    $id = fw_id('id');

    $czy = $pdo->prepare('SELECT 1 FROM ' . $tabela . ' WHERE id = ?');
    $czy->execute([$id]);
    if ($czy->fetchColumn() === false) {
        fw_blad(404, 'Nie ma takiej treści.');
    }
    $pdo->prepare('UPDATE ' . $tabela . ' SET status = ? WHERE id = ?')
        ->execute([$akcja === 'ukryj' ? 'odrzucony' : 'opublikowany', $id]);
    fw_odpowiedz([
        'ok'        => true,
        'komunikat' => $akcja === 'ukryj' ? 'Treść ukryta — widzi ją tylko autor.' : 'Treść znów publiczna.',
    ]);
}

// ------------------------------------------------------- blokada użytkownika
if ($akcja === 'blokuj') {
    fw_wymagaj_post();
    fw_sprawdz_csrf();
    $id = fw_id('id');
    $zablokowany = fw_pole('zablokowany') === '1' ? 1 : 0;

    $st = $pdo->prepare('SELECT rola FROM ' . fw_tabela('uzytkownicy') . ' WHERE id = ?');
    $st->execute([$id]);
    $rola = $st->fetchColumn();
    if ($rola === false) {
        fw_blad(404, 'Nie ma takiego konta.');
    }
    if ($rola === 'admin') {
        fw_blad(422, 'Konta administratora nie da się zablokować z panelu.');
    }

    $pdo->prepare('UPDATE ' . fw_tabela('uzytkownicy') . ' SET zablokowany = ? WHERE id = ?')
        ->execute([$zablokowany, $id]);
    // Blokada od razu unieważnia otwarte sesje tego konta.
    if ($zablokowany === 1) {
        $pdo->prepare('DELETE FROM ' . fw_tabela('sesje') . ' WHERE uzytkownik_id = ?')->execute([$id]);
    }

    fw_odpowiedz(['ok' => true, 'zablokowany' => $zablokowany === 1]);
}

fw_blad(404, 'Nieznana akcja.');
