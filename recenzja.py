# -*- coding: utf-8 -*-
"""
Agent kontroli treści — recenzuje szkic wpisu przed automatyczną publikacją.

Po co: gdy kolejka akceptacji urośnie do progu, `autopublikuj.py` publikuje
najstarszy szkic bez udziału człowieka. Tekstu, którego nikt nie przeczytał,
nie wypuszczamy na produkcję na słowo modelu, który go napisał — najpierw
przechodzi przez dwie niezależne warstwy kontroli:

  1. Warstwa deterministyczna (bez modelu): dozwolone znaczniki, brak atrybutów
     zdarzeń, linki wyłącznie względne, domknięte listy i tabele, minimalna
     objętość, brak pustych sekcji.
  2. Warstwa merytoryczna (Gemini): sekcja po sekcji szuka błędów rzeczowych —
     złych wartości z jednostkami, sprzeczności wewnątrz tekstu, wymyślonych
     norm i oznaczeń, mylących zaleceń warsztatowych — i zwraca poprawiony HTML.

Poprawka modelu wchodzi do pliku tylko wtedy, gdy sama przejdzie warstwę
deterministyczną i nie utnie sekcji poniżej 60% objętości. Model „poprawiający"
przez skracanie to najczęstszy sposób, w jaki taka pętla psuje dobry tekst.

Jak użyć:

    py recenzja.py SLUG              raport, nic nie zapisuje
    py recenzja.py SLUG --popraw     wpuszcza przyjęte poprawki do src/
    py recenzja.py SLUG --model gemini-3.1-flash

Kod wyjścia:
    0 — wpis nadaje się do publikacji (czysty albo poprawiony)
    1 — zostały twarde błędy, wpis NIE nadaje się do publikacji
    2 — błąd użycia (brak pliku, zły slug)

Raport ląduje w `.ostatnia-recenzja.json` — czyta go `autopublikuj.py`,
żeby mieć co wpisać do notatki w panelu.

Klucz Gemini bierze tak samo jak agent bloga: ze zmiennej GEMINI_API_KEY,
a lokalnie z pliku poza repozytorium.
"""

import argparse
import importlib.util
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

for _strumien in (sys.stdout, sys.stderr):
    if hasattr(_strumien, "reconfigure"):
        _strumien.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "src")
RAPORT = os.path.join(BASE, ".ostatnia-recenzja.json")

MODEL_DOMYSLNY = "gemini-3.1-flash-lite"
# Model, na ktorym pisze agent bloga — sprawdzony na tym kluczu. Sluzy za
# zapasowy, gdy nazwa modelu recenzenta okaze sie na kluczu niedostepna.
MODEL_ZAPASOWY = "gemini-3.1-flash-lite"
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
PONAWIALNE = (429, 500, 502, 503, 504)
PROBY = 4

# Treść wpisu ma być tekstem, nie aplikacją. Ta sama lista co w agencie bloga —
# tam pilnuje świeżo napisanego wpisu, tu poprawek wracających od modelu.
ZABRONIONE = re.compile(r"<\s*(script|style|iframe|h1|h2|form|input|button)\b", re.I)
ZDARZENIA = re.compile(r"\son[a-z]+\s*=", re.I)
LINK_ZEWNETRZNY = re.compile(r'href\s*=\s*"(?!/)')

# Znaczniki, których niedomknięcie rozjeżdża układ strony. `img`, `br` i `hr`
# są puste z definicji, więc ich tu nie ma.
PAROWANE = ("p", "ul", "ol", "li", "table", "thead", "tbody", "tr", "th", "td",
            "h3", "strong", "em", "code", "figure", "figcaption")

MIN_SLOW_WPISU = 900
MIN_SLOW_SEKCJI = 40
# Poprawka krótsza niż tyle części oryginału to nie poprawka, tylko skrót.
PROG_SKROCENIA = 0.6
RUNDY = 2

POCZATEK_TRESCI = '<div id="blog-full-content" class="article-body">'
KONIEC_TRESCI = '<section class="comments-section">'


def blad_uzycia(tekst):
    print("BŁĄD:", tekst, file=sys.stderr)
    sys.exit(2)


