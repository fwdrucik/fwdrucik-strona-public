# -*- coding: utf-8 -*-
"""
Autonomiczny agent bloga fwdrucik.pl.

Bierze temat z kolejki (tematy.md), pisze wpis przez Gemini API, wstawia go do
src/, pages.py i src/blog.html, buduje serwis, sprawdza jakość i — o ile nie
wyłączono — zakłada gałąź `blog/<slug>` z gotowym commitem do przeglądu.

Na produkcję nic nie idzie automatycznie. Wysyłkę robi człowiek po scaleniu:
    python build.py && python sprawdz.py && python wyslij.py --wykonaj

Uruchomienie:
    python agent-bloga.py                          # pierwszy temat z kolejki
    python agent-bloga.py --temat "Magistrala LIN"
    python agent-bloga.py --losowo                 # losowa dziedzina z tematy.md
    python agent-bloga.py --bez-gita               # tylko pliki + build + kontrola
    python agent-bloga.py --model gemini-2.5-pro

Klucz API:
    zmienna środowiskowa GEMINI_API_KEY
    albo plik ~/.claude/.gemini-fwdrucik.json  ->  {"api_key": "..."}
Klucza nigdy nie trzymamy w repozytorium.
"""

import argparse
import datetime
import json
import os
import random
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

# Konsola Windows domyślnie koduje w cp1250, w której nie ma choćby strzałki
# z komunikatów postępu — bez tego skrypt wywala się na własnym print().
for _strumien in (sys.stdout, sys.stderr):
    if hasattr(_strumien, "reconfigure"):
        _strumien.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "src")
PAGES = os.path.join(BASE, "pages.py")
BLOG_INDEX = os.path.join(SRC, "blog.html")
KOLEJKA = os.path.join(BASE, "tematy.md")

# Model dobrany pod darmowy poziom klucza — mocniejsze warianty (gemini-3.1-pro-preview)
# działają tak samo, ale wyczerpują dzienny limit po kilku wpisach.
MODEL_DOMYSLNY = "gemini-3.1-flash-lite"
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SZKICE = os.path.join(BASE, "szkice")

# Znaczniki, między które wstawiane są nowe wpisy. Nie usuwać z plików.
MARKER_PAGES = "# === AGENT BLOGA: nowe wpisy wstawiane powyżej tej linii ==="
MARKER_BLOG = "<!-- === nowe karty wstawiane powyżej tej linii === -->"

# Linia dopisywana do wpisu w pages.py, dopóki czeka na akceptację.
# Akceptacja usuwa dokładnie ten ciąg — stąd musi być jednoznaczny.
SZKIC_ZNACZNIK = 'robots="noindex,nofollow", noindex=True,  # SZKIC'

KATEGORIE = {
    "Elektromechanika": "badge-blue",
    "Elektronika i magistrale": "badge-blue",
    "Klimatyzacja": "badge-green",
    "Spawanie & CNC": "badge-orange",
    "Programowanie i kursy": "badge-orange",
    "AI i automatyzacja": "badge-orange",
    "Druk 3D": "badge-green",
}

# Frazy, których model nie ma prawa wymyślić — dane firmowe, ceny, uprawnienia.
# Trafienie nie blokuje generowania, ale trafia do raportu przed przeglądem.
RYZYKOWNE = [
    (r"\b\d[\d\s]*\s*z[łl]\b", "kwota w złotych"),
    (r"\blat (?:doświadczenia|na rynku)\b", "staż firmy"),
    (r"\bcertyfikat|uprawnieni|ISO\s?9001|akredyt", "certyfikaty/uprawnienia"),
    (r"\bnasz zespół liczy|zatrudniamy\b", "dane kadrowe"),
    (r"\b\d+\s*(?:\+|tys\.?)\s*(?:zleceń|klientów|realizacji)", "statystyki firmy"),
    (r"\bgwarantujemy \d", "obietnice liczbowe"),
]

INSTRUKCJA = """\
Jesteś redaktorem technicznym bloga warsztatu F.W. DRUCIK (Domosław 13A, 06-120
Winnica, powiat pułtuski). Piszesz po polsku, rzeczowo, dla mechanika,
elektronika i technika utrzymania ruchu — nie dla copywritera.

ZASADY BEZWZGLĘDNE:
1. Nie wymyślasz żadnych faktów o firmie: cen, widełek cenowych, liczby zleceń,
   stażu, certyfikatów, uprawnień, nazwisk, marek posiadanego sprzętu.
   Dozwolone dane firmowe to wyłącznie: adres Domosław 13A, 06-120 Winnica,
   telefon 601 726 924, e-mail fwdrucik@gmail.com, NIP 888-292-19-00,
   godziny Pon-Pt 8-17 / Sob 9-13 i lista usług z serwisu.
2. Podajesz tylko wiedzę techniczną, którą da się zweryfikować w normie,
   nocie katalogowej albo dokumentacji producenta. Przy każdej liczbie
   (napięcie, ciśnienie, prędkość transmisji, rezystancja, temperatura)
   dopisujesz źródło typu normy lub zaznaczasz, że wartość jest orientacyjna
   i trzeba ją sprawdzić w danych serwisowych pojazdu/maszyny.
3. Czego nie wiesz na pewno — pomijasz. Lepiej krótszy wpis niż zmyślony.
   Nie podajesz konkretnych wartości serwisowych dla konkretnych modeli aut.
4. Bez marketingowego lania wody, bez wykrzykników, bez "rewolucyjny",
   "kompleksowy", "profesjonalizm na najwyższym poziomie".
5. Gdzie sensowne, wtrącasz ostrzeżenie BHP (czynniki chłodnicze, układy
   ciśnieniowe, akumulatory, prace pod napięciem, kody błędów kasowane
   bez usunięcia przyczyny).

FORMAT HTML w polu "html" każdej sekcji:
- dozwolone znaczniki: <p>, <ul>, <ol>, <li>, <strong>, <em>, <code>, <table>,
  <thead>, <tbody>, <tr>, <th>, <td>, <blockquote>, <h3>
- ZABRONIONE: <h1>, <h2> (nagłówek sekcji generuje szablon), <script>,
  <style>, atrybuty on*, linki do stron zewnętrznych
- linki wewnętrzne tylko do adresów z listy: /uslugi/elektromechanika/,
  /uslugi/klimatyzacja-samochodowa/, /uslugi/spawanie/, /uslugi/lutowanie-twarde/,
  /uslugi/remonty-silnikow/, /uslugi/maszyny-cnc/, /uslugi/druk-3d/,
  /uslugi/programowanie-aplikacje/, /uslugi/zywica-epoksydowa/, /kontakt/, /blog/
"""

