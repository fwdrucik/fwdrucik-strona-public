# -*- coding: utf-8 -*-
"""Kontrola jakości wygenerowanego serwisu w dist/ — uruchamiać po każdym build.py.

    py sprawdz.py                 kontrola całego serwisu, kod 1 przy każdej usterce
    py sprawdz.py --tylko SLUG    kod 1 wyłącznie za usterki wpisu SLUG

Tryb --tylko jest dla agenta bloga i recenzenta. Bez niego agent przerywał pracę
nad własnym, poprawnym wpisem, bo gdzieś indziej w serwisie leżała zastana
usterka — i cały przebieg szedł na czerwono. Zastane usterki dalej są wypisywane
(i tak łapie je wachdog.py), ale nie wywracają publikacji jednego wpisu.
"""

import collections
import glob
import hashlib
import json
import os
import re
import sys

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
SITE = "https://fwdrucik.pl"

# Wpisy krotsze od tego progu przegrywaja na tych samych frazach z tekstami,
# ktore odpowiadaja na pytanie do konca. Trzy najstarsze wpisy mialy po
# 184-311 slow i to one wyznaczyly ten prog — nie ma byc do niego powrotu.
MIN_SLOW_WPISU = 450

# Przezwajanie silników zleca F.W. DRUCIK zewnętrznej pracowni nawojowej
# (decyzja właściciela 2026-11-11). Nazwa partnera nie może trafić na stronę
# ani do kodu, dlatego tu są tylko skróty SHA-256 jej zapisów (małe litery).
SKROTY_PARTNERA = {
    "ab77ced131f2ddf64915f035d327eae43ef4945595413bfec00087664019cd49",
    "e3ebd3970f3291989afadeba1ae8c35a138d5ded3544b370063523f92c94c261",
    "91f578f2b77a64406e9468ef8689292cd4cfd8c9a3871998116c09dd3495007d",
}
SLOWO = re.compile(r"[a-ząćęłńóśźż]+(?:-[a-ząćęłńóśźż]+)*")
# Treść nie może też sugerować, że przezwajamy u siebie.
WLASNE_PRZEZWAJANIE = re.compile(
    r"\bprzezwaj(?:amy|am)\b|\bprzezwijamy\b|przezwajanie na inne napięcie", re.I)


def zakazana_fraza(tekst):
    """Opis pierwszego naruszenia albo None. Nazwy partnera nie wypisuje."""
    slowa = SLOWO.findall(tekst.lower())
    kandydaci = set(slowa) | {a + b for a, b in zip(slowa, slowa[1:])}
    if any(hashlib.sha256(s.encode()).hexdigest() in SKROTY_PARTNERA for s in kandydaci):
        return "nazwa partnera nawojowego"
    m = WLASNE_PRZEZWAJANIE.search(tekst)
    return f"deklaracja własnego przezwajania „{m.group(0)}”" if m else None


