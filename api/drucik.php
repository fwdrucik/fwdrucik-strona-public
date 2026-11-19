<?php
declare(strict_types=1);

require_once __DIR__ . '/_lib.php';

$u = fw_wymagaj_logowania();
$wlasciciel = (int) $u['id'];
$tabela = fw_tabela('drucik');
$pdo = fw_baza();

if (fw_metoda() === 'GET') {
    try {
        $st = $pdo->prepare("SELECT wersja, profil FROM $tabela WHERE wlasciciel_id = ?");
        $st->execute([$wlasciciel]);
        $zapis = $st->fetch();
    } catch (PDOException $e) {
        if ($e->getCode() !== '42S02') {
            throw $e;
        }
        $zapis = false;
    }
    fw_odpowiedz([
        'ok' => true,
        'wersja' => $zapis ? (int) $zapis['wersja'] : 0,
        'profil' => $zapis ? json_decode($zapis['profil'], true, 8, JSON_THROW_ON_ERROR) : null,
    ]);
}

fw_wymagaj_post();
fw_sprawdz_csrf();
fw_limit('drucik-zapis', 60, 3600);
$dane = fw_wejscie();
$wersja = $dane['wersja'] ?? null;
$energia = $dane['energia'] ?? null;
$kolor = $dane['kolor'] ?? null;
$paliwo = $dane['paliwo'] ?? null;
$kroki = $dane['kroki'] ?? null;
$imie = fw_tekst(fw_pole('imie'), 'Imię robota', 1, 24);
$sceny = ['glowa', 'spacer', 'czysci', 'puka', 'spawa', 'tnie', 'silnik', 'elektronika'];
if (!is_int($wersja) || $wersja < 0 || $wersja >= 4294967295
    || !is_int($energia) || $energia < 0 || $energia > 100
    || !in_array($kolor, ['mosiadz', 'plazma', 'miedz', 'stal'], true)
    || !in_array($paliwo, ['diesel', 'benzyna', 'lpg'], true)
    || !is_array($kroki) || !array_is_list($kroki) || count($kroki) > 5
    || !preg_match('/^[\p{L}\p{N} _-]+$/u', $imie)) {
    fw_blad(422, 'Sprawdź imię, kolor i ustawienia Drucika.');
}
foreach ($kroki as $krok) {
    if (!in_array($krok, $sceny, true)) {
        fw_blad(422, 'Nieznane polecenie w programie Drucika.');
    }
}

$profil = compact('imie', 'kolor', 'paliwo', 'energia', 'kroki');
$json = json_encode($profil, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE);
$nowaWersja = $wersja + 1;

if ($wersja === 0) {
    $uzytkownicy = fw_tabela('uzytkownicy');
    $pdo->exec("CREATE TABLE IF NOT EXISTS $tabela ("
        . 'wlasciciel_id INT UNSIGNED NOT NULL PRIMARY KEY, wersja INT UNSIGNED NOT NULL,'
        . ' profil VARCHAR(1024) NOT NULL,'
        . " FOREIGN KEY (wlasciciel_id) REFERENCES $uzytkownicy (id) ON DELETE CASCADE"
        . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci');
    $st = $pdo->prepare("INSERT INTO $tabela (wlasciciel_id, wersja, profil) VALUES (?, ?, ?)");
    try {
        $st->execute([$wlasciciel, $nowaWersja, $json]);
    } catch (PDOException $e) {
        if ((int) ($e->errorInfo[1] ?? 0) !== 1062) {
            throw $e;
        }
        fw_blad(409, 'Zapis istnieje w innej karcie. Odśwież stronę przed zmianami.');
    }
} else {
    $st = $pdo->prepare("UPDATE $tabela SET wersja = ?, profil = ? WHERE wlasciciel_id = ? AND wersja = ?");
    $st->execute([$nowaWersja, $json, $wlasciciel, $wersja]);
    if ($st->rowCount() !== 1) {
        fw_blad(409, 'Profil zmienił się w innej karcie. Odśwież stronę przed zapisem.');
    }
}
fw_odpowiedz(['ok' => true, 'wersja' => $nowaWersja, 'profil' => $profil]);
