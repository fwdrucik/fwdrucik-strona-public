# -*- coding: utf-8 -*-
"""
Melduje w panelu szkice, które nie trafiły do kolejki akceptacji.

Po co: `zglos-wpis.py` zgłasza wyłącznie ostatni wpis (`.ostatni-wpis.json`),
bo tyle wystarcza w normalnym przebiegu agenta. Gdy jednak workflow przerwał
się przed krokiem „Zgłoszenie do akceptacji" — a tak było przy pustym
`agent_token` i przy błędzie kolumny `lead` — szkic wylądował na serwerze
i w repozytorium, ale w panelu go nie ma. Ten skrypt uzupełnia zaległości.

Jak użyć:

    py zglos-zalegle.py                 pokazuje, co by zgłosił (nic nie wysyła)
    py zglos-zalegle.py --wykonaj       zgłasza wszystkie zaległe szkice
    py zglos-zalegle.py --wykonaj --slug uds-iso-14229-diagnostyka-warsztatowa

Skąd bierze dane: szkice rozpoznaje po `noindex` w `pages.py` (tak samo jak
build.py wycina je z sitemapy), tytuł i opis bierze z tego samego wpisu.

Skąd bierze token: domyślnie z konfiguracji backendu na serwerze, przez
FTPS — nie musisz go nigdzie wklejać ani znać. Token nie jest wypisywany
ani logowany. Można go też podać przez zmienną `AGENT_TOKEN`.

Powtórne zgłoszenie tego samego sluga jest bezpieczne: API robi
`ON DUPLICATE KEY UPDATE` i nie rusza statusu, więc raz odrzucony wpis
nie wraca do kolejki tylnymi drzwiami.
"""

import argparse
import io
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from ftplib import FTP, FTP_TLS

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FTP = os.path.expanduser(r"~\.claude\.ftp-fwdrucik.json")
KONCOWKA = os.environ.get("API_WPISY", "https://fwdrucik.pl/api/wpisy.php?akcja=zglos")

# Kolejność ta sama co w api/_lib.php — backend czyta pierwszy istniejący.
KANDYDACI = (
    "public_html/autoinstalator/fw-konfiguracja.php",
    "public_html/autoinstalator/joomla/api/konfiguracja.php",
)


class FTPS(FTP_TLS):
    """Pure-FTPd na home.pl wymaga wznowienia sesji TLS na kanale danych."""

    def ntransfercmd(self, cmd, rest=None):
        conn, size = FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.sock.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session)
        return conn, size


def blad(tekst):
    print("BŁĄD:", tekst, file=sys.stderr)
    sys.exit(1)


def token_z_serwera():
    """Wyciąga `agent_token` z konfiguracji backendu. Wartości nie pokazuje."""
    if not os.path.isfile(CONFIG_FTP):
        blad(f"brak danych logowania FTP — utwórz {CONFIG_FTP}")
    with open(CONFIG_FTP, encoding="utf-8") as f:
        c = json.load(f)
    kontekst = ssl.create_default_context()
    kontekst.check_hostname = False
    kontekst.verify_mode = ssl.CERT_NONE
    ftp = FTPS(context=kontekst)
    ftp.connect(c["host"], int(c.get("port", 21)), timeout=60)
    ftp.login(c["user"], c["password"])
    ftp.prot_p()
    ftp.set_pasv(True)

    tresc = None
    for kandydat in KANDYDACI:
        bufor = io.BytesIO()
        try:
            ftp.retrbinary("RETR " + kandydat, bufor.write)
        except Exception:
            continue
        tresc = bufor.getvalue().decode("utf-8")
        break
    ftp.quit()

    if tresc is None:
        blad("nie znalazłem konfiguracji backendu na serwerze")
    m = re.search(r"['\"]agent_token['\"]\s*=>\s*'((?:[^'\\]|\\.)*)'", tresc)
    if not m:
        blad("w konfiguracji nie ma `agent_token` — uruchom najpierw ustaw-token-agenta.py")
    token = m.group(1).replace("\\'", "'").replace("\\\\", "\\")
    if not token:
        blad("`agent_token` na serwerze jest pusty — uruchom ustaw-token-agenta.py")
    return token


def szkice():
    """Wpisy blogowe oznaczone jako szkic — po tym samym `noindex`, którym
    build.py wycina je z sitemapy."""
    sys.path.insert(0, BASE)
    import pages  # noqa: E402  (import po ustawieniu ścieżki)

    wynik = []
    for p in pages.STRONY:
        if not p["url"].startswith("/blog/") or p["url"] == "/blog/":
            continue
        if not p.get("noindex"):
            continue
        wynik.append({
            "slug": p["url"].strip("/").split("/")[-1],
            "tytul": p["title"],
            "lead": p["desc"],
            "url": p["url"],
        })
    return wynik


def zglos(wpis, token):
    dane = json.dumps({
        "slug": wpis["slug"],
        "tytul": wpis["tytul"],
        "lead": wpis["lead"],
        "url": wpis["url"],
        "run_url": "",
    }, ensure_ascii=False).encode("utf-8")

    zadanie = urllib.request.Request(
        KONCOWKA, data=dane, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8",
                 "X-Agent-Token": token},
    )
    try:
        with urllib.request.urlopen(zadanie, timeout=60) as odp:
            return True, json.loads(odp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"
    except urllib.error.URLError as e:
        return False, f"brak połączenia: {e.reason}"


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--wykonaj", action="store_true", help="faktycznie wyślij zgłoszenia")
    ap.add_argument("--slug", action="append", help="zgłoś tylko ten slug (można powtórzyć)")
    ap.add_argument("-h", "--help", action="store_true")
    args = ap.parse_args()

    if args.help:
        print(__doc__)
        return 0

    lista = szkice()
    if args.slug:
        znane = {w["slug"] for w in lista}
        for s in args.slug:
            if s not in znane:
                blad(f"nie ma szkicu o slugu {s}. Dostępne: " + ", ".join(sorted(znane)))
        lista = [w for w in lista if w["slug"] in set(args.slug)]

    if not lista:
        print("Nie ma szkiców do zgłoszenia.")
        return 0

    print(f"{'ZGŁOSZENIE' if args.wykonaj else 'PLAN (próba na sucho)'}: {len(lista)} szkiców\n")
    for w in lista:
        print(f"  {w['slug']}")
        print(f"      {w['tytul'][:78]}")

    if not args.wykonaj:
        print("\nNic nie wysłano. Aby zgłosić naprawdę: py zglos-zalegle.py --wykonaj")
        return 0

    token = os.environ.get("AGENT_TOKEN", "").strip()
    zrodlo = "zmienna AGENT_TOKEN"
    if not token:
        token = token_z_serwera()
        zrodlo = "konfiguracja na serwerze"
    print(f"\nToken agenta: {len(token)} znaków ({zrodlo}), treści nie pokazuję.\n")

    bledy = 0
    for w in lista:
        ok, odp = zglos(w, token)
        if ok:
            print(f"  zgłoszono: {w['slug']} -> id={odp.get('id')} status={odp.get('status')}")
        else:
            bledy += 1
            print(f"  BŁĄD przy {w['slug']}: {odp}", file=sys.stderr)

    print(f"\nGotowe — {len(lista) - bledy} z {len(lista)} w kolejce.")
    return 1 if bledy else 0


if __name__ == "__main__":
    sys.exit(main())
