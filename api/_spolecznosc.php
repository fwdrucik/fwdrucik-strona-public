<?php
declare(strict_types=1);
require_once __DIR__ . '/_lib.php';

function fw_spolecznosc_migracja(): void {
    $pdo = fw_baza();
    $schemas = [
        'opinie' => 'id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, autor_id INT UNSIGNED NOT NULL, przedmiot VARCHAR(12) NOT NULL, ocena TINYINT UNSIGNED NOT NULL, tresc TEXT NOT NULL, status VARCHAR(16) NOT NULL DEFAULT "oczekuje", utworzony DATETIME NOT NULL, zmieniony DATETIME NOT NULL, UNIQUE KEY autor_przedmiot (autor_id, przedmiot), KEY lista (przedmiot,status,zmieniony)',
        'odpowiedzi_firmy' => 'typ VARCHAR(12) NOT NULL, tresc_id INT UNSIGNED NOT NULL, tresc TEXT NOT NULL, admin_id INT UNSIGNED NOT NULL, zmieniony DATETIME NOT NULL, PRIMARY KEY (typ,tresc_id)',
        'moderacja_historia' => 'id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, admin_id INT UNSIGNED NOT NULL, typ VARCHAR(12) NOT NULL, tresc_id INT UNSIGNED NOT NULL, decyzja VARCHAR(24) NOT NULL, kiedy DATETIME NOT NULL, KEY data (kiedy)',
        'polecenia_kody' => 'uzytkownik_id INT UNSIGNED PRIMARY KEY, kod CHAR(24) NOT NULL UNIQUE',
        'polecenia' => 'polecony_id INT UNSIGNED PRIMARY KEY, polecajacy_id INT UNSIGNED NOT NULL, kiedy DATETIME NOT NULL, KEY polecajacy (polecajacy_id)',
        'udostepnienia' => 'uzytkownik_id INT UNSIGNED NOT NULL, dzien DATE NOT NULL, PRIMARY KEY (uzytkownik_id,dzien)',
        'ai_budzet' => 'okres VARCHAR(80) PRIMARY KEY, zuzycie INT UNSIGNED NOT NULL DEFAULT 0'
    ];
    foreach ($schemas as $table => $schema) {
        $pdo->exec('CREATE TABLE IF NOT EXISTS ' . fw_tabela($table) . ' (' . $schema . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci');
    }
}
function fw_spolecznosc_gotowa(): bool {
    static $ready = null;
    if ($ready === null) {
        $st = fw_baza()->prepare('SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=?');
        $st->execute([fw_tabela('ai_budzet')]);
        $ready = (int)$st->fetchColumn() === 1;
    }
    return $ready;
}
function fw_spolecznosc_wymagaj(): void {
    if (!fw_spolecznosc_gotowa()) fw_blad(503, 'Sekcja jest przygotowywana. Spróbuj później.');
}
function fw_spolecznosc_skalar(string $sql, array $args): int {
    $st = fw_baza()->prepare($sql); $st->execute($args); return (int)$st->fetchColumn();
}
function fw_poziom(int $punkty): array {
    $levels = [[0,'Nowy'],[20,'Bywalec'],[60,'Aktywny'],[150,'Stały uczestnik'],[350,'Ambasador']];
    $index = 0;
    foreach ($levels as $i => $l) if ($punkty >= $l[0]) $index = $i;
    return ['gwiazdki'=>$index+1, 'nazwa'=>$levels[$index][1], 'punkty'=>$punkty, 'nastepny_prog'=>$levels[$index+1][0] ?? null];
}
function fw_zakupy_liczba(int $id): int {
    return fw_spolecznosc_skalar('SELECT COUNT(*) FROM ' . fw_tabela('zamowienia') . ' WHERE uzytkownik_id=? AND status="zakonczone"', [$id]);
}
function fw_profil_aktywnosci(int $id): array {
    static $cache = [];
    if (isset($cache[$id])) return $cache[$id];
    $pdo = fw_baza();
    $zakupy = fw_zakupy_liczba($id);
    // Derivation from current source records makes reversals and retries idempotent.
    $st = $pdo->prepare('SELECT dzien, SUM(punkty) punkty FROM ('
        . 'SELECT DATE(utworzony) dzien, 5 punkty FROM ' . fw_tabela('watki') . ' WHERE autor_id=? AND status="opublikowany"'
        . ' UNION ALL SELECT DATE(o.utworzona) dzien, 2 punkty FROM ' . fw_tabela('odpowiedzi') . ' o JOIN ' . fw_tabela('watki') . ' w ON w.id=o.watek_id WHERE o.autor_id=? AND o.status="opublikowany" AND w.status="opublikowany") x GROUP BY dzien');
    $st->execute([$id,$id]);
    $forumPoints = 0; foreach ($st->fetchAll() as $r) $forumPoints += min(20,(int)$r['punkty']);
    $watki = fw_spolecznosc_skalar('SELECT COUNT(*) FROM ' . fw_tabela('watki') . ' WHERE autor_id=? AND status="opublikowany"',[$id]);
    $odpowiedzi = fw_spolecznosc_skalar('SELECT COUNT(*) FROM ' . fw_tabela('odpowiedzi') . ' o JOIN ' . fw_tabela('watki') . ' w ON w.id=o.watek_id WHERE o.autor_id=? AND o.status="opublikowany" AND w.status="opublikowany"',[$id]);
    $polecenia = fw_spolecznosc_skalar('SELECT COUNT(*) FROM ' . fw_tabela('polecenia') . ' p JOIN ' . fw_tabela('uzytkownicy') . ' u ON u.id=p.polecony_id WHERE p.polecajacy_id=? AND u.zablokowany=0 AND EXISTS (SELECT 1 FROM ' . fw_tabela('zamowienia') . ' z WHERE z.uzytkownik_id=p.polecony_id AND z.status="zakonczone")',[$id]);
    $udostepnienia = fw_spolecznosc_skalar('SELECT COUNT(*) FROM ' . fw_tabela('udostepnienia') . ' WHERE uzytkownik_id=?',[$id]);
    return $cache[$id] = ['poziom'=>fw_poziom($zakupy*20+$forumPoints+$polecenia*3), 'zakupy'=>$zakupy, 'watki'=>$watki, 'odpowiedzi'=>$odpowiedzi, 'polecenia'=>$polecenia,'udostepnienia'=>$udostepnienia];
}
function fw_spolecznosc_audyt(int $admin, string $typ, int $id, string $decyzja): void {
    fw_baza()->prepare('INSERT INTO ' . fw_tabela('moderacja_historia') . ' (admin_id,typ,tresc_id,decyzja,kiedy) VALUES (?,?,?,?,?)')->execute([$admin,$typ,$id,$decyzja,fw_teraz()]);
}
function fw_opinia_przedmiot(string $value): string {
    if (!in_array($value,['sklep','strona'],true)) fw_blad(422,'Wybierz sklep lub stronę.');
    return $value;
}