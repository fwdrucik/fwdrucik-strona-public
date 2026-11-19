<?php
declare(strict_types=1);
require_once __DIR__.'/_czat.php';
try {
 $action=$_GET['akcja']??'';$input=[];$pdo=fw_baza();
 if(fw_metoda()==='POST'){
   if((int)($_SERVER['CONTENT_LENGTH']??0)>12000)fw_blad(413,'Za duża wiadomość.');
   $raw=file_get_contents('php://input',false,null,0,12001);if($raw===false||strlen($raw)>12000)fw_blad(413,'Za duża wiadomość.');
   $input=json_decode($raw,true);if(!is_array($input))fw_blad(422,'Niepoprawne dane.');
 }
 if($action==='migracja'){fw_wymagaj_post();fw_wymagaj_admina_lub_tokenu();fw_czat_migracja();fw_odpowiedz(['ok'=>true]);}
 if($action==='kolejka'){fw_wymagaj_post();fw_wymagaj_admina_lub_tokenu();fw_czat_retencja();fw_czat_push();fw_odpowiedz(['ok'=>true]);}
 if($action==='start'){
   fw_wymagaj_post();fw_sprawdz_csrf();fw_limit('czat_start',15,3600);fw_czat_retencja();
   $cookie=(string)($_COOKIE['fw_czat']??'');
   $r=preg_match('/^[a-f0-9]{64}$/',$cookie)?fw_czat_sql('SELECT id,tryb FROM '.fw_tabela('czat_rozmowy').' WHERE token_hash=?',[hash('sha256',$cookie)])->fetch():false;
   if(!$r){$cookie=bin2hex(random_bytes(32));fw_czat_sql('INSERT INTO '.fw_tabela('czat_rozmowy').' (token_hash,utworzona,zmieniona) VALUES (?,NOW(),NOW())',[hash('sha256',$cookie)]);$r=['id'=>(int)$pdo->lastInsertId(),'tryb'=>'bot'];}
   fw_ustaw_cookie('fw_czat',$cookie,time()+86400*30,true);fw_odpowiedz(['ok'=>true,'rozmowa'=>$r,'wiadomosci'=>fw_czat_lista_wiadomosci((int)$r['id'])]);
 }
 if($action==='odczyt'){
   $r=fw_czat_rozmowa();fw_odpowiedz(['ok'=>true,'rozmowa'=>['id'=>$r['id'],'tryb'=>$r['tryb']],'wiadomosci'=>fw_czat_lista_wiadomosci((int)$r['id'],max(0,(int)($_GET['po']??0)))]);
 }
 if($action==='wyslij'||$action==='czlowiek'){
   fw_wymagaj_post();fw_sprawdz_csrf();fw_limit('czat_wyslij',30,3600);
   $text=$action==='czlowiek'?'Proszę o rozmowę z człowiekiem.':($input['tresc']??'');
   if(!is_string($text)||trim($text)===''||mb_strlen($text)>1500)fw_blad(422,'Wpisz od 1 do 1500 znaków.');
   $request=$input['request_id']??'';if(!is_string($request)||!preg_match('/^[a-f0-9-]{36}$/',$request))fw_blad(422,'Brak identyfikatora wiadomości.');
   $pdo->beginTransaction();$r=fw_czat_rozmowa(true);$id=(int)$r['id'];
   $existing=fw_czat_sql('SELECT id FROM '.fw_tabela('czat_wiadomosci').' WHERE rozmowa_id=? AND request_id=?',[$id,$request])->fetchColumn();
   if($existing){$pdo->commit();fw_odpowiedz(['ok'=>true,'powtorzenie'=>true]);}
   if($r['tryb']==='zamkniety'){$pdo->rollBack();fw_blad(409,'Rozmowa została zamknięta. Skontaktuj się telefonicznie.');}
   if($r['pending']&&strtotime($r['pending_od'])>time()-60&&$action!=='czlowiek'){$pdo->rollBack();fw_blad(409,'Poczekaj na odpowiedź na poprzednią wiadomość.');}
   $count=(int)fw_czat_sql('SELECT COUNT(*) FROM '.fw_tabela('czat_wiadomosci').' WHERE rozmowa_id=?',[$id])->fetchColumn();
   if($count>=190){$pdo->rollBack();fw_blad(429,'Ta rozmowa osiągnęła limit. Skontaktuj się telefonicznie.');}
   $mid=fw_czat_dodaj($id,'klient',trim($text),$request);
   if($action==='czlowiek'&&$r['tryb']==='bot'){$r['tryb']='oczekuje';$r['wersja']=(int)$r['wersja']+1;}
   $ai=$r['tryb']==='bot';
   fw_czat_sql('UPDATE '.fw_tabela('czat_rozmowy').' SET tryb=?,wersja=?,pending=?,pending_od=NOW(),zmieniona=NOW() WHERE id=?',[$r['tryb'],$r['wersja'],$ai?$request:null,$id]);
   fw_czat_sql('INSERT INTO '.fw_tabela('czat_push').' (rozmowa_id,wiadomosc_id,nastepna,kiedy) VALUES (?,?,NOW(),NOW())',[$id,$mid]);$pdo->commit();
   if($ai){
     $history=fw_czat_sql('SELECT rola,tresc FROM '.fw_tabela('czat_wiadomosci').' WHERE rozmowa_id=? AND id<? AND rola IN ("klient","bot") ORDER BY id DESC LIMIT 6',[$id,$mid])->fetchAll();
     $history=array_map(static fn($m)=>['role'=>$m['rola']==='klient'?'user':'assistant','content'=>mb_substr($m['tresc'],0,1500)],array_reverse($history));
     try{$answer=fw_ai_generuj(['pytanie'=>trim($text),'historia'=>$history]);$role='bot';}
     catch(Throwable $e){$answer='Asystent chwilowo nie odpowiada. Możesz poprosić o człowieka lub zadzwonić: 601 726 924.';$role='system';error_log('FW chat AI '.get_class($e));}
     $pdo->beginTransaction();$current=fw_czat_sql('SELECT * FROM '.fw_tabela('czat_rozmowy').' WHERE id=? FOR UPDATE',[$id])->fetch();
     if($current&&$current['tryb']==='bot'&&(int)$current['wersja']===(int)$r['wersja']&&$current['pending']===$request){fw_czat_dodaj($id,$role,$answer);fw_czat_sql('UPDATE '.fw_tabela('czat_rozmowy').' SET pending=NULL,zmieniona=NOW() WHERE id=?',[$id]);}
     $pdo->commit();
   }
   fw_czat_zakoncz();
 }
 $u=fw_wymagaj_admina();
 if($action==='lista'){
   fw_czat_retencja();$page=max(1,min(10000,(int)($_GET['strona']??1)));$offset=($page-1)*30;
   $rows=fw_czat_sql('SELECT id,tryb,admin_id,utworzona,zmieniona,(SELECT COUNT(*) FROM '.fw_tabela('czat_wiadomosci').' m WHERE m.rozmowa_id=r.id) AS liczba FROM '.fw_tabela('czat_rozmowy').' r ORDER BY zmieniona DESC LIMIT 30 OFFSET '.$offset)->fetchAll();
   $pending=(int)fw_czat_sql('SELECT COUNT(*) FROM '.fw_tabela('czat_push').' WHERE status<>"wyslano"')->fetchColumn();
   fw_odpowiedz(['ok'=>true,'rozmowy'=>$rows,'push_oczekuje'=>$pending,'urzadzenia'=>(int)fw_czat_sql('SELECT COUNT(*) FROM '.fw_tabela('czat_urzadzenia').' WHERE admin_id=?',[$u['id']])->fetchColumn()]);
 }
 $id=max(0,(int)($input['id']??$_GET['id']??0));
 if($action==='rozmowa'){$r=fw_czat_sql('SELECT id,tryb,admin_id FROM '.fw_tabela('czat_rozmowy').' WHERE id=?',[$id])->fetch();if(!$r)fw_blad(404,'Brak rozmowy.');fw_odpowiedz(['ok'=>true,'rozmowa'=>$r,'wiadomosci'=>fw_czat_lista_wiadomosci($id,max(0,(int)($_GET['po']??0)))]);}
 fw_wymagaj_post();fw_sprawdz_csrf();
 if($action==='urzadzenie'){
   $token=$input['token']??'';if(!is_string($token)||strlen($token)<20||strlen($token)>4096||preg_match('/[\x00-\x20\x7f]/',$token))fw_blad(422,'Niepoprawny token urządzenia.');
   fw_czat_sql('INSERT INTO '.fw_tabela('czat_urzadzenia').' (token_hash,token,admin_id,zmieniony) VALUES (?,?,?,NOW()) ON DUPLICATE KEY UPDATE admin_id=VALUES(admin_id),zmieniony=NOW()',[hash('sha256',$token),$token,$u['id']]);fw_odpowiedz(['ok'=>true]);
 }
 if($action==='wylacz-push'){fw_czat_sql('DELETE FROM '.fw_tabela('czat_urzadzenia').' WHERE admin_id=?',[$u['id']]);fw_odpowiedz(['ok'=>true]);}
 if(!in_array($action,['przejmij','bot','zamknij','usun','odpowiedz'],true))fw_blad(404,'Nieznana operacja.');
 $answer=$input['tresc']??'';if($action==='odpowiedz'&&(!is_string($answer)||trim($answer)===''||mb_strlen($answer)>4000))fw_blad(422,'Odpowiedź musi mieć od 1 do 4000 znaków.');
 $request=$input['request_id']??null;if($action==='odpowiedz'&&(!is_string($request)||!preg_match('/^[a-f0-9-]{36}$/',$request)))fw_blad(422,'Brak identyfikatora odpowiedzi.');
 $pdo->beginTransaction();$r=fw_czat_sql('SELECT * FROM '.fw_tabela('czat_rozmowy').' WHERE id=? FOR UPDATE',[$id])->fetch();if(!$r){$pdo->rollBack();fw_blad(404,'Brak rozmowy.');}
 if($action==='usun'){foreach(['czat_wiadomosci','czat_push'] as $t)fw_czat_sql('DELETE FROM '.fw_tabela($t).' WHERE rozmowa_id=?',[$id]);fw_czat_sql('DELETE FROM '.fw_tabela('czat_rozmowy').' WHERE id=?',[$id]);}
 else {
   if($action==='odpowiedz'&&fw_czat_sql('SELECT id FROM '.fw_tabela('czat_wiadomosci').' WHERE rozmowa_id=? AND request_id=?',[$id,$request])->fetchColumn()){$pdo->commit();fw_odpowiedz(['ok'=>true,'powtorzenie'=>true]);}
   if($action==='odpowiedz'&&($r['tryb']!=='czlowiek'||(int)$r['admin_id']!==$u['id'])){$pdo->rollBack();fw_blad(409,'Najpierw przejmij rozmowę.');}
   if($action==='odpowiedz')fw_czat_dodaj($id,'firma',trim($answer),$request);
   else{
     $mode=['przejmij'=>'czlowiek','bot'=>'bot','zamknij'=>'zamkniety'][$action];
     fw_czat_sql('UPDATE '.fw_tabela('czat_rozmowy').' SET tryb=?,wersja=wersja+1,pending=NULL,admin_id=? WHERE id=?',[$mode,$mode==='czlowiek'?$u['id']:null,$id]);
     fw_czat_dodaj($id,'system',['przejmij'=>'Rozmowę przejął pracownik F.W. DRUCIK. Odpowiedzi AI są wstrzymane.','bot'=>'Rozmowę ponownie obsługuje asystent AI.','zamknij'=>'Rozmowa została zamknięta. Dziękujemy za kontakt.'][$action]);
   }
   fw_czat_sql('UPDATE '.fw_tabela('czat_rozmowy').' SET zmieniona=NOW() WHERE id=?',[$id]);
 }
 fw_czat_sql('INSERT INTO '.fw_tabela('moderacja_historia').' (admin_id,typ,tresc_id,decyzja,kiedy) VALUES (?,"czat",?,?,NOW())',[$u['id'],$id,$action]);$pdo->commit();fw_odpowiedz(['ok'=>true]);
} catch(Throwable $e){if(isset($pdo)&&$pdo->inTransaction())$pdo->rollBack();error_log('FW chat '.get_class($e));fw_blad(503,'Czat chwilowo niedostępny. Kontakt: 601 726 924.');}
