# -*- coding: utf-8 -*-
"""Podstrony sekcji /kompendium-ai/ budowane z modułu `kompendium`.

Treść nie leży w src/ jak reszta serwisu — powstaje tutaj, z danych. Dzięki temu
dopisanie artykułu do modułu `kompendium` wystarcza, żeby pojawił się nowy adres,
wpis w mapie serwisu i pozycja w wyszukiwarce.
"""

import re

from build import SITE, breadcrumbs_ld, czas_czytania, kompendium_html
from kompendium import ARTYKULY, DZIALY, PROMPTY, SLOWNIK, SPRZET, WORKFLOWY

GLOWNA = ("Strona główna", "/")
SEKCJA = ("Kompendium AI", "/kompendium-ai/")

DZIAL_PO_SLUGU = {d["slug"]: d for d in DZIALY}


def _skroc(tekst, limit):
    """Skraca na granicy słowa, bez wielokropka — ten też liczy się do limitu."""
    tekst = tekst.strip()
    if len(tekst) <= limit:
        return tekst
    uciety = tekst[:limit].rstrip()
    if " " in uciety:
        uciety = uciety[:uciety.rfind(" ")]
    return uciety.rstrip(" ,;:—–-")


def _tytul_seo(tytul, dopisek=""):
    """Tytuł w granicach 62 znaków, których pilnuje kontrola jakości.

    Najpierw bierzemy człon przed myślnikiem — w tytułach kompendium to zwykle
    właściwy temat, a reszta jest doprecyzowaniem. Dopiero gdy i to nie wchodzi,
    tniemy na granicy słowa.
    """
    pelny = tytul + dopisek
    if len(pelny) <= 62:
        return pelny
    czlon = re.split(r"\s+[—–]\s+", tytul, maxsplit=1)[0].strip()
    if len(czlon + dopisek) <= 62:
        return czlon + dopisek
    return _skroc(czlon, 62 - len(dopisek)) + dopisek


def _strona(url, title, desc, html, okruszki, dodatkowe=None, priority="0.6"):
    graph = []
    from build import ORGANIZACJA, WEBSITE
    graph.extend([ORGANIZACJA, WEBSITE])
    sciezka = [GLOWNA] + okruszki
    graph.append(breadcrumbs_ld(sciezka))
    graph.extend(dodatkowe or [])
    return {
        "url": url,
        "src": None,
        "html": html,
        "title": title,
        "desc": desc,
        "graph": graph,
        "okruszki": sciezka,
        "priority": priority,
        "changefreq": "monthly",
    }


# ------------------------------------------------------------------ artykuły

def _naglowek_artykulu(a, minuty):
    dzial = DZIAL_PO_SLUGU.get(a["dzial"], {"nazwa": "Kompendium"})
    tagi = "".join(f'<li>{t}</li>' for t in a["tagi"])
    return f"""<section class="page-hero">
  <div class="container">
    <div class="eyebrow">{dzial['nazwa']}</div>
    <h1>{a['tytul']}</h1>
    <p class="lead">{a['zajawka']}</p>
    <div class="komp-meta">
      <span class="badge badge-blue">{a['poziom']}</span>
      <span>{minuty} min czytania</span>
      <ul class="komp-tagi">{tagi}</ul>
    </div>
  </div>
</section>
"""


def _powiazane(a):
    """Trzy inne artykuły: najpierw z tego samego działu, potem pozostałe."""
    inne = [x for x in ARTYKULY if x["slug"] != a["slug"]]
    inne.sort(key=lambda x: 0 if x["dzial"] == a["dzial"] else 1)
    poz = "".join(
        f'<li><a href="/kompendium-ai/{x["slug"]}/">'
        f'<span class="powiazane-kat">{DZIAL_PO_SLUGU[x["dzial"]]["nazwa"]}</span>'
        f'<span class="powiazane-tytul">{x["tytul"]}</span></a></li>'
        for x in inne[:3]
    )
    return ('<section class="powiazane">\n  <div class="container">\n'
            '    <h2>Dalej w kompendium</h2>\n'
            '    <p class="powiazane-opis">Materiały z tego samego obszaru.</p>\n'
            f'    <ul class="powiazane-lista">{poz}</ul>\n'
            '  </div>\n</section>\n')


