"""Opt-in isolated hosting tests. No real AI, push, users, or application tables."""
import sys, io, json, secrets, concurrent.futures, uuid, time
from pathlib import Path
import requests
if '--wykonaj-test' not in sys.argv:
    raise SystemExit('Pass --wykonaj-test to create and clean isolated hosting fixtures.')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); import wyslij
suffix=secrets.token_hex(4);prefix='c'+suffix+'_';dirname='fw-chat-test-'+suffix
remote=wyslij.ZDALNY_ROOT+'/api/'+dirname;base='https://fwdrucik.pl/api/'+dirname
key=secrets.token_hex(32);files={};passed=[];failure=None;cleanup={}
for name in ['_lib.php','_spolecznosc.php','_czat.php','czat.php']:
    s=(ROOT/'api'/name).read_text(encoding='utf-8-sig')
    if name=='_lib.php':s=s.replace('declare(strict_types=1);','declare(strict_types=1);\nif (!hash_equals('+repr(key)+', (string)($_SERVER["HTTP_X_TEST_TOKEN"]??""))) {http_response_code(404);exit;}')
    files[name]=s.encode()
files['_asystent.php']=b'''<?php
require_once __DIR__.'/_spolecznosc.php';
function fw_ai_generuj(array $input): string { if($input['pytanie']==='DELAY')sleep(5);return 'TEST AI: '.$input['pytanie']; }
'''
files['konfiguracja.php']=("<?php return array_replace(require __DIR__.'/../../../fw-konfiguracja.php', ['prefiks'=>'"+prefix+"','sherlock_api_key'=>'']);").encode()
files['.htaccess']=(ROOT/'api/.htaccess').read_bytes()
files['fixture.php']=r'''<?php
declare(strict_types=1);
require_once __DIR__.'/_czat.php';
$pdo=fw_baza();$action=$_GET['action']??'';
$tables=['czat_rozmowy','czat_wiadomosci','czat_urzadzenia','czat_push','opinie','odpowiedzi_firmy','moderacja_historia','polecenia_kody','polecenia','udostepnienia','ai_budzet','uzytkownicy','sesje','limity'];
if($action==='cleanup'){foreach($tables as $t)$pdo->exec('DROP TABLE IF EXISTS '.fw_tabela($t));fw_odpowiedz(['ok'=>true]);}
if($action==='setup'){
$schema=[
'uzytkownicy'=>'id INT UNSIGNED PRIMARY KEY,nick VARCHAR(40),email VARCHAR(190),rola VARCHAR(10),zaufany INT DEFAULT 0,zablokowany INT DEFAULT 0,utworzony DATETIME',
'sesje'=>'token_hash CHAR(64) PRIMARY KEY,uzytkownik_id INT,utworzona DATETIME,wygasa DATETIME,ip VARCHAR(45),przegladarka VARCHAR(255)',
'limity'=>'ip VARCHAR(45),akcja VARCHAR(40),kiedy DATETIME'];
foreach($schema as $t=>$s)$pdo->exec('CREATE TABLE '.fw_tabela($t).' ('.$s.') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
$pdo->exec('INSERT INTO '.fw_tabela('uzytkownicy').' (id,nick,email,rola,utworzony) VALUES (1,"Admin","a@example.invalid","admin",NOW()),(2,"User","u@example.invalid","user",NOW()),(3,"Admin2","b@example.invalid","admin",NOW())');
fw_spolecznosc_migracja();fw_czat_migracja();fw_odpowiedz(['ok'=>true]);}
if($action==='login'){fw_zaloz_sesje((int)$_GET['id']);fw_odpowiedz(['ok'=>true,'csrf'=>fw_token_csrf()]);}
if($action==='csrf')fw_odpowiedz(['ok'=>true,'csrf'=>fw_token_csrf()]);
$id=(int)($_GET['id']??0);
if($action==='state')fw_odpowiedz(['ok'=>true,'rozmowa'=>fw_czat_sql('SELECT * FROM '.fw_tabela('czat_rozmowy').' WHERE id=?',[$id])->fetch(),'push'=>(int)fw_czat_sql('SELECT COUNT(*) FROM '.fw_tabela('czat_push').' WHERE rozmowa_id=?',[$id])->fetchColumn()]);
if($action==='seed'){for($i=0;$i<220;$i++)fw_czat_dodaj($id,'firma','history-'.$i);fw_odpowiedz(['ok'=>true]);}
'''.encode()
def session():
    s=requests.Session();s.headers['X-Test-Token']=key;return s
def call(s,action,data=None,expect=200,script='czat.php'):
    url=base+'/'+script+'?'+('action=' if script=='fixture.php' else 'akcja=')+action
    r=s.post(url,json=data,timeout=40) if data is not None else s.get(url,timeout=40)
    assert r.status_code==expect,(action,r.status_code,r.text[:250])
    return r.json()
def test(name,condition=True):
    assert condition,name
    passed.append(name);print('PASS',name,flush=True)
def msg(text='Czesc'):
    return {'tresc':text,'request_id':str(uuid.uuid4())}
