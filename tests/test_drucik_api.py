"""Integracja profilu z izolowaną bazą MySQL w CI."""
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
assert os.environ.get("FW_DRUCIK_TEST_DB") == "1", "Test wymaga jawnego wyboru bazy testowej."

with tempfile.TemporaryDirectory(prefix="fw-drucik-test-") as tmp:
    api = Path(tmp) / "api"
    api.mkdir()
    for name in ("_lib.php", "drucik.php"):
        shutil.copyfile(ROOT / "api" / name, api / name)
    (api / "konfiguracja.php").write_text(
        "<?php return ['db_host'=>'127.0.0.1','db_port'=>3306,'db_nazwa'=>'fw_drucik_test',"
        "'db_uzytkownik'=>'root','db_haslo'=>'drucik-test-local','prefiks'=>'fw_'];",
        encoding="utf-8",
    )
    seed = """require $argv[1]; $p=fw_baza(); $p->exec(file_get_contents($argv[2]));
    foreach ([1,2] as $id) {
      $p->prepare("INSERT INTO fw_uzytkownicy (id,nick,email,haslo_hash,utworzony) VALUES (?,?,?,?,NOW())")
        ->execute([$id,'Test'.$id,'test'.$id.'@example.invalid','fixture']);
      $p->prepare("INSERT INTO fw_sesje (token_hash,uzytkownik_id,utworzona,wygasa,ip,przegladarka) VALUES (?,?,NOW(),NOW()+INTERVAL 1 DAY,'test','test')")
        ->execute([hash('sha256',str_repeat($id===1?'a':'b',64)),$id]);
    }"""
    subprocess.run(["php", "-r", seed, str(api / "_lib.php"), str(ROOT / "api/schemat.sql")], check=True)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    process = subprocess.Popen(["php", "-S", f"127.0.0.1:{port}", "-t", tmp],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=.1):
                    break
            except OSError:
                time.sleep(.1)
        def request(user=0, data=None, csrf=True):
            headers = {"Content-Type": "application/json"}
            if user:
                token = ("a" if user == 1 else "b") * 64
                headers["Cookie"] = "fw_sesja=" + token + "; fw_csrf=" + "c" * 64
            if csrf:
                headers["X-FW-CSRF"] = "c" * 64
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/drucik.php",
                                         data=json.dumps(data).encode() if data is not None else None,
                                         headers=headers)
            try:
                response = urllib.request.urlopen(req, timeout=10)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                return response.status, json.loads(response.read())

        assert request()[0] == 401
        assert request(1) == (200, {"ok": True, "wersja": 0, "profil": None})
        payload = {"wersja": 0, "imie": "Testowy", "energia": 80, "kolor": "plazma",
                   "paliwo": "lpg", "kroki": ["glowa", "spawa"]}
        assert request(1, payload, csrf=False)[0] == 403
        assert request(1, {**payload, "energia": "80"})[0] == 422
        assert request(1, {**payload, "imie": "<script>"})[0] == 422
        assert request(1, {**payload, "kroki": ["nieznane"]})[0] == 422
        assert request(1, {**payload, "kroki": ["spawa"] * 6})[0] == 422
        code, saved = request(1, {**payload, "wlasciciel_id": 2})
        assert code == 200, saved
        assert saved["wersja"] == 1
        assert "wlasciciel_id" not in saved["profil"]
        assert request(2)[1]["profil"] is None
        assert request(1, payload)[0] == 409
        assert request(1, {**payload, "wersja": 1, "energia": 65})[0] == 200
        assert request(1, {**payload, "wersja": 1})[0] == 409
        assert request(1)[1]["profil"]["energia"] == 65
        assert request(2, {**payload, "imie": "Drugi"})[0] == 200
        assert request(1)[1]["profil"]["imie"] == "Testowy"
        assert request(2)[1]["profil"]["imie"] == "Drugi"
        cleanup = """require $argv[1]; $p=fw_baza(); $p->exec('DELETE FROM fw_uzytkownicy WHERE id=1');
        if ((int)$p->query('SELECT COUNT(*) FROM fw_drucik WHERE wlasciciel_id=1')->fetchColumn()!==0) exit(1);"""
        subprocess.run(["php", "-r", cleanup, str(api / "_lib.php")], check=True)
        print("OK: sesje, CSRF, walidacja, dwa konta, konflikty wersji i usunięcie z kontem")
    finally:
        process.terminate()
        process.wait(timeout=10)
