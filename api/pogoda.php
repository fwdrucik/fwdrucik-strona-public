<?php
declare(strict_types=1);

/**
 * Pogoda do paska strony i chmurki nad robotem.
 *
 * Pośredniczy w zapytaniu do Open-Meteo (bez klucza), żeby adres IP odwiedzającego
 * nie trafiał do obcej usługi. Współrzędne zaokrąglamy do 0,25° (ok. 20–30 km),
 * a wynik trzymamy 15 minut w katalogu tymczasowym — jedno zapytanie na okolicę.
 *
 * GET /api/pogoda.php?lat=52.25&lon=21.0
 * → {"ok":true,"temp":7,"kod":61,"wiatr":18,"porywy":40,"dzien":1}
 */

ini_set('display_errors', '0');
header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

$lat = filter_input(INPUT_GET, 'lat', FILTER_VALIDATE_FLOAT);
$lon = filter_input(INPUT_GET, 'lon', FILTER_VALIDATE_FLOAT);
if (!is_float($lat) || !is_float($lon) || abs($lat) > 90 || abs($lon) > 180) {
    http_response_code(400);
    echo '{"ok":false}';
    exit;
}
$lat = round($lat * 4) / 4;
$lon = round($lon * 4) / 4;

$katalog = sys_get_temp_dir() . '/fw-pogoda';
if (!is_dir($katalog)) {
    @mkdir($katalog, 0700, true);
}
$plik = sprintf('%s/%.2f_%.2f.json', $katalog, $lat, $lon);
if (is_file($plik) && time() - (int) filemtime($plik) < 900) {
    readfile($plik);
    exit;
}

$url = 'https://api.open-meteo.com/v1/forecast?' . http_build_query([
    'latitude' => $lat,
    'longitude' => $lon,
    'current' => 'temperature_2m,weather_code,wind_speed_10m,wind_gusts_10m,is_day',
    'wind_speed_unit' => 'kmh',
    'timezone' => 'auto',
]);

$surowe = false;
if (function_exists('curl_init')) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 6,
        CURLOPT_USERAGENT => 'fwdrucik.pl/pogoda',
    ]);
    $surowe = curl_exec($ch);
    curl_close($ch);
} else {
    $surowe = @file_get_contents($url, false, stream_context_create([
        'http' => ['timeout' => 6, 'header' => "User-Agent: fwdrucik.pl/pogoda\r\n"],
    ]));
}

$dane = is_string($surowe) ? json_decode($surowe, true) : null;
if (!is_array($dane) || !isset($dane['current']) || !is_array($dane['current'])) {
    http_response_code(502);
    echo '{"ok":false}';
    exit;
}

$c = $dane['current'];
$wynik = json_encode([
    'ok' => true,
    'temp' => (int) round((float) ($c['temperature_2m'] ?? 0)),
    'kod' => (int) ($c['weather_code'] ?? 0),
    'wiatr' => (int) round((float) ($c['wind_speed_10m'] ?? 0)),
    'porywy' => (int) round((float) ($c['wind_gusts_10m'] ?? 0)),
    'dzien' => (int) ($c['is_day'] ?? 1),
]);
@file_put_contents($plik, (string) $wynik, LOCK_EX);
echo $wynik;
