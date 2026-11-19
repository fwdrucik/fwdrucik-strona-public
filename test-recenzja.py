# -*- coding: utf-8 -*-
"""Testy recenzja.py bez wołania Gemini — model podstawiony atrapą.

    py test-recenzja.py

Chodzą w workflow „Kontrola" przy każdym pushu. Nie potrzebują klucza API
ani sieci: odpowiedzi modelu podstawia atrapa, a treść bierzemy
z prawdziwego, opublikowanego wpisu w src/.
"""
import importlib.util
import io
import json
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

spec = importlib.util.spec_from_file_location("recenzja", os.path.join(BASE, "recenzja.py"))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

zaliczone, oblane = [], []


def sprawdz(nazwa, warunek, szczegol=""):
    (zaliczone if warunek else oblane).append(nazwa)
    print(("  OK   " if warunek else "  BLAD ") + nazwa + (f" — {szczegol}" if szczegol else ""))


class Atrapa:
    """Udaje moduł agenta bloga: oddaje z góry ustaloną odpowiedź modelu."""

    def __init__(self, odpowiedz, blad=None):
        self.odpowiedz = odpowiedz
        self.blad = blad
        self.pytania = 0

    def klucz_api(self):
        return "atrapa"


def podstaw_model(atrapa):
    """Zastępuje wywołanie Gemini odpowiedzią atrapy."""
    def pytaj(agent, prompt, model):
        atrapa.pytania += 1
        if atrapa.blad:
            return None, atrapa.blad
        odp = atrapa.odpowiedz
        return (odp if isinstance(odp, str) else json.dumps(odp, ensure_ascii=False)), None
    r.pytaj_model = pytaj
    return atrapa


# ---------------------------------------------------------------- warstwa 1
print("\nWarstwa deterministyczna:")
sprawdz("czysty HTML przechodzi", r.usterki_html("<p>Tekst pomiarowy 12 V.</p>", "x") == [])
sprawdz("script odrzucony", r.usterki_html('<p>a</p><script>x()</script>', "x") != [])
sprawdz("atrybut zdarzenia odrzucony", r.usterki_html('<p onclick="x()">a</p>', "x") != [])
sprawdz("link zewnetrzny odrzucony", r.usterki_html('<p><a href="https://obcy.pl">a</a></p>', "x") != [])
sprawdz("link wewnetrzny przechodzi", r.usterki_html('<p><a href="/blog/">a</a></p>', "x") == [])
sprawdz("niedomkniety znacznik odrzucony", r.usterki_html("<ul><li>a</ul>", "x") != [])
sprawdz("blok ``` odrzucony", r.usterki_html("<p>a</p>```", "x") != [])

# ------------------------------------------------------- prawdziwy wpis z repo
zrodlo = None
for nazwa in sorted(os.listdir(os.path.join(BASE, "src"))):
    if nazwa.startswith("blog-") and nazwa.endswith(".html"):
        zrodlo = os.path.join(BASE, "src", nazwa)
        break

print("\nParsowanie prawdziwego wpisu:", os.path.basename(zrodlo))
strona = io.open(zrodlo, encoding="utf-8").read()
sekcje = r.sekcje_wpisu(strona)
sprawdz("wpis ma sekcje", len(sekcje) >= 3, f"znaleziono {len(sekcje)}")
sprawdz("FAQ nie jest sekcja tresci", all(s["id"] != "faq" for s in sekcje))
problemy = r.kontrola_deterministyczna(sekcje, strona)
sprawdz("opublikowany wpis przechodzi kontrole", problemy == [], "; ".join(problemy[:3]))

tekst, figury = r.rozdziel_ilustracje(sekcje[0]["html"])
sprawdz("ilustracja wyjeta z tekstu dla modelu", "<figure" not in tekst)

# ------------------------------------------------ warstwa 2: wpuszczanie poprawek
print("\nWpuszczanie poprawek modelu:")
sekcja = sekcje[0]
oryginal = r.rozdziel_ilustracje(sekcja["html"])[0]

nowy, uwagi, powod, ocena = r.recenzuj_sekcje(
    podstaw_model(Atrapa({"werdykt": "ok", "uwagi": []})), sekcja, "Tytul", "atrapa")
sprawdz("werdykt ok nie zmienia sekcji", nowy is None and powod is None)
sprawdz("werdykt ok liczy sie jako ocena", ocena is True)

nowy, uwagi, powod, ocena = r.recenzuj_sekcje(
    podstaw_model(Atrapa(None, blad="HTTP 429: limit")), sekcja, "Tytul", "atrapa")