def _strony_artykulow():
    strony = []
    for a in ARTYKULY:
        minuty = czas_czytania(a["tresc"])
        html = (
            _naglowek_artykulu(a, minuty)
            + '<section class="diamond-bg">\n  <div class="container">\n'
            + '    <article class="komp-artykul article-body">\n'
            + kompendium_html(a["tresc"])
            + "\n    </article>\n  </div>\n</section>\n"
            + _powiazane(a)
        )
        dzial = DZIAL_PO_SLUGU[a["dzial"]]
        strony.append(_strona(
            f"/kompendium-ai/{a['slug']}/",
            a.get("tytul_seo") or _tytul_seo(a["tytul"]),
            _skroc(a["zajawka"], 158),
            html,
            [SEKCJA, (_skroc(a["tytul"], 48), f"/kompendium-ai/{a['slug']}/")],
            dodatkowe=[{
                "@type": "TechArticle",
                "@id": SITE + f"/kompendium-ai/{a['slug']}/#artykul",
                "headline": a["tytul"],
                "description": a["zajawka"],
                "url": SITE + f"/kompendium-ai/{a['slug']}/",
                "articleSection": dzial["nazwa"],
                "proficiencyLevel": a["poziom"],
                "keywords": ", ".join(a["tagi"]),
                "inLanguage": "pl-PL",
                "isPartOf": {"@id": SITE + "/kompendium-ai/#kompendium"},
                "author": {"@id": SITE + "/#organizacja"},
                "publisher": {"@id": SITE + "/#organizacja"},
            }],
        ))
    return strony


# ------------------------------------------------------------------- słownik

def _strona_slownika():
    dzialy = {}
    for h in SLOWNIK:
        dzialy.setdefault(h["dzial"], []).append(h)

    spis = "".join(
        f'<li><a href="#{_kotwica(d)}">{d}</a> <span>{len(h)}</span></li>'
        for d, h in dzialy.items()
    )
    sekcje = []
    for d, hasla in dzialy.items():
        pozycje = "".join(
            f'<div class="haslo" id="{_kotwica(h["termin"])}">'
            f'<h3>{h["termin"]}</h3><p>{h["definicja"]}</p></div>'
            for h in hasla
        )
        sekcje.append(f'<h2 id="{_kotwica(d)}">{d}</h2>\n<div class="hasla">{pozycje}</div>')

    html = f"""<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Kompendium AI</div>
    <h1>Słownik pojęć — {len(SLOWNIK)} haseł</h1>
    <p class="lead">Pojęcia AI wyjaśnione na potrzeby pracy: checkpoint, przestrzeń ukryta, okno kontekstu i wstrzykiwanie poleceń.</p>
  </div>
</section>

<section class="diamond-bg">
  <div class="container">
    <nav class="slownik-spis" aria-label="Działy słownika"><ul>{spis}</ul></nav>
    <div class="slownik">
      {"".join(sekcje)}
    </div>
  </div>
</section>
"""
    return _strona(
        "/kompendium-ai/slownik/",
        "Słownik pojęć AI — modele, sampling, agenci",
        f"{len(SLOWNIK)} haseł z generowania obrazów i modeli językowych: checkpoint, LoRA, "
        "CFG, kwantyzacja, okno kontekstu, MCP i pozostałe — wyjaśnione po ludzku.",
        html,
        [SEKCJA, ("Słownik pojęć", "/kompendium-ai/slownik/")],
        dodatkowe=[{
            "@type": "DefinedTermSet",
            "@id": SITE + "/kompendium-ai/slownik/#slownik",
            "name": "Słownik pojęć AI",
            "url": SITE + "/kompendium-ai/slownik/",
            "inLanguage": "pl-PL",
            "hasDefinedTerm": [
                {
                    "@type": "DefinedTerm",
                    "name": h["termin"],
                    "description": h["definicja"],
                    "inDefinedTermSet": {"@id": SITE + "/kompendium-ai/slownik/#slownik"},
                }
                for h in SLOWNIK
            ],
        }],
        priority="0.7",
    )


def _kotwica(tekst):
    zamiana = str.maketrans("ąćęłńóśźż", "acelnoszz")
    s = tekst.lower().translate(zamiana)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# ----------------------------------------------------------------- workflowy