def agent_bloga():
    """Agent bloga jako moduł — dla klucza API i pojedynczego pytania do modelu.

    Myślnik w nazwie pliku wyklucza zwykły import, więc ładujemy go ze ścieżki,
    tak samo jak `dopublikuj.py` ładuje `zglos-zalegle.py`.
    """
    sciezka = os.path.join(BASE, "agent-bloga.py")
    spec = importlib.util.spec_from_file_location("agent_bloga", sciezka)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def czytaj(sciezka):
    return io.open(sciezka, encoding="utf-8").read()


def zapisz(sciezka, tresc):
    io.open(sciezka, "w", encoding="utf-8", newline="\n").write(tresc)


def slow(html):
    return len(re.sub(r"<[^>]+>", " ", html).split())


# --------------------------------------------------- warstwa deterministyczna

def usterki_html(html, etykieta):
    """Twarde błędy w kawałku treści. Pusta lista = kawałek jest w porządku."""
    problemy = []
    if ZABRONIONE.search(html):
        problemy.append(f"{etykieta}: zabroniony znacznik (script/style/iframe/h1/h2/form)")
    if ZDARZENIA.search(html):
        problemy.append(f"{etykieta}: atrybut zdarzenia on*")
    if LINK_ZEWNETRZNY.search(html):
        problemy.append(f"{etykieta}: link poza serwis — dozwolone tylko adresy od /")
    for znacznik in PAROWANE:
        otwarcia = len(re.findall(rf"<{znacznik}\b", html, re.I))
        zamkniecia = len(re.findall(rf"</{znacznik}\s*>", html, re.I))
        if otwarcia != zamkniecia:
            problemy.append(
                f"{etykieta}: niedomknięty <{znacznik}> ({otwarcia} otwarć, {zamkniecia} zamknięć)")
    if "```" in html:
        problemy.append(f"{etykieta}: blok ``` z odpowiedzi modelu")
    return problemy


def sekcje_wpisu(strona):
    """Sekcje treści: (id, numer, nagłówek, html, początek, koniec).

    Wycinamy dokładnie ten fragment, który agent bloga wstawił między nagłówki
    H2 — bez FAQ i bez sekcji komentarzy, których model nie ma prawa ruszać.
    """
    start = strona.find(POCZATEK_TRESCI)
    if start < 0:
        blad_uzycia("nie znalazłem bloku treści wpisu — czy to na pewno plik wpisu?")
    koniec_tresci = strona.find(KONIEC_TRESCI, start)
    if koniec_tresci < 0:
        koniec_tresci = len(strona)

    naglowki = list(re.finditer(r'\n    <h2 id="([^"]+)">(?:(\d+)\.\s*)?([^<]+)</h2>\n',
                                strona[start:koniec_tresci]))
    wynik = []
    for i, m in enumerate(naglowki):
        if m.group(1) == "faq":
            continue
        poczatek = start + m.end()
        nast = start + naglowki[i + 1].start() if i + 1 < len(naglowki) else koniec_tresci
        wynik.append({
            "id": m.group(1),
            "numer": m.group(2) or str(i + 1),
            "naglowek": m.group(3).strip(),
            "html": strona[poczatek:nast].rstrip(),
            "poczatek": poczatek,
            "koniec": nast,
        })
    return wynik


def rozdziel_ilustracje(html):
    """Rozdziela treść sekcji na tekst i bloki <figure>.

    Ilustracja ma podpis z licencją CC — jej brzmienie jest warunkiem legalnego
    użycia zdjęcia, więc model nie dostaje jej do ręki i nie może jej przepisać.
    """
    figury = list(re.finditer(r"(?s)\s*<figure>.*?</figure>", html))
    tekst = html
    for m in reversed(figury):
        tekst = tekst[:m.start()] + tekst[m.end():]
    return tekst.strip(), [m.group(0) for m in figury]


