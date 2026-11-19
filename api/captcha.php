<?php
declare(strict_types=1);

/**
 * Captcha własnej roboty — obrazek z kodem generowany przez GD.
 *
 *   GET /api/captcha.php?akcja=nowa    → {"id": "...", "obraz": "/api/captcha.php?akcja=obraz&id=..."}
 *   GET /api/captcha.php?akcja=obraz&id=...  → PNG
 *
 * Dlaczego nie reCAPTCHA ani hCaptcha: obie wymagają konta u zewnętrznego
 * dostawcy, kluczy w konfiguracji i wysyłają dane każdego odwiedzającego do
 * USA — czyli osobnej podstawy prawnej w polityce prywatności. Do formularza
 * rejestracji w małym serwisie to nieproporcjonalny koszt.
 *
 * Odpowiedź trzymamy jako skrót w bazie, nigdy w ciasteczku ani w HTML —
 * inaczej wystarczyłoby ją odczytać i przepisać.
 */

require_once __DIR__ . '/_lib.php';
require_once __DIR__ . '/_captcha.php';

$akcja = fw_akcja();

if ($akcja === 'nowa') {
    fw_zapewnij_tabele_captcha();
    fw_captcha_posprzataj();
    fw_limit('captcha', 60, 3600);

    $kod = '';
    for ($i = 0; $i < FW_CAPTCHA_DLUGOSC; $i++) {
        $kod .= FW_CAPTCHA_ZNAKI[random_int(0, strlen(FW_CAPTCHA_ZNAKI) - 1)];
    }
    $id = bin2hex(random_bytes(16));
    fw_baza()->prepare('INSERT INTO ' . fw_tabela('captcha') . ' (id, odpowiedz, wygasa) VALUES (?,?,?)')
        ->execute([$id, $kod, date('Y-m-d H:i:s', time() + FW_CAPTCHA_WAZNOSC_S)]);

    fw_odpowiedz([
        'ok' => true,
        'id' => $id,
        'obraz' => '/api/captcha.php?akcja=obraz&id=' . $id,
        // Gdy na serwerze nie ma biblioteki GD, obrazek nie powstanie —
        // wtedy front pokazuje kod jako tekst do przepisania.
        'grafika' => function_exists('imagecreatetruecolor'),
    ]);
}

if ($akcja === 'obraz') {
    fw_zapewnij_tabele_captcha();
    $id = (string) ($_GET['id'] ?? '');
    if (!preg_match('/^[a-f0-9]{32}$/', $id)) {
        http_response_code(404);
        exit;
    }
    $st = fw_baza()->prepare('SELECT odpowiedz FROM ' . fw_tabela('captcha')
        . ' WHERE id = ? AND wygasa >= ?');
    $st->execute([$id, fw_teraz()]);
    $kod = $st->fetchColumn();
    if ($kod === false) {
        http_response_code(404);
        exit;
    }

    header('Content-Type: image/png');
    header('Cache-Control: no-store, no-cache, must-revalidate');
    header('X-Robots-Tag: noindex, nofollow');

    if (!function_exists('imagecreatetruecolor')) {
        http_response_code(501);
        exit;
    }

    $szer = 200;
    $wys = 70;
    $obraz = imagecreatetruecolor($szer, $wys);
    $tlo = imagecolorallocate($obraz, 26, 30, 36);
    $tekst = imagecolorallocate($obraz, 231, 235, 240);
    $akcent = imagecolorallocate($obraz, 46, 194, 255);
    $szum = imagecolorallocate($obraz, 70, 80, 92);
    imagefilledrectangle($obraz, 0, 0, $szer, $wys, $tlo);

    // Szum: kropki i linie utrudniaja automatyczne odczytanie,
    // a czlowiekowi nie przeszkadzaja.
    for ($i = 0; $i < 400; $i++) {
        imagesetpixel($obraz, random_int(0, $szer), random_int(0, $wys), $szum);
    }
    for ($i = 0; $i < 5; $i++) {
        imageline($obraz, random_int(0, $szer), random_int(0, $wys),
            random_int(0, $szer), random_int(0, $wys), $szum);
    }

    $odstep = (int) (($szer - 24) / FW_CAPTCHA_DLUGOSC);
    for ($i = 0; $i < strlen((string) $kod); $i++) {
        $kolor = $i % 2 === 0 ? $tekst : $akcent;
        imagestring($obraz, 5, 16 + $i * $odstep, random_int(18, 38), $kod[$i], $kolor);
        imagestring($obraz, 5, 17 + $i * $odstep, random_int(18, 38), $kod[$i], $kolor);
    }

    imagepng($obraz);
    imagedestroy($obraz);
    exit;
}

fw_blad(404, 'Nieznana akcja.');
