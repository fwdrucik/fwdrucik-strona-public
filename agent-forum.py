# -*- coding: utf-8 -*-
"""
Autonomiczny Agent Administrator Forum — fwdrucik.pl.

Rola:
  Prowadzi forum techniczne F.W. DRUCIK, zakłada i zarządza oficjalnymi wątkami
  bazowymi (Regulamin, Witam, FAQ, Poczekalnia, General, Instrukcje, Książki Serwisowe),
  odpowiada merytorycznie na pytania użytkowników i automatycznie moderuje kolejkę wpisów.

Uruchomienie:
  py agent-forum.py --status                       # Sprawdza stan forum i wątków bazowych
  py agent-forum.py --bootstrap                    # Zakłada brakujące oficjalne wątki bazowe
  py agent-forum.py --odpowiedz                    # Odpowiada na oczekujące pytania użytkowników
  py agent-forum.py --moderuj                      # Weryfikuje i moderuje oczekujące wpisy
  py agent-forum.py --auto                         # Pełny cykl (bootstrap + moderacja + odpowiedzi)
  py agent-forum.py --auto --petla 300             # Cykliczne działanie co 5 minut
  py agent-forum.py --dry-run                      # Tryb symulacji (bez zapisywania w bazie)
  py agent-forum.py --silnik [gemini|lm-studio|szablon]

Klucz API Gemini:
  Zmienna środowiskowa GEMINI_API_KEY albo plik ~/.claude/.gemini-fwdrucik.json
"""

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Poprawne kodowanie konsoli Windows (UTF-8)
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://fwdrucik.pl"
API_ENDPOINT = os.environ.get("FW_API_URL", f"{SITE_URL}/api/agent.php")
MODEL_GEMINI = "gemini-3.6-flash"

SYSTEM_PROMPT_INZYNIER = """\
Jesteś Inżynierem i Głównym Administratorem Forum Technicznego F.W. DRUCIK
(Domosław 13A, 06-120 Winnica, powiat pułtuski, tel. 601 726 924, fwdrucik@gmail.com).

Twoje zasady:
1. Odpowiadasz po polsku, życzliwie, profesjonalnie i z najwyższą kulturą techniczną.
2. Jesteś mistrzem praktykiem i inżynierem — posługujesz się precyzyjną wiedzą warsztatową:
   - Elektromechanika i instalacje: 12V i 24V, alternatory (tętnienia AC, diody, spadek B+), rozruszniki (zacisk 50).
   - Magistrale cyfrowe: CAN-Bus (ISO 11898, rezystancja 60Ω, terminatory 120Ω, poziomy 2.5V recesywny, CAN-H 3.5V, CAN-L 1.5V), protokół SAE J1939 dla ciągników i ciężarówek, magistrala LIN.
   - Diagnostyka: oscyloskop dwukanałowy, próby spadków napięć, dekodowanie kodów DTC.
   - Spawanie i obróbka: TIG AC/DC z pulsem (aluminium, kwasówka), MIG/MAG w osłonach Ar/CO2, frezowanie CNC (tolerancje H7/g6, ISO 2768-m).
   - Druk 3D techniczny: PETG (odporność na oleje/paliwa), ASA (odporność na UV i warunki zewnętrzne), PA-CF (sztywne elementy konstrukcyjne).
   - Klimatyzacja: czynniki R134a i R1234yf, próby ciśnieniowe wyłącznie suchym azotem (15-20 bar), ZAKAZ używania tlenu.
   - Maszyny i ciągniki: Ursus, Zetor, John Deere, Case, New Holland, JCB, CAT, pojazdy ciężarowe (Volvo, Scania, MAN, DAF).
3. Struktura odpowiedzi na problem użytkownika:
   a) Wstępna diagnoza i najbardziej prawdopodobne przyczyny awarii (uporządkowane od najprostszych).
   b) Procedura diagnostyczno-pomiarowa krok po kroku (jakie nastawy miernika/oscyloskopu, oczekiwane wartości).
   c) Wskazówki bezpieczeństwa i BHP (np. odłączenie mas akumulatora przed spawaniem, ostrożność przy 24V).
   d) Praktyczne rozwiązanie lub propozycja doboru podzespołów.
4. Nigdy nie zmyślasz cen usług ani nie deklarujesz fałszywych obietnic. Podajesz tylko realne fakty firmowe.
"""

