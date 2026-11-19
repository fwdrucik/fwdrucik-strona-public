<?php
declare(strict_types=1);

/**
 * Wpisy blogowe agenta — zgłoszenie szkicu do kolejki akceptacji.
 *
 *   POST /api/wpisy.php?akcja=zglos         — melduje nowy szkic (token agenta)
 *   GET  /api/wpisy.php?akcja=oczekujace    — kolejka szkiców (token agenta)
 *   POST /api/wpisy.php?akcja=auto-decyzja  — decyzja agenta kontroli (token agenta)
 *   POST /api/wpisy.php?akcja=migracja      — zakłada tabelę fw_wpisy (admin)
 *
 * Kolejkę i decyzje obsługuje moderacja.php, tak jak dla wątków i komentarzy.
 *
 * Zgłoszenie woła GitHub Actions, nie przeglądarka, więc zamiast sesji jest
 * wspólny sekret w nagłówku X-Agent-Token. Z tego samego powodu nie ma tu
 * kontroli CSRF — nie ma ciasteczka, które dałoby się podszyć.
 */

require_once __DIR__ . '/_lib.php';

$akcja = fw_akcja();

// -------------------------------------------------------------- zgłoszenie
if ($akcja === 'zglos') {
    fw_wymagaj_post();
    fw_wymagaj_tokenu_agenta();

    $slug  = fw_slug(fw_pole('slug'));
    $tytul = fw_tekst(fw_pole('tytul'), 'Tytuł', 3, 255);
    $lead  = fw_tekst(fw_pole('lead'), 'Lead', 3, 2000);
    $url   = fw_pole('url') !== '' ? fw_pole('url') : '/blog/' . $slug . '/';
    $run   = fw_pole('run_url');

    // Adresy przyjmujemy wyłącznie względne — inaczej link "podgląd"
    // w panelu dałoby się skierować na obcy serwer.
    if ($url[0] !== '/' || str_starts_with($url, '//')) {
        fw_blad(422, 'Adres wpisu musi być względny.');
    }
    if ($run !== '' && !str_starts_with($run, 'https://github.com/')) {
        fw_blad(422, 'Link do przebiegu musi wskazywać na github.com.');
    }

    $pdo = fw_baza();
    fw_zapewnij_tabele_wpisow();
    $tabela = fw_tabela('wpisy');

    // Powtórzone zgłoszenie tego samego sluga (ponowiony workflow) tylko
    // odświeża opis. Statusu nie ruszamy — raz odrzucony wpis nie wraca
    // do kolejki tylnymi drzwiami.
    $st = $pdo->prepare(
        'INSERT INTO ' . $tabela . ' (slug, tytul, `lead`, url, status, utworzony, run_url)'
        . ' VALUES (?, ?, ?, ?, "oczekuje", ?, ?)'
        . ' ON DUPLICATE KEY UPDATE tytul = VALUES(tytul), `lead` = VALUES(`lead`),'
        . ' url = VALUES(url), run_url = VALUES(run_url)'
    );
    $st->execute([$slug, $tytul, $lead, $url, fw_teraz(), $run !== '' ? $run : null]);

    $st = $pdo->prepare('SELECT id, status FROM ' . $tabela . ' WHERE slug = ?');
    $st->execute([$slug]);
    $wpis = $st->fetch();

    fw_odpowiedz([
        'ok'        => true,
        'id'        => (int) $wpis['id'],
        'status'    => $wpis['status'],
        'komunikat' => 'Szkic czeka na akceptację.',
    ]);
}

// ------------------------------------------------------- lista do publikacji
if ($akcja === 'do-publikacji') {
    // Zatwierdzenie w panelu odpala workflow przez repository_dispatch, ale
    // GitHub kolejkuje tylko jeden oczekujacy przebieg na grupe wspolbieznosci
    // — przy kilku akceptacjach pod rzad nadmiarowe sa anulowane i wpis zostaje
    // zatwierdzony w bazie, a nieopublikowany na stronie. Ta koncowka pozwala
    // sprzatajacemu przebiegowi odtworzyc, co powinno byc juz na blogu.
    fw_wymagaj_tokenu_agenta();

    $pdo = fw_baza();
    fw_zapewnij_tabele_wpisow();
    $tabela = fw_tabela('wpisy');

    $st = $pdo->query(
        'SELECT slug, url, rozstrzygniety FROM ' . $tabela
        . " WHERE status = 'opublikowany' ORDER BY rozstrzygniety ASC"
    );
    $wpisy = [];
    foreach ($st->fetchAll() as $w) {
        $wpisy[] = [
            'slug'           => $w['slug'],
            'url'            => $w['url'],
            'rozstrzygniety' => $w['rozstrzygniety'],
        ];
    }

    fw_odpowiedz(['ok' => true, 'wpisy' => $wpisy, 'ile' => count($wpisy)]);
}

