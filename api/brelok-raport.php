<?php
declare(strict_types=1);

/**
 * Raport dzienny testu „brelok 3D" — przyjmuje tekst od brelok-worker (Cloudflare)
 * i wysyła go mailem do warsztatu. Nic nie zapisuje.
 * Konfiguracja: 'brelok_raport_sekret' (ten sam co RAPORT_SEKRET workera), 'email_zamowien'.
 */
require_once __DIR__ . '/_lib.php';
require_once __DIR__ . '/_poczta.php';

fw_wymagaj_post();

$cfg = fw_konfiguracja();
$sekret = (string) ($cfg['brelok_raport_sekret'] ?? '');
$podany = (string) ($_SERVER['HTTP_X_SEKRET'] ?? '');
if ($sekret === '' || !hash_equals($sekret, $podany)) {
    fw_blad(403, 'Brak dostępu.');
}

fw_limit('brelok-raport', 10, 3600);

$dane = json_decode((string) file_get_contents('php://input'), true);
$tekst = is_array($dane) ? trim((string) ($dane['tekst'] ?? '')) : '';
if ($tekst === '' || mb_strlen($tekst) > 5000) {
    fw_blad(400, 'Pusty albo za długi raport.');
}

$do = (string) ($cfg['email_zamowien'] ?? FW_NADAWCA_DOMYSLNY);
$ok = fw_wyslij_mail($do, 'Brelok 3D — raport dnia', $tekst);
fw_odpowiedz(['ok' => $ok], $ok ? 200 : 502);
