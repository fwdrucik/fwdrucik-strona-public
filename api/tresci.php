<?php
declare(strict_types=1);
require_once __DIR__.'/_lib.php';
require_once __DIR__.'/_tresci.php';
fw_wymagaj_admina();
function cms_github(string $path,string $method='GET',?array $body=null): array {
    $key=(string)(fw_konfiguracja()['github_token']??'');
    if($key==='')fw_blad(503,'Brak konfiguracji edytora GitHub.');
    $ch=curl_init('https://api.github.com/repos/fwdrucik/fwdrucik-strona/'.$path);
    curl_setopt_array($ch,[CURLOPT_RETURNTRANSFER=>true,CURLOPT_CUSTOMREQUEST=>$method,CURLOPT_CONNECTTIMEOUT=>5,CURLOPT_TIMEOUT=>25,CURLOPT_FOLLOWLOCATION=>false,CURLOPT_HTTPHEADER=>['Accept: application/vnd.github+json','Authorization: Bearer '.$key,'User-Agent: FWDrucik-CMS','Content-Type: application/json','X-GitHub-Api-Version: 2022-11-28']]);
    if($body!==null)curl_setopt($ch,CURLOPT_POSTFIELDS,json_encode($body,JSON_UNESCAPED_UNICODE));
    $raw=curl_exec($ch);$status=(int)curl_getinfo($ch,CURLINFO_RESPONSE_CODE);
    return [$status,is_string($raw)?json_decode($raw,true):null];
}
$action=(string)($_GET['akcja']??'lista');
$manifest=json_decode((string)@file_get_contents(__DIR__.'/_tresci_manifest.json'),true);
if(!is_array($manifest))fw_blad(503,'Lista stron do edycji nie jest jeszcze gotowa.');
$manifest=array_values(array_filter($manifest,fn($p)=>is_string($p)&&preg_match('/^[a-z0-9-]+\.html$/D',$p)&&!in_array($p,['admin.html','konto.html','logowanie.html','rejestracja.html','reset-hasla.html'],true)));
if($action==='lista')fw_odpowiedz(['ok'=>true,'strony'=>$manifest]);
if($action==='publikuj') {
    fw_wymagaj_post();fw_sprawdz_csrf();fw_limit('cms-publikacja',10,3600);
    [$status]=cms_github('actions/workflows/wysylka.yml/dispatches','POST',['ref'=>'main']);
    if($status!==204)fw_blad(502,'Nie udało się uruchomić publikacji. Zapisane treści pozostają w repozytorium.');
    fw_odpowiedz(['ok'=>true,'komunikat'=>'Publikacja została zlecona. Sprawdź wynik w GitHub Actions.','url'=>'https://github.com/fwdrucik/fwdrucik-strona/actions/workflows/wysylka.yml']);
}
$page=(string)($_GET['strona']??'');
if(!in_array($page,$manifest,true))fw_blad(404,'Strona nie jest dostępna w edytorze.');
if(!in_array($action,['czytaj','zapisz'],true))fw_blad(404,'Nieznana operacja.');
if($action==='zapisz'){fw_wymagaj_post();fw_sprawdz_csrf();fw_limit('cms-zapis',30,3600);}
[$status,$file]=cms_github('contents/src/'.rawurlencode($page).'?ref=main');
if($status!==200||!isset($file['content'],$file['sha']))fw_blad(502,'Nie udało się odczytać źródła z GitHub.');
$html=base64_decode($file['content'],true);
if($html===false||strlen($html)>1000000)fw_blad(422,'Nieobsługiwany rozmiar źródła.');
if($action==='czytaj') {
    $blocks=array_map(function($b){unset($b['offset'],$b['length']);return $b;},fw_tresci_bloki($html));
    fw_odpowiedz(['ok'=>true,'sha'=>$file['sha'],'bloki'=>$blocks]);
}
$raw=file_get_contents('php://input',false,null,0,262145);
if($raw===false||strlen($raw)>262144)fw_blad(413,'Za dużo zmian w jednym zapisie.');
$data=json_decode($raw,true);
if(!is_array($data)||!isset($data['sha'],$data['zmiany'])||!is_array($data['zmiany'])||count($data['zmiany'])>500)fw_blad(422,'Niepoprawne dane.');
if(!is_string($data['sha'])||!hash_equals($file['sha'],$data['sha']))fw_blad(409,'Ktoś zmienił tę stronę. Wczytaj aktualną wersję przed zapisem.');
try{$updated=fw_tresci_zmien($html,$data['zmiany']);}catch(InvalidArgumentException $e){fw_blad(422,$e->getMessage());}
if($updated===$html)fw_odpowiedz(['ok'=>true,'komunikat'=>'Brak zmian.','sha'=>$file['sha']]);
[$status,$result]=cms_github('contents/src/'.rawurlencode($page),'PUT',['message'=>'content: edit '.$page.' from admin panel','branch'=>'main','sha'=>$file['sha'],'content'=>base64_encode($updated)]);
if($status===409||$status===422)fw_blad(409,'Konflikt wersji. Wczytaj stronę ponownie; zmiany nie zostały zapisane.');
if($status!==200)fw_blad(502,'GitHub nie potwierdził zapisu. Wczytaj źródło ponownie przed ponowieniem.');
fw_odpowiedz(['ok'=>true,'sha'=>$result['content']['sha']??'','komunikat'=>'Zapisano źródło i historię w GitHub. Kliknij Publikuj, aby zaktualizować stronę.','url'=>'https://github.com/fwdrucik/fwdrucik-strona/commits/main/src/'.rawurlencode($page)]);
