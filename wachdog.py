# -*- coding: utf-8 -*-
"""
Codzienny przegląd stanu serwisu — wykrywa i naprawia rozjazdy.

Po co: między repozytorium, katalogiem `dist/` a serwerem może zrobić się
różnica, której nikt nie zauważy, bo strona dalej się wyświetla. Zdarzyło się
to już kilka razy: ręczna edycja `src/` bez przebudowy, publikacja anulowana
przez kolejkę współbieżności, wysyłka przerwana w połowie. Ten skrypt raz
dziennie sprawdza wszystkie te miejsca i — tam gdzie to bezpieczne — sam
naprawia.

Co sprawdza:

  1. `build.py`      — czy `dist/` odpowiada źródłom (naprawa: przebudowa + commit)
  2. `sprawdz.py`    — kontrola jakości SEO i struktury (bez automatycznej naprawy)
  3. wersja CSS      — czy serwer ma aktualne zasoby (naprawa: wysyłka)
  4. adresy z sitemap — czy każdy zwraca 200
  5. szkice          — czy mają `noindex` i czy nie wyciekły do sitemapy
  6. kolejka tematów — czy nie kończą się tematy dla agenta

Jak użyć:

    py wachdog.py              tylko raport, niczego nie zmienia
    py wachdog.py --napraw     dodatkowo naprawia to, co da się naprawić

Kod wyjścia: 0 gdy wszystko gra albo wszystko naprawiono, 1 gdy zostało coś,
czego skrypt nie tknie sam (np. błąd jakości treści wymagający decyzji).
"""

import argparse
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(BASE, "dist")
PAGES = os.path.join(BASE, "pages.py")
KOLEJKA = os.path.join(BASE, "tematy.md")
SITE = "https://fwdrucik.pl"
PROG_TEMATOW = 20  # poniżej tylu wolnych tematów wołamy o uzupełnienie


class Raport:
    def __init__(self):
        self.problemy = []   # wymagają człowieka
        self.naprawione = []
        self.ok = []

    def zle(self, tekst):
        self.problemy.append(tekst)
        print(f"  [PROBLEM] {tekst}")

    def naprawa(self, tekst):
        self.naprawione.append(tekst)
        print(f"  [NAPRAWIONO] {tekst}")

    def dobrze(self, tekst):
        self.ok.append(tekst)
        print(f"  [OK] {tekst}")