// ------------------------------------------------------ kolejka dla agenta
if ($akcja === 'oczekujace') {
    // Agent autopublikacji musi wiedzieć, ile szkiców czeka na decyzję i który
    // czeka najdłużej. Panel ma to w moderacja.php?akcja=kolejka, ale tamta
    // końcówka wymaga sesji administratora — GitHub Actions ma tylko token.
    fw_wymagaj_tokenu_agenta();

    $pdo = fw_baza();
    fw_zapewnij_tabele_wpisow();
    $tabela = fw_tabela('wpisy');

    $st = $pdo->query(
        'SELECT slug, tytul, url, utworzony, notatka FROM ' . $tabela
        . " WHERE status = 'oczekuje' ORDER BY utworzony ASC"
    );
    $wpisy = [];
    foreach ($st->fetchAll() as $w) {
        $wpisy[] = [
            'slug'      => $w['slug'],
            'tytul'     => $w['tytul'],
            'url'       => $w['url'],
            'utworzony' => $w['utworzony'],
            'notatka'   => $w['notatka'],
        ];
    }

    fw_odpowiedz(['ok' => true, 'wpisy' => $wpisy, 'ile' => count($wpisy)]);
}

// ------------------------------------------------- decyzja agenta kontroli
if ($akcja === 'auto-decyzja') {
    // Wpis przepuszczony przez agenta kontroli po przekroczeniu progu kolejki.
    // `rozstrzygnal` zostaje NULL — po tym w panelu widać, że decyzji nie podjął
    // człowiek. `notatka` mówi, co agent poprawił albo dlaczego wpis zostawił.
    fw_wymagaj_post();
    fw_wymagaj_tokenu_agenta();

    $slug    = fw_slug(fw_pole('slug'));
    $notatka = fw_pole('notatka');
    // Dwa dozwolone wyniki: publikacja albo pozostawienie w kolejce z notatką.
    // Kasowania treści agent nie robi — to zostaje decyzją człowieka.
    $decyzja = fw_pole('decyzja') !== '' ? fw_pole('decyzja') : 'publikuj';
    if (!in_array($decyzja, ['publikuj', 'zostaw'], true)) {
        fw_blad(422, 'Nieznana decyzja agenta.');
    }
    if (mb_strlen($notatka) > 2000) {
        $notatka = mb_substr($notatka, 0, 2000);
    }

    $pdo = fw_baza();
    fw_zapewnij_tabele_wpisow();
    $tabela = fw_tabela('wpisy');

    $st = $pdo->prepare('SELECT id, status FROM ' . $tabela . ' WHERE slug = ?');
    $st->execute([$slug]);
    $wpis = $st->fetch();
    if ($wpis === false) {
        fw_blad(404, 'Nie ma takiego wpisu.');
    }
    // Wpis rozstrzygnięty przez człowieka zostaje jak jest — agent nie cofa
    // ani nie nadpisuje cudzej decyzji.
    if ($wpis['status'] !== 'oczekuje') {
        fw_odpowiedz([
            'ok'        => true,
            'zmieniono' => false,
            'status'    => $wpis['status'],
            'komunikat' => 'Wpis był już rozstrzygnięty — bez zmian.',
        ]);
    }

    if ($decyzja === 'publikuj') {
        $st = $pdo->prepare(
            'UPDATE ' . $tabela . " SET status = 'opublikowany', rozstrzygniety = ?,"
            . ' rozstrzygnal = NULL, notatka = ? WHERE id = ?'
        );
        $st->execute([fw_teraz(), $notatka !== '' ? $notatka : null, (int) $wpis['id']]);
        $status = 'opublikowany';
    } else {
        $st = $pdo->prepare('UPDATE ' . $tabela . ' SET notatka = ? WHERE id = ?');
        $st->execute([$notatka !== '' ? $notatka : null, (int) $wpis['id']]);
        $status = 'oczekuje';
    }

    fw_odpowiedz([
        'ok'        => true,
        'zmieniono' => true,
        'status'    => $status,
        'komunikat' => $decyzja === 'publikuj'
            ? 'Wpis opublikowany przez agenta kontroli.'
            : 'Wpis zostaje w kolejce z notatką agenta.',
    ]);
}

// --------------------------------------------------------------- migracja
if ($akcja === 'migracja') {
    // Hosting nie daje shella ani MySQL z zewnątrz, więc tabelę zakłada
    // zalogowany administrator jednym kliknięciem w panelu. Zapytanie jest
    // idempotentne — powtórzenie niczego nie psuje.
    fw_wymagaj_post();
    fw_wymagaj_admina();
    fw_sprawdz_csrf();

    fw_zapewnij_tabele_wpisow();

    fw_odpowiedz(['ok' => true, 'komunikat' => 'Tabela wpisów gotowa.']);
}

fw_blad(404, 'Nieznana akcja.');