# Kompletna baza 7 oficjalnych wątków bazowych dla forum F.W. DRUCIK
WATKI_BAZOWE = {
    "regulamin": {
        "kategoria": "regulamin",
        "tytul": "[REGULAMIN] Zasady Społeczności Technicznej F.W. DRUCIK — Netykieta, Standard Zgłoszeń i BHP",
        "tresc": """\
Witamy na Forum Dyskusyjnym F.W. DRUCIK!

Nasza społeczność powstała z myślą o inżynierach, mechanikach, elektromechanikach, operatorach maszyn CNC, pasjonatach druku 3D oraz rolnikach i przewoźnikach, którzy stawiają na rzetelną wiedzę techniczną i sprawdzoną praktykę warsztatową.

Aby forum pozostało miejscem wartościowym i przyjaznym dla każdego specjalisty, obowiązują poniższe zasady:

1. KULTURA I NETYKIETA WARSZTATU
• Zwracamy się do siebie z szacunkiem. Na naszym forum nie ma miejsca na wulgaryzmy, złośliwości czy wyśmiewanie osób początkujących.
• Doceniamy konstruktywną dyskusję opartą na faktach, pomiarach i normach inżynierskich.

2. STANDARD ZGŁASZANIA USTEREK (JAK ZADAWAĆ PYTANIA)
Aby uzyskać szybką i celną pomoc, w każdym zapytaniu technicznym podaj:
• Markę, model oraz rocznik pojazdu lub maszyny (np. Ursus C-360, Volvo FH13 2012, JCB 3CX).
• Typ silnika / rodzaj sterownika (jeśli jest znany).
• Odczytane kody błędów (DTC) wraz ze standardem (np. OBD2, SAE J1939).
• Wykonane dotychczas pomiary (np. napięcie ładowania, rezystancja linii CAN, ciśnienie na listwie).
• Załącz zdjęcia, schematy lub zrzuty z oscyloskopu, jeśli nimi dysponujesz.

3. BEZPIECZEŃSTWO I ZASADY BHP
• Prace przy instalacjach 24V maszyn ciężkich i układach wysokoprądowych wymagają szczególnej ostrożności. Zawsze odłączaj akumulator przy spawaniu lub wymianie sterowników.
• Próby szczelności układów klimatyzacji wykonujemy WYŁĄCZNIE suchym azotem technicznym z certyfikowanym reduktorem. Bezwzględnie zakazuje się używania tlenu lub sprężonego powietrza z kompresora (ryzyko eksplozji oleju sprężarkowego!).

4. PRAWO I BRAK TOLERANCJI DLA DZIAŁAŃ SZKODLIWYCH
• Obowiązuje całkowity zakaz publikowania i propagowania oprogramowania do nielegalnej korekty drogomierzy (cofanie liczników) oraz omijania systemów bezpieczeństwa.
• Szanujemy prawa autorskie producentów dokumentacji technicznych.

5. MODERACJA I STATUS ZAUFANY
• Pierwsze wpisy nowych użytkowników mogą przechodzić szybką weryfikację antyspamową.
• Po zatwierdzeniu pierwszego wartościowego wpisu Twoje konto otrzymuje status Użytkownika Zaufanego, a kolejne posty pojawiają się natychmiast.

Życzymy owocnych dyskusji, bezbłędnych oscylogramów i satysfakcji z rozwiązanych zagadek technicznych!
— Zespół i Administrator AI F.W. DRUCIK"""
    },
    "witam": {
        "kategoria": "witam",
        "tytul": "[WITAM] Przywitaj się ze społecznością warsztatu F.W. DRUCIK — Przedstaw swój sprzęt i profil pracy",
        "tresc": """\
Dzień dobry! Cieszymy się, że dołączyłeś do społeczności technicznej F.W. DRUCIK.

Każdy z nas ma inne doświadczenia: jedni specjalizują się w ciągnikach rolniczych i hydraulice siłowej, inni w magistralach cyfrowych CAN maszyn budowlanych, spawaniu TIG stopów aluminium czy obróbce skrawaniem CNC i druku 3D.

Napisz kilka zdań o sobie:
1. Skąd jesteś i czym zajmujesz się na co dzień (warsztat, serwis mobilny, gospodarstwo, majsterkowanie)?
2. Z jakimi maszynami i urządzeniami masz najczęściej do czynienia?
3. Jakim sprzętem diagnostycznym, spawalniczym lub wytwórczym dysponujesz w swoim warsztacie?
4. Jaki obszar techniki interesuje Cię najbardziej?

Rozgość się, napisz swój powitalny post poniżej, a w razie pytań nasz zespół i Administrator AI służą pomocą!"""
    },
    "faq": {
        "kategoria": "faq",
        "tytul": "[FAQ] Najczęściej Zadawane Pytania Techniczne — Kompendium Diagnostyki i Napraw Warsztatowych",
        "tresc": """\
Zebrałem odpowiedzi na najczęściej powtarzające się pytania techniczne w naszym warsztacie:

Q1: Jaka powinna być prawidłowa rezystancja magistrali CAN-Bus?
A1: Przy całkowicie wyłączonym zasilaniu i uśpionych sterownikach rezystancja pomiędzy linią CAN-High i CAN-Low powinna wynosić dokładnie ok. 60 Ω. Wynika to z równoległego połączenia dwóch rezystorów terminujących 120 Ω umieszczonych na krańcach magistrali. Wynik 120 Ω oznacza przerwę w wiązce do jednego z terminatorów, a wynik bliski 0 Ω oznacza zwarcie między liniami.

Q2: Jak prawidłowo zmierzyć tętnienia alternatora pod kątem uszkodzenia diod?
A2: Miernik cyfrowy ustawiamy na pomiar napięcia zmiennego (AC) i podłączamy bezpośrednio do śruby B+ alternatora oraz obudowy masy. Przy włączonym silniku i włączonych światłach napięcie zmienne AC nie powinno przekraczać 0.2V – 0.5V. Wartość powyżej 0.8V AC jednoznacznie wskazuje na przebicie lub przerwę w mostku prostowniczym (dioda główna lub wzbudzenia).

Q3: Jaki filament wybrać do druku części pracujących pod maską pojazdu lub w maszynie?
A3: Zwykłe PLA i PETG ulegają deformacji w temperaturze powyżej 60–75°C. Do komory silnika, uchwytów czujników i złączy narażonych na ciepło i UV stosujemy:
• ASA — odporność do 95°C, pełna odporność na promieniowanie słoneczne i chemię drogową.
• PA-CF (Nylon z włóknem węglowym) — odporność do 140–160°C, znakomita sztywność konstrukcyjna i odporność na wibracje.

Q4: Dlaczego próżnia nie daje gwarancji szczelności układu klimatyzacji?
A4: Test próżniowy (podciśnienie -1 bar) działa w odwrotnym kierunku niż ciśnienie robocze (które dochodzi do 15–20 bar). Uszczelnienia wargowe sprężarek i o-ringi podciśnienie potrafi doszczelnić, natomiast pod ciśnieniem gaz ucieka. Prawdziwy test szczelności przeprowadza się suchym azotem pod ciśnieniem min. 15 bar przez minimum 20–30 minut z obserwacją manometru różnicowego.

Q5: Gdzie mieści się warsztat stacjonarny F.W. DRUCIK?
A5: Nasz warsztat mieści się w miejscowości Domosław 13A, 06-120 Winnica (powiat pułtuski, woj. mazowieckie). Pracujemy Pon-Pt 8:00–17:00, Sob 9:00–13:00. Telefon kontaktowy: 601 726 924, e-mail: fwdrucik@gmail.com."""
    },
    "poczekalnia": {
        "kategoria": "poczekalnia",
        "tytul": "[POCZEKALNIA] Warsztatowy Hyde Park — Luźne rozmowy, kawa, patenty warsztatowe i nowości sprzętowe",
        "tresc": """\
Witaj w Poczekalni F.W. DRUCIK!

To jest strefa nieformalna naszego forum — miejsce na luźne rozmowy przy kawie po ciężkim dniu na warsztacie lub w polu.

O czym tutaj rozmawiamy?
• Prezentacje ciekawych patentów i samodzielnie wykonanych narzędzi warsztatowych.
• Dyskusje o nowościach sprzętowych: prasy, podnośniki, oscyloskopy, mikroskopy inspekcyjne, spawarki TIG.
• Niezwykłe zagadki i „kwiatki” pozostawione przez poprzednich mechaników.
• Pytania o opinię przed zakupem sprzętu.

Pamiętaj o kulturze wypowiedzi i życzliwości. Dobrego odpoczynku i udanych dyskusji!"""
    },
    "general": {
        "kategoria": "general",
        "tytul": "[GENERAL] Aktualności i Kierunki Rozwoju Warsztatu F.W. DRUCIK — Nowe Możliwości i Projekty",
        "tresc": """\
Czołem Społeczności!

W tym wątku informujemy o aktualnościach, nowych technologiach i kierunkach rozwoju warsztatu F.W. DRUCIK:

1. SPECJALIZACJA WARSZTATOWA
• Diagnostyka instalacji pojazdów i maszyn, serwis elektronarzędzi, programowanie falowników. Firma nie naprawia i nie regeneruje alternatorów ani rozruszników.
• Kompleksowa diagnostyka oscyloskopowa magistral CAN-Bus, LIN i SAE J1939 w ciągnikach rolniczych, maszynach budowlanych i autach ciężarowych.
• Spawanie precyzyjne TIG AC/DC stopów aluminium, stali nierdzewnej oraz lutowanie twarde chłodnic i rurek klimatyzacji.
• Wytwarzanie części technicznych metodą druku 3D (FDM / SLA żywice inżynieryjne) oraz frezowanie CNC.

2. ROZWÓJ PLATFORMY FWDRUCIK.PL
• Działające forum dyskusyjne z dedykowanym wsparciem Agenta Administratora AI.
• Baza poradników warsztatowych i kompendium wiedzy technicznej.
• Sklep z modelami 3D STL oraz odlewami z żywicy epoksydowej.

Dziękujemy za zaufanie i zapraszamy do dzielenia się swoimi uwagami dotyczącymi działania serwisu!"""
    },
    "instrukcje": {
        "kategoria": "instrukcje",
        "tytul": "[INSTRUKCJA] Krok po kroku: Diagnostyka magistrali CAN-Bus 24V (J1939) oscyloskopem cyfrowym",
        "tresc": """\
Diagnostyka magistrali CAN w pojazdach ciężarowych i maszynach rolniczych (SAE J1939) za pomocą multimetru i oscyloskopu.

KROK 1: KONTROLA STATYCZNA (BEZ ZASILANIA)
1. Wyłącz zapłon i odczekaj min. 3 minuty do całkowitego uśpienia sterowników (BCM, ECU, TCU).
2. Odłącz klemy akumulatora dla bezpieczeństwa.
3. Multimetrem ustawionym na zakres rezystancji (omomierz) zmierz opór między pinem CAN-H (zazwyczaj żółty przewód) a CAN-L (zielony przewód).
• Prawidłowy wynik: 58 – 62 Ω.
• Wynik ok. 120 Ω: uszkodzenie jednego z rezystorów terminujących (często wbudowanego w ECU silnika lub moduł zamykający na ramie).
• Wynik poniżej 50 Ω: zwarcie między przewodami lub dodatkowy niepoprawny rezystor w układzie.

KROK 2: KONTROLA NAPIĘĆ SKŁADOWYCH (ZASILANIE WŁĄCZONE)
1. Włącz zapłon (akumulatory podłączone, instalacja 24V).
2. Mierz napięcie stałe (DC) względem solidnej masy pojazdu:
• CAN-High: średnio 2.6V – 3.0V (w stanie recesywnym 2.5V, w dominującym rośnie do 3.5V).
• CAN-Low: średnio 2.0V – 2.4V (w stanie recesywnym 2.5V, w dominującym spada do 1.5V).
• Suma CAN-H + CAN-L powinna wynosić w przybliżeniu 5.0V!

KROK 3: POMIAR OSCYLOSKOPEM CYFROWYM
1. Ustawienia oscyloskopu (2 kanały):
• Sprzężenie: DC.
• Podstawa czasu: 2 µs/dz lub 5 µs/dz (dla prędkości 250 kbit/s typowej w J1939) lub 1 µs/dz (dla 500 kbit/s).
• Czułość pionowa: 1V/dz na obu kanałach.
• Wyzwalanie (Trigger): zbocze opadające na CAN-L lub rosnące na CAN-H.
2. Ocena przebiegu:
• Ramki muszą być idealnym lustrzanym odbiciem względem linii 2.5V.
• Zbocza sygnału powinny być strome, bez zaokrągleń (zaokrąglenia = nadmierna pojemność wiązki lub wilgoć w złączach).
• Brak oscylacji tłumionych (dzwonienia) na wierzchołkach impulsów (dzwonienie = brak terminatora 120 Ω).

W razie pytań o konkretny przypadek wklej zrzut ekranu z oscyloskopu w nowym wątku w dziale Elektromechanika!"""
    },
    "ksiazkiserwisowe": {
        "kategoria": "ksiazkiserwisowe",
        "tytul": "[DTR & SCHEMATY] Centralne Repozytorium Dokumentacji Maszyn, Ciągników i Pojazdów Ciężarowych",
        "tresc": """\
W tym dziale gromadzimy i indeksujemy sprawdzoną dokumentację techniczno-ruchową (DTR), katalogi części i schematy instalacji elektrycznych/hydraulicznych:

1. CIĄGNIKI I MASZYNY ROLNICZE:
• Ursus: C-330, C-360, C-385 oraz seria ciężka (912, 914, 1014, 1224, 1614) — schematy instalacji 12V, układy ładowania z prądnicą/alternatorem, układy rozruchu 24V (przełącznik 12/24V).
• Zetor: seria 5211 - 7745, Forterra, Proxima — instalacje elektryczne, rozdzielacze hydrauliczne.
• Maszyny zachodnie: John Deere, New Holland, Case IH, Deutz-Fahr — schematy szyn CAN i pinouty sterowników silnika.

2. MASZYNY BUDOWLANE:
• Koparko-ładowarki JCB 3CX / 4CX (Project 12, 21, Tier 3, Tier 4) — schematy zasilania cewek skrzyni biegów Powershift, linie CAN układu sterowania.
• Minikoparki i ładowarki CAT, Komatsu, Yanmar, Kubota.

3. POJAZDY CIĘŻAROWE:
• Volvo FH12 / FH13 (D12, D13) — schematy szyny J1939, sterowniki EMS, VMCU.
• Scania seria 4 oraz R (HPI, PDE, XPI) — koordynator COO7, jednostka sterująca EMS.
• DAF XF 95 / 105 — moduły DMUX, VIC, EBS.

JAK ZGŁOSIĆ PROŚBĘ O SCHEMAT?
Jeśli szukasz schematu do konkretnej maszyny, załóż wątek w tym dziale podając:
• Dokładny model maszyny i rok produkcji.
• Numer seryjny (VIN / PIN) lub oznaczenie silnika.
• Sekcję, której dotyczy problem (np. układ rozruchu, zasilanie pompy wtryskowej, klimatyzacja, joysticki hydrauliczne).

Nasz zespół i społeczność postarają się pomóc w odnalezieniu właściwego schematu!"""
    }
}


