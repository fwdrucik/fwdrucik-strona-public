"""Isolated integration test on the existing MySQL host. Creates and removes only unique test tables/files."""
import sys,io,json,secrets,concurrent.futures
from pathlib import Path
import requests
if '--wykonaj-test' not in sys.argv:
 raise SystemExit('Creates isolated tables and temporary files on configured host. Pass --wykonaj-test to execute.')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import wyslij
ROOT=Path(__file__).resolve().parents[1];suffix=secrets.token_hex(4);prefix='t'+suffix+'_';dirname='fw-test-'+suffix
remote=wyslij.ZDALNY_ROOT+'/api/'+dirname;base='https://fwdrucik.pl/api/'+dirname
key=secrets.token_hex(32);files={};outputs=[]
for name in ['_lib.php','_spolecznosc.php','spolecznosc.php','_asystent.php','asystent.php','komentarze.php']:
 s=(ROOT/'api'/name).read_text(encoding='utf-8')
 if name=='_lib.php':s=s.replace('declare(strict_types=1);','declare(strict_types=1);\nif (!hash_equals('+repr(key)+', (string)($_SERVER["HTTP_X_TEST_TOKEN"]??""))) {http_response_code(404);exit;}')
 files[name]=s.encode()
files['konfiguracja.php']=("<?php return array_replace(require __DIR__.'/../../../fw-konfiguracja.php', ['prefiks'=>'"+prefix+"','sherlock_api_key'=>'','asystent_budzet_microeur'=>1000]);").encode()
files['.htaccess']=(ROOT/'api/.htaccess').read_bytes()
files['fixture.php']=r'''<?php
declare(strict_types=1);
require_once __DIR__.'/_asystent.php';
$pdo=fw_baza();$action=$_GET['action']??'setup';
$tables=['opinie','odpowiedzi_firmy','moderacja_historia','polecenia_kody','polecenia','udostepnienia','ai_budzet','uzytkownicy','sesje','limity','watki','odpowiedzi','zamowienia','komentarze'];
if ($action==='cleanup') {foreach($tables as $t)$pdo->exec('DROP TABLE IF EXISTS '.fw_tabela($t));fw_odpowiedz(['ok'=>true]);}
if ($action==='setup') {
 $schema=[
 'uzytkownicy'=>'id INT UNSIGNED PRIMARY KEY, nick VARCHAR(40),email VARCHAR(190),rola VARCHAR(10), zaufany INT DEFAULT 0,zablokowany INT DEFAULT 0,utworzony DATETIME',
 'sesje'=>'token_hash CHAR(64) PRIMARY KEY,uzytkownik_id INT,utworzona DATETIME,wygasa DATETIME,ip VARCHAR(45),przegladarka VARCHAR(255)',
 'limity'=>'ip VARCHAR(45),akcja VARCHAR(40),kiedy DATETIME',
 'watki'=>'id INT AUTO_INCREMENT PRIMARY KEY,autor_id INT,status VARCHAR(16),utworzony DATETIME',
 'odpowiedzi'=>'id INT AUTO_INCREMENT PRIMARY KEY,autor_id INT,watek_id INT,status VARCHAR(16),utworzona DATETIME',
 'zamowienia'=>'id INT AUTO_INCREMENT PRIMARY KEY,uzytkownik_id INT,status VARCHAR(16)',
 'komentarze'=>'id INT AUTO_INCREMENT PRIMARY KEY,autor_id INT,slug VARCHAR(190),tresc TEXT,status VARCHAR(16),utworzony DATETIME'];
 foreach($schema as $t=>$s)$pdo->exec('CREATE TABLE '.fw_tabela($t).' ('.$s.') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
 $pdo->exec('INSERT INTO '.fw_tabela('uzytkownicy').' (id,nick,email,rola,utworzony) VALUES (1,"Administrator","test1@example.invalid","admin",NOW()),(2,"Klient","test2@example.invalid","user",NOW()),(3,"Polecony","test3@example.invalid","user",NOW())');
 fw_spolecznosc_migracja();fw_odpowiedz(['ok'=>true]);
}
if ($action==='login') {fw_zaloz_sesje((int)$_GET['id']);fw_odpowiedz(['ok'=>true,'csrf'=>fw_token_csrf()]);}
if ($action==='seed') {
 $pdo->exec('INSERT INTO '.fw_tabela('watki').' (autor_id,status,utworzony) VALUES (2,"opublikowany",NOW()),(2,"opublikowany",NOW()),(2,"opublikowany",NOW()),(2,"opublikowany",NOW()),(2,"opublikowany",NOW())');
 $pdo->exec('INSERT INTO '.fw_tabela('zamowienia').' (uzytkownik_id,status) VALUES (2,"zakonczone"),(3,"zakonczone")');
 $pdo->exec('INSERT INTO '.fw_tabela('komentarze').' (autor_id,slug,tresc,status,utworzony) VALUES (2,"testowy-wpis","Komentarz testowy","opublikowany",NOW())');
 fw_odpowiedz(['ok'=>true]);
}
if ($action==='reverse') {$pdo->exec('UPDATE '.fw_tabela('watki').' SET status="odrzucony"');$pdo->exec('UPDATE '.fw_tabela('zamowienia').' SET status="anulowane"');fw_odpowiedz(['ok'=>true]);}
if ($action==='reserve') fw_odpowiedz(['ok'=>fw_ai_rezerwuj(300)]);
''' .encode()
ftp=wyslij.polacz();wyslij.utworz_katalog(ftp,remote)
try:
 for name,data in files.items():ftp.storbinary('STOR '+remote+'/'+name,io.BytesIO(data))
 ftp.quit()
 def sess():
  s=requests.Session();s.headers['X-Test-Token']=key;return s
 guest=sess();admin=sess();user=sess();ref=sess()
 def call(s,action,data=None,expect=200,script='spolecznosc.php'):
  url=base+'/'+script+'?'+('action=' if script=='fixture.php' else 'akcja=')+action
  r=s.post(url,json=data,timeout=40) if data is not None else s.get(url,timeout=40)
  assert r.status_code==expect,(action,r.status_code,r.text[:350])
  result=r.json();return result
 def test(name,condition):assert condition,name;outputs.append(name);print('PASS',name)
 call(guest,'setup',script='fixture.php')
 for s,uid in [(admin,1),(user,2),(ref,3)]:
  x=call(s,'login&id='+str(uid),script='fixture.php');s.headers['X-FW-CSRF']=x['csrf']
 test('empty average is null',call(guest,'lista')['srednia'] is None)
 call(guest,'zapisz',{'przedmiot':'sklep','ocena':5,'tresc':'test text'},401);test('anonymous review denied',True)
 call(user,'admin',expect=403);test('user cannot moderate',True)
 old=user.headers.pop('X-FW-CSRF');call(user,'zapisz',{'przedmiot':'sklep','ocena':5,'tresc':'test text'},403);user.headers['X-FW-CSRF']=old;test('CSRF required',True)
 for rating in [0,6,'1.5','<script>']:
  call(user,'zapisz',{'przedmiot':'sklep','ocena':rating,'tresc':'test text'},422)
 test('rating validation',True)
 call(user,'zapisz',{'przedmiot':'sklep','ocena':4,'tresc':'Dobry kontakt <img src=x onerror=alert(1)>'})
 mine=call(user,'moja')['opinie'];oid=mine[0]['id'];test('pending hidden',call(guest,'lista')['liczba']==0)
 call(admin,'moderuj',{'typ':'opinia','id':oid,'decyzja':'opublikowany'})
 test('published average',call(guest,'lista')['srednia']==4)
 call(admin,'odpowiedz',{'typ':'opinia','id':oid,'tresc':'Dziękujemy za opinię.'});test('company reply visible',bool(call(guest,'lista')['opinie'][0]['odpowiedz']))
 call(user,'zapisz',{'przedmiot':'sklep','ocena':2,'tresc':'Poprawiona opinia'});test('unique opinion updated',len(call(user,'moja')['opinie'])==1);test('edited review pending',call(guest,'lista')['liczba']==0)
 call(admin,'moderuj',{'typ':'opinia','id':oid,'decyzja':'opublikowany'});test('reply cleared on rewrite',call(guest,'lista')['opinie'][0]['odpowiedz'] is None)
 code=call(user,'kod',{})['kod'];call(ref,'polecenie',{'kod':code});call(ref,'polecenie',{'kod':code});call(user,'polecenie',{'kod':code},422);test('unique referral and no self referral',True)
 call(guest,'seed',script='fixture.php')
 p=call(user,'profil')['profil'];test('daily forum cap and completed orders',p['poziom']['punkty']==43 and p['polecenia']==1 and p['zakupy']==1)
 test('verified purchase badge',call(guest,'lista')['opinie'][0]['potwierdzony_zakup'])
 public=call(guest,'poziomy&ids=2')['poziomy'][0];test('public rank excludes purchase stats','zakupy' not in public)
 call(admin,'odpowiedz',{'typ':'komentarz','id':1,'tresc':'Odpowiedź na komentarz'});comments=call(guest,'lista&slug=testowy-wpis',script='komentarze.php');test('blog company reply',comments['komentarze'][0]['odpowiedz']=='Odpowiedź na komentarz')
 call(guest,'reverse',script='fixture.php');test('reversals remove points',call(user,'profil')['profil']['poziom']['punkty']==0)
 call(user,'udostepnij',{});call(user,'udostepnij',{});p=call(user,'profil')['profil'];test('share attempts capped without points',p['udostepnienia']==1 and p['poziom']['punkty']==0)
 call(admin,'moderuj',{'typ':'opinia','id':oid,'decyzja':'usun'});test('delete removes from average',call(guest,'lista')['liczba']==0)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  values=list(pool.map(lambda _:call(sess(),'reserve',script='fixture.php')['ok'],range(6)))
 test('atomic budget never overspends',sum(values)==3)
 test('missing AI key reports unavailable',not call(guest,'status',script='asystent.php')['dostepny'])
 call(user,'',{'pytanie':'Cześć'},503,script='asystent.php');test('no fabricated fallback',True)
 (ROOT/'docs'/'testy-spolecznosc-2026-09-20.json').write_text(json.dumps({'passed':outputs,'isolated_prefix':prefix,'database':'MySQL hosting, isolated tables','cleanup':'pending'},ensure_ascii=False,indent=2),encoding='utf-8')
finally:
 try:
  s=requests.Session();s.headers['X-Test-Token']=key;r=s.get(base+'/fixture.php?action=cleanup',timeout=30);print('Test tables cleanup HTTP',r.status_code)
 except Exception as e:print('CLEANUP ERROR',type(e).__name__)
 ftp=wyslij.polacz()
 for name in files:
  try:ftp.delete(remote+'/'+name)
  except Exception:pass
 try:ftp.rmd(remote)
 except Exception:pass
 ftp.quit()