<?php
declare(strict_types=1);
require_once __DIR__.'/_asystent.php';

function fw_czat_migracja(): void {
    $schemas=[
      'czat_rozmowy'=>'id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, token_hash CHAR(64) NOT NULL UNIQUE, tryb VARCHAR(16) NOT NULL DEFAULT "bot", wersja INT UNSIGNED NOT NULL DEFAULT 0, pending CHAR(36) NULL, pending_od DATETIME NULL, admin_id INT UNSIGNED NULL, utworzona DATETIME NOT NULL, zmieniona DATETIME NOT NULL, KEY data (zmieniona)',
      'czat_wiadomosci'=>'id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, rozmowa_id BIGINT UNSIGNED NOT NULL, rola VARCHAR(16) NOT NULL, tresc TEXT NOT NULL, request_id CHAR(36) NULL, kiedy DATETIME NOT NULL, UNIQUE KEY request (rozmowa_id,request_id), KEY rozmowa (rozmowa_id,id)',
      'czat_urzadzenia'=>'token_hash CHAR(64) PRIMARY KEY, token TEXT NOT NULL, admin_id INT UNSIGNED NOT NULL, zmieniony DATETIME NOT NULL',
      'czat_push'=>'id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, rozmowa_id BIGINT UNSIGNED NOT NULL, wiadomosc_id BIGINT UNSIGNED NOT NULL UNIQUE, status VARCHAR(12) NOT NULL DEFAULT "oczekuje", proby INT UNSIGNED NOT NULL DEFAULT 0, dostarczone TEXT NULL, nastepna DATETIME NOT NULL, kiedy DATETIME NOT NULL, KEY kolejka (status,nastepna)'
    ];
    foreach($schemas as $t=>$schema) fw_baza()->exec('CREATE TABLE IF NOT EXISTS '.fw_tabela($t).' ('.$schema.') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci');
    $st=fw_baza()->prepare('SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=? AND COLUMN_NAME="dostarczone"');
    $st->execute([fw_tabela('czat_push')]);if(!(int)$st->fetchColumn())fw_baza()->exec('ALTER TABLE '.fw_tabela('czat_push').' ADD COLUMN dostarczone TEXT NULL');
}
function fw_czat_sql(string $sql,array $args=[]): PDOStatement {$s=fw_baza()->prepare($sql);$s->execute($args);return $s;}
function fw_czat_retencja(): void {
    $pdo=fw_baza();$pdo->beginTransaction();
    $ids=$pdo->query('SELECT id FROM '.fw_tabela('czat_rozmowy').' WHERE zmieniona<NOW()-INTERVAL 30 DAY ORDER BY id LIMIT 100 FOR UPDATE')->fetchAll(PDO::FETCH_COLUMN);
    foreach($ids as $id) {foreach(['czat_wiadomosci','czat_push'] as $t)fw_czat_sql('DELETE FROM '.fw_tabela($t).' WHERE rozmowa_id=?',[$id]);fw_czat_sql('DELETE FROM '.fw_tabela('czat_rozmowy').' WHERE id=?',[$id]);}
    $pdo->commit();
}
function fw_czat_rozmowa(bool $lock=false): array {
    $token=(string)($_COOKIE['fw_czat']??'');
    if(!preg_match('/^[a-f0-9]{64}$/',$token))fw_blad(401,'Rozpocznij rozmowę.');
    $r=fw_czat_sql('SELECT * FROM '.fw_tabela('czat_rozmowy').' WHERE token_hash=?'.($lock?' FOR UPDATE':''),[hash('sha256',$token)])->fetch();
    if(!$r)fw_blad(404,'Rozmowa wygasła lub została usunięta. Rozpocznij nową.');return $r;
}
function fw_czat_lista_wiadomosci(int $id,int $after=0): array {
    return fw_czat_sql('SELECT id,rola,tresc,kiedy FROM '.fw_tabela('czat_wiadomosci').' WHERE rozmowa_id=? AND id>? ORDER BY id LIMIT 200',[$id,$after])->fetchAll();
}
function fw_czat_dodaj(int $id,string $role,string $text,?string $request=null): int {
    fw_czat_sql('INSERT INTO '.fw_tabela('czat_wiadomosci').' (rozmowa_id,rola,tresc,request_id,kiedy) VALUES (?,?,?,?,NOW())',[$id,$role,$text,$request]);return (int)fw_baza()->lastInsertId();
}
function fw_czat_push(): void {
    if(!is_file(__DIR__.'/_push.php'))return;
    require_once __DIR__.'/_push.php';
    $tokens=fw_czat_sql('SELECT d.token FROM '.fw_tabela('czat_urzadzenia').' d JOIN '.fw_tabela('uzytkownicy').' u ON u.id=d.admin_id WHERE u.rola="admin" AND u.zablokowany=0')->fetchAll(PDO::FETCH_COLUMN);
    if(!$tokens)return;
    $pdo=fw_baza();$pdo->beginTransaction();
    $jobs=fw_czat_sql('SELECT * FROM '.fw_tabela('czat_push').' WHERE status IN ("oczekuje","wysylanie") AND nastepna<=NOW() ORDER BY id LIMIT 1 FOR UPDATE')->fetchAll();
    foreach($jobs as $j)fw_czat_sql('UPDATE '.fw_tabela('czat_push').' SET status="wysylanie", proby=proby+1,nastepna=NOW()+INTERVAL 2 MINUTE WHERE id=?',[$j['id']]);
    $pdo->commit();
    foreach($jobs as $j){
        try{$done=json_decode($j['dostarczone']??'[]',true)?:[];$remaining=array_values(array_filter($tokens,static fn($t)=>!in_array(hash('sha256',$t),$done,true)));$r=fw_push_wyslij($remaining,(int)$j['rozmowa_id'],(int)$j['wiadomosc_id']);
            $retry=$r['retry_tokens']??$remaining;foreach($remaining as $t)if(!in_array($t,$retry,true))$done[]=hash('sha256',$t);$ok=count($retry)===0;$delay=max(60,(int)($r['retry_after']??60),min(3600,60*(2**min(5,(int)$j['proby']))));
            foreach(($r['invalid_tokens']??[]) as $token)fw_czat_sql('DELETE FROM '.fw_tabela('czat_urzadzenia').' WHERE token_hash=?',[hash('sha256',$token)]);
            fw_czat_sql('UPDATE '.fw_tabela('czat_push').' SET status=?,dostarczone=?,nastepna=DATE_ADD(NOW(),INTERVAL '.$delay.' SECOND) WHERE id=?',[$ok?'wyslano':'oczekuje',json_encode(array_values(array_unique($done))),$j['id']]);
        }catch(Throwable $e){error_log('FW chat push '.get_class($e));}
    }
}

function fw_czat_zakoncz(): never {
    $body=json_encode(['ok'=>true]);header('Content-Type: application/json; charset=utf-8');header('Cache-Control: no-store');header('Content-Length: '.strlen($body));echo $body;
    if(function_exists('fastcgi_finish_request')){fastcgi_finish_request();try{fw_czat_push();}catch(Throwable $e){error_log('FW push deferred error');}}
    exit;
}
