<?php
declare(strict_types=1);
require __DIR__ . '/api/_sklep.php';

$checks = 0;
function check(bool $ok, string $name): void {
    global $checks;
    $checks++;
    if (!$ok) { throw new RuntimeException($name); }
}
check(function_exists('fw_allegro_url'), 'Missing Allegro URL safety boundary');
foreach (['https://allegro.pl/oferta/polka-12345678901', 'https://www.allegro.pl/oferta/a',
          'https://allegrolokalnie.pl/oferta/a', 'https://www.allegrolokalnie.pl/oferta/a'] as $url) {
    check(fw_allegro_url($url) === $url, 'Valid public Allegro HTTPS rejected');
}
foreach (['javascript:alert(1)', 'https://allegro.pl.evil.example/a', 'https://evil.example/allegro.pl',
          'http://allegro.pl/oferta/a', 'https://user:PRIVATE@allegro.pl/a', 'https://127.0.0.1/a',
          'https://allegro.pl:444/a', "https://allegro.pl/a\nPRIVATE", '//allegro.pl/a'] as $url) {
    check(fw_allegro_url($url) === null, 'Unsafe Allegro URL accepted');
}
$product = ['id'=>1,'slug'=>'polka','nazwa'=>'Polka','kategoria'=>'inne','opis_krotki'=>'Opis',
 'opis'=>'Opis','cena_gr'=>100,'cena_promo_gr'=>null,'stan'=>1,'waga_g'=>0,'jednostka'=>'szt.',
 'czas_realizacji'=>'','status'=>'opublikowany','pozycja'=>1,'allegro_url'=>'javascript:alert(1)'];
$public = fw_produkt_publiczny($product, []);
check($public['allegro_url'] === null && $public['url'] === '/sklep/polka/', 'Legacy URL did not fall back safely');
$json = fw_json_ld(['name'=>'</script><img src=x onerror=PRIVATE>', 'description'=>'Żywica & dąb']);
check(!str_contains($json, '</script>') && !str_contains($json, '<img'), 'JSON terminates script element');
check(json_decode($json, true)['description'] === 'Żywica & dąb', 'JSON text corrupted');
$dns = fn($host) => [['ip'=>'93.184.216.34']];
$options = fw_allegro_import_options('https://allegro.pl/oferta/a', $dns);
check($options !== null && $options[CURLOPT_SSL_VERIFYPEER] === true
    && $options[CURLOPT_SSL_VERIFYHOST] === 2 && $options[CURLOPT_FOLLOWLOCATION] === false,
    'Import TLS or redirect policy unsafe');
check($options[CURLOPT_RESOLVE] === ['allegro.pl:443:93.184.216.34'], 'DNS was not pinned');
foreach (['127.0.0.1','10.0.0.1','169.254.169.254','192.168.1.1','::1','fd00::1','::ffff:127.0.0.1',
          '100.64.0.10','198.18.0.1','224.0.0.1','2001:db8::1'] as $ip) {
    check(fw_allegro_import_options('https://allegro.pl/oferta/a', fn($host)=>[['ip'=>$ip]]) === null,
          'Private/reserved DNS accepted: ' . $ip);
}
check(fw_allegro_import_options('https://allegro.pl/a', fn($host)=>[]) === null, 'Empty DNS accepted');
check(fw_allegro_import_options('https://allegro.pl/a', fn($host)=>[['ip'=>'93.184.216.34'],['ip'=>'10.0.0.1']]) === null,
      'Mixed private/public DNS accepted');
$safe = fw_sklep_opis_html('<div class="opis-allegro-kontener"><p onclick="PRIVATE">Dąb</p><script>PRIVATE</script></div>');
check(!str_contains($safe, 'PRIVATE') && str_contains($safe, 'Dąb'), 'Description marker bypass');
$calls = 0;
$fixture = '<script type="application/ld+json">{"@type":"Product","name":"Półka dębowa","description":"Opis klienta",'
    . '"image":["https://a.allegroimg.com/original/test.jpg"],"offers":{"price":"129.90"}}</script>';
$transport = function ($received) use (&$calls, $fixture) {
    $calls++;
    check($received[CURLOPT_SSL_VERIFYPEER] && !$received[CURLOPT_FOLLOWLOCATION], 'Unsafe real import options');
    return [200, $fixture];
};
$imported = fw_pobierz_dane_aukcji_allegro('https://allegro.pl/oferta/polka-12345678901', $dns, $transport);
check($calls === 1 && $imported['nazwa'] === 'Półka dębowa' && $imported['cena_gr'] === 12990
    && $imported['allegro_id'] === '12345678901', 'Realistic JSON-LD import broken');
check(fw_pobierz_dane_aukcji_allegro('https://allegro.pl/a', $dns, fn($opts)=>[302, $fixture]) === null,
      'Redirect response imported instead of rejected');
$local = fw_pobierz_dane_aukcji_allegro('https://allegrolokalnie.pl/oferta/polka', $dns,
    fn($opts)=>[200, '<meta property="og:title" content="Półka"><meta property="product:price:amount" content="50.00">']);
