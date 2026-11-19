"""Kolejność lekcji w Pracowni. Brak kotwicy oznacza lekcję w przygotowaniu."""
import json
from html import escape
from pathlib import Path

from pracownia_wiedza import HASLA, OPISY_PLANSZ, PROBY

KOMPENDIUM = "/pracownia/kompendium/"
SCIEZKI = (
    ("Elektronika", "elektronika", "E"),
    ("Arduino", "arduino", "A"),
    ("Druk 3D", "druk-3d", "D"),
)
PILOTAZE = {
    "E01": ("Pierwsze obwody na płytce stykowej", "obwody"),
    "A01": ("Pierwsze mrugnięcie robota", "arduino"),
    "D01": ("Znajdź pierwszą warstwę", "druk-3d"),
}


def kotwica(kod):
    return PILOTAZE[kod][1] if kod in PILOTAZE else "proba-" + kod.lower()


NOTA = """
<aside class="container pracownia-sekcja" aria-labelledby="od-dawida">
  <div class="kurs-nota">
    <h2 id="od-dawida">Od Dawida</h2>
    <p>Jeśli choć jedno dziecko po tych lekcjach pomyśli „Chcę zobaczyć, jak to działa” i wpadnie na pomysł, który zechce sprawdzić, to dla mnie już będzie nagroda.</p>
    <p>Gdy robicie próbę razem, dajcie sobie chwilę na zgadywanie. Opowiedz dziecku, jak sam pierwszy raz coś naprawiłeś. Może następnym razem to ono pokaże Ci, od czego zacząć.</p>
  </div>
</aside>
"""


RGB = """
<fieldset class="kurs-rgb" data-rgb hidden>
  <legend>Zmieszaj światło</legend>
  <div class="kurs-linki">
    <label><input type="checkbox" value="1"> Czerwone</label>
    <label><input type="checkbox" value="2"> Zielone</label>
    <label><input type="checkbox" value="4"> Niebieskie</label>
  </div>
  <p role="status"><span class="kurs-rgb-swiatlo" aria-hidden="true"></span> <span data-rgb-wynik>Zgaszona</span></p>
</fieldset>"""


def _wstawka_ide(kod):
    """Film 8 s z kodem w Arduino IDE (wstawka z odcinka A-S01Exx), jeśli istnieje."""
    slug = kod.lower()
    if not (Path(__file__).parent / "assets" / "pracownia-ide" / f"{slug}.mp4").is_file():
        return ""
    return f"""
  <details class="kurs-klip">
    <summary>Zobacz kod w Arduino IDE (8 s, bez dźwięku)</summary>
    <video controls muted playsinline preload="none" poster="/assets/pracownia-ide/{slug}.webp" width="1280" height="720" aria-label="Kod programu {slug}.ino w Arduino IDE">
      <source src="/assets/pracownia-ide/{slug}.mp4" type="video/mp4">
    </video>
    <p><a href="/assets/pracownia-kod/{slug}/{slug}.ino" download>Pobierz {slug}.ino</a></p>
  </details>"""


def _proba(kod):
    pytanie, opcje, poprawna, wynik, podpowiedz = PROBY[kod]
    przyciski = "".join(
        f'<button type="button" class="btn btn-outline" data-opcja="{i}" aria-pressed="false">{escape(etykieta)}</button>'
        for i, etykieta in enumerate(opcje)
    )
    instrukcja = {
        "E02": "Kliknij „Próba z jedną LED”, włącz baterię, żeby zamknąć obwód. Odczytaj prąd dla 470 Ω, potem zmień opór na 1000 Ω i odczytaj ponownie.",
        "E04": "Kliknij „Przywróć żarówki”, włącz baterię w układzie szeregowym i zmień element 2 na puste pole, a potem przełącz na układ równoległy i porównaj światło pozostałych żarówek.",
        "E10": "Uruchom poprawny obwód z jedną LED. Jedna osoba wprowadza zmianę, a druga przywraca działający układ. Porównujcie po jednym ustawieniu.",
    }.get(kod)
    plytka = f'\n  <p>{instrukcja} <a href="#obwody">Przejdź do płytki stykowej</a></p>' if instrukcja else ""
    kolory = RGB if kod == "A06" else ""
    return f"""
<div class="lab-panel" data-proba data-poprawna="{poprawna}">
  <h3>{escape(pytanie)}</h3>
  <div class="kurs-linki" data-opcje hidden>{przyciski}</div>
  <p role="status" data-wynik></p>
  <template data-wskazowka>{escape(podpowiedz)}</template>
  <details><summary>Pokaż wyjaśnienie</summary><p data-odpowiedz>{escape(wynik)}</p></details>{plytka}{kolory}
{_wstawka_ide(kod)}
  <p><a href="/pracownia/kompendium/#{kod.lower()}">Otwórz w symulatorze</a></p>
</div>"""