def _strona_workflowow():
    karty = []
    for w in WORKFLOWY:
        wezly = "".join(
            f"<tr><td>{n}</td><td>{typ}</td><td>{par or '—'}</td></tr>"
            for n, typ, par in w["wezly"]
        )
        polaczenia = "".join(f"<li><code>{p}</code></li>" for p in w["polaczenia"])
        uwaga = (f'<div class="uwaga"><p>{w["uwaga"]}</p></div>' if w.get("uwaga") else "")
        karty.append(f"""<article class="komp-workflow" id="{w['slug']}">
  <h2>{w['tytul']}</h2>
  <p class="komp-meta"><span class="badge badge-blue">{w['poziom']}</span>
    <span>Pamięć karty: {w['vram']}</span></p>
  <p>{w['opis']}</p>
  <h3>Węzły</h3>
  <div class="tabela-wrap"><table>
    <thead><tr><th>Węzeł</th><th>Rola</th><th>Ustawienia</th></tr></thead>
    <tbody>{wezly}</tbody>
  </table></div>
  <h3>Połączenia</h3>
  <ul class="komp-polaczenia">{polaczenia}</ul>
  {uwaga}
</article>""")

    html = f"""<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Kompendium AI</div>
    <h1>Biblioteka schematów ComfyUI</h1>
    <p class="lead">Pięć schematów z listami połączeń: SDXL, Flux.1 z podwójnym enkoderem, łączenie LoRA, powiększanie do 4K i inpainting z maską.</p>
  </div>
</section>

<section class="diamond-bg">
  <div class="container">
    {"".join(karty)}
  </div>
</section>
"""
    return _strona(
        "/kompendium-ai/workflowy/",
        "Schematy workflow ComfyUI — SDXL, Flux, LoRA",
        "Pięć układów węzłów ComfyUI z listą połączeń: podstawowy SDXL, Flux.1 z DualCLIP, "
        "łączenie LoRA, powiększanie kafelkowe do 4K i inpainting z maską.",
        html,
        [SEKCJA, ("Schematy workflow", "/kompendium-ai/workflowy/")],
        priority="0.7",
    )


# -------------------------------------------------------------------- sprzęt

def _strona_sprzetu():
    karty = []
    for s in SPRZET:
        llm = "".join(f"<li>{x}</li>" for x in s["llm"])
        obraz = "".join(f"<li>{x}</li>" for x in s["obraz"])
        karty.append(f"""<article class="komp-sprzet" id="{s['slug']}">
  <h2>{s['poziom']}</h2>
  <p class="komp-karty"><strong>Przykładowe karty:</strong> {s['karty']}</p>
  <h3>Modele językowe</h3>
  <ul>{llm}</ul>
  <h3>Generowanie obrazów</h3>
  <ul>{obraz}</ul>
  <div class="uwaga"><p>{s['wskazowka']}</p></div>
</article>""")

    html = f"""<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Kompendium AI</div>
    <h1>Dobór sprzętu — co uruchomisz na swojej karcie</h1>
    <p class="lead">Cztery progi pamięci GPU: sprawdź, jakie modele językowe i obrazu uruchomisz na swojej karcie.</p>
  </div>
</section>

<section class="diamond-bg">
  <div class="container">
    <p>Reguła, od której warto zacząć: <strong>model językowy musi zmieścić się w pamięci karty
      w całości</strong>. Model rozłożony między kartę a pamięć operacyjną działa wielokrotnie
      wolniej — zwykle lepiej wybrać mniejszy model w mocniejszej kwantyzacji niż większy
      z częściowym przeniesieniem.</p>
    <p>Przy generowaniu obrazu jest odwrotnie: programy takie jak Forge i Fooocus potrafią
      przenosić warstwy w locie i dzięki temu uruchamiają modele znacznie większe niż pamięć
      karty. Płaci się za to czasem, nie jakością.</p>
    {"".join(karty)}
  </div>
</section>
"""
    return _strona(
        "/kompendium-ai/sprzet/",
        "Jaki sprzęt do AI lokalnie — dobór według VRAM",
        "Cztery progi pamięci karty i konkretne modele, które na nich działają: od 4 GB "
        "po 24 GB. Modele językowe, generowanie obrazów i wskazówki konfiguracyjne.",
        html,
        [SEKCJA, ("Dobór sprzętu", "/kompendium-ai/sprzet/")],
        priority="0.7",
    )


# ------------------------------------------------------------------- prompty

def _strona_promptow():
    karty = []
    for p in PROMPTY:
        karty.append(f"""<article class="komp-prompt" id="{p['slug']}">
  <h2>{p['tytul']}</h2>
  <p class="komp-cel"><strong>Dla:</strong> {p['cel']}</p>
  <pre><code>{p['prompt']}</code></pre>
  <div class="uwaga"><p>{p['uwagi']}</p></div>
</article>""")

    html = f"""<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Kompendium AI</div>
    <h1>Szablony promptów — obraz i modele językowe</h1>
    <p class="lead">Wzorce z objaśnieniami: dwa do generowania obrazu, jeden do podmiany twarzy i dwa prompty systemowe dla modeli językowych.</p>
  </div>
</section>

<section class="diamond-bg">
  <div class="container">
    {"".join(karty)}
  </div>
</section>
"""
    return _strona(
        "/kompendium-ai/prompty/",
        "Szablony promptów — Flux, SDXL i modele językowe",
        "Gotowe prompty do generowania obrazu i system prompty do modeli językowych, "
        "z wyjaśnieniem, która część za co odpowiada.",
        html,
        [SEKCJA, ("Szablony promptów", "/kompendium-ai/prompty/")],
        priority="0.6",
    )


# ----------------------------------------------------------------------- hub