def pobierz_klucz_gemini() -> str:
    """Odczytuje klucz Gemini API ze zmiennej środowiskowej lub pliku konfiguracyjnego."""
    klucz = os.environ.get("GEMINI_API_KEY", "").strip()
    if klucz:
        return klucz

    sciezka_pliku = os.path.expanduser("~/.claude/.gemini-fwdrucik.json")
    if os.path.isfile(sciezka_pliku):
        try:
            with open(sciezka_pliku, "r", encoding="utf-8") as f:
                dane = json.load(f)
                return dane.get("api_key", "").strip()
        except Exception:
            pass
    return ""


def pobierz_token_agenta() -> str:
    """Pobiera token agenta ze środowiska lub z konfiguracji backendu na serwerze przez FTPS."""
    token = os.environ.get("FW_AGENT_TOKEN", "").strip() or os.environ.get("AGENT_TOKEN", "").strip()
    if token:
        return token

    # Próba odczytania tokenu bezpośrednio z serwera przez moduł zglos-zalegle
    try:
        import importlib.util
        sciezka = os.path.join(BASE_DIR, "zglos-zalegle.py")
        if os.path.isfile(sciezka):
            spec = importlib.util.spec_from_file_location("zglos_zalegle", sciezka)
            modul = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modul)
            t = modul.token_z_serwera()
            if t:
                return t
    except Exception:
        pass

    sciezka_cfg = os.path.join(BASE_DIR, "api", "konfiguracja.php")
    if os.path.isfile(sciezka_cfg):
        try:
            with open(sciezka_cfg, "r", encoding="utf-8") as f:
                zawartosc = f.read()
                m = re.search(r"['\"]agent_token['\"]\s*=>\s*['\"]([^'\"]+)['\"]", zawartosc)
                if m and m.group(1):
                    return m.group(1).strip()
        except Exception:
            pass
    return ""