def kontrola_deterministyczna(sekcje, strona):
    problemy = []
    for s in sekcje:
        tekst, _ = rozdziel_ilustracje(s["html"])
        etykieta = f'sekcja „{s["naglowek"]}"'
        problemy += usterki_html(tekst, etykieta)
        if slow(tekst) < MIN_SLOW_SEKCJI:
            problemy.append(f"{etykieta}: pusta albo szczątkowa ({slow(tekst)} słów)")
    lacznie = sum(slow(rozdziel_ilustracje(s["html"])[0]) for s in sekcje)
    if lacznie < MIN_SLOW_WPISU:
        problemy.append(f"cały wpis: {lacznie} słów, minimum {MIN_SLOW_WPISU}")
    if not sekcje:
        problemy.append("wpis nie ma ani jednej sekcji treści")
    if "<h1" not in strona:
        problemy.append("wpis bez nagłówka H1")
    return problemy


# ------------------------------------------------------ warstwa merytoryczna

PROMPT = """Jesteś redaktorem technicznym w warsztacie mechaniki i elektroniki
pojazdowej. Sprawdzasz sekcję artykułu na blogu firmowym.

Szukasz wyłącznie błędów rzeczowych i redakcyjnych:
- wartości liczbowych i jednostek, które są nieprawdziwe albo niemożliwe,
- sprzeczności wewnątrz tekstu,
- wymyślonych norm, oznaczeń, nazw części i standardów,
- zaleceń warsztatowych, które są niebezpieczne albo prowadzą do uszkodzenia,
- zdań niezrozumiałych, urwanych albo powtórzonych.

Nie zmieniaj stylu, nie skracaj tekstu, nie usuwaj akapitów ani tabel.
Jeśli sekcja jest poprawna, zwróć ją bez zmian z werdyktem "ok".

Odpowiedz WYŁĄCZNIE obiektem JSON, bez bloków ```:
{{"werdykt": "ok" albo "poprawki", "uwagi": ["krótko, co było źle"], "html": "HTML sekcji"}}

W polu "html" dozwolone znaczniki: p, ul, ol, li, table, thead, tbody, tr, th,
td, h3, strong, em, code. Bez h1, h2, script, style, iframe. Linki wyłącznie
względne, zaczynające się od ukośnika.

Tytuł artykułu: {tytul}
Nagłówek sekcji: {naglowek}

HTML sekcji:
{html}"""