def main(tylko=None):
    os.chdir(DIST)
    problemy = []
    tytuly, opisy, kanoniczne = collections.Counter(), collections.Counter(), collections.Counter()

    for f in sorted(glob.glob("**/*.html", recursive=True)):
        if f.startswith("google"):
            continue
        h = open(f, encoding="utf-8").read()

        t = re.search(r"<title>(.*?)</title>", h, re.S).group(1)
        d = re.search(r'name="description" content="(.*?)"', h, re.S).group(1)
        c = re.search(r'rel="canonical" href="(.*?)"', h).group(1)
        tytuly[t] += 1
        opisy[d] += 1
        kanoniczne[c] += 1

        if len(t) > 62:
            problemy.append(f"{f}: title {len(t)} znaków (limit 62)")
        if len(d) > 160:
            problemy.append(f"{f}: description {len(d)} znaków (limit 160)")

        if h.count("<h1") != 1:
            problemy.append(f"{f}: {h.count('<h1')} nagłówków H1")

        poziomy = [int(x) for x in re.findall(r"<h([1-6])[ >]", h)]
        for a, b in zip(poziomy, poziomy[1:]):
            if b > a + 1:
                problemy.append(f"{f}: przeskok w hierarchii nagłówków H{a} -> H{b}")
                break

        for img in re.findall(r"<img\b[^>]*>", h):
            if "alt=" not in img:
                problemy.append(f"{f}: <img> bez atrybutu alt")
            if "width=" not in img or "height=" not in img:
                problemy.append(f"{f}: <img> bez width/height (ryzyko CLS)")

        for blok in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
            try:
                json.loads(blok)
            except Exception as e:
                problemy.append(f"{f}: niepoprawny JSON-LD ({e})")

    for f in sorted(glob.glob("**/*", recursive=True)):
        if not f.endswith((".html", ".txt", ".json", ".xml", ".php", ".js")) or not os.path.isfile(f):
            continue
        naruszenie = zakazana_fraza(open(f, encoding="utf-8", errors="replace").read())
        if naruszenie:
            problemy.append(f"{f}: {naruszenie}")

    for licznik, nazwa in ((tytuly, "title"), (opisy, "description"), (kanoniczne, "canonical")):
        for wartosc, ile in licznik.items():
            if ile > 1:
                problemy.append(f"zduplikowany {nazwa} ({ile}x): {wartosc[:70]}")

    # --- wpisy bloga: objetosc i wyjscie dalej ------------------------------
    for f in sorted(glob.glob("blog/*/index.html")):
        h = open(f, encoding="utf-8").read()
        if re.search(r'<meta name="robots" content="[^"]*noindex', h):
            continue  # szkic czeka na akceptacje, nie oceniamy go jeszcze

        tresc = re.search(r'(?s)<div id="blog-full-content"[^>]*>(.*?)\n  </div>', h)
        if tresc:
            slow = len(re.sub(r"<[^>]+>", " ", tresc.group(1)).split())
            if slow < MIN_SLOW_WPISU:
                problemy.append(f"{f}: wpis ma {slow} slow (minimum {MIN_SLOW_WPISU})")

        if 'class="powiazane-lista"' not in h:
            problemy.append(f"{f}: brak bloku powiazanych wpisow — artykul konczy sie slepa uliczka")

    # --- kanal RSS ---------------------------------------------------------
    if not os.path.isfile("rss.xml"):
        problemy.append("brak rss.xml")
    else:
        rss = open("rss.xml", encoding="utf-8").read()
        ile_wpisow = len(glob.glob("blog/*/index.html"))
        if rss.count("<item>") == 0:
            problemy.append("rss.xml bez zadnej pozycji")
        elif rss.count("<item>") > ile_wpisow:
            problemy.append("rss.xml wskazuje wiecej wpisow, niz jest w serwisie")

    sm = open("sitemap.xml", encoding="utf-8").read()

    # lastmod, ktory dla wszystkich adresow jest taki sam, nie niesie zadnej
    # informacji — wyszukiwarki przestaja go wtedy brac pod uwage.
    lastmody = set(re.findall(r"<lastmod>(.*?)</lastmod>", sm))
    if len(lastmody) == 1 and len(re.findall(r"<lastmod>", sm)) > 5:
        problemy.append("sitemap.xml: wszystkie adresy maja te sama date lastmod")
    w_mapie = set(re.findall(r"<loc>(.*?)</loc>", sm))
    # Strony z noindex celowo nie trafiają do sitemapy (build.py je pomija).
    # Tak działa szkic wpisu: leży na serwerze pod znanym adresem, ale nie ma
    # go w mapie ani na /blog/, dopóki człowiek go nie zaakceptuje. Bez tego
    # wyjątku kontrola zgłaszała każdy szkic jako „stronę spoza sitemap.xml"
    # i agent bloga przerywał pracę na własnym, poprawnym wyniku.
    na_dysku = set()
    # Podstrona skladana przez PHP sama decyduje o swoim `robots` w chwili
    # odpowiedzi — statycznie nie da sie orzec, czy ma trafic do mapy serwisu.
    # Liczymy ja wiec jako istniejaca (mapa moze na nia wskazywac), ale nie
    # wymagamy jej obecnosci w mapie.
    php_na_dysku = {
        SITE + "/" + f.replace(os.sep, "/").replace("index.php", "")
        for f in glob.glob("**/index.php", recursive=True)
    }
    for f in glob.glob("**/index.html", recursive=True):
        if f.startswith("admin"):
            continue
        if re.search(r'<meta name="robots" content="[^"]*noindex', open(f, encoding="utf-8").read()):
            continue
        na_dysku.add(SITE + "/" + f.replace(os.sep, "/").replace("index.html", ""))
    for brak in sorted(na_dysku - w_mapie):
        problemy.append(f"strona spoza sitemap.xml: {brak}")
    for nadmiar in sorted(w_mapie - na_dysku - php_na_dysku):
        problemy.append(f"sitemap.xml wskazuje nieistniejącą stronę: {nadmiar}")

    # --- strony bez linkow przychodzacych z tresci --------------------------
    # Podstrona, do ktorej prowadzi tylko menu, dostaje najslabszy sygnal
    # z calego serwisu. Strona glowna i 404 sa z tego wylaczone z definicji.
    przychodzace = collections.Counter()
    wszystkie = set()
    for f in glob.glob("**/index.html", recursive=True):
        adres = "/" + f.replace(os.sep, "/").replace("index.html", "")
        h = open(f, encoding="utf-8").read()
        # Szkic (noindex) z zalozenia nie ma karty na /blog/ ani wpisu w menu,
        # wiec zerowa liczba linkow przychodzacych to jego stan poprawny, a nie
        # blad. Bez tego wyjatku agent bloga wywracal wlasny, udany przebieg.
        if not re.search(r'<meta name="robots" content="[^"]*noindex', h):
            wszystkie.add(adres)
        m = re.search(r"(?s)<main[^>]*>(.*?)</main>", h)
        for cel in set(re.findall(r'href="(/[^"#?]*)"', m.group(1) if m else "")):
            if cel != adres:
                przychodzace[cel] += 1
    for f in glob.glob("**/index.php", recursive=True):
        wszystkie.add("/" + f.replace(os.sep, "/").replace("index.php", ""))
    # Strona z noindex nie ma trafic do wyszukiwarki, wiec brak linkow
    # z tresci nie jest dla niej problemem — koszyk i kasa sa tu z zalozenia.
    noindeksowane = set()
    for f in glob.glob("**/index.html", recursive=True):
        adres = "/" + f.replace(os.sep, "/").replace("index.html", "")
        if re.search(r'<meta name="robots" content="[^"]*noindex',
                     open(f, encoding="utf-8").read()):
            noindeksowane.add(adres)

    for adres in sorted(wszystkie):
        if adres in ("/", "/admin/") or adres in noindeksowane or przychodzace[adres]:
            continue
        problemy.append(f"strona bez linku z tresci innej podstrony: {adres}")

    print(f"Sprawdzono {len(tytuly)} unikalnych tytułów, {len(w_mapie)} adresów w sitemap.xml")
    if not problemy:
        print("Brak problemów.")
        return

    if tylko is None:
        print("\nZNALEZIONE PROBLEMY:")
        for p in problemy:
            print(" -", p)
        sys.exit(1)

    # Duplikat tytułu, opisu albo adresu kanonicznego zgłaszamy zawsze: nowy wpis
    # jest zwykle jego przyczyną, a komunikat nie niesie ścieżki, po której dałoby
    # się to rozstrzygnąć. Ukośniki normalizujemy, bo w komunikatach z Windows
    # siedzi separator katalogów tej maszyny, a slug zawsze ma ukośnik zwykły.
    moje, obce = [], []
    for p in problemy:
        if f"/{tylko}/" in p.replace(os.sep, "/") or p.startswith("zduplikowany"):
            moje.append(p)
        else:
            obce.append(p)

    if obce:
        print(f"\nZASTANE USTERKI SERWISU (poza wpisem {tylko}) — nie blokują publikacji:")
        for p in obce:
            print(" -", p)
    if moje:
        print(f"\nPROBLEMY WPISU {tylko}:")
        for p in moje:
            print(" -", p)
        sys.exit(1)
    print(f"Wpis {tylko} bez zastrzeżeń.")


if __name__ == "__main__":
    argumenty = sys.argv[1:]
    slug = None
    if argumenty[:1] == ["--tylko"]:
        if len(argumenty) < 2:
            print("Użycie: py sprawdz.py --tylko SLUG", file=sys.stderr)
            sys.exit(2)
        slug = argumenty[1]
    elif argumenty:
        print(__doc__)
        sys.exit(2)
    main(slug)