SCHEMAT = {
    "type": "object",
    "properties": {
        "slug": {"type": "string"},
        "title_seo": {"type": "string"},
        "opis_seo": {"type": "string"},
        "tytul_h1": {"type": "string"},
        "kategoria": {"type": "string", "enum": list(KATEGORIE)},
        "minuty_czytania": {"type": "integer"},
        "lead": {"type": "string"},
        "excerpt": {"type": "string"},
        "sekcje": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "naglowek": {"type": "string"},
                    "html": {"type": "string"},
                },
                "required": ["id", "naglowek", "html"],
            },
        },
        "obraz_zapytanie": {"type": "string"},
        "obraz_podpis": {"type": "string"},
        "faq": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pytanie": {"type": "string"},
                    "odpowiedz": {"type": "string"},
                },
                "required": ["pytanie", "odpowiedz"],
            },
        },
    },
    "required": ["slug", "title_seo", "opis_seo", "tytul_h1", "kategoria",
                 "minuty_czytania", "lead", "excerpt", "sekcje", "faq",
                 "obraz_zapytanie", "obraz_podpis"],
}


# ------------------------------------------------------------------ narzędzia

def blad(tekst):
    print("BŁĄD:", tekst, file=sys.stderr)
    sys.exit(1)


def klucz_api():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if k:
        return k
    plik = os.path.join(os.path.expanduser("~"), ".claude", ".gemini-fwdrucik.json")
    if os.path.isfile(plik):
        with open(plik, encoding="utf-8") as f:
            k = (json.load(f).get("api_key") or "").strip()
        if k:
            return k
    blad("brak klucza — ustaw GEMINI_API_KEY albo utwórz ~/.claude/.gemini-fwdrucik.json")


def slugify(tekst):
    t = tekst.replace("ł", "l").replace("Ł", "L")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return re.sub(r"-{2,}", "-", t)[:70]


def czytaj(sciezka):
    with open(sciezka, encoding="utf-8") as f:
        return f.read()


def zapisz(sciezka, tresc):
    with open(sciezka, "w", encoding="utf-8", newline="\n") as f:
        f.write(tresc)


# ------------------------------------------------------------------ kolejka

def kolejka_wczytaj():
    """Zwraca listę (numer_linii, temat) niewykonanych pozycji z tematy.md."""
    if not os.path.isfile(KOLEJKA):
        return []
    wynik = []
    for i, linia in enumerate(czytaj(KOLEJKA).splitlines()):
        m = re.match(r"^-\s*\[( |x|X)\]\s*(.+?)\s*$", linia)
        if m and m.group(1) == " ":
            wynik.append((i, m.group(2)))
    return wynik


def kolejka_wczytaj_wg_dziedzin():
    """Grupuje niewykonane pozycje pod nagłówkiem `## dziedzina`, w tej samej
    kolejności co w pliku. Pozycje sprzed pierwszego nagłówka lądują w "".

    Do losowania między dziedzinami (--losowo) — bez grupowania kolejność
    w pliku decydowałaby o wszystkim i agent siedziałby w jednej sekcji,
    tak jak stało się to w praktyce: sześć wpisów z rzędu z jednej dziedziny.
    """
    if not os.path.isfile(KOLEJKA):
        return {}
    grupy, dziedzina = {}, ""
    for i, linia in enumerate(czytaj(KOLEJKA).splitlines()):
        naglowek = re.match(r"^##\s*(.+?)\s*$", linia)
        if naglowek:
            dziedzina = naglowek.group(1)
            continue
        m = re.match(r"^-\s*\[( |x|X)\]\s*(.+?)\s*$", linia)
        if m and m.group(1) == " ":
            grupy.setdefault(dziedzina, []).append((i, m.group(2)))
    return grupy


def kolejka_odhacz(numer_linii, slug):
    linie = czytaj(KOLEJKA).splitlines()
    dzis = datetime.date.today().isoformat()
    linie[numer_linii] = linie[numer_linii].replace("- [ ]", "- [x]", 1) + \
        f"  <!-- {dzis}, /blog/{slug}/ -->"
    zapisz(KOLEJKA, "\n".join(linie) + "\n")


# ------------------------------------------------------------------ Gemini