def pytaj_model(agent, prompt, model):
    """Pyta Gemini o ocenę sekcji. Zwraca (tekst_odpowiedzi, błąd).

    Nie korzystamy z `gemini_tekst` agenta bloga, bo tamta funkcja połyka każdy
    błąd i oddaje pusty łańcuch. Recenzja musi odróżnić „model nie ma zastrzeżeń"
    od „model w ogóle nie odpowiedział" — w drugim przypadku wpis nie ma prawa
    pójść na produkcję jako zrecenzowany.

    `responseMimeType` wymusza czysty JSON, więc odpada połowa przypadków,
    w których model opakowywał odpowiedź w blok ```.
    """
    ciało = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }
    ostatni = "brak odpowiedzi"
    for proba in range(1, PROBY + 1):
        req = urllib.request.Request(
            API.format(model=model),
            data=json.dumps(ciało, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": agent.klucz_api()},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as odp:
                dane = json.loads(odp.read().decode("utf-8"))
            try:
                return dane["candidates"][0]["content"]["parts"][0]["text"], None
            except (KeyError, IndexError):
                return None, f"nieoczekiwana odpowiedź API: {json.dumps(dane)[:200]}"
        except urllib.error.HTTPError as e:
            tresc = e.read().decode("utf-8", "replace")[:200]
            ostatni = f"HTTP {e.code}: {tresc}"
            if e.code not in PONAWIALNE:
                return None, ostatni
            time.sleep(2 ** proba * 5)
        except urllib.error.URLError as e:
            ostatni = f"brak połączenia: {e.reason}"
            time.sleep(2 ** proba * 5)
    return None, ostatni


def json_z_odpowiedzi(tekst):
    """Model mimo instrukcji lubi opakować JSON w blok ``` albo dopisać zdanie."""
    tekst = re.sub(r"^```(?:json)?\s*|\s*```$", "", (tekst or "").strip())
    try:
        return json.loads(tekst)
    except json.JSONDecodeError:
        pass
    m = re.search(r"(?s)\{.*\}", tekst)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def recenzuj_sekcje(agent, sekcja, tytul, model):
    """Zwraca (nowy_html_albo_None, uwagi, powod, ocenione).

    `ocenione` mówi, czy model w ogóle wydał werdykt o tej sekcji. Bez tego
    wpis bez ani jednej ocenionej sekcji wyglądałby jak wpis bez zastrzeżeń.
    """
    tekst, figury = rozdziel_ilustracje(sekcja["html"])
    prompt = PROMPT.format(tytul=tytul, naglowek=sekcja["naglowek"], html=tekst)
    surowa, blad_api = pytaj_model(agent, prompt, model)
    if blad_api:
        return None, [], f"model nie odpowiedział ({blad_api})", False
    odpowiedz = json_z_odpowiedzi(surowa)

    if odpowiedz is None:
        return None, [], "model nie zwrócił poprawnego JSON-a", False
    uwagi = [str(u)[:200] for u in odpowiedz.get("uwagi", [])][:5]
    if odpowiedz.get("werdykt") != "poprawki":
        return None, uwagi, None, True

    nowy = re.sub(r"^```(?:html)?\s*|\s*```$", "", str(odpowiedz.get("html", "")).strip())
    if not nowy:
        return None, uwagi, "poprawka bez treści", True

    usterki = usterki_html(nowy, "poprawka")
    if usterki:
        return None, uwagi, usterki[0], True
    if slow(nowy) < slow(tekst) * PROG_SKROCENIA:
        return None, uwagi, (f"poprawka skraca sekcję z {slow(tekst)} do {slow(nowy)} słów "
                             f"— odrzucona"), True

    # Ilustracja wraca na koniec sekcji, w tej samej postaci, w jakiej była.
    return ("\n" + nowy + ("\n" + "\n".join(figury) if figury else "") + "\n",
            uwagi, None, True)


# ------------------------------------------------------------------- przebieg

def recenzja(slug, popraw, model):
    plik = os.path.join(SRC, f"blog-{slug}.html")
    if not os.path.isfile(plik):
        blad_uzycia(f"nie ma pliku {os.path.relpath(plik, BASE)}")

    agent = agent_bloga()
    strona = czytaj(plik)
    tytul = (re.search(r"(?s)<h1[^>]*>(.*?)</h1>", strona) or re.search(r"^(.*)$", slug)).group(1)
    tytul = re.sub(r"<[^>]+>", "", tytul).strip()

    uwagi_lacznie = []
    odrzucone = []
    zmienione = 0

    for runda in range(1, RUNDY + 1):
        sekcje = sekcje_wpisu(strona)
        problemy = kontrola_deterministyczna(sekcje, strona)
        print(f"Runda {runda}: {len(sekcje)} sekcji, "
              f"{'brak usterek formalnych' if not problemy else str(len(problemy)) + ' usterek formalnych'}")
        for p in problemy:
            print("  formalne:", p)

        zmiany = []  # (poczatek, koniec, nowy_html) — nakładane od końca pliku
        ocenione = 0
        # Sekcje, do których model miał zastrzeżenia merytoryczne, a poprawka
        # nie weszła do pliku. Publikacja takiego wpisu byłaby publikacją
        # tekstu, o którym wiemy, że zawiera błąd — i o którym nikt nie
        # zdecydował, że to błąd nieistotny.
        nienaprawione = []
        for s in sekcje:
            nowy, uwagi, powod, byla_ocena = recenzuj_sekcje(agent, s, tytul, model)
            # Nazwa modelu bywa na kluczu niedostępna (HTTP 404). Zamiast oblać
            # cały wpis, przechodzimy raz na model agenta bloga — ten na pewno
            # na tym kluczu działa.
            if not byla_ocena and model != MODEL_ZAPASOWY and powod and "404" in powod:
                print(f"  model {model} niedostępny — przechodzę na {MODEL_ZAPASOWY}")
                model = MODEL_ZAPASOWY
                nowy, uwagi, powod, byla_ocena = recenzuj_sekcje(agent, s, tytul, model)
            ocenione += 1 if byla_ocena else 0
            etykieta = s["naglowek"]
            for u in uwagi:
                uwagi_lacznie.append(f"{etykieta}: {u}")
                print(f"  uwaga [{etykieta}]: {u}")
            if powod:
                odrzucone.append(f"{etykieta}: {powod}")
                print(f"  odrzucona poprawka [{etykieta}]: {powod}")
            if nowy and nowy.strip() != s["html"].strip():
                zmiany.append((s["poczatek"], s["koniec"], nowy))
            elif uwagi:
                nienaprawione.append(f"{etykieta}: {uwagi[0]}")

        # Wpis, którego model nie ocenił, nie jest wpisem zrecenzowanym — nawet
        # gdy przechodzi kontrolę formalną. To była cicha dziura: przy padniętym
        # API wszystko wyglądało na czyste i wpis szedł na produkcję bez oceny.
        if ocenione < len(sekcje):
            problemy.append(
                f"agent kontroli ocenił {ocenione} z {len(sekcje)} sekcji — "
                f"reszta bez recenzji merytorycznej")
        for u in nienaprawione:
            problemy.append(f"zastrzeżenie merytoryczne bez poprawki — {u}")

        if not popraw:
            # W trybie raportu nic nie wchodzi do pliku, więc sekcja czekająca
            # na poprawkę jest sekcją z niezaadresowanym błędem. Inaczej próbny
            # przebieg mówiłby "nadaje się do publikacji" o tekście, który
            # dopiero po poprawkach by się nadawał.
            for poczatek, koniec, _ in zmiany:
                problemy.append("sekcja wymaga poprawki, której tryb raportu nie wpuszcza")
            print("Tryb raportu — nic nie zapisuję.")
            return ("ok" if not problemy else "zostaw"), uwagi_lacznie, odrzucone, 0, problemy

        if not zmiany:
            # Bez zmian kolejna runda pytałaby model o dokładnie ten sam tekst.
            return (("ok" if not problemy else "zostaw"), uwagi_lacznie, odrzucone,
                    zmienione, problemy)

        for poczatek, koniec, nowy in sorted(zmiany, reverse=True):
            strona = strona[:poczatek] + nowy + strona[koniec:]
        zmienione += len(zmiany)
        zapisz(plik, strona)
        print(f"  zapisano {len(zmiany)} poprawionych sekcji")

    sekcje = sekcje_wpisu(strona)
    problemy = kontrola_deterministyczna(sekcje, strona)
    if ocenione < len(sekcje):
        problemy.append(
            f"agent kontroli ocenił {ocenione} z {len(sekcje)} sekcji — "
            f"reszta bez recenzji merytorycznej")
    for u in nienaprawione:
        problemy.append(f"zastrzeżenie merytoryczne bez poprawki — {u}")
    return ("ok" if not problemy else "zostaw"), uwagi_lacznie, odrzucone, zmienione, problemy


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--popraw", action="store_true", help="wpuść przyjęte poprawki do src/")
    ap.add_argument("--model", default=MODEL_DOMYSLNY)
    ap.add_argument("-h", "--help", action="store_true")
    args = ap.parse_args()

    if args.help or not args.slug:
        print(__doc__)
        return 0 if args.help else 2

    slug = args.slug.strip("/").split("/")[-1]
    werdykt, uwagi, odrzucone, zmienione, problemy = recenzja(slug, args.popraw, args.model)

    raport = {
        "slug": slug,
        "werdykt": werdykt,
        "zmienione_sekcje": zmienione,
        "uwagi": uwagi,
        "odrzucone_poprawki": odrzucone,
        "problemy": problemy,
        "model": args.model,
    }
    zapisz(RAPORT, json.dumps(raport, ensure_ascii=False, indent=2))

    print()
    if werdykt == "ok":
        print(f"WERDYKT: wpis {slug} nadaje się do publikacji"
              + (f" (poprawionych sekcji: {zmienione})" if zmienione else ""))
        return 0
    print(f"WERDYKT: wpis {slug} zostaje do decyzji człowieka — {len(problemy)} usterek")
    return 1


if __name__ == "__main__":
    sys.exit(main())