def _pozostale(plan, kod_serii):
    sezony = {}
    for odcinek in plan:
        kod = odcinek["id"]
        if kod[0] != kod_serii:
            continue
        sezon, numer = int(kod[3:5]), int(kod[-2:])
        if sezon == 1 and f"{kod_serii}{numer:02}" in HASLA:
            continue
        sezony.setdefault(sezon, []).append(f'<li value="{numer}">{escape(odcinek["title"])}</li>')
    return "".join(
        f'<details><summary>Sezon {sezon} · planowane lekcje</summary><ol>{"".join(wpisy)}</ol></details>'
        for sezon, wpisy in sezony.items()
    )


def render_kurs(html, katalog):
    plan = json.loads((Path(katalog).parent / "pracownia_plan.json").read_text(encoding="utf-8"))
    odcinki = {wpis["id"]: wpis for wpis in plan}
    karty = []
    lekcje = []
    for sciezka, _, kod_serii in SCIEZKI:
        linki = []
        kody = sorted(kod for kod in HASLA if kod[0] == kod_serii)
        for indeks, kod in enumerate(kody):
            numer = int(kod[1:])
            adres = kotwica(kod)
            film = odcinki[f"{kod_serii}-S01E{numer:02}"]
            if kod in PILOTAZE:
                tytul, _ = PILOTAZE[kod]
                tresc = (Path(katalog) / "pracownia" / f"{adres}.html").read_text(encoding="utf-8")
                status = " · Pilotaż"
            else:
                tytul, tresc, status = film["title"], _proba(kod), ""
            razem = film["home"]
            tytul = escape(tytul)
            pilotaz = "<small>Pilotaż</small>" if numer == 1 else ""
            linki.append(f'<li><a href="#{adres}">{tytul}</a>{pilotaz}</li>')
            nastepna = kotwica(kody[indeks+1]) if indeks+1 < len(kody) else ""
            dalej = f'<a href="#{nastepna}">Następna lekcja</a>' if nastepna else ""
            lekcje.append(f"""
<section class="container pracownia-sekcja" id="{adres}" aria-labelledby="{kod}-tytul">
  <p class="kurs-etap">{sciezka} · Lekcja {numer}{status}</p>
  <h2 id="{kod}-tytul">{tytul}</h2>
{tresc}
  <div class="kurs-razem">
    <h3>Sprawdźcie razem</h3>
    <p>{escape(razem)}</p>
  </div>
  <div class="kurs-linki">{dalej}<a href="{KOMPENDIUM}#{kod.lower()}">Przeczytaj w kompendium</a>
    <a href="#kurs">Wróć do mapy kursu</a>
  </div>
</section>""")
        karty.append(f'<div class="kurs-sciezka"><h3>{sciezka}</h3><ol>{"".join(linki)}</ol>{_pozostale(plan, kod_serii)}</div>')

    mapa = f"""
<nav class="container pracownia-sekcja" id="kurs" aria-labelledby="kurs-tytul">
  <h2 id="kurs-tytul">Mapa kursu</h2>
  <p>Otwórz lekcję z pierwszego sezonu i zrób próbę.</p>
  <div class="kurs-linki"><a href="{KOMPENDIUM}">Kompendium dla dzieci</a><a href="#twoj-drucik">Studio robota</a></div>
  <div class="kurs-sciezki">{"".join(karty)}</div>
</nav>
"""
    znacznik = "<!-- PRACOWNIA_KURS -->"
    if html.count(znacznik) != 1:
        raise ValueError("Pracownia wymaga jednego znacznika kursu.")
    return html.replace(znacznik, mapa + "\n".join(lekcje) + NOTA)


KOD_DIR = Path(__file__).parent / "assets" / "pracownia-kod"
MONITOR = {
    "A07": "Pokrętło: 0\nPokrętło: 348\nPokrętło: 1023",
    "A09": "czas_ms;stan\n4210;wcisniety\n4630;puszczony",
}
_SLOWA_IDE = r"\b(void|int|bool|const|unsigned|long|if|else|for|true|false|HIGH|LOW|OUTPUT|INPUT_PULLUP|A0)\b"
_FUNKCJE_IDE = r"\b(setup|loop|pinMode|digitalWrite|digitalRead|analogWrite|analogRead|delay|millis|tone|Serial|begin|println|print|attach|write)\b"