class KlientApiForum:
    """Klient komunikacji HTTP z backendem api/agent.php."""

    def __init__(self, endpoint: str, token: str):
        self.endpoint = endpoint
        self.token = token

    def zapytaj(self, akcja: str, metoda: str = "GET", dane: dict = None) -> dict:
        url = f"{self.endpoint}?akcja={urllib.parse.quote(akcja)}"
        naglowki = {
            "User-Agent": "FW-Drucik-Forum-AI-Agent/1.0",
            "Accept": "application/json",
        }
        if self.token:
            naglowki["X-Agent-Token"] = self.token

        cialo = None
        if dane is not None:
            cialo = json.dumps(dane).encode("utf-8")
            naglowki["Content-Type"] = "application/json; charset=utf-8"

        req = urllib.request.Request(url, data=cialo, headers=naglowki, method=metoda)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                kod = resp.getcode()
                odp_tekst = resp.read().decode("utf-8", errors="replace")
                return json.loads(odp_tekst)
        except urllib.error.HTTPError as e:
            tresc_bledu = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(tresc_bledu)
                komunikat = err_json.get("blad", tresc_bledu)
            except Exception:
                komunikat = tresc_bledu
            raise RuntimeError(f"Błąd HTTP {e.code} z API ({akcja}): {komunikat}")
        except Exception as e:
            raise RuntimeError(f"Błąd połączenia z API ({akcja}): {e}")