sprawdz("brak odpowiedzi modelu to brak oceny", ocena is False and powod is not None, powod or "")

nowy, uwagi, powod, ocena = r.recenzuj_sekcje(
    podstaw_model(Atrapa({"werdykt": "poprawki", "uwagi": ["zle napiecie"], "html": "<p>Za krotko.</p>"})),
    sekcja, "Tytul", "atrapa")
sprawdz("skracajaca poprawka odrzucona", nowy is None and powod and "skraca" in powod, powod or "")

nowy, uwagi, powod, ocena = r.recenzuj_sekcje(
    podstaw_model(Atrapa({"werdykt": "poprawki", "uwagi": [], "html": oryginal + '<script>x()</script>'})),
    sekcja, "Tytul", "atrapa")
sprawdz("poprawka z zabronionym znacznikiem odrzucona", nowy is None and powod is not None, powod or "")

poprawiony = oryginal + "<p>Dopisek redakcyjny z wartoscia 12,6 V po recenzji.</p>"
nowy, uwagi, powod, ocena = r.recenzuj_sekcje(
    podstaw_model(Atrapa({"werdykt": "poprawki", "uwagi": ["doprecyzowano napiecie"], "html": poprawiony})),
    sekcja, "Tytul", "atrapa")
sprawdz("dobra poprawka przyjeta", nowy is not None and powod is None, powod or "")
sprawdz("ilustracja wraca do sekcji", (not figury) or (nowy and "<figure" in nowy))
sprawdz("uwagi modelu przekazane dalej", uwagi == ["doprecyzowano napiecie"])

# ------------------------------------------------------- przebieg na kopii wpisu
print("\nPelny przebieg na kopii wpisu:")
kopia = os.path.join(BASE, "src", "blog-test-recenzja-tymczasowa.html")
shutil.copy(zrodlo, kopia)
raport = os.path.join(BASE, ".ostatnia-recenzja.json")
# Raport, ktory lezal tu przed testami, nalezy do prawdziwego przebiegu —
# odkladamy go i oddajemy na koniec, zamiast kasowac cudza prace.
raport_wczesniej = io.open(raport, encoding="utf-8").read() if os.path.exists(raport) else None
try:
    r.agent_bloga = lambda: podstaw_model(Atrapa({"werdykt": "ok", "uwagi": []}))
    werdykt, uwagi, odrzucone, zmienione, problemy = r.recenzja(
        "test-recenzja-tymczasowa", popraw=True, model="atrapa")
    sprawdz("czysty wpis dostaje werdykt ok", werdykt == "ok", "; ".join(problemy[:2]))
    sprawdz("nic nie zmieniono, gdy model nie ma zastrzezen", zmienione == 0)

    r.agent_bloga = lambda: podstaw_model(Atrapa({"werdykt": "poprawki", "uwagi": ["x"],
                                                  "html": "<p>Skrot.</p>"}))
    przed = io.open(kopia, encoding="utf-8").read()
    werdykt, uwagi, odrzucone, zmienione, problemy = r.recenzja(
        "test-recenzja-tymczasowa", popraw=True, model="atrapa")
    po = io.open(kopia, encoding="utf-8").read()
    sprawdz("skracajace poprawki nie ruszaja pliku", przed == po and zmienione == 0)
    sprawdz("odrzucone poprawki sa raportowane", len(odrzucone) > 0)
    sprawdz("uwaga bez wpuszczonej poprawki blokuje publikacje", werdykt == "zostaw",
            "; ".join(problemy[:2]))
    sprawdz("powod wskazuje zastrzezenie merytoryczne",
            any("zastrzeżenie merytoryczne" in p for p in problemy))
    r.agent_bloga = lambda: podstaw_model(Atrapa(None, blad="HTTP 503: usluga niedostepna"))
    werdykt, uwagi, odrzucone, zmienione, problemy = r.recenzja(
        "test-recenzja-tymczasowa", popraw=True, model="atrapa")
    sprawdz("padniete API nie przepuszcza wpisu", werdykt == "zostaw",
            "; ".join(problemy[:2]))
    sprawdz("powod mowi o braku recenzji merytorycznej",
            any("bez recenzji merytorycznej" in p for p in problemy))
finally:
    os.remove(kopia)
    if raport_wczesniej is None:
        if os.path.exists(raport):
            os.remove(raport)
    else:
        io.open(raport, "w", encoding="utf-8").write(raport_wczesniej)

print(f"\nZaliczone: {len(zaliczone)}, oblane: {len(oblane)}")
if oblane:
    print("OBLANE:", ", ".join(oblane))
sys.exit(1 if oblane else 0)
