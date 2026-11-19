# -*- coding: utf-8 -*-
"""
Publikuje najstarszy szkic, gdy kolejka akceptacji urośnie ponad próg.

Po co: szkice agenta czekają w panelu na ręczną akceptację. Gdy nie ma czasu ich
czytać, kolejka rośnie, a gotowa treść leży na serwerze niewidoczna dla nikogo
(noindex, poza /blog/ i sitemapą). Ten skrypt jest zaworem: po przekroczeniu
progu bierze wpis czekający najdłużej, przepuszcza go przez agenta kontroli
(`recenzja.py`) i — o ile recenzja wypadnie czysto — publikuje go tą samą drogą
co akceptacja z panelu.

Jeden przebieg publikuje jeden wpis. Kolejka schodzi po jednym, a blog nie
dostaje pięciu wpisów tego samego dnia.

Wpis, który obleje recenzję, ZOSTAJE w kolejce — do panelu leci notatka
z powodem. Kasowania treści ten skrypt nie robi w ogóle.

Jak użyć:

    py autopublikuj.py               pokazuje, co by zrobił (nic nie zmienia)
    py autopublikuj.py --wykonaj     recenzuje i publikuje
    py autopublikuj.py --recenzja    recenzuje na sucho, nic nie publikuje
    py autopublikuj.py --prog 3      inny próg kolejki niż domyślny

Token agenta bierze ze zmiennej AGENT_TOKEN, a poza Actions — z konfiguracji
backendu przez FTPS, tak samo jak `dopublikuj.py`.

Kod wyjścia: 0 także wtedy, gdy nie było nic do roboty albo wpis został
w kolejce. Kod 1 to prawdziwa awaria (brak API, nieudany build, nieudana
wysyłka) — tylko ona ma prawo zapalić czerwone w Actions.
"""

import argparse
import importlib.util
import io
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

for _strumien in (sys.stdout, sys.stderr):
    if hasattr(_strumien, "reconfigure"):
        _strumien.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(BASE, "pages.py")
RAPORT_RECENZJI = os.path.join(BASE, ".ostatnia-recenzja.json")

API_OCZEKUJACE = os.environ.get(
    "API_OCZEKUJACE", "https://fwdrucik.pl/api/wpisy.php?akcja=oczekujace")
API_DECYZJA = os.environ.get(
    "API_AUTO_DECYZJA", "https://fwdrucik.pl/api/wpisy.php?akcja=auto-decyzja")

# Pięć czekających wpisów to około dziesięciu dni bez akceptacji — wtedy zawór
# się otwiera. Próg jest w jednym miejscu, bo to jedyne pokrętło tego skryptu.
PROG_DOMYSLNY = 5


def blad(tekst):
    print("BŁĄD:", tekst, file=sys.stderr)
    sys.exit(1)


def modul(nazwa_pliku, nazwa):
    """Skrypty z myślnikiem w nazwie nie dają się zaimportować wprost."""
    spec = importlib.util.spec_from_file_location(nazwa, os.path.join(BASE, nazwa_pliku))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def token():
    t = os.environ.get("AGENT_TOKEN", "").strip()
    if t:
        return t
    return modul("zglos-zalegle.py", "zglos_zalegle").token_z_serwera()