def _strona_glowna():
    sekcje = []
    for d in DZIALY:
        pozycje = "".join(
            f'<li><a href="/kompendium-ai/{a["slug"]}/">'
            f'<span class="komp-poziom">{a["poziom"]}</span>'
            f'<span class="komp-tytul">{a["tytul"]}</span>'
            f'<span class="komp-zajawka">{a["zajawka"]}</span></a></li>'
            for a in ARTYKULY if a["dzial"] == d["slug"]
        )
        sekcje.append(f"""<section class="komp-dzial">
  <h2>{d['nazwa']}</h2>
  <p class="komp-dzial-opis">{d['opis']}</p>
  <ul class="komp-lista">{pozycje}</ul>
</section>""")

    slow = sum(len(re.sub(r"[#*|`>-]", " ", a["tresc"]).split()) for a in ARTYKULY)

    html = f"""<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Baza wiedzy</div>
    <h1>Kompendium wiedzy AI — modele lokalne od strony praktycznej</h1>
    <p class="lead">Materiały z naszego warsztatu: ComfyUI, Flux.1, lokalne modele językowe, Fooocus, SD WebUI Forge i agenci z narzędziami. Instrukcje uwzględniają możliwości domowego sprzętu.</p>
    <div class="hero-cta">
      <a class="btn btn-primary" href="/kompendium-ai/slownik/">Słownik pojęć</a>
      <a class="btn btn-outline" href="/kompendium-ai/sprzet/">Sprawdź swoją kartę</a>
    </div>
  </div>
</section>

<section class="diamond-bg">
  <div class="container">
    <div class="komp-liczby">
      <div><strong>{len(ARTYKULY)}</strong><span>opracowań</span></div>
      <div><strong>{len(SLOWNIK)}</strong><span>haseł słownika</span></div>
      <div><strong>{len(WORKFLOWY)}</strong><span>schematów węzłów</span></div>
      <div><strong>{slow // 100 * 100}</strong><span>słów treści</span></div>
    </div>

    {"".join(sekcje)}

    <section class="komp-dzial">
      <h2>Materiały uzupełniające</h2>
      <ul class="komp-lista">
        <li><a href="/kompendium-ai/slownik/"><span class="komp-poziom">Encyklopedia</span>
          <span class="komp-tytul">Słownik pojęć — {len(SLOWNIK)} haseł</span>
          <span class="komp-zajawka">Od checkpointu i przestrzeni ukrytej po okno kontekstu
            i wstrzykiwanie poleceń.</span></a></li>
        <li><a href="/kompendium-ai/workflowy/"><span class="komp-poziom">Schematy</span>
          <span class="komp-tytul">Biblioteka układów węzłów ComfyUI</span>
          <span class="komp-zajawka">Pięć gotowych schematów z pełną listą połączeń
            do odtworzenia.</span></a></li>
        <li><a href="/kompendium-ai/sprzet/"><span class="komp-poziom">Sprzęt</span>
          <span class="komp-tytul">Co uruchomisz na swojej karcie</span>
          <span class="komp-zajawka">Cztery progi pamięci i konkretne modele, które mają
            na nich sens.</span></a></li>
        <li><a href="/kompendium-ai/prompty/"><span class="komp-poziom">Wzorce</span>
          <span class="komp-tytul">Szablony promptów</span>
          <span class="komp-zajawka">Gotowe do skopiowania, z wyjaśnieniem, która część
            za co odpowiada.</span></a></li>
      </ul>
    </section>

    <div class="uwaga">
      <p>Kompendium powstało przy okazji budowy własnych narzędzi w warsztacie — między innymi
        aplikacji z modelem językowym działającym bez internetu. Jeśli szukasz wykonawcy takiego
        systemu, opisaliśmy to na stronie
        <a href="/uslugi/programowanie-aplikacje/">programowania i aplikacji</a>.</p>
    </div>
  </div>
</section>
"""
    return _strona(
        "/kompendium-ai/",
        "Kompendium wiedzy AI — ComfyUI, Flux, modele lokalne",
        "Praktyczna baza wiedzy o modelach uruchamianych lokalnie: ComfyUI i Flux.1, "
        "LM Studio i pliki GGUF, Fooocus, Forge oraz agenci z narzędziami.",
        html,
        [SEKCJA],
        dodatkowe=[{
            "@type": "Collection",
            "@id": SITE + "/kompendium-ai/#kompendium",
            "name": "Kompendium wiedzy AI",
            "url": SITE + "/kompendium-ai/",
            "inLanguage": "pl-PL",
            "publisher": {"@id": SITE + "/#organizacja"},
        }],
        priority="0.8",
    )


STRONY = [_strona_glowna()] + _strony_artykulow() + [
    _strona_slownika(),
    _strona_workflowow(),
    _strona_sprzetu(),
    _strona_promptow(),
]