def _koloruj(linia):
    """Kolorowanie składni jak w Arduino IDE 2: komentarz, tekst, słowa kluczowe, funkcje, liczby."""
    import re
    kod, _, kom = linia.partition("//")
    czesci = re.split(r'("[^"]*")', kod)
    out = []
    for i, c in enumerate(czesci):
        c = escape(c)
        if i % 2:
            out.append(f'<span class="ide-t">{c}</span>')
            continue
        c = re.sub(_SLOWA_IDE, r'<span class="ide-k">\1</span>', c)
        c = re.sub(_FUNKCJE_IDE, r'<span class="ide-f">\1</span>', c)
        c = re.sub(r"(?<![\w>#])(\d+)\b", r'<span class="ide-n">\1</span>', c)
        out.append(c)
    if _ or kom:
        out.append(f'<span class="ide-c">//{escape(kom)}</span>')
    return "".join(out)


def okno_ide(kod):
    """Plansza kodu w stylu okna Arduino IDE; szkic skompilowany arduino-cli dla UNO R3."""
    slug = kod.lower()
    plik = KOD_DIR / slug / f"{slug}.ino"
    if not plik.is_file():
        return ""
    linie = plik.read_text(encoding="utf-8").rstrip("\n").split("\n")
    wiersze = "".join(f'<span class="ide-l"><span class="ide-nr" aria-hidden="true">{n}</span>{_koloruj(l) or " "}</span>'
                      for n, l in enumerate(linie, 1))
    monitor = MONITOR.get(kod)
    dol = (f'<div class="ide-monitor"><span>Monitor portu szeregowego · 9600 baud · przykładowy odczyt</span><pre>{escape(monitor)}</pre></div>'
           if monitor else '<div class="ide-status">Wgrywanie zakończone · Arduino Uno na COM3</div>')
    return f"""
  <figure class="ide" aria-label="Kod programu w Arduino IDE: {escape(slug)}.ino">
    <div class="ide-pasek"><span class="ide-btn" aria-hidden="true">✓</span><span class="ide-btn" aria-hidden="true">→</span><span class="ide-plyta">Arduino Uno</span><a class="ide-pobierz" href="/assets/pracownia-kod/{slug}/{slug}.ino" download>Pobierz {slug}.ino</a></div>
    <div class="ide-karta">{slug}.ino</div>
    <pre class="ide-kod"><code>{wiersze}</code></pre>
    {dol}
  </figure>"""


def render_kompendium(html):
    dzialy = []
    for nazwa, slug, seria in SCIEZKI:
        karty = []
        for kod, (tytul, slowa, tresc) in HASLA.items():
            if kod[0] != seria:
                continue
            slug_hasla = kod.lower()
            rysunek = f'/assets/pracownia-plansze/{slug_hasla}.webp'
            klip = ""
            if kod in PILOTAZE:
                media = f'/assets/pracownia-klipy/{slug_hasla}'
                klip = f"""
  <details class="kurs-klip">
    <summary>Zobacz scenę z Panem Drucikiem</summary>
    <video controls preload="none" poster="{media}.webp" width="960" height="540" aria-label="{escape(tytul)} · Pan Drucik">
      <source src="{media}.mp4" type="video/mp4">
      <track kind="captions" src="{media}.vtt" srclang="pl" label="Polski" default>
    </video>
  </details>"""
            karty.append(f"""
<article class="kurs-haslo" id="{kod.lower()}" data-haslo data-slowa="{escape(slowa)}">
  <h3>{escape(tytul)}</h3>
  <img class="kurs-rysunek" src="{rysunek}" width="880" height="370" loading="lazy" decoding="async" alt="{escape(OPISY_PLANSZ[kod])}">
  <div class="gen" data-gen="{slug_hasla}" hidden></div>
  <p>{escape(tresc)}</p>{okno_ide(kod)}{klip}
  <a href="/pracownia/#{kotwica(kod)}" aria-label="Zrób próbę: {escape(tytul)}">Zrób próbę</a>
</article>""")
        dzialy.append(f"""
<section class="container pracownia-sekcja" id="wiedza-{slug}" data-dzial-wiedzy>
  <h2>{nazwa}</h2>
  <div class="kurs-hasla">{"".join(karty)}</div>
</section>""")
    return html.replace("<!-- PRACOWNIA_WIEDZA -->", "\n".join(dzialy))
