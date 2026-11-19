# -*- coding: utf-8 -*-
"""
Dopublikowuje wpisy zatwierdzone w panelu, które nie trafiły na stronę.

Po co: akceptacja w panelu odpala workflow „Decyzja o wpisie" przez
`repository_dispatch`, ale GitHub trzyma w kolejce **tylko jeden** oczekujący
przebieg na grupę współbieżności — każdy kolejny jest anulowany. Przy dwóch
akceptacjach pod rząd (albo akceptacji w trakcie pracy agenta) wpis zostaje
oznaczony w bazie jako opublikowany, a na stronie go nie ma. Ten skrypt
wyrównuje różnicę: pyta API o wpisy ze statusem `opublikowany` i publikuje te,
które w repozytorium nadal są szkicami.

Jak użyć:

    py dopublikuj.py             pokazuje, co wymaga publikacji (nic nie zmienia)
    py dopublikuj.py --wykonaj   publikuje zaległe wpisy i wysyła je na serwer

Token agenta bierze ze zmiennej `AGENT_TOKEN`, a poza Actions — z konfiguracji
backendu na serwerze przez FTPS, tak samo jak `zglos-zalegle.py`. Nie jest
nigdzie wypisywany.

Skrypt jest bezpieczny przy powtórzeniu: wpis, który nie jest już szkicem,
zostaje pominięty, a `agent-bloga.py --publikuj` sam odmawia pracy na wpisie
bez statusu szkicu.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(BASE, "pages.py")
KONCOWKA = os.environ.get(
    "API_DO_PUBLIKACJI", "https://fwdrucik.pl/api/wpisy.php?akcja=do-publikacji")


def blad(tekst):
    print("BŁĄD:", tekst, file=sys.stderr)
    sys.exit(1)


def token():
    """Zmienna środowiskowa (tak działa to w Actions), a lokalnie — z serwera."""
    t = os.environ.get("AGENT_TOKEN", "").strip()
    if t:
        return t
    import importlib.util
    sciezka = os.path.join(BASE, "zglos-zalegle.py")
    spec = importlib.util.spec_from_file_location("zglos_zalegle", sciezka)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul.token_z_serwera()


def zatwierdzone(tok):
    """Slugi, które panel uznał za opublikowane."""
    req = urllib.request.Request(KONCOWKA, headers={"X-Agent-Token": tok})
    try:
        with urllib.request.urlopen(req, timeout=60) as odp:
            dane = json.loads(odp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        blad(f"API odpowiedziało {e.code}: {e.read().decode('utf-8', 'replace')[:200]}")
    except urllib.error.URLError as e:
        blad(f"brak połączenia z API: {e.reason}")
    if not dane.get("ok"):
        blad(f"API zwróciło błąd: {dane.get('blad', dane)}")
    return [w["slug"] for w in dane.get("wpisy", [])]


def szkice_w_repo():
    """Slugi wpisów, które w pages.py nadal mają znacznik szkicu.

    Ten sam znacznik decyduje o `noindex`, więc jeśli wpis go ma, to na
    stronie jest niewidoczny — niezależnie od tego, co mówi baza.
    """
    tresc = open(PAGES, encoding="utf-8").read()
    wynik = set()
    for blok in re.findall(r"strona\((.*?)\n    \),", tresc, re.S):
        if "# SZKIC" not in blok:
            continue
        m = re.search(r'"/blog/([a-z0-9-]+)/"', blok)
        if m:
            wynik.add(m.group(1))
    return wynik


def uruchom(polecenie, opis):
    print(f"→ {opis}")
    wynik = subprocess.run(polecenie, cwd=BASE)
    if wynik.returncode != 0:
        blad(f"{opis} zakończone kodem {wynik.returncode}")


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--wykonaj", action="store_true", help="faktycznie opublikuj zaległe wpisy")
    ap.add_argument("-h", "--help", action="store_true")
    args = ap.parse_args()

    if args.help:
        print(__doc__)
        return 0

    szkice = szkice_w_repo()
    zaakceptowane = zatwierdzone(token())
    # Zaległe = panel mówi „opublikowany", a w repozytorium to nadal szkic.
    zalegle = [s for s in zaakceptowane if s in szkice]

    print(f"Zatwierdzonych w panelu: {len(zaakceptowane)}")
    print(f"Szkiców w repozytorium:  {len(szkice)}")

    if not zalegle:
        print("\nNic nie zostało w tyle — panel i strona się zgadzają.")
        return 0

    print(f"\n{'PUBLIKACJA' if args.wykonaj else 'PLAN (próba na sucho)'}: {len(zalegle)} wpisów\n")
    for s in zalegle:
        print("  " + s)

    if not args.wykonaj:
        print("\nNic nie opublikowano. Aby opublikować: py dopublikuj.py --wykonaj")
        return 0

    for s in zalegle:
        uruchom([sys.executable, "agent-bloga.py", "--publikuj", s], f"publikacja {s}")

    # Wysyłka raz, po wszystkich zmianach — dist i tak jest przebudowywany
    # w całości, więc nie ma sensu wysyłać serwisu po każdym wpisie osobno.
    uruchom([sys.executable, "wyslij.py", "--wykonaj"], "wysyłka na serwer")

    print(f"\nGotowe — dopublikowano {len(zalegle)} wpisów.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
