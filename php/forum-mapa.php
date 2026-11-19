<?php
declare(strict_types=1);

/**
 * Mapa serwisu dla wątków forum.
 *
 * Wątki powstają w bazie, a nie przy budowaniu serwisu, więc nie mogą trafić
 * do statycznego sitemap.xml — do wczoraj nie było ich tam wcale i żadna
 * dyskusja nie miała szans trafić do wyszukiwarki. Ta mapa liczy się na bieżąco
 * i jest podana w robots.txt obok mapy głównej.
 */

require_once __DIR__ . '/../api/_lib.php';

header('Content-Type: application/xml; charset=UTF-8');
// Mapa nie musi być świeża co do minuty — godzina w cache oszczędza bazie
// zapytań przy każdej wizycie robota.
header('Cache-Control: public, max-age=3600');

$pdo = fw_baza();
$st = $pdo->query('SELECT id, tytul, ostatnia_aktywnosc'
    . ' FROM ' . fw_tabela('watki')
    . ' WHERE status = "opublikowany"'
    . ' ORDER BY ostatnia_aktywnosc DESC LIMIT 5000');

$wiersze = [];
foreach ($st->fetchAll() as $w) {
    $slug = fw_slug_tytulu((string) $w['tytul']);
    $adres = 'https://fwdrucik.pl/forum/watek/' . (int) $w['id']
        . ($slug !== '' ? '-' . $slug : '') . '/';
    $data = date_create((string) $w['ostatnia_aktywnosc']);
    $wiersze[] = "  <url>\n"
        . '    <loc>' . htmlspecialchars($adres, ENT_XML1) . "</loc>\n"
        . '    <lastmod>' . ($data ? $data->format('Y-m-d') : date('Y-m-d')) . "</lastmod>\n"
        . "    <changefreq>weekly</changefreq>\n"
        . "    <priority>0.6</priority>\n"
        . '  </url>';
}

echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n"
    . '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n"
    . implode("\n", $wiersze)
    . ($wiersze ? "\n" : '')
    . "</urlset>\n";