def generuj_odpowiedz_gemini(tytul: str, tresc: str, kategoria: str, api_key: str) -> str:
    """Generuje profesjonalną odpowiedź inżynierską za pomocą Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_GEMINI}:generateContent?key={api_key}"

    prompt_uzytkownika = (
        f"Kategoria forum: {kategoria}\n"
        f"Tytuł wątku: {tytul}\n"
        f"Treść pytania użytkownika:\n{tresc}\n\n"
        f"Napisz kompletną, merytoryczną odpowiedź techniczną jako Inżynier i Administrator F.W. DRUCIK. "
        f"Podaj konkretne parametry, nastawy mierników, procedurę krok po kroku oraz środki ostrożności."
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": SYSTEM_PROMPT_INZYNIER + "\n\n" + prompt_uzytkownika}]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048,
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        dane = json.loads(resp.read().decode("utf-8"))
        kandydaci = dane.get("candidates", [])
        if not kandydaci:
            raise RuntimeError("Gemini API nie zwróciło kandydatów odpowiedzi.")
        czesci = kandydaci[0].get("content", {}).get("parts", [])
        return "".join(c.get("text", "") for c in czesci).strip()


def generuj_odpowiedz_lm_studio(tytul: str, tresc: str, kategoria: str, host: str = "http://127.0.0.1:1234") -> str:
    """Generuje odpowiedź za pośrednictwem lokalnego serwera LM Studio (Bielik/DeepSeek)."""
    url = f"{host}/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_INZYNIER},
            {"role": "user", "content": f"Kategoria: {kategoria}\nTytuł: {tytul}\n\nProblem:\n{tresc}"}
        ],
        "temperature": 0.3,
        "max_tokens": 1500
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        dane = json.loads(resp.read().decode("utf-8"))
        wybory = dane.get("choices", [])
        if not wybory:
            raise RuntimeError("LM Studio nie zwróciło żadnej odpowiedzi.")
        return wybory[0].get("message", {}).get("content", "").strip()


def generuj_odpowiedz_heurystyczna(tytul: str, tresc: str, kategoria: str) -> str:
    """Wbudowany awaryjny silnik ekspercki oparty na heurystyce warsztatowej."""
    tresc_l = (tytul + " " + tresc).lower()

    if "can" in tresc_l or "j1939" in tresc_l or "szyn" in tresc_l:
        return (
            "Dzień dobry! Z punktu widzenia diagnostyki magistrali CAN w Twoim przypadku zalecam procedurę:\n\n"
            "1. Kontrola statyczna na odłączonym akumulatorze:\n"
            "   - Zmierz rezystancję między liniami CAN-H i CAN-L (pomiędzy pinami złącza diagnostycznego lub sterownika).\n"
            "   - Prawidłowa wartość: 60 Ω (±2 Ω). Jeśli masz 120 Ω — przerwany jeden obwód terminatora.\n\n"
            "2. Kontrola napięć przy włączonym zapłonie:\n"
            "   - CAN-High: ok. 2.6 – 3.0V DC względem masy.\n"
            "   - CAN-Low: ok. 2.0 – 2.4V DC względem masy.\n"
            "   - Suma obu linii powinna wynosić 5.0V.\n\n"
            "3. Sprawdzenie ekranowania i ciągłości mas:\n"
            "   - Uszkodzona plecionka ekranu lub zagięta wiązka potrafi generować błędy przy obciążeniu przetwornicami.\n\n"
            "W razie dalszych trudności podaj dokładny kod błędu DTC z diagnostyki!"
        )

    if "ładowan" in tresc_l or "alternator" in tresc_l or "akumulator" in tresc_l:
        return (
            "Czołem! Typowy problem z układem ładowania należy zdiagnozować wielopunktowo:\n\n"
            "1. Pomiar spadku napięcia na przewodzie głównym B+:\n"
            "   - Przy włączonych światłach i obciążeniu zmierz spadek napięcia między śrubą B+ alternatora a klemą (+) akumulatora.\n"
            "   - Dopuszczalny spadek to maksymalnie 0.2V. Większy spadek oznacza utlenioną końcówkę oczkową lub przetarty przewód.\n\n"
            "2. Sprawdzenie tętnień mostka diodowego (napięcie AC):\n"
            "   - Ustaw miernik na woltomierz prądu zmiennego (AC). Jeśli na B+ masz ponad 0.5V AC, padła dioda w mostku prostowniczym.\n\n"
            "3. Kontrola napięcia wzbudzenia (zacisk D+):\n"
            "   - Sprawdź żarówkę kontrolki na desce i stan szczotek regulatora.\n\n"
            "Napisz, jakie napięcia zmierzyłeś na samym alternatorze, a jakie bezpośrednio na słupkach akumulatora!"
        )

    return (
        "Dzień dobry! Dziękuję za zgłoszenie tematu na forum F.W. DRUCIK.\n\n"
        "Abyśmy mogli precyzyjnie ustalić przyczynę problemu, przygotuj i uzupełnij w wątku:\n"
        "1. Dokładny model maszyny / rocznik oraz oznaczenie silnika lub modułu.\n"
        "2. Pomiary wykonane miernikiem w spoczynku i pod obciążeniem roboczym.\n"
        "3. Kody błędów, jeśli maszyna była podłączana pod tester diagnostyczny.\n\n"
        "Zajmiemy się analizą Twojego przypadku i wrócimy z konkretną procedurą naprawczą!"
    )


def akcja_status(klient: KlientApiForum) -> None:
    """Sprawdza i wyświetla szczegółowy stan forum."""
    print("=" * 60)
    print("🔍 SPRAWDZANIE STANU FORUM FWDRUCIK.PL")
    print("=" * 60)
    try:
        odp = klient.zapytaj("status")
        f = odp.get("forum", {})
        print(f"• Wątki opublikowane:     {f.get('watki_opublikowane', 0)}")
        print(f"• Odpowiedzi opublikowane: {f.get('odpowiedzi_opublikowane', 0)}")
        print(f"• Oczekujące na moderację: {f.get('kolejka_oczekuje', {}).get('suma', 0)}")

        kategorie = f.get("kategorie", {})
        if not isinstance(kategorie, dict):
            kategorie = {}
        print("\n📊 Wątki według kategorii:")
        if kategorie:
            for kat, ile in kategorie.items():
                print(f"   - {kat:<18}: {ile} wątków")
        else:
            print("   (brak aktywnych wątków w kategoriach)")

        watki_bazowe = f.get("watki_bazowe", {})
        if not isinstance(watki_bazowe, dict):
            watki_bazowe = {}
        brakujace = f.get("brakujace_bazowe", [])

        print("\n🏛️ Stan 7 wątków bazowych:")
        for kat in ["regulamin", "witam", "faq", "poczekalnia", "general", "instrukcje", "ksiazkiserwisowe"]:
            obecny = kat in watki_bazowe
            znacznik = "✅ ZAŁOŻONY" if obecny else "❌ BRAK"
            print(f"   - {kat:<18}: {znacznik}")

        if brakujace:
            print(f"\n⚠️  Brakuje {len(brakujace)} wątków bazowych! Użyj opcji --bootstrap, aby je utworzyć.")
        else:
            print("\n🎉 Wszystkie 7 wątków bazowych są obecne na forum!")

    except Exception as e:
        print(f"❌ Błąd podczas odpytywania API: {e}")


def akcja_bootstrap(klient: KlientApiForum, dry_run: bool = False) -> None:
    """Zakłada brakujące oficjalne wątki bazowe."""
    print("=" * 60)
    print("🚀 BOOTSTRAP WĄTKÓW BAZOWYCH FORUM")
    print("=" * 60)

    try:
        odp = klient.zapytaj("status")
        obecne = odp.get("forum", {}).get("watki_bazowe", {})
        if not isinstance(obecne, dict):
            obecne = {}
    except Exception as e:
        print(f"⚠️  Nie udało się pobrać statusu online ({e}). Sprawdzam wszystkie...")
        obecne = {}

    utworzone = 0
    for slug, dane in WATKI_BAZOWE.items():
        if slug in obecne:
            print(f"⏭️  Wątek '{slug}' już istnieje (ID: {obecne[slug].get('id')}). Pomijam.")
            continue

        print(f"➕ Zakładanie wątku [{slug}]: '{dane['tytul']}'...")
        if dry_run:
            print(f"   [DRY-RUN] Wątek '{slug}' zostałby utworzony.")
            utworzone += 1
            continue

        try:
            r = klient.zapytaj("zaloz-watek", metoda="POST", dane=dane)
            print(f"   ✅ Utworzono pomyślnie! ID nowego wątku: {r.get('id')}")
            utworzone += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"   ❌ Błąd tworzenia wątku '{slug}': {e}")

    print(f"\nPodsumowanie: utworzono {utworzone} wątków bazowych.")


def akcja_odpowiedz(klient: KlientApiForum, silnik: str, api_key: str, dry_run: bool = False) -> None:
    """Przeszukuje forum pod kątem pytań bez odpowiedzi i generuje porady."""
    print("=" * 60)
    print("🤖 AUTOMATYCZNE ODPOWIADANIE NA PYTANIA UŻYTKOWNIKÓW")
    print("=" * 60)

    try:
        odp = klient.zapytaj("nieodpowiedziane")
        watki = odp.get("watki", [])
    except Exception as e:
        print(f"❌ Błąd pobierania wątków bez odpowiedzi: {e}")
        return

    if not watki:
        print("✅ Brak wątków oczekujących na odpowiedź eksperta.")
        return

    print(f"Znaleziono {len(watki)} wątków wymagających odpowiedzi eksperta:")

    for w in watki:
        w_id = w["id"]
        w_tytul = w["tytul"]
        w_kat = w["kategoria"]
        w_autor = w["autor"]
        w_tresc = w["tresc"]

        print(f"\n--- Wątek #{w_id} [{w_kat}] przez @{w_autor}: '{w_tytul}' ---")

        # Generowanie treści odpowiedzi
        odpowiedz_tekst = ""
        try:
            if silnik == "gemini" and api_key:
                print("   📡 Generowanie odpowiedzi przez Gemini API...")
                odpowiedz_tekst = generuj_odpowiedz_gemini(w_tytul, w_tresc, w_kat, api_key)
            elif silnik == "lm-studio":
                print("   💻 Generowanie odpowiedzi przez lokalne LM Studio...")
                odpowiedz_tekst = generuj_odpowiedz_lm_studio(w_tytul, w_tresc, w_kat)
            else:
                print("   ⚙️  Generowanie odpowiedzi przez silnik heurystyczny...")
                odpowiedz_tekst = generuj_odpowiedz_heurystyczna(w_tytul, w_tresc, w_kat)
        except Exception as e:
            print(f"   ⚠️  Błąd silnika AI ({e}). Przełączam na silnik heurystyczny...")
            odpowiedz_tekst = generuj_odpowiedz_heurystyczna(w_tytul, w_tresc, w_kat)

        # Dodanie stopki administratorskiej
        odpowiedz_tekst += (
            f"\n\n---\n"
            f"🛡️ *Wpis wygenerowany i autoryzowany przez Administratora AI F.W. DRUCIK.*\n"
            f"📍 *Warsztat stacjonarny: Domosław 13A, 06-120 Winnica | Tel: 601 726 924*"
        )

        if dry_run:
            print("   [DRY-RUN] Zaplanowana odpowiedź:")
            print(f"   {odpowiedz_tekst[:200]}...")
            continue

        try:
            r = klient.zapytaj("odpowiedz", metoda="POST", dane={"watek_id": w_id, "tresc": odpowiedz_tekst})
            print(f"   ✅ Odpowiedź opublikowana pomyślnie! ID: {r.get('id')}")
            time.sleep(1)
        except Exception as e:
            print(f"   ❌ Błąd publikacji odpowiedzi: {e}")


def akcja_moderuj(klient: KlientApiForum, dry_run: bool = False) -> None:
    """Weryfikuje wpisy czekające w kolejce moderacyjnej."""
    print("=" * 60)
    print("🛡️ MODERACJA TREŚCI FORUM")
    print("=" * 60)

    try:
        odp = klient.zapytaj("kolejka")
        kolejka = odp.get("kolejka", [])
    except Exception as e:
        print(f"❌ Błąd pobierania kolejki moderacyjnej: {e}")
        return

    if not kolejka:
        print("✅ Kolejka moderacyjna jest pusta.")
        return

    print(f"Znaleziono {len(kolejka)} pozycji oczekujących na moderację:")

    slowa_zakazane = ["kasyno", "kryptowalut", "pozyczki", "chwilowki", "porno", "viagra", "dropshipping", "http://", "https://"]

    for item in kolejka:
        typ = item["typ"]
        p_id = item["id"]
        autor = item["autor"]
        tresc = item["tresc"]
        naglowek = item.get("tytul", item.get("watek_tytul", ""))

        print(f"\n• Pozycja {typ} #{p_id} od @{autor}: '{naglowek}'")

        # Prosta reguła wykrywania spamu
        tekst_caly = (naglowek + " " + tresc).lower()
        jest_spam = any(z in tekst_caly for z in slowa_zakazane)

        decyzja = "odrzuc" if jest_spam else "zatwierdz"
        powod = "Wykryto spam lub niedozwolone linki" if jest_spam else "Merytoryczna treść techniczna"

        print(f"   Decyzja: {decyzja.upper()} ({powod})")

        if dry_run:
            print("   [DRY-RUN] Pomiędzy symulacją a bazą.")
            continue

        try:
            r = klient.zapytaj("moderuj", metoda="POST", dane={"typ": typ, "id": p_id, "decyzja": decyzja})
            print(f"   ✅ Zastosowano decyzję: {r.get('nowy_status')}")
        except Exception as e:
            print(f"   ❌ Błąd moderacji #{p_id}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Autonomiczny Agent Administrator Forum FW DRUCIK")
    parser.add_argument("--status", action="store_true", help="Pobiera i wyświetla statystyki forum")
    parser.add_argument("--bootstrap", action="store_true", help="Tworzy 7 oficjalnych wątków bazowych")
    parser.add_argument("--odpowiedz", action="store_true", help="Odpowiada na oczekujące wątki")
    parser.add_argument("--moderuj", action="store_true", help="Przeprowadza moderację oczekujących wpisów")
    parser.add_argument("--auto", action="store_true", help="Pełny cykl administracyjny (bootstrap + moderacja + odpowiedzi)")
    parser.add_argument("--petla", type=int, default=0, help="Uruchamia cykl w pętli co N sekund")
    parser.add_argument("--dry-run", action="store_true", help="Tryb symulacji bez zapisywania w bazie")
    parser.add_argument("--silnik", choices=["gemini", "lm-studio", "szablon"], default="gemini", help="Wybór silnika generowania treści")
    parser.add_argument("--endpoint", default=API_ENDPOINT, help="Adres URL API agent.php")
    parser.add_argument("--podglad-watkow", action="store_true", help="Wyświetla pełne teksty wątków bazowych")

    args = parser.parse_args()

    if args.podglad_watkow:
        print("=" * 70)
        print("📖 PODGLĄD 7 OFICJALNYCH WĄTKÓW BAZOWYCH F.W. DRUCIK")
        print("=" * 70)
        for slug, d in WATKI_BAZOWE.items():
            print(f"\n[{slug.upper()}] {d['tytul']}\n")
            print(d["tresc"][:350] + "\n... [skrót] ...\n")
        return

    klucz_gemini = pobierz_klucz_gemini()
    token_agenta = pobierz_token_agenta()

    klient = KlientApiForum(args.endpoint, token_agenta)

    if not any([args.status, args.bootstrap, args.odpowiedz, args.moderuj, args.auto]):
        # Domyślnie pokaż status
        akcja_status(klient)
        return

    def wykonaj_wszystko():
        if args.status:
            akcja_status(klient)
        if args.bootstrap or args.auto:
            akcja_bootstrap(klient, dry_run=args.dry_run)
        if args.moderuj or args.auto:
            akcja_moderuj(klient, dry_run=args.dry_run)
        if args.odpowiedz or args.auto:
            akcja_odpowiedz(klient, args.silnik, klucz_gemini, dry_run=args.dry_run)

    if args.petla > 0:
        print(f"🔄 Rozpoczynanie pętli nadzorcy forum co {args.petla} sekund (Ctrl+C aby zakończyć)...")
        while True:
            try:
                print(f"\n⏰ [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Wykonanie cyklu...")
                wykonaj_wszystko()
                time.sleep(args.petla)
            except KeyboardInterrupt:
                print("\nZatrzymano pętlę.")
                break
            except Exception as e:
                print(f"⚠️  Wyjątek w pętli: {e}")
                time.sleep(args.petla)
    else:
        wykonaj_wszystko()


if __name__ == "__main__":
    main()