check($local['nazwa'] === 'Półka' && $local['cena_gr'] === 5000, 'Allegro Lokalnie OG fixture broken');
$calls = 0;
check(fw_pobierz_dane_aukcji_allegro('https://allegro.pl/a', fn($host)=>[['ip'=>'127.0.0.1']], $transport) === null
    && $calls === 0, 'Private DNS reached transport');
// Render the real list template, replacing only database/config boundaries.
function fw_konfiguracja(): array { return ['sklep_otwarty'=>true]; }
function fw_uzytkownik(): ?array { return null; }
function fw_zlote(int $value): string { return number_format($value / 100, 2, ',', ' ') . ' zł'; }
$GLOBALS['fixtureProduct'] = $public;
$GLOBALS['fixtureProduct']['nazwa'] = '</script><img src=x onerror=PRIVATE>';
$GLOBALS['fixtureProduct']['obrazy'] = [['src'=>'/assets/sklep/demo.mp4','alt'=>'Demo','szerokosc'=>720,'wysokosc'=>1280]];
$template = file_get_contents(__DIR__ . '/php/sklep-lista.php');
$template = preg_replace('/^require_once .*;\r?$/m', '', $template);
$template = preg_replace('/^\$produkty = .*;\r?$/m', '$produkty = [$GLOBALS["fixtureProduct"]];', $template);
ob_start();
try { eval('?>' . $template); $rendered = ob_get_contents(); }
finally { ob_end_clean(); }
check(!str_contains($rendered, '<img src=x onerror=PRIVATE>'), 'Rendered list allows script termination');
check(!str_contains($rendered, 'href="javascript:'), 'Rendered legacy link is clickable');
check(str_contains($rendered, 'href="/sklep/polka/"'), 'Legacy local fallback missing');
check(str_contains($rendered, 'autoplay loop muted playsinline'), 'Video playback attributes lost');
check(!str_contains($rendered, 'darmową dostawę') && !str_contains($rendered, 'pełną ochronę'), 'Unconditional claims remain');

// Every JSON-LD expression, including product breadcrumbs, must be script-safe.
foreach (['php/sklep-lista.php', 'php/sklep-produkt.php', 'dist/sklep/index.php', 'dist/sklep/produkt.php'] as $path) {
    preg_match_all('~<script type="application/ld\+json"><\?=\s*(.*?)\s*\?></script>~s', file_get_contents(__DIR__ . '/' . $path), $expressions);
    foreach ($expressions[1] as $expression) {
        $ld = $ldWideo = $okruszki = ['name' => '</script><img src=x onerror=PRIVATE>'];
        ob_start();
        try { eval('echo ' . $expression . ';'); $jsonBlock = ob_get_contents(); }
        finally { ob_end_clean(); }
        check(!str_contains($jsonBlock, '</script>'), 'Unsafe JSON-LD expression in ' . $path);
    }
}
// -------------------------------------------------------------------------
// Kolejka Allegro: testy na żywo przeciw produkcji (wymaga sieci). Uruchamiane
// po wysyłce (Step 6) — jeśli produkcja nieosiągalna, ostrzegają i nie liczą się
// do $checks, zamiast fałszywie psuć resztę zestawu.
function fw_test_zapytanie(string $metoda, string $akcja, array $naglowki = [], ?string $cialo = null): int
{
    $ch = curl_init('https://fwdrucik.pl/api/sklep.php?akcja=' . $akcja);
    curl_setopt_array($ch, [
        CURLOPT_CUSTOMREQUEST => $metoda,
        CURLOPT_HTTPHEADER => $naglowki,
        CURLOPT_POSTFIELDS => $cialo,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 10,
    ]);
    curl_exec($ch);
    $kod = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return $kod;
}
/** Jak fw_test_zapytanie, ale zwraca tresc odpowiedzi zamiast tylko kodu. */
function fw_test_zapytanie_tresc(string $metoda, string $url, array $naglowki = [], ?string $cialo = null): string
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_CUSTOMREQUEST => $metoda,
        CURLOPT_HTTPHEADER => $naglowki,
        CURLOPT_POSTFIELDS => $cialo,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 10,
    ]);
    $tresc = curl_exec($ch);
    curl_close($ch);
    return (string) $tresc;
}
$pominieteAllegro = 0;
$siecOk = fw_test_zapytanie('GET', 'produkty') > 0;
if (!$siecOk) {
    echo "UWAGA: produkcja nieosiągalna — pomijam testy kolejki Allegro na żywo.\n";
    $pominieteAllegro += 4;
} else {
    check(fw_test_zapytanie('GET', 'allegro-kolejka') === 403, 'allegro-kolejka bez tokenu powinno dać 403');
    check(fw_test_zapytanie('GET', 'allegro-kolejka', ['X-Agent-Token: zly-token']) === 403,
        'allegro-kolejka z błędnym tokenem powinno dać 403');
    check(fw_test_zapytanie('POST', 'allegro-wynik', ['Content-Type: application/json'], '{"id":1,"allegro_status":"aktywna"}') === 403,
        'allegro-wynik bez tokenu powinno dać 403');
    check(in_array(fw_test_zapytanie('POST', 'allegro-wystaw', [], 'id=1'), [401, 403], true),
        'allegro-wystaw bez sesji admina powinno dać 401 lub 403');

    $token = null;
    $sciezkaKonfiga = 'D:/DrucikSerwer/allegro_config.json';
    if (is_file($sciezkaKonfiga)) {
        $token = (string) (json_decode((string) file_get_contents($sciezkaKonfiga), true)['site_agent_token'] ?? '') ?: null;
    }
    if ($token === null) {
        echo "UWAGA: brak D:/DrucikSerwer/allegro_config.json — pomijam test wymagający tokenu.\n";
        $pominieteAllegro += 1;
    } else {
        check(fw_test_zapytanie('POST', 'allegro-wynik', ['X-Agent-Token: ' . $token, 'Content-Type: application/json'],
            '{"id":1,"allegro_status":"aktywna-hack"}') === 422,
            'allegro-wynik z nieprawidłowym allegro_status powinno dać 422');
    }
}