def pobierz(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": "fwdrucik-wachdog/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as odp:
        return odp.status, odp.read().decode("utf-8", "replace")


def uruchom(polecenie, cwd=BASE):
    return subprocess.run(polecenie, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


# ------------------------------------------------------------------ kontrole

def sprawdz_build(r, napraw):
    """dist/ musi odpowiadać źródłom — inaczej wysyłamy na serwer nieaktualne pliki."""
    wynik = uruchom([sys.executable, "build.py"])
    if wynik.returncode != 0:
        r.zle(f"build.py zakończone kodem {wynik.returncode}: {wynik.stderr.strip()[:200]}")
        return
    zmiany = uruchom(["git", "status", "--porcelain", "dist"]).stdout.strip()
    if not zmiany:
        r.dobrze("dist/ zgodny ze źródłami")
        return
    ile = len(zmiany.splitlines())
    if not napraw:
        r.zle(f"dist/ rozjechany ze źródłami ({ile} plików) — uruchom build.py i zacommituj")
        return
    uruchom(["git", "add", "-A", "dist"])
    uruchom(["git", "commit", "-m", "chore: przebudowa dist po rozjezdzie ze zrodlami"])
    r.naprawa(f"przebudowano dist/ i zapisano zmianę ({ile} plików)")


def sprawdz_jakosc(r):
    """sprawdz.py pilnuje SEO i struktury — tego nie naprawiamy automatycznie,
    bo poprawka dotyczy treści i wymaga decyzji człowieka."""
    wynik = uruchom([sys.executable, "sprawdz.py"])
    if wynik.returncode == 0:
        r.dobrze("kontrola jakości bez zastrzeżeń")
        return
    linie = [l.strip() for l in wynik.stdout.splitlines() if l.strip().startswith("-")]
    r.zle("kontrola jakości zgłasza: " + ("; ".join(linie[:5]) or wynik.stdout.strip()[:200]))


def wersja_css_lokalnie():
    plik = os.path.join(DIST, "index.html")
    if not os.path.isfile(plik):
        return None
    m = re.search(r"style\.css\?v=([a-z0-9]+)", open(plik, encoding="utf-8").read())
    return m.group(1) if m else None


def sprawdz_serwer(r, napraw):
    """Serwer musi mieć to, co jest w dist/. Wersja CSS ma w nazwie skrót treści,
    więc wystarcza jako znacznik — zmienia się przy każdej zmianie stylów."""
    try:
        _, strona = pobierz(SITE + "/")
    except Exception as e:
        r.zle(f"strona główna nieosiągalna: {e}")
        return
    m = re.search(r"style\.css\?v=([a-z0-9]+)", strona)
    zdalna, lokalna = (m.group(1) if m else None), wersja_css_lokalnie()
    if not lokalna:
        r.zle("brak dist/index.html — nie mam do czego porównać serwera")
        return
    if zdalna == lokalna:
        r.dobrze(f"serwer ma aktualne zasoby (css {lokalna})")
        return
    if not napraw:
        r.zle(f"serwer ma starsze zasoby (css {zdalna}, lokalnie {lokalna}) — potrzebna wysyłka")
        return
    wynik = uruchom([sys.executable, "wyslij.py", "--wykonaj"])
    if wynik.returncode != 0:
        r.zle(f"wysyłka nie powiodła się: {wynik.stderr.strip()[:200]}")
        return
    r.naprawa(f"wysłano serwis na serwer (css {lokalna})")


def sprawdz_adresy(r):
    """Każdy adres z sitemapy musi odpowiadać — inaczej mamy martwy link w indeksie."""
    try:
        _, mapa = pobierz(SITE + "/sitemap.xml")
    except Exception as e:
        r.zle(f"sitemap.xml nieosiągalna: {e}")
        return
    adresy = re.findall(r"<loc>(.*?)</loc>", mapa)
    martwe = []
    for adres in adresy:
        try:
            kod, _ = pobierz(adres, timeout=30)
            if kod != 200:
                martwe.append(f"{adres} ({kod})")
        except urllib.error.HTTPError as e:
            martwe.append(f"{adres} ({e.code})")
        except Exception as e:
            martwe.append(f"{adres} ({e})")
    if martwe:
        r.zle(f"martwe adresy w sitemapie: {', '.join(martwe[:5])}")
    else:
        r.dobrze(f"wszystkie adresy z sitemapy odpowiadają ({len(adresy)})")


def sprawdz_szkice(r):
    """Szkic ma być niewidoczny: noindex na stronie i brak w sitemapie.
    Wyciek szkicu do wyszukiwarki to gorszy problem niż brak publikacji."""
    tresc = open(PAGES, encoding="utf-8").read()
    slugi = []
    for blok in re.findall(r"strona\((.*?)\n    \),", tresc, re.S):
        if "# SZKIC" not in blok:
            continue
        m = re.search(r'"/blog/([a-z0-9-]+)/"', blok)
        if m:
            slugi.append(m.group(1))
    if not slugi:
        r.dobrze("brak szkiców oczekujących")
        return
    try:
        _, mapa = pobierz(SITE + "/sitemap.xml")
    except Exception as e:
        r.zle(f"nie mogę sprawdzić sitemapy: {e}")
        return
    wycieki = []
    for slug in slugi:
        if slug in mapa:
            wycieki.append(f"{slug} (w sitemapie)")
            continue
        try:
            _, strona = pobierz(f"{SITE}/blog/{slug}/")
            if "noindex" not in strona:
                wycieki.append(f"{slug} (bez noindex)")
        except Exception:
            pass  # szkic może jeszcze nie być wysłany — to nie wyciek
    if wycieki:
        r.zle("szkice widoczne dla wyszukiwarek: " + ", ".join(wycieki))
    else:
        r.dobrze(f"szkice ukryte poprawnie ({len(slugi)})")


def sprawdz_kolejke(r):
    if not os.path.isfile(KOLEJKA):
        r.zle("brak pliku tematy.md")
        return
    wolne = len(re.findall(r"^-\s*\[ \]", open(KOLEJKA, encoding="utf-8").read(), re.M))
    if wolne == 0:
        r.zle("kolejka tematów pusta — agent nie ma o czym pisać")
    elif wolne < PROG_TEMATOW:
        r.zle(f"kolejka tematów na wyczerpaniu: {wolne} pozycji")
    else:
        r.dobrze(f"kolejka tematów: {wolne} pozycji")


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--napraw", action="store_true", help="naprawiaj, nie tylko raportuj")
    ap.add_argument("-h", "--help", action="store_true")
    args = ap.parse_args()
    if args.help:
        print(__doc__)
        return 0

    print(f"Przegląd serwisu {SITE}" + (" (z naprawą)" if args.napraw else " (tylko raport)"))
    r = Raport()

    print("\n1/6  Zgodność dist ze źródłami")
    sprawdz_build(r, args.napraw)
    print("\n2/6  Kontrola jakości")
    sprawdz_jakosc(r)
    print("\n3/6  Zgodność serwera z dist")
    sprawdz_serwer(r, args.napraw)
    print("\n4/6  Adresy z sitemapy")
    sprawdz_adresy(r)
    print("\n5/6  Ukrycie szkiców")
    sprawdz_szkice(r)
    print("\n6/6  Kolejka tematów")
    sprawdz_kolejke(r)

    print(f"\nPodsumowanie: {len(r.ok)} w porządku, "
          f"{len(r.naprawione)} naprawionych, {len(r.problemy)} do decyzji")
    if r.naprawione:
        print("\nNaprawione samodzielnie:")
        for x in r.naprawione:
            print("  -", x)
    if r.problemy:
        print("\nWymaga uwagi:")
        for x in r.problemy:
            print("  -", x)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
