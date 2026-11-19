<?php
/**
 * Jednorazowe naniesienie znaku wodnego na zdjęcia, które już leżą w sklepie.
 *
 * Nowe zdjęcia dostają logo przy wgrywaniu (patrz `_znak_wodny.php` wpięty
 * w `sklep.php`). Ten skrypt zajmuje się tym, co zostało wgrane wcześniej.
 *
 * Uruchomienie na serwerze:
 *
 *     php api/znakuj-istniejace.php            # tylko pokazuje, co by zrobił
 *     php api/znakuj-istniejace.php --zapisz   # naprawdę nanosi znak
 *
 * BEZ `--zapisz` nic nie jest zmieniane. To nie jest ostrożność na wyrost:
 * znak wypala się w pikselach i drugie przejście nałożyłoby drugie logo na
 * pierwsze. Dlatego skrypt zapisuje obok pliku znacznik `.znak`, a plik
 * z takim znacznikiem pomija przy kolejnym uruchomieniu.
 *
 * Kopie oryginałów lądują w podkatalogu `bez-znaku/`. Zajmują miejsce, ale są
 * jedyną drogą powrotu, gdy znak wyjdzie za duży albo w złym rogu.
 */

if (PHP_SAPI !== 'cli') {
    http_response_code(403);
    exit("Ten skrypt uruchamia się wyłącznie z linii poleceń.\n");
}

require_once __DIR__ . '/_lib.php';
require_once __DIR__ . '/_znak_wodny.php';

$zapisz = in_array('--zapisz', $argv, true);

$katalog = FW_KATALOG_OBRAZOW;
if (!is_dir($katalog)) {
    exit("Nie ma katalogu ze zdjęciami: $katalog\n");
}

$kopie = $katalog . '/bez-znaku';
if ($zapisz && !is_dir($kopie) && !@mkdir($kopie, 0755, true)) {
    exit("Nie mogę utworzyć katalogu na kopie: $kopie\n");
}

$zrobione = 0;
$pominiete = 0;
$bledy = 0;

foreach (scandir($katalog) ?: [] as $nazwa) {
    $sciezka = $katalog . '/' . $nazwa;
    if (!is_file($sciezka)) {
        continue;
    }

    $info = @getimagesize($sciezka);
    if ($info === false || !in_array($info[2], [IMAGETYPE_JPEG, IMAGETYPE_PNG, IMAGETYPE_WEBP], true)) {
        continue;   // GIF-y i wszystko, co nie jest obrazem, zostawiamy
    }

    if (is_file($sciezka . '.znak')) {
        $pominiete++;
        continue;
    }

    if (!$zapisz) {
        echo "[próba] $nazwa ({$info[0]}x{$info[1]})\n";
        $zrobione++;
        continue;
    }

    if (!@copy($sciezka, $kopie . '/' . $nazwa)) {
        echo "[błąd] nie udało się zrobić kopii $nazwa — pomijam\n";
        $bledy++;
        continue;
    }

    if (fw_nanies_znak_wodny($sciezka, $info[2])) {
        @touch($sciezka . '.znak');
        echo "[znak] $nazwa\n";
        $zrobione++;
    } else {
        // Kopia niepotrzebna, skoro plik został nietknięty.
        @unlink($kopie . '/' . $nazwa);
        echo "[pomijam] $nazwa — nie udało się nanieść znaku\n";
        $bledy++;
    }
}

echo "\n";
echo $zapisz ? "Zrobione: $zrobione" : "Do zrobienia: $zrobione";
echo " | już ze znakiem: $pominiete | błędy: $bledy\n";
if (!$zapisz) {
    echo "Nic nie zostało zmienione. Powtórz z --zapisz, żeby nanieść znak.\n";
}