// -------------------------------------------------------------------------
// Naprawy z końcowego przeglądu (14.09) na żywo: wyciek pól Allegro dla
// anonima i cofnięcie wskrzeszania usuniętych produktów. Ten sam wzorzec —
// loud skip bez sieci/tokenu, zamiast fałszywie psuć resztę zestawu.
if (!$siecOk) {
    echo "UWAGA: produkcja nieosiągalna — pomijam testy finalnego przeglądu na żywo.\n";
    $pominieteAllegro += 5;
} else {
    $szkice = json_decode(fw_test_zapytanie_tresc('GET', 'https://fwdrucik.pl/api/sklep.php?akcja=allegro-szkice'), true) ?: [];
    foreach (($szkice['szkice'] ?? []) as $s) {
        check(!array_key_exists('allegro_parametry', $s) && !array_key_exists('parametry', $s)
            && !array_key_exists('sales_center_url', $s),
            'allegro-szkice anonimowo wycieka pola admina dla produktu ' . ($s['id'] ?? '?'));
    }

    $produkty = json_decode(fw_test_zapytanie_tresc('GET', 'https://fwdrucik.pl/api/sklep.php?akcja=produkty'), true) ?: [];
    $szkicowyProdukt = null;
    foreach (($produkty['produkty'] ?? []) as $p) {
        if (($p['allegro_status'] ?? null) !== 'aktywna') {
            check(empty($p['allegro_url']) && empty($p['allegro_id']),
                'produkty anonimowo wycieka allegro_url/id dla nieaktywnej oferty ' . ($p['id'] ?? '?'));
        }
        if ((int) ($p['id'] ?? 0) === 21) {
            $szkicowyProdukt = $p;
        }
    }
    if ($szkicowyProdukt === null) {
        echo "UWAGA: produkt 21 (szkic) nie jest już publiczny — pomijam sprawdzenie karty produktu.\n";
        $pominieteAllegro += 1;
    } else {
        $strona = fw_test_zapytanie_tresc('GET', 'https://fwdrucik.pl/sklep/' . $szkicowyProdukt['slug'] . '/');
        check(!str_contains($strona, 'Kup na Allegro'), 'Karta produktu szkicu Allegro pokazuje link zakupu');
    }

    check(fw_test_zapytanie('GET', 'produkty') === 200, 'akcja=produkty przestało odpowiadać 200');

    if (!isset($token) || $token === null) {
        echo "UWAGA: brak tokenu agenta — pomijam sprawdzenie admin-produkty/produkt-zapisz 404.\n";
        $pominieteAllegro += 2;
    } else {
        $adminProdukty = json_decode(fw_test_zapytanie_tresc('GET',
            'https://fwdrucik.pl/api/sklep.php?akcja=admin-produkty', ['X-Agent-Token: ' . $token]), true) ?: [];
        $maPolaAllegro = false;
        foreach (($adminProdukty['produkty'] ?? []) as $p) {
            if (array_key_exists('allegro_status', $p)) {
                $maPolaAllegro = true;
                break;
            }
        }
        check($maPolaAllegro, 'admin-produkty z tokenem agenta nie zwraca pól allegro_*');

        check(fw_test_zapytanie('POST', 'produkt-zapisz', ['X-Agent-Token: ' . $token, 'Content-Type: application/json'],
            '{"id":999999,"nazwa":"test","kategoria":"inne","cena":"1.00"}') === 404,
            'produkt-zapisz z id>0 spoza bazy nie daje 404 (wskrzesza usunięty produkt)');
    }
}

echo "OK: $checks security checks\n";
if ($pominieteAllegro > 0) {
    echo "POMINIETO $pominieteAllegro testow Allegro — brak sieci/tokenu\n";
    exit(2);
}