def gemini(temat, model, klucz, wskazowki=""):
    prompt = f"""Napisz wpis na blog techniczny F.W. DRUCIK na temat:

{temat}

{wskazowki}

Wymagania redakcyjne:
- 5-8 sekcji merytorycznych, każda z własnym id (krótkie, bez polskich znaków)
- KAŻDA sekcja po 250-350 słów w polu "html" — nie po dwa akapity. Łącznie
  1400-2000 słów. Krótszy wpis zostanie odesłany do rozbudowy, więc od razu
  pisz konkretami: wartości pomiarowe z jednostkami, kolejność czynności,
  typowe błędy i po czym je poznać, przykładowe objawy usterki
- gdzie temat na to pozwala, jedna sekcja z tabelą wartości albo listą kroków
  procedury
- ostatnia sekcja praktyczna: co z tym zrobić w warsztacie, z odesłaniem do
  właściwej podstrony usługi i do /kontakt/
- "title_seo" to zawartość znacznika <title>: maksymalnie 62 znaki razem
  z dopiskiem marki, więc trzymaj się 55 znaków na sam temat
- "opis_seo" maksymalnie 155 znaków
- "excerpt" 150-220 znaków, zajawka na listę wpisów
- 3-5 pytań w "faq", odpowiedzi po 2-4 zdania, czysty tekst bez HTML
- "slug" po polsku bez znaków diakrytycznych, myślniki, bez przedrostka "blog-"
- "obraz_zapytanie": 2-4 słowa PO ANGIELSKU opisujące zdjęcie ilustrujące temat,
  do wyszukania w Wikimedia Commons (np. "OBD-II connector", "TIG welding
  aluminium"). Rzecz konkretna i fotografowalna, nie pojęcie abstrakcyjne.
- "obraz_podpis": jedno zdanie po polsku pod zdjęcie — opis tego, co widać,
  powiązany z treścią wpisu. Bez nazwiska autora i licencji, te dopisuje skrypt.
"""
    ciało = {
        "systemInstruction": {"parts": [{"text": INSTRUKCJA}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.35,
            "responseMimeType": "application/json",
            "responseSchema": SCHEMAT,
        },
    }
    # Kody, przy których ponawiamy: przeciążenie modelu (503), limit zapytań
    # (429) i awarie po stronie bramy (500, 502, 504). Przebieg 31911098012
    # padł na "This model is currently experiencing high demand" — chwilowa
    # rzecz po stronie Google, która zabijała całą pracę agenta.
    PONAWIALNE = {429, 500, 502, 503, 504}
    PROBY = 4

    dane = None
    for proba in range(1, PROBY + 1):
        req = urllib.request.Request(
            API.format(model=model),
            data=json.dumps(ciało, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": klucz},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as odp:
                dane = json.loads(odp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            tresc = e.read().decode("utf-8", "replace")[:400]
            if e.code not in PONAWIALNE or proba == PROBY:
                blad(f"Gemini API {e.code}: {tresc}")
            czekaj = 2 ** proba * 5  # 10 s, 20 s, 40 s
            print(f"Gemini API {e.code} — ponawiam za {czekaj} s (próba {proba}/{PROBY - 1})")
            time.sleep(czekaj)
        except urllib.error.URLError as e:
            if proba == PROBY:
                blad(f"brak połączenia z Gemini API: {e.reason}")
            czekaj = 2 ** proba * 5
            print(f"Brak połączenia z Gemini API ({e.reason}) — ponawiam za {czekaj} s")
            time.sleep(czekaj)

    try:
        tekst = dane["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        blad(f"nieoczekiwana odpowiedź API: {json.dumps(dane)[:400]}")
    try:
        return json.loads(tekst)
    except json.JSONDecodeError as e:
        blad(f"model zwrócił niepoprawny JSON ({e})")


# ------------------------------------------------------------------ ilustracja

COMMONS = "https://commons.wikimedia.org/w/api.php"
OPENVERSE = "https://api.openverse.org/v1/images/"
PEXELS = "https://api.pexels.com/v1/search"
UA_COMMONS = "fwdrucik.pl-site-builder/1.0 (fwdrucik@gmail.com)"
LICENCJE_OK = ("cc0", "cc by", "cc by-sa", "public domain", "pd")
KLUCZ_PEXELS = os.path.expanduser(r"~\.claude\.pexels-fwdrucik.json")


def klucz_pexels():
    """Klucz Pexels ze zmiennej albo z pliku poza repozytorium. Brak klucza
    nie jest błędem — po prostu pomijamy to źródło."""
    k = os.environ.get("PEXELS_API_KEY", "").strip()
    if k:
        return k
    if os.path.isfile(KLUCZ_PEXELS):
        try:
            with open(KLUCZ_PEXELS, encoding="utf-8") as f:
                return json.load(f).get("api_key", "").strip()
        except Exception:
            return ""
    return ""


def _zapisz_obraz(url, slug, naglowki=None):
    """Pobiera plik i zapisuje w assets/blog/. Zwraca (nazwa, szer, wys)."""
    pg = _pomocnik_grafik()
    req = urllib.request.Request(url, headers=naglowki or {"User-Agent": UA_COMMONS})
    with urllib.request.urlopen(req, timeout=120) as odp:
        bajty = odp.read()
    rozszerzenie, szer, wys = pg.format_i_wymiary(bajty)
    if not szer or not wys:
        return None
    katalog = os.path.join(BASE, "assets", "blog")
    os.makedirs(katalog, exist_ok=True)
    nazwa = slug + rozszerzenie
    with open(os.path.join(katalog, nazwa), "wb") as f:
        f.write(bajty)
    return nazwa, szer, wys


def _pomocnik_grafik():
    """Ładuje pobierz-grafiki.py — nazwa z myślnikiem nie przechodzi importem."""
    import importlib.util
    sciezka = os.path.join(BASE, "pobierz-grafiki.py")
    spec = importlib.util.spec_from_file_location("pobierz_grafiki", sciezka)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def ilustracja(zapytanie, slug):
    """Szuka zdjęcia na licencji dopuszczającej użycie komercyjne, pobiera je
    do assets/blog/ i zwraca dane do podpisu.

    Źródła po kolei: Wikimedia Commons, Openverse, Pexels. Sam Commons bywa
    ubogi w tematy warsztatowe i zwracał „brak trafnego pliku", stąd dwa
    kolejne. Każde źródło oddaje wyłącznie materiał wolny komercyjnie i wraca
    z danymi do podpisu — bez autora i licencji nie publikujemy niczego.
    Brak wyniku nie jest błędem — wpis powstanie bez ilustracji."""
    if not zapytanie:
        return None
    for szukaj in (_szukaj_commons, _szukaj_openverse, _szukaj_pexels):
        try:
            obraz = szukaj(zapytanie, slug)
        except Exception as e:
            print(f"Źródło {szukaj.__name__} pominięte: {e}")
            continue
        if obraz:
            return obraz
    print("Ilustracja pominięta: brak trafnego pliku na dopuszczalnej licencji")
    return None


def _szukaj_commons(zapytanie, slug):
    pg = _pomocnik_grafik()
    adres = COMMONS + "?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": "filetype:bitmap " + zapytanie, "gsrnamespace": "6",
        "gsrlimit": "10", "prop": "imageinfo",
        "iiprop": "url|extmetadata", "iiurlwidth": "1200",
    })
    try:
        req = urllib.request.Request(adres, headers={"User-Agent": UA_COMMONS})
        with urllib.request.urlopen(req, timeout=60) as odp:
            dane = json.load(odp)
    except Exception as e:
        print(f"Ilustracja pominięta (wyszukiwanie): {e}")
        return None

    # Wyszukiwarka Commons potrafi zwrócić zdjęcie zupełnie niezwiązane z tematem
    # (np. zapytanie „car battery" trafiło kiedyś w „Battery Street Tunnel"
    # w Seattle — jedno wspólne słowo to za mało). Wymagamy więc, by pasowało
    # więcej niż jedno słowo zapytania, gdy zapytanie ma ich kilka.
    slowa = [s.lower() for s in re.findall(r"[A-Za-z0-9-]{3,}", zapytanie)]
    wymagane = min(2, len(slowa))

    for p in (dane.get("query", {}).get("pages") or {}).values():
        if "imageinfo" not in p:
            continue
        tytul = p["title"].lower()
        if slowa and sum(s in tytul for s in slowa) < wymagane:
            continue
        ii = p["imageinfo"][0]
        meta = ii["extmetadata"]
        licencja = pg.bez_html(meta.get("LicenseShortName", {}).get("value", ""))
        if not licencja.lower().startswith(LICENCJE_OK):
            continue
        try:
            zapis = _zapisz_obraz(ii["thumburl"], slug)
        except Exception:
            continue
        if not zapis:
            continue
        nazwa, szer, wys = zapis
        print(f"Ilustracja: {p['title']} ({licencja}, Wikimedia Commons)"
              " — sprawdź trafność przed scaleniem")
        return {
            "plik": f"/assets/blog/{nazwa}",
            "szerokosc": szer, "wysokosc": wys,
            "autor": pg.bez_html(meta.get("Artist", {}).get("value", "")) or "autor nieznany",
            "licencja": licencja,
            "licencja_url": meta.get("LicenseUrl", {}).get("value", ""),
            "strona": ii["descriptionurl"],
            "zrodlo": "Wikimedia Commons",
        }
    return None


def _szukaj_openverse(zapytanie, slug):
    """Openverse — wyszukiwarka Creative Commons po wielu serwisach naraz.

    `license_type=commercial,modification` zawęża wynik do licencji, które
    dopuszczają użycie komercyjne ORAZ przeróbki. Przeróbki są potrzebne,
    bo zdjęcie i tak skalujemy — przy licencji ND (bez utworów zależnych)
    samo przeskalowanie bywa uznawane za utwór zależny. Bez tego filtra
    API zwraca też zdjęcia NC (tylko niekomercyjne), a strona firmowa jest
    użyciem komercyjnym.
    """
    adres = OPENVERSE + "?" + urllib.parse.urlencode({
        "q": zapytanie,
        "license_type": "commercial,modification",
        "page_size": "10",
        "mature": "false",
    })
    req = urllib.request.Request(adres, headers={"User-Agent": UA_COMMONS})
    with urllib.request.urlopen(req, timeout=60) as odp:
        dane = json.load(odp)

    # Openverse zwraca wyniki posortowane wg trafności, ale bez żadnej
    # weryfikacji — pierwszy wynik bywał zupełnie nie na temat (np. zapytanie
    # o czujnik drgań trafiło w zdjęcie słupa energetycznego, bo oba mają
    # wspólny tag „maintenance"). Wymagamy więc, by tytuł lub tagi zawierały
    # więcej niż jedno słowo zapytania, gdy zapytanie ma ich kilka.
    slowa = [s.lower() for s in re.findall(r"[A-Za-z0-9-]{3,}", zapytanie)]
    wymagane = min(2, len(slowa))

    for w in dane.get("results", []):
        url = w.get("url")
        if not url:
            continue
        # Druga bramka poza filtrem API: gdyby kiedyś zmieniło się znaczenie
        # parametru albo odpowiedź przyszła z pamięci podręcznej, NC (tylko
        # niekomercyjne) i ND (bez przeróbek) nie mają prawa tu przejść.
        czlony = (w.get("license") or "").lower().split("-")
        if "nc" in czlony or "nd" in czlony:
            continue
        tekst = ((w.get("title") or "") + " " + " ".join(
            t.get("name", "") for t in (w.get("tags") or []) if isinstance(t, dict)
        )).lower()
        if slowa and sum(s in tekst for s in slowa) < wymagane:
            continue
        try:
            zapis = _zapisz_obraz(url, slug)
        except Exception:
            continue
        if not zapis:
            continue
        nazwa, szer, wys = zapis
        licencja = " ".join(x for x in ("CC", (w.get("license") or "").upper(),
                                        w.get("license_version") or "") if x).strip()
        print(f"Ilustracja: {w.get('title') or nazwa} ({licencja}, Openverse)"
              " — sprawdź trafność przed scaleniem")
        return {
            "plik": f"/assets/blog/{nazwa}",
            "szerokosc": szer, "wysokosc": wys,
            "autor": w.get("creator") or "autor nieznany",
            "licencja": licencja or "CC",
            "licencja_url": w.get("license_url") or "",
            "strona": w.get("foreign_landing_url") or url,
            "zrodlo": "Openverse",
        }
    return None


def _szukaj_pexels(zapytanie, slug):
    """Pexels — licencja pozwala na użycie komercyjne bez pytania o zgodę.

    Podpisu nie wymaga, ale i tak go dajemy: autor zdjęcia należy mu się
    tak samo jak przy CC, a czytelnik widzi, skąd wzięliśmy materiał.
    """
    klucz = klucz_pexels()
    if not klucz:
        return None
    adres = PEXELS + "?" + urllib.parse.urlencode({"query": zapytanie, "per_page": "10"})
    req = urllib.request.Request(adres, headers={
        "Authorization": klucz, "User-Agent": UA_COMMONS,
    })
    with urllib.request.urlopen(req, timeout=60) as odp:
        dane = json.load(odp)

    for f in dane.get("photos", []):
        url = (f.get("src") or {}).get("large") or (f.get("src") or {}).get("original")
        if not url:
            continue
        try:
            zapis = _zapisz_obraz(url, slug)
        except Exception:
            continue
        if not zapis:
            continue
        nazwa, szer, wys = zapis
        print(f"Ilustracja: {f.get('alt') or nazwa} (licencja Pexels)"
              " — sprawdź trafność przed scaleniem")
        return {
            "plik": f"/assets/blog/{nazwa}",
            "szerokosc": szer, "wysokosc": wys,
            "autor": f.get("photographer") or "autor nieznany",
            "licencja": "licencja Pexels",
            "licencja_url": "https://www.pexels.com/license/",
            "strona": f.get("url") or url,
            "zrodlo": "Pexels",
        }
    return None


def figure_html(obraz, podpis, alt):
    lic = obraz["licencja"]
    lic_html = (f'<a href="{obraz["licencja_url"]}" target="_blank" rel="noopener nofollow">{lic}</a>'
                if obraz["licencja_url"] else lic)
    # Nazwa serwisu jest częścią warunków licencji CC (wskazanie źródła),
    # więc bierzemy ją z danych obrazu — kiedyś była wpisana na sztywno
    # i po dołożeniu Openverse oraz Pexels podpisywałaby cudze zdjęcia
    # jako pochodzące z Wikimedia Commons.
    zrodlo = obraz.get("zrodlo", "Wikimedia Commons")
    return (
        '    <figure>\n'
        f'      <img src="{obraz["plik"]}" width="{obraz["szerokosc"]}" height="{obraz["wysokosc"]}"'
        f' loading="lazy" alt="{alt}">\n'
        f'      <figcaption>{podpis}\n'
        f'        <span class="zrodlo">Fot. <a href="{obraz["strona"]}" target="_blank" rel="noopener nofollow">'
        f'{obraz["autor"]}</a>, {lic_html}, {zrodlo}.</span>\n'
        '      </figcaption>\n'
        '    </figure>\n'
    )


# ------------------------------------------------------------------ kontrola

ZABRONIONE_ZNACZNIKI = re.compile(r"<\s*(script|style|iframe|h1|h2)\b", re.I)


LIMIT_TITLE = 62
LIMIT_DESC = 160


def popraw_limity_seo(w, temat, model, wskazowki):
    """Doprowadza title i description do limitów, których pilnuje sprawdz.py.

    Model regularnie przekracza 62 znaki w title (przebieg 31902904594: 68
    znaków). Wcześniej kończyło się to tak: agent wypisywał ostrzeżenie, brnął
    dalej, budował serwis i dopiero sprawdz.py przerywał pracę — po opłaceniu
    wywołania API i bez żadnego wpisu na wyjściu. Najpierw prosimy model o samo
    skrócenie (tanie, jedno pole), a gdy i to nie wejdzie w limit, ucinamy po
    granicy słowa. Lepszy krótszy tytuł niż stracony przebieg.
    """
    for pole, limit, etykieta in (("title_seo", LIMIT_TITLE, "title"),
                                  ("opis_seo", LIMIT_DESC, "description")):
        wartosc = (w.get(pole) or "").strip()
        if len(wartosc) <= limit:
            continue

        print(f"{etykieta} ma {len(wartosc)} znaków (limit {limit}) — proszę model o skrócenie")
        prosba = (
            f'Skróć poniższy {etykieta} wpisu o "{temat}" do maksymalnie {limit} znaków '
            f"razem ze spacjami. Zachowaj sens i słowa kluczowe, nie dodawaj cudzysłowów.\n\n"
            f"{wartosc}"
        )
        try:
            krotszy = (gemini_tekst(prosba, model) or "").strip().strip('"')
        except SystemExit:
            krotszy = ""
        if krotszy and len(krotszy) <= limit:
            print(f"   skrócony do {len(krotszy)} znaków")
            w[pole] = krotszy
            continue

        # Zapasowo: ucinamy po ostatniej spacji przed limitem, żeby nie zostawić
        # połowy wyrazu. Bez wielokropka — ten też liczy się do limitu.
        uciety = wartosc[:limit].rstrip()
        if " " in uciety:
            uciety = uciety[:uciety.rfind(" ")].rstrip(" -–—:,|")
        print(f"   model nie skrócił — ucinam do {len(uciety)} znaków")
        w[pole] = uciety
    return w


def gemini_tekst(prompt, model):
    """Jedno krótkie pytanie do modelu, odpowiedź jako czysty tekst.

    Osobno od gemini(), bo tamta funkcja wymusza JSON według schematu wpisu,
    a tu chodzi o jedną linijkę.
    """
    ciało = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }
    req = urllib.request.Request(
        API.format(model=model),
        data=json.dumps(ciało, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": klucz_api()},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as odp:
            dane = json.loads(odp.read().decode("utf-8"))
        return dane["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return ""


MIN_SLOW = 1100


def policz_slowa(w):
    """Slowa samej tresci sekcji — bez znacznikow, bez FAQ i leadu."""
    tekst = re.sub(r"<[^>]+>", " ", " ".join(s["html"] for s in w["sekcje"]))
    return len(tekst.split())


def poglebij_tresc(w, temat, model):
    """Dopisuje tresc, gdy model oddal wpis plytszy niz zamowiony.

    Prompt prosi o 1400-2000 slow, a wpisy wychodza po 600-700 — i to
    systematycznie, nie raz na jakis czas. Krotszy tekst przegrywa na tych
    samych frazach z artykulami konkurencji, wiec zamiast wierzyc promptowi
    sprawdzamy wynik i prosimy o rozwiniecie najkrotszych sekcji. Rozwiniecie,
    ktore nie przeszlo tych samych kontroli co tresc glowna, jest odrzucane —
    lepszy krotszy wpis niz wpis z wstrzyknietym znacznikiem.
    """
    slow = policz_slowa(w)
    if slow >= MIN_SLOW:
        print(f"Objetosc wpisu: {slow} slow — bez rozbudowy.")
        return w

    print(f"Objetosc wpisu: {slow} slow (cel {MIN_SLOW}) — rozwijam najkrotsze sekcje")
    for sekcja in sorted(w["sekcje"], key=lambda s: len(s["html"].split())):
        if policz_slowa(w) >= MIN_SLOW:
            break
        prosba = (
            f'Rozwin ponizsza sekcje wpisu o "{temat}", zatytulowana '
            f'"{sekcja["naglowek"]}", do 250-350 slow. Dopisz konkrety: wartosci '
            "pomiarowe z jednostkami, kolejnosc czynnosci, typowe bledy i ich objawy. "
            "Zachowaj sens tego, co juz jest. Zwroc WYLACZNIE HTML tej sekcji. "
            "Dozwolone znaczniki: p, ul, ol, li, table, thead, tbody, tr, th, td, "
            "h3, strong, em, code. Bez naglowka h2, bez blokow ``` i bez linkow "
            "poza adresami zaczynajacymi sie od ukosnika.\n\n"
            f"{sekcja['html']}"
        )
        rozwiniete = (gemini_tekst(prosba, model) or "").strip()
        rozwiniete = re.sub(r"^```(?:html)?\s*|\s*```$", "", rozwiniete).strip()
        etykieta = sekcja["naglowek"]
        if len(rozwiniete.split()) <= len(sekcja["html"].split()):
            print(f"   {etykieta}: model nie dolozyl tresci, zostawiam")
            continue
        if ZABRONIONE_ZNACZNIKI.search(rozwiniete) or re.search(r"\son[a-z]+\s*=", rozwiniete, re.I):
            print(f"   {etykieta}: odrzucone, zabroniony znacznik w odpowiedzi")
            continue
        if re.search(r'href\s*=\s*"(?!/)', rozwiniete):
            print(f"   {etykieta}: odrzucone, link poza serwis")
            continue
        sekcja["html"] = rozwiniete
        print(f"   {etykieta}: teraz {policz_slowa(w)} slow lacznie")

    koniec = policz_slowa(w)
    if koniec < MIN_SLOW:
        print(f"UWAGA: wpis ma {koniec} slow, ponizej celu {MIN_SLOW}.")
    # Czas czytania ma odpowiadac temu, co naprawde jest na stronie.
    w["minuty_czytania"] = max(3, round(koniec / 200))
    return w


def sprawdz_wpis(w):
    """Twarde błędy przerywają pracę, miękkie wracają jako lista ostrzeżeń."""
    if not w.get("sekcje"):
        blad("model nie zwrócił żadnej sekcji")

    cały = " ".join(s["html"] for s in w["sekcje"])
    if ZABRONIONE_ZNACZNIKI.search(cały):
        blad("treść zawiera zabroniony znacznik (script/style/iframe/h1/h2)")
    if re.search(r"\son[a-z]+\s*=", cały, re.I):
        blad("treść zawiera atrybut zdarzenia on*")
    if re.search(r'href\s*=\s*"(?!/)', cały):
        blad("treść zawiera link zewnętrzny — dozwolone tylko adresy z /")

    ostrzezenia = []
    tytul = w["title_seo"].strip()
    if len(tytul) > 62:
        ostrzezenia.append(f"title ma {len(tytul)} znaków — sprawdz.py wymaga max 62")
    if len(w["opis_seo"].strip()) > 160:
        ostrzezenia.append(f"description ma {len(w['opis_seo'].strip())} znaków — max 160")

    do_skanu = cały + " " + w["lead"] + " " + " ".join(f["odpowiedz"] for f in w.get("faq", []))
    for wzor, opis in RYZYKOWNE:
        for trafienie in re.findall(wzor, do_skanu, re.I):
            ostrzezenia.append(f"do weryfikacji ({opis}): {str(trafienie)[:60]}")
    return ostrzezenia


# ------------------------------------------------------------------ szablony

def render_wpis(w, slug, data_iso, data_pl, obraz=None):
    kat = w["kategoria"]
    badge = KATEGORIE.get(kat, "badge-blue")
    url = f"/blog/{slug}/"

    ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": w["tytul_h1"],
        "description": w["opis_seo"],
        "author": {"@type": "Organization", "name": "F.W. DRUCIK"},
        "publisher": {
            "@type": "Organization", "name": "F.W. DRUCIK",
            "logo": {"@type": "ImageObject", "url": "https://fwdrucik.pl/assets/favicon.png"},
        },
        "datePublished": data_iso,
        "dateModified": data_iso,
        "inLanguage": "pl-PL",
        "mainEntityOfPage": "https://fwdrucik.pl" + url,
    }

    toc = "\n".join(
        f'      <li><a href="#{s["id"]}">{s["naglowek"]}</a></li>' for s in w["sekcje"]
    )
    czesci = []
    for i, s in enumerate(w["sekcje"], start=1):
        czesci.append(f'    <h2 id="{s["id"]}">{i}. {s["naglowek"]}</h2>\n{s["html"]}')
        # ilustracja po pierwszej sekcji — nad zwięzłym wstępem wygląda gorzej
        if i == 1 and obraz:
            czesci.append(figure_html(obraz, w.get("obraz_podpis", ""), w["tytul_h1"]))
    sekcje = "\n\n".join(czesci)
    faq = ""
    if w.get("faq"):
        pozycje = "\n".join(
            f'      <details>\n'
            f'        <summary>{f["pytanie"]}</summary>\n'
            f'        <p>{f["odpowiedz"]}</p>\n'
            f'      </details>'
            for f in w["faq"]
        )
        faq = (f'\n    <h2 id="faq">Najczęstsze pytania</h2>\n'
               f'    <div class="faq">\n{pozycje}\n    </div>\n')

    return f"""<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=2)}
</script>

<article class="article-container" style="padding:60px 24px;">
  <header style="margin-bottom:30px;">
    <div style="display:flex;gap:12px;align-items:center;margin-bottom:12px;flex-wrap:wrap;">
      <span class="badge {badge}">{kat}</span>
      <span style="color:var(--muted);font-size:0.88rem;">⏱️ {w['minuty_czytania']} min czytania</span>
      <span style="color:var(--muted);font-size:0.88rem;">📅 {data_pl}</span>
    </div>
    <h1 style="font-size:clamp(1.8rem,3.5vw,2.6rem);color:#fff;line-height:1.15;margin-bottom:16px;">{w['tytul_h1']}</h1>
    <p class="lead" style="color:var(--metal-light);font-size:1.1rem;">{w['lead']}</p>
  </header>

  <div class="toc-box">
    <div class="toc-title">📍 Spis treści</div>
    <ol class="toc-list">
{toc}
    </ol>
  </div>

  <div id="blog-full-content" class="article-body">
{sekcje}
{faq}  </div>

  <section class="comments-section">
    <h2 style="font-size:1.4rem;color:#fff;margin-bottom:20px;">💬 Komentarze czytelników</h2>
    <div id="comments-list"></div>
    <form id="comment-form" style="margin-top:24px;">
      <div style="margin-bottom:12px;">
        <textarea id="comment-text" class="form-control" rows="3" placeholder="Napisz komentarz lub zadaj pytanie..." required></textarea>
      </div>
      <button type="submit" class="btn btn-primary">Wyślij komentarz</button>
    </form>
  </section>
</article>
"""


def okruszek_z_tytulu(tytul):
    """Krotka etykieta do okruszkow nawigacyjnych.

    Google pokazuje okruszki w wyniku wyszukiwania, wiec ucinanie tytulu na
    sztywno wypuszczalo w swiat etykiety typu "Retrofit starej frezarki na
    sterowanie CNC -...". Bierzemy czlon przed myslnikiem albo dwukropkiem —
    to zwykle jest wlasciwy temat — i dopiero gdy nadal jest za dlugi, tniemy
    na granicy slowa, bez wielokropka.
    """
    etykieta = re.split(r"\s+[—–-]\s+|:\s+", tytul, maxsplit=1)[0].strip()
    if len(etykieta) > 48:
        etykieta = etykieta[:48].rsplit(" ", 1)[0].rstrip(" ,;")
    return etykieta or tytul[:48]


def wpis_pages(w, slug, plik, szkic=False):
    url = f"/blog/{slug}/"
    okruszek = okruszek_z_tytulu(w["tytul_h1"])
    # Szkic zostaje wygenerowany i wysłany na serwer, ale ma być niewidoczny:
    # noindex=True wycina go z sitemap.xml, robots blokuje wyszukiwarki,
    # a karty na /blog/ po prostu jeszcze nie ma. Linia ze SZKIC_ZNACZNIK
    # znika przy akceptacji — to ona odróżnia szkic od wpisu opublikowanego.
    linia_szkicu = f"\n        {SZKIC_ZNACZNIK}" if szkic else ""
    return f"""    strona(
        "{url}", "{plik}",
        {json.dumps(w['title_seo'].strip(), ensure_ascii=False)},
        {json.dumps(w['opis_seo'].strip(), ensure_ascii=False)},
        okruszki=[("Blog", "/blog/"), ({json.dumps(okruszek, ensure_ascii=False)}, "{url}")],
        priority="0.8", og_type="article",{linia_szkicu}
    ),

"""


def karta_bloga(w, slug, data_pl):
    badge = KATEGORIE.get(w["kategoria"], "badge-blue")
    url = f"/blog/{slug}/"
    return f"""      <article class="blog-card card-glow">
        <div class="blog-card-body">
          <div>
            <div class="blog-card-meta">
              <span class="badge {badge}">{w['kategoria']}</span>
              <span>⏱️ {w['minuty_czytania']} min czytania</span>
              <span>📅 {data_pl}</span>
            </div>
            <h3 class="blog-card-title"><a href="{url}">{w['tytul_h1']}</a></h3>
            <p class="blog-card-excerpt">{w['excerpt']}</p>
          </div>
          <div style="margin-top:20px;">
            <a href="{url}" class="btn btn-primary" style="width:100%;justify-content:center;">Czytaj pełny artykuł →</a>
          </div>
        </div>
      </article>

"""


def wstaw_przed(sciezka, marker, tekst):
    tresc = czytaj(sciezka)
    if marker not in tresc:
        blad(f"brak znacznika w {os.path.basename(sciezka)}: {marker}")
    zapisz(sciezka, tresc.replace(marker, tekst + marker, 1))


# --------------------------------------------------------- szkice i decyzje

def sciezka_karty(slug):
    """Karta na /blog/ czeka tu, dopóki wpis nie zostanie zaakceptowany."""
    return os.path.join(SZKICE, f"{slug}.karta.html")


def granice_wpisu(tresc, slug):
    """Zakres bloku strona(...) danego wpisu w pages.py albo None."""
    znacznik = tresc.find(f'"/blog/{slug}/", "blog-')
    if znacznik == -1:
        return None
    poczatek = tresc.rfind("    strona(", 0, znacznik)
    koniec = tresc.find("    ),\n", znacznik)
    if poczatek == -1 or koniec == -1:
        return None
    koniec += len("    ),\n")
    # Blok kończy się pustą linią — zabieramy ją razem z nim.
    if tresc[koniec:koniec + 1] == "\n":
        koniec += 1
    return poczatek, koniec


def publikuj(slug):
    """Zdejmuje ze wpisu status szkicu: noindex znika, karta wchodzi na /blog/."""
    tresc = czytaj(PAGES)
    zakres = granice_wpisu(tresc, slug)
    if zakres is None:
        blad(f"nie znalazłem wpisu {slug} w pages.py")
    poczatek, koniec = zakres
    blok = tresc[poczatek:koniec]
    if SZKIC_ZNACZNIK not in blok:
        print(f"Wpis {slug} nie jest szkicem — pomijam zmianę w pages.py.")
    else:
        zapisz(PAGES, tresc[:poczatek]
               + blok.replace("\n        " + SZKIC_ZNACZNIK, "", 1)
               + tresc[koniec:])

    karta = sciezka_karty(slug)
    if os.path.exists(karta):
        wstaw_przed(BLOG_INDEX, MARKER_BLOG, czytaj(karta))
        os.remove(karta)
        print(f"Karta wpisu {slug} wstawiona na /blog/.")
    else:
        print(f"Brak karty szkicu dla {slug} — /blog/ bez zmian.")


def wytnij_karte(slug):
    """Wycina kartę wpisu z /blog/ i zwraca jej HTML (None, gdy karty tam nie ma)."""
    tresc_bloga = czytaj(BLOG_INDEX)
    odnosnik = tresc_bloga.find(f'href="/blog/{slug}/"')
    if odnosnik == -1:
        return None
    poczatek = tresc_bloga.rfind("      <article", 0, odnosnik)
    koniec = tresc_bloga.find("</article>", odnosnik)
    if poczatek == -1 or koniec == -1:
        print("UWAGA: nie rozpoznałem granic karty — sprawdź src/blog.html.")
        return None
    koniec += len("</article>\n")
    if tresc_bloga[koniec:koniec + 1] == "\n":
        koniec += 1
    zapisz(BLOG_INDEX, tresc_bloga[:poczatek] + tresc_bloga[koniec:])
    return tresc_bloga[poczatek:koniec]


def ukryj(slug):
    """Cofa opublikowany wpis do szkicu: noindex, bez karty na /blog/, adres zostaje.

    Odwrotność publikuj() — ten sam znacznik i ta sama karta w szkice/, więc
    przywrócenie idzie zwykłą ścieżką publikacji.
    """
    tresc = czytaj(PAGES)
    zakres = granice_wpisu(tresc, slug)
    if zakres is None:
        blad(f"nie znalazłem wpisu {slug} w pages.py")
    poczatek, koniec = zakres
    blok = tresc[poczatek:koniec]
    if "noindex=" in blok:
        print(f"Wpis {slug} jest już niewidoczny — pomijam zmianę w pages.py.")
    else:
        zamkniecie = blok.rfind("\n    ),")
        zapisz(PAGES, tresc[:poczatek] + blok[:zamkniecie] + "\n        " + SZKIC_ZNACZNIK
               + blok[zamkniecie:] + tresc[koniec:])

    karta = wytnij_karte(slug)
    if karta is not None:
        os.makedirs(SZKICE, exist_ok=True)
        zapisz(sciezka_karty(slug), karta)
        print(f"Karta wpisu {slug} zdjęta z /blog/ do szkice/.")


def odrzuc(slug):
    """Kasuje wpis z repozytorium. Zwraca ścieżki do skasowania na serwerze."""
    tresc = czytaj(PAGES)
    zakres = granice_wpisu(tresc, slug)
    # Wpisy pisane ręcznie mają plik źródłowy nazwany inaczej niż slug
    # (blog-regeneracja-alternatorow.html dla regeneracji-...-pultusk).
    plik_src = f"blog-{slug}.html"
    if zakres is not None:
        poczatek, koniec = zakres
        trafienie = re.search(r'"(blog-[a-z0-9-]+\.html)"', tresc[poczatek:koniec])
        if trafienie:
            plik_src = trafienie.group(1)
        zapisz(PAGES, tresc[:poczatek] + tresc[koniec:])
        print(f"Wpis {slug} usunięty z pages.py.")

    zdalne = [f"blog/{slug}/index.html"]
    do_kasacji = [os.path.join(SRC, plik_src), sciezka_karty(slug)]
    katalog_grafik = os.path.join(BASE, "assets", "blog")
    if os.path.isdir(katalog_grafik):
        for nazwa in os.listdir(katalog_grafik):
            if nazwa.startswith(slug + "."):
                do_kasacji.append(os.path.join(katalog_grafik, nazwa))
                zdalne.append(f"assets/blog/{nazwa}")

    for sciezka in do_kasacji:
        if os.path.exists(sciezka):
            os.remove(sciezka)
            print("usunięto:", os.path.relpath(sciezka, BASE).replace("\\", "/"))

    # Karta mogła już trafić na /blog/, jeśli wpis wcześniej zaakceptowano.
    if wytnij_karte(slug) is not None:
        print(f"Karta wpisu {slug} usunięta z /blog/.")

    return zdalne


# ------------------------------------------------------------------ build/git

def uruchom(polecenie, opis):
    print(f"→ {opis}")
    wynik = subprocess.run(polecenie, cwd=BASE, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    if wynik.stdout.strip():
        print(wynik.stdout.strip())
    if wynik.returncode != 0:
        if wynik.stderr.strip():
            print(wynik.stderr.strip(), file=sys.stderr)
        blad(f"{opis} zakończone kodem {wynik.returncode} — nic nie publikuję")
    return wynik.stdout


def git(*argumenty):
    return uruchom(["git", *argumenty], "git " + " ".join(argumenty))


# ------------------------------------------------------------------ główna

def main():
    ap = argparse.ArgumentParser(description="Agent bloga fwdrucik.pl")
    ap.add_argument("--temat", help="temat wpisu; bez tego brany pierwszy z tematy.md")
    ap.add_argument("--losowo", action="store_true",
                    help="losuj dziedzinę (nagłówek ## w tematy.md), a w niej pierwszy temat, "
                         "zamiast zawsze brać pierwszy wolny wiersz pliku")
    ap.add_argument("--wskazowki", default="", help="dodatkowe wytyczne do promptu")
    ap.add_argument("--model", default=MODEL_DOMYSLNY)
    ap.add_argument("--bez-gita", action="store_true", help="nie zakładaj gałęzi ani commita")
    ap.add_argument("--bez-pusha", action="store_true", help="commit lokalnie, bez push")
    ap.add_argument("--szkic", action="store_true",
                    help="wpis jako szkic (noindex, bez karty na /blog/), commit na bieżącą gałąź")
    ap.add_argument("--publikuj", metavar="SLUG", help="zdejmij ze wpisu status szkicu")
    ap.add_argument("--odrzuc", metavar="SLUG", help="skasuj szkic z repozytorium")
    ap.add_argument("--ukryj", metavar="SLUG", help="cofnij opublikowany wpis do szkicu")
    args = ap.parse_args()

    # Tryby decyzji: wołane przez workflow po kliknięciu w panelu admina.
    if args.publikuj or args.odrzuc or args.ukryj:
        slug = slugify(args.publikuj or args.odrzuc or args.ukryj)
        if args.publikuj:
            publikuj(slug)
            opis = f"Publikacja wpisu: {slug}"
        elif args.ukryj:
            ukryj(slug)
            opis = f"Ukrycie wpisu: {slug}"
        else:
            zdalne = odrzuc(slug)
            zapisz(os.path.join(BASE, ".do-skasowania.txt"), "\n".join(zdalne) + "\n")
            opis = f"Odrzucenie wpisu: {slug}"

        uruchom([sys.executable, "build.py"], "build.py")
        # Kontrola zawężona do tego wpisu: zastana usterka gdzie indziej
        # w serwisie nie ma prawa wywrócić publikacji jednego szkicu.
        uruchom([sys.executable, "sprawdz.py", "--tylko", slug],
                f"sprawdz.py --tylko {slug}")

        if not args.bez_gita:
            # -A bez listy ścieżek: przy odrzuceniu znikają pliki, których
            # nazw nie znamy z góry (grafika wpisu, karta ze szkice/).
            git("add", "-A")
            # Powtórna akceptacja tego samego wpisu w panelu nie zmienia już
            # niczego w repozytorium, a `git commit` bez zmian kończy się
            # kodem 1 i cały przebieg szedł na czerwono z mailem o awarii.
            # To nie jest błąd — wpis po prostu jest opublikowany.
            if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=BASE).returncode == 0:
                print("Brak zmian do zapisania — wpis był już opublikowany.")
                print("\nGotowe:", opis)
                return
            git("commit", "-m", opis)
            if not args.bez_pusha:
                git("push")
        print("\nGotowe:", opis)
        return

    temat, linia_kolejki = args.temat, None
    if temat:
        # Temat podany z ręki potrafi być dokładnie tą samą pozycją, co w
        # kolejce. Bez odhaczenia zostawał jako wolny i harmonogram trafiał
        # na niego ponownie — wtedy agent przerywał pracę na „plik już
        # istnieje" (przebieg 31913732360).
        for numer, pozycja in kolejka_wczytaj():
            if pozycja.strip() == temat.strip():
                linia_kolejki = numer
                print("Temat pokrywa się z pozycją w kolejce — zostanie odhaczony.")
                break
    if not temat and args.losowo:
        grupy = kolejka_wczytaj_wg_dziedzin()
        if not grupy:
            print("Kolejka tematy.md pusta — nic do zrobienia.")
            return
        # Losowanie ważone liczbą wolnych tematów: dziedzina z 70 pozycjami
        # wypada mniej więcej 70 razy częściej niż ta z jedną. Przy losowaniu
        # równym mała sekcja miała tę samą szansę co największa, więc wyczerpane
        # dziedziny znikały szybko, a proporcje bloga rozjeżdżały się z tym,
        # ile materiału faktycznie na dany temat przygotowano.
        dziedziny = list(grupy.keys())
        wagi = [len(grupy[d]) for d in dziedziny]
        dziedzina = random.choices(dziedziny, weights=wagi, k=1)[0]
        linia_kolejki, temat = grupy[dziedzina][0]
        szansa = 100 * len(grupy[dziedzina]) / sum(wagi)
        print(f"Dziedzina (losowo, waga {len(grupy[dziedzina])}/{sum(wagi)}"
              f" = {szansa:.1f}%): {dziedzina}")
    elif not temat:
        oczekujace = kolejka_wczytaj()
        if not oczekujace:
            print("Kolejka tematy.md pusta — nic do zrobienia.")
            return
        linia_kolejki, temat = oczekujace[0]
    print(f"Temat: {temat}")

    w = gemini(temat, args.model, klucz_api(), args.wskazowki)
    w = poglebij_tresc(w, temat, args.model)
    w = popraw_limity_seo(w, temat, args.model, args.wskazowki)
    ostrzezenia = sprawdz_wpis(w)

    slug = slugify(w["slug"] or w["tytul_h1"])
    plik = f"blog-{slug}.html"
    if os.path.exists(os.path.join(SRC, plik)):
        # Wpis o tym adresie już powstał. Jeśli temat przyszedł z kolejki,
        # odhaczamy go — inaczej agent uruchamiany z harmonogramu wracałby
        # na tę samą pozycję przy każdym przebiegu i za każdym razem padał.
        if linia_kolejki is not None:
            kolejka_odhacz(linia_kolejki, slug)
            print(f"Pozycja w kolejce odhaczona — wpis src/{plik} już istnieje.")
        blad(f"plik src/{plik} już istnieje — zmień temat albo usuń stary wpis")

    obraz = ilustracja(w.get("obraz_zapytanie", ""), slug)
    dzis = datetime.date.today()
    zapisz(os.path.join(SRC, plik),
           render_wpis(w, slug, dzis.isoformat(), dzis.strftime("%d.%m.%Y"), obraz))
    wstaw_przed(PAGES, MARKER_PAGES, wpis_pages(w, slug, plik, szkic=args.szkic))
    karta = karta_bloga(w, slug, dzis.strftime("%d.%m.%Y"))
    if args.szkic:
        # Karta czeka w szkice/ na akceptację — do tego czasu wpisu nie ma
        # ani na /blog/, ani w sitemapie, choć plik leży już na serwerze.
        os.makedirs(SZKICE, exist_ok=True)
        zapisz(sciezka_karty(slug), karta)
        print(f"Zapisano src/{plik} i wpis w pages.py jako SZKIC (bez karty na /blog/)")
    else:
        wstaw_przed(BLOG_INDEX, MARKER_BLOG, karta)
        print(f"Zapisano src/{plik}, wpis w pages.py i kartę na /blog/")

    uruchom([sys.executable, "build.py"], "build.py")
    uruchom([sys.executable, "sprawdz.py", "--tylko", slug],
            f"sprawdz.py --tylko {slug}")

    # Raport dla workflow: z tego powstaje zgłoszenie do api/wpisy.php.
    zapisz(os.path.join(BASE, ".ostatni-wpis.json"), json.dumps({
        "slug": slug,
        "tytul": w["tytul_h1"],
        "lead": w["excerpt"],
        "url": f"/blog/{slug}/",
        "szkic": bool(args.szkic),
    }, ensure_ascii=False, indent=1))

    if not args.bez_gita:
        if linia_kolejki is not None:
            kolejka_odhacz(linia_kolejki, slug)
        # daty.json trzyma rejestr dat modyfikacji do sitemapy — bez niego
        # kolejna budowa uznalaby wszystkie strony za zmienione dzisiaj.
        pliki = [f"src/{plik}", "pages.py", "src/blog.html", "assets/blog", "dist",
                 "daty.json",
                 *(["szkice"] if args.szkic else []),
                 *(["tematy.md"] if linia_kolejki is not None else [])]
        if args.szkic:
            # Szkic idzie prosto na bieżącą gałąź (main) — przeglądem jest
            # akceptacja w panelu, nie Pull Request.
            git("add", *pliki)
            git("commit", "-m", f"Szkic wpisu: {w['tytul_h1']}")
            if not args.bez_pusha:
                git("push")
            print("\nGotowe. Szkic czeka na akceptację w panelu.")
        else:
            galaz = f"blog/{slug}"
            git("switch", "-c", galaz)
            git("add", *pliki)
            git("commit", "-m", f"Wpis na blog: {w['tytul_h1']}")
            if not args.bez_pusha:
                git("push", "-u", "origin", galaz)
            print(f"\nGotowe. Gałąź {galaz} czeka na przegląd.")
    elif linia_kolejki is not None:
        kolejka_odhacz(linia_kolejki, slug)

    if ostrzezenia:
        print("\nDO SPRAWDZENIA PRZED SCALENIEM:")
        for o in ostrzezenia:
            print(" -", o)


if __name__ == "__main__":
    main()