guest=session();other=session();admin=session();admin2=session();user=session()
try:
    ftp=wyslij.polacz();wyslij.utworz_katalog(ftp,remote)
    for name,data in files.items():ftp.storbinary('STOR '+remote+'/'+name,io.BytesIO(data))
    ftp.quit()
    call(guest,'setup',script='fixture.php')
    test('private fixture requires unpredictable header',requests.get(base+'/fixture.php?action=state',timeout=20).status_code==404)
    for s,uid in [(admin,1),(admin2,3),(user,2)]:s.headers['X-FW-CSRF']=call(s,'login&id='+str(uid),script='fixture.php')['csrf']
    for s in [guest,other]:s.headers['X-FW-CSRF']=call(s,'csrf',script='fixture.php')['csrf']
    call(guest,'lista',expect=401);call(user,'lista',expect=403);test('admin reads reject guest and regular user')
    token=guest.headers.pop('X-FW-CSRF');call(guest,'start',{},403);guest.headers['X-FW-CSRF']=token;test('guest start requires CSRF')
    rid=int(call(guest,'start',{})['rozmowa']['id']);oid=int(call(other,'start',{})['rozmowa']['id']);test('independent guest conversations',rid!=oid)
    test('start resumes own conversation',int(call(guest,'start',{})['rozmowa']['id'])==rid)
    first=msg();call(guest,'wyslij',first);call(guest,'wyslij',first)
    history=call(guest,'odczyt')['wiadomosci'];test('request retry is idempotent',len(history)==2 and history[0]['rola']=='klient' and history[1]['rola']=='bot')
    test('one notification per actual client message',call(guest,'state&id='+str(rid),script='fixture.php')['push']==1)
    test('guest cannot select another history',len(call(other,'odczyt&id='+str(rid))['wiadomosci'])==0)
    call(user,'przejmij',{'id':rid},403);call(guest,'rozmowa&id='+str(rid),expect=401);test('ownership admin APIs denied to nonadmin')
    call(admin,'przejmij&id='+str(rid),expect=405);test('read-only request cannot mutate')
    token=admin.headers.pop('X-FW-CSRF');call(admin,'przejmij',{'id':rid},403);admin.headers['X-FW-CSRF']=token;test('admin mutation requires CSRF')
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(call,guest,'wyslij',msg('DELAY'))
        for _ in range(40):
            state=call(admin,'state&id='+str(rid),script='fixture.php')['rozmowa']
            if state['pending']:break
            time.sleep(.1)
        assert state['pending'],'AI did not reach delayed section'
        call(admin,'przejmij',{'id':rid});pending.result()
    history=call(guest,'odczyt')['wiadomosci'];test('takeover during AI discards late answer',not any(m['tresc']=='TEST AI: DELAY' for m in history))
    call(guest,'czlowiek',msg());state=call(guest,'odczyt')['rozmowa'];test('human request preserves existing takeover',state['tryb']=='czlowiek')
    call(admin2,'odpowiedz',{'id':rid,'tresc':'wrong owner','request_id':str(uuid.uuid4())},409);test('only current operator can reply')
    reply={'id':rid,'tresc':'Odpowiedz pracownika','request_id':str(uuid.uuid4())};call(admin,'odpowiedz',reply);call(admin,'odpowiedz',reply);test('operator reply retry is idempotent',sum(m['tresc']=='Odpowiedz pracownika' for m in call(guest,'odczyt')['wiadomosci'])==1);test('operator reply visible',call(guest,'odczyt')['wiadomosci'][-1]['rola']=='firma')
    call(admin,'bot',{'id':rid});call(guest,'wyslij',msg('Powrot'));test('return to AI',call(guest,'odczyt')['wiadomosci'][-1]['tresc']=='TEST AI: Powrot')
    fake='test-fcm-token-'+secrets.token_hex(24)
    call(user,'urzadzenie',{'token':fake},403);call(guest,'urzadzenie',{'token':fake},401);test('device registration admin only')
    call(admin,'urzadzenie',{'token':fake});call(admin,'urzadzenie',{'token':fake});test('device registration idempotent',call(admin,'lista')['urzadzenia']==1)
    call(admin,'wylacz-push',{});test('device removal',call(admin,'lista')['urzadzenia']==0)
    call(admin,'seed&id='+str(oid),script='fixture.php');h1=call(other,'odczyt')['wiadomosci'];h2=call(other,'odczyt&po='+str(h1[-1]['id']))['wiadomosci'];test('history cursor retrieves messages beyond 200',len(h1)==200 and len(h2)==20 and h2[0]['id']>h1[-1]['id'])
    ah=call(admin,'rozmowa&id='+str(oid)+'&po='+str(h1[-1]['id']))['wiadomosci'];test('admin cursor beyond 200',len(ah)==20)
    call(admin,'zamknij',{'id':rid});call(guest,'wyslij',msg('Closed'),409);test('closed conversation rejects messages',call(guest,'odczyt')['rozmowa']['tryb']=='zamkniety')
    call(admin,'usun',{'id':rid});call(guest,'odczyt',expect=404);test('deleted conversation inaccessible and queue cleaned',call(admin,'state&id='+str(rid),script='fixture.php')['push']==0)
except Exception as e:
    failure=str(e);print('FAIL',failure,flush=True)
finally:
    try:
        r=call(session(),'cleanup',script='fixture.php');cleanup['tables']=bool(r['ok'])
    except Exception as e:cleanup['tables']=str(e)
    try:
        ftp=wyslij.polacz();errors=[]
        for name in files:
            try:ftp.delete(remote+'/'+name)
            except Exception as e:errors.append(name+':'+type(e).__name__)
        try:ftp.rmd(remote)
        except Exception as e:errors.append('directory:'+type(e).__name__)
        ftp.quit();cleanup['files']=True if not errors else errors
    except Exception as e:cleanup['files']=type(e).__name__
    (ROOT/'docs/test-czat-host.json').write_text(json.dumps({'passed':passed,'failure':failure,'isolated_prefix':prefix,'ai':'deterministic stub; delayed takeover test','push':'omitted _push.php; no deliveries','cleanup':cleanup},ensure_ascii=False,indent=2),encoding='utf-8')
    print('CLEANUP',cleanup,flush=True)
if failure or cleanup.get('tables') is not True or cleanup.get('files') is not True:raise SystemExit(1)