def zapytaj_api(adres, tok, dane=None):
    naglowki = {"X-Agent-Token": tok}
    ciało = None
    if dane is not None:
        ciało = json.dumps(dane, ensure_ascii=False).encode("utf-8")
        naglowki["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(adres, data=ciało, headers=naglowki,
                                 method="POST" if dane is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as odp:
            odpowiedz = json.loads(odp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        blad(f"API odpowiedziało {e.code}: {e.read().decode('utf-8', 'replace')[:200]}")
    except urllib.error.URLError as e:
        blad(f"brak połączenia z API: {e.reason}")
    if not odpowiedz.get("ok"):
        blad(f"API zwróciło błąd: {odpowiedz.get('blad', odpowiedz)}")
    return odpowiedz


def uruchom(polecenie, opis, dopuszczalne=(0,)):
    print(f"→ {opis}")
    wynik = subprocess.run(polecenie, cwd=BASE)
    if wynik.returncode not in dopuszczalne:
        blad(f"{opis} zakończone kodem {wynik.returncode}")
    return wynik.returncode


def git(*argumenty):
    wynik = subprocess.run(["git", *argumenty], cwd=BASE)
    if wynik.returncode != 0:
        blad("git " + " ".join(argumenty) + f" zakończone kodem {wynik.returncode}")


def zachowaj_poprawki(slug, raport):
    """Zapisuje poprawiony szkic, choć wpis zostaje w kolejce.

    Recenzja pisze prosto do src/. Gdy werdykt wypadnie „zostaw", publikacja się
    nie odbywa — a razem z nią nie odbywał się commit, więc poprawki ginęły wraz
    z katalogiem roboczego przebiegu. Następny przebieg zaczynał od tego samego
    tekstu i płacił za te same poprawki jeszcze raz, a człowiek dostawał
    do przeczytania wersję gorszą niż ta, którą agent zdążył już naprawić.

    Szkic zostaje szkicem: `noindex`, bez karty na /blog/, poza sitemapą.
    """
    if not raport.get("zmienione_sekcje"):
        return False

    uruchom([sys.executable, "build.py"], "build.py")
    uruchom([sys.executable, "sprawdz.py", "--tylko", slug], f"sprawdz.py --tylko {slug}")

    git("add", "-A")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=BASE).returncode == 0:
        print("Poprawki nie zmieniły żadnego pliku — nie ma czego zapisywać.")
        return False
    git("commit", "-m", f"Poprawki agenta kontroli w szkicu: {slug}")
    git("push")
    uruchom([sys.executable, "wyslij.py", "--wykonaj"], "wysyłka poprawionego szkicu")
    return True


def raport_recenzji():
    if not os.path.isfile(RAPORT_RECENZJI):
        return {}
    try:
        return json.loads(io.open(RAPORT_RECENZJI, encoding="utf-8").read())
    except json.JSONDecodeError:
        return {}


def notatka_z_raportu(raport, opublikowany):
    """Jedno zdanie dla panelu: co agent zrobił i czego się przyczepił."""
    czesci = []
    if opublikowany:
        czesci.append("Opublikowane automatycznie po przekroczeniu progu kolejki.")
    else:
        czesci.append("Agent kontroli nie przepuścił wpisu — czeka na decyzję człowieka.")
    if raport.get("zmienione_sekcje"):
        czesci.append(f"Poprawionych sekcji: {raport['zmienione_sekcje']}.")
    for pole, etykieta in (("problemy", "Usterki"), ("uwagi", "Uwagi"),
                           ("odrzucone_poprawki", "Odrzucone poprawki")):
        if raport.get(pole):
            czesci.append(f"{etykieta}: " + "; ".join(raport[pole][:5]))
    return " ".join(czesci)[:2000]


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--wykonaj", action="store_true", help="faktycznie recenzuj i publikuj")
    ap.add_argument("--recenzja", action="store_true",
                    help="przepuść kandydata przez recenzję, ale niczego nie publikuj")
    ap.add_argument("--prog", type=int, default=PROG_DOMYSLNY,
                    help=f"ile wpisów musi czekać, żeby zawór się otworzył (domyślnie {PROG_DOMYSLNY})")
    ap.add_argument("--model", default="", help="model do recenzji (domyślnie ten z recenzja.py)")
    ap.add_argument("-h", "--help", action="store_true")
    args = ap.parse_args()

    if args.help:
        print(__doc__)
        return 0

    tok = token()
    kolejka = zapytaj_api(API_OCZEKUJACE, tok).get("wpisy", [])
    print(f"Oczekujących w kolejce: {len(kolejka)} (próg: {args.prog})")

    if len(kolejka) < args.prog:
        print("Poniżej progu — nic nie robię.")
        return 0

    # Znacznik szkicu w pages.py, a nie status w bazie, rozstrzyga o tym, czy
    # wpis naprawdę jest niewidoczny na stronie. Baza może się rozjechać z repo.
    szkice = modul("dopublikuj.py", "dopublikuj").szkice_w_repo()
    kandydaci = [w for w in kolejka if w["slug"] in szkice]
    if not kandydaci:
        print("Żaden oczekujący wpis nie jest szkicem w repozytorium — nic do publikacji.")
        return 0

    # Kolejka przychodzi posortowana rosnąco po dacie zgłoszenia, więc pierwszy
    # kandydat to ten, który czeka najdłużej.
    wpis = kandydaci[0]
    slug = wpis["slug"]
    print(f"Najstarszy szkic: {slug} (zgłoszony {wpis.get('utworzony', '?')})")

    if args.recenzja:
        # Pełna ścieżka decyzji bez skutków: recenzja bez --popraw nie tyka
        # plików, a publikacja i zapis do panelu w ogóle się nie odbywają.
        # Tym sprawdzamy, czy agent kontroli działa, nie ruszając bloga.
        polecenie = [sys.executable, "recenzja.py", slug]
        if args.model:
            polecenie += ["--model", args.model]
        kod = uruchom(polecenie, f"recenzja na sucho {slug}", dopuszczalne=(0, 1))
        raport = raport_recenzji()
        print(f"\nWerdykt próbny: {raport.get('werdykt', '?')} — "
              f"{notatka_z_raportu(raport, opublikowany=(kod == 0))}")
        print("Nic nie opublikowano — to była próba.")
        return 0

    if not args.wykonaj:
        print("\nPRÓBA NA SUCHO — nic nie zmieniam.")
        print(f"Do zrobienia: recenzja {slug}, a po czystej recenzji publikacja.")
        print("Aby wykonać: py autopublikuj.py --wykonaj")
        return 0

    polecenie = [sys.executable, "recenzja.py", slug, "--popraw"]
    if args.model:
        polecenie += ["--model", args.model]
    # Kod 1 z recenzji to nie awaria, tylko werdykt „zostaw" — obsługujemy go niżej.
    kod = uruchom(polecenie, f"recenzja {slug}", dopuszczalne=(0, 1))
    raport = raport_recenzji()

    if kod != 0:
        # Najpierw utrwalamy to, co agent zdążył poprawić — dopiero potem notatka,
        # żeby jej treść odpowiadała temu, co naprawdę leży na serwerze.
        zachowane = zachowaj_poprawki(slug, raport)
        notatka = notatka_z_raportu(raport, opublikowany=False)
        if zachowane:
            notatka = ("Poprawki agenta kontroli zapisane w szkicu — podgląd jest już "
                       "po nich. " + notatka)[:2000]
        zapytaj_api(API_DECYZJA, tok, {"slug": slug, "decyzja": "zostaw", "notatka": notatka})
        print(f"\nWpis {slug} zostaje w kolejce. Notatka trafiła do panelu.")
        # Nie awaria: skrypt zrobił dokładnie to, co miał zrobić.
        return 0

    uruchom([sys.executable, "agent-bloga.py", "--publikuj", slug], f"publikacja {slug}")
    uruchom([sys.executable, "wyslij.py", "--wykonaj"], "wysyłka na serwer")
    zapytaj_api(API_DECYZJA, tok,
                {"slug": slug, "decyzja": "publikuj",
                 "notatka": notatka_z_raportu(raport, opublikowany=True)})

    print(f"\nGotowe — wpis {slug} opublikowany automatycznie.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
