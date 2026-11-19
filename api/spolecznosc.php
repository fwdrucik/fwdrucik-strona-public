<?php
declare(strict_types=1);
require_once __DIR__ . '/_spolecznosc.php';
try {
    $akcja = fw_akcja();
    if ($akcja === 'migracja') {
        fw_wymagaj_post(); fw_wymagaj_admina_lub_tokenu();
        fw_spolecznosc_migracja(); fw_odpowiedz(['ok'=>true]);
    }
    fw_spolecznosc_wymagaj(); $pdo = fw_baza();
    if ($akcja === 'lista') {
        $przedmiot = fw_opinia_przedmiot((string)($_GET['przedmiot'] ?? 'sklep'));
        $page = max(1,min(10000,(int)($_GET['page'] ?? 1))); $offset = ($page-1)*10;
        $st = $pdo->prepare('SELECT COUNT(*) liczba, ROUND(AVG(o.ocena),2) srednia FROM ' . fw_tabela('opinie') . ' o JOIN ' . fw_tabela('uzytkownicy') . ' u ON u.id=o.autor_id WHERE o.przedmiot=? AND o.status="opublikowany" AND u.zablokowany=0');
        $st->execute([$przedmiot]); $stats = $st->fetch();
        $st = $pdo->prepare('SELECT o.id,o.ocena,o.tresc,o.zmieniony data,u.nick autor,o.autor_id, f.tresc odpowiedz,f.zmieniony odpowiedz_data FROM ' . fw_tabela('opinie') . ' o JOIN ' . fw_tabela('uzytkownicy') . ' u ON u.id=o.autor_id LEFT JOIN ' . fw_tabela('odpowiedzi_firmy') . ' f ON f.typ="opinia" AND f.tresc_id=o.id WHERE o.przedmiot=? AND o.status="opublikowany" AND u.zablokowany=0 ORDER BY o.zmieniony DESC,o.id DESC LIMIT 10 OFFSET ' . $offset);
        $st->execute([$przedmiot]); $rows = $st->fetchAll();
        foreach ($rows as &$r) {
            $r['ocena']=(int)$r['ocena']; $r['id']=(int)$r['id'];
            $r['potwierdzony_zakup']=$przedmiot==='sklep' && fw_zakupy_liczba((int)$r['autor_id'])>0;
            $r['poziom']=fw_profil_aktywnosci((int)$r['autor_id'])['poziom']; unset($r['autor_id']);
        } unset($r);
        fw_odpowiedz(['ok'=>true,'opinie'=>$rows,'liczba'=>(int)$stats['liczba'],'srednia'=>$stats['srednia']===null?null:(float)$stats['srednia'],'page'=>$page]);
    }
    if ($akcja === 'odpowiedzi-komentarzy') {
        $slug = fw_slug((string)($_GET['slug'] ?? ''));
        $st=$pdo->prepare('SELECT f.tresc_id id,f.tresc,f.zmieniony FROM ' . fw_tabela('odpowiedzi_firmy') . ' f JOIN ' . fw_tabela('komentarze') . ' k ON k.id=f.tresc_id WHERE f.typ="komentarz" AND k.slug=? AND k.status="opublikowany" LIMIT 300');
        $st->execute([$slug]); fw_odpowiedz(['ok'=>true,'odpowiedzi'=>$st->fetchAll()]);
    }
    if ($akcja === 'poziomy') {
        // Public endpoint returns only public nick and rank, never purchase counters.
        $ids=array_slice(array_unique(array_filter(array_map('intval',explode(',',(string)($_GET['ids']??''))),static fn($x)=>$x>0)),0,30);
        $rows=[];
        foreach ($ids as $id) {
            $st=$pdo->prepare('SELECT nick FROM ' . fw_tabela('uzytkownicy') . ' WHERE id=? AND zablokowany=0'); $st->execute([$id]); $nick=$st->fetchColumn();
            if ($nick!==false) $rows[]=['id'=>$id,'nick'=>$nick,'poziom'=>fw_profil_aktywnosci($id)['poziom']];
        }
        fw_odpowiedz(['ok'=>true,'poziomy'=>$rows]);
    }
    $u=fw_wymagaj_logowania();
    if ($akcja === 'moja') {
        $st=$pdo->prepare('SELECT id,przedmiot,ocena,tresc,status FROM ' . fw_tabela('opinie') . ' WHERE autor_id=?'); $st->execute([$u['id']]);
        fw_odpowiedz(['ok'=>true,'opinie'=>$st->fetchAll()]);
    }
    if ($akcja === 'profil') {
        $st=$pdo->prepare('SELECT kod FROM ' . fw_tabela('polecenia_kody') . ' WHERE uzytkownik_id=?'); $st->execute([$u['id']]); $kod=$st->fetchColumn();
        fw_odpowiedz(['ok'=>true,'profil'=>fw_profil_aktywnosci($u['id']),'kod'=>$kod?:null]);
    }
    if ($akcja === 'admin') {
        fw_wymagaj_admina();
        $typ=(string)($_GET['typ']??'opinia'); if (!in_array($typ,['opinia','komentarz'],true)) fw_blad(422,'Nieznany typ.');
        $table=fw_tabela($typ==='opinia'?'opinie':'komentarze');
        $status=(string)($_GET['status']??''); if (!in_array($status,['','oczekuje','opublikowany','odrzucony'],true)) fw_blad(422,'Nieznany status.');
        $przedmiot=(string)($_GET['przedmiot']??''); if ($przedmiot!=='') fw_opinia_przedmiot($przedmiot);
        $page=max(1,min(10000,(int)($_GET['page']??1))); $offset=($page-1)*20;
        $where=' WHERE 1=1'; $args=[$typ];
        if ($status!=='') {$where.=' AND o.status=?';$args[]=$status;}
        if ($typ==='opinia' && $przedmiot!=='') {$where.=' AND o.przedmiot=?';$args[]=$przedmiot;}
        $fields=$typ==='opinia'?'o.przedmiot,o.ocena':'o.slug';
        $sql='SELECT o.id,o.tresc,o.status,o.utworzony data,u.nick autor,f.tresc odpowiedz,' . $fields . ' FROM ' . $table . ' o JOIN ' . fw_tabela('uzytkownicy') . ' u ON u.id=o.autor_id LEFT JOIN ' . fw_tabela('odpowiedzi_firmy') . ' f ON f.typ=? AND f.tresc_id=o.id' . $where . ' ORDER BY o.utworzony DESC,o.id DESC LIMIT 21 OFFSET ' . $offset;
        $st=$pdo->prepare($sql);$st->execute($args);$rows=$st->fetchAll();$more=count($rows)>20;
        fw_odpowiedz(['ok'=>true,'pozycje'=>array_slice($rows,0,20),'wiecej'=>$more,'page'=>$page]);
    }
    fw_wymagaj_post(); fw_sprawdz_csrf();
    if ($akcja === 'zapisz') {
        fw_limit('opinia',10,3600);
        $przedmiot=fw_opinia_przedmiot(fw_pole('przedmiot')); $rating=fw_pole('ocena');
        if (!preg_match('/^[1-5]$/',$rating)) fw_blad(422,'Ocena musi być liczbą od 1 do 5.');
        $tresc=fw_tekst(fw_pole('tresc'),'Opinia',5,3000);
        $pdo->beginTransaction();
        $st=$pdo->prepare('INSERT INTO ' . fw_tabela('opinie') . ' (autor_id,przedmiot,ocena,tresc,status,utworzony,zmieniony) VALUES (?,?,?,?,"oczekuje",?,?) ON DUPLICATE KEY UPDATE ocena=VALUES(ocena),tresc=VALUES(tresc),status="oczekuje",zmieniony=VALUES(zmieniony)');
        $st->execute([$u['id'],$przedmiot,(int)$rating,$tresc,fw_teraz(),fw_teraz()]);
        // An old company reply must not become attached to a rewritten opinion.
        $pdo->prepare('DELETE f FROM ' . fw_tabela('odpowiedzi_firmy') . ' f JOIN ' . fw_tabela('opinie') . ' o ON f.typ="opinia" AND f.tresc_id=o.id WHERE o.autor_id=? AND o.przedmiot=?')->execute([$u['id'],$przedmiot]);
        $pdo->commit(); fw_odpowiedz(['ok'=>true,'komunikat'=>'Dziękujemy. Opinia czeka na sprawdzenie.']);
    }
    if ($akcja === 'kod') {
        $pdo->prepare('INSERT IGNORE INTO ' . fw_tabela('polecenia_kody') . ' (uzytkownik_id,kod) VALUES (?,?)')->execute([$u['id'],bin2hex(random_bytes(12))]);
        $st=$pdo->prepare('SELECT kod FROM ' . fw_tabela('polecenia_kody') . ' WHERE uzytkownik_id=?');$st->execute([$u['id']]);
        fw_odpowiedz(['ok'=>true,'kod'=>$st->fetchColumn()]);
    }
    if ($akcja === 'udostepnij') {
        fw_limit('udostepnienie',10,3600);
        $pdo->prepare('INSERT IGNORE INTO ' . fw_tabela('udostepnienia') . ' (uzytkownik_id,dzien) VALUES (?,CURRENT_DATE)')->execute([$u['id']]);
        fw_odpowiedz(['ok'=>true]);
    }
    if ($akcja === 'polecenie') {
        fw_limit('polecenie',10,3600); $kod=fw_pole('kod');
        if (!preg_match('/^[a-f0-9]{24}$/',$kod)) fw_blad(422,'Niepoprawny kod polecenia.');
        $pdo->beginTransaction();
        $st=$pdo->prepare('SELECT utworzony FROM ' . fw_tabela('uzytkownicy') . ' WHERE id=? FOR UPDATE');$st->execute([$u['id']]);$created=$st->fetchColumn();
        if (strtotime((string)$created)<time()-3600) { $pdo->rollBack(); fw_blad(422,'Polecenie przypisujemy przy zakładaniu nowego konta.'); }
        $st=$pdo->prepare('SELECT k.uzytkownik_id FROM ' . fw_tabela('polecenia_kody') . ' k JOIN ' . fw_tabela('uzytkownicy') . ' u ON u.id=k.uzytkownik_id WHERE k.kod=? AND u.zablokowany=0');$st->execute([$kod]);$ref=(int)$st->fetchColumn();
        if (!$ref || $ref===$u['id']) {$pdo->rollBack();fw_blad(422,'Nie można przypisać tego polecenia.');}
        if (fw_spolecznosc_skalar('SELECT COUNT(*) FROM ' . fw_tabela('zamowienia') . ' WHERE uzytkownik_id=?',[$u['id']])>0) {$pdo->rollBack();fw_blad(422,'Polecenie przypisujemy przed pierwszym zamówieniem.');}
        $pdo->prepare('INSERT IGNORE INTO ' . fw_tabela('polecenia') . ' (polecony_id,polecajacy_id,kiedy) VALUES (?,?,?)')->execute([$u['id'],$ref,fw_teraz()]);
        $pdo->commit();fw_odpowiedz(['ok'=>true]);
    }
    if (in_array($akcja,['moderuj','odpowiedz'],true)) {
        $admin=fw_wymagaj_admina(); $id=fw_id('id'); $typ=fw_pole('typ','opinia');
        if (!in_array($typ,['opinia','komentarz'],true)) fw_blad(422,'Nieznany typ.');
        $table=fw_tabela($typ==='opinia'?'opinie':'komentarze');
        $pdo->beginTransaction();$st=$pdo->prepare('SELECT id FROM ' . $table . ' WHERE id=? FOR UPDATE');$st->execute([$id]);
        if (!$st->fetchColumn()) {$pdo->rollBack();fw_blad(404,'Treść już nie istnieje.');}
        if ($akcja==='odpowiedz') {
            $text=fw_pole('tresc');
            if ($text==='') {$pdo->prepare('DELETE FROM ' . fw_tabela('odpowiedzi_firmy') . ' WHERE typ=? AND tresc_id=?')->execute([$typ,$id]);}
            else {
                $text=fw_tekst($text,'Odpowiedź',2,3000);
                $pdo->prepare('INSERT INTO ' . fw_tabela('odpowiedzi_firmy') . ' (typ,tresc_id,tresc,admin_id,zmieniony) VALUES (?,?,?,?,?) ON DUPLICATE KEY UPDATE tresc=VALUES(tresc),admin_id=VALUES(admin_id),zmieniony=VALUES(zmieniony)')->execute([$typ,$id,$text,$admin['id'],fw_teraz()]);
            }
            fw_spolecznosc_audyt($admin['id'],$typ,$id,$text===''?'usun_odpowiedz':'odpowiedz');
        } else {
            $decision=fw_pole('decyzja');
            if (!in_array($decision,['opublikowany','odrzucony','usun'],true)) {$pdo->rollBack();fw_blad(422,'Nieznana decyzja.');}
            if ($decision==='usun') {
                $pdo->prepare('DELETE FROM ' . fw_tabela('odpowiedzi_firmy') . ' WHERE typ=? AND tresc_id=?')->execute([$typ,$id]);
                $pdo->prepare('DELETE FROM ' . $table . ' WHERE id=?')->execute([$id]);
            } else $pdo->prepare('UPDATE ' . $table . ' SET status=? WHERE id=?')->execute([$decision,$id]);
            fw_spolecznosc_audyt($admin['id'],$typ,$id,$decision);
        }
        $pdo->commit();fw_odpowiedz(['ok'=>true,'komunikat'=>'Zapisano.']);
    }
    fw_blad(404,'Nieznana akcja.');
} catch (Throwable $e) {
    if (isset($pdo) && $pdo->inTransaction()) $pdo->rollBack();
    error_log('FW spolecznosc: ' . $e->getMessage()); fw_blad(503,'Sekcja jest chwilowo niedostępna. Spróbuj później.');
}