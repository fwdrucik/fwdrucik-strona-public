# -*- coding: utf-8 -*-
"""
Generator statycznej strony fwdrucik.pl zoptymalizowanej pod SEO.

Uruchomienie:
    py build.py

Czyta:
    pages.py        — metadane wszystkich podstron (tytuł, opis, JSON-LD, breadcrumbs)
    src/<slug>.html — fragment HTML z treścią danej podstrony
    assets/         — CSS, JS, ikony, grafiki

Zapisuje gotowy serwis do dist/ (razem z robots.txt, sitemap.xml, .htaccess).
"""

import hashlib
import json
import os
import re
import shutil
from datetime import date
from html import escape, unescape
from pracownia_kurs import render_kompendium, render_kurs
from spolecznosc_build import community_body, public_knowledge, REVIEWS

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "src")
DIST = os.path.join(BASE, "dist")
ASSETS = os.path.join(BASE, "assets")
API = os.path.join(BASE, "api")

SITE = "https://fwdrucik.pl"
FIRMA = "F.W. DRUCIK"
TELEFON = "+48601726924"
TELEFON_TXT = "601 726 924"
EMAIL = "fwdrucik@gmail.com"
ULICA = "Domosław 13A"
KOD = "06-120"
# Punkt adresowy Domosław 13A z rejestru GUGiK, WGS 84.
LAT, LON = 52.622611, 20.978160
MIASTO = "Winnica"
NIP = "888-292-19-00"
OG_IMAGE = SITE + "/assets/og-fwdrucik.jpg"
# Wspólny zestaw źródeł obrazu hero — używany w preload i w <picture> na stronie głównej.
HERO_SIZES = "(max-width: 760px) calc(100vw - 36px), 56vw"
HERO_SRCSET_WEBP = "/assets/mechanizm-640.webp 640w, /assets/mechanizm-1100.webp 1100w"
MAPA = "https://www.google.com/maps/search/?api=1&query=Domos%C5%82aw+13A%2C+06-120+Winnica"

# Autor poradnikow. Przy tresciach technicznych wyszukiwarka wazy, kto za nimi
# stoi: podpis czlowieka z doswiadczeniem znaczy wiecej niz nazwa firmy.
# Puste "imie" wylacza mechanizm — wpisy podpisuje wtedy sama firma, tak jak
# dzialo sie to wczesniej.
AUTOR = {
    "imie": "Dawid Tutak",
    "rola": "Właściciel warsztatu F.W. DRUCIK",
    "opis": ("Dawid Tutak — inżynier Politechniki Łódzkiej, mechanik konstruktor i elektromechanik. "
             "Specjalizuje się w AI-native engineering. Dwukrotny Mechanik Roku powiatu pułtuskiego. Prowadzi warsztat F.W. DRUCIK "
             "i odpowiada za treść poradników."),
}


def autor_ld():
    """Wezel Person albo None, gdy nazwisko nie zostalo jeszcze podane."""
    if not AUTOR["imie"]:
        return None
    return {
        "@type": "Person",
        "@id": SITE + "/#autor",
        "name": AUTOR["imie"],
        "jobTitle": AUTOR["rola"],
        "description": AUTOR["opis"],
        "worksFor": {"@id": SITE + "/#organizacja"},
        "url": SITE + "/o-nas/",
        # Wyksztalcenie, kompetencje i wyroznienia. Google buduje z tego obraz
        # autora tresci — przy poradnikach technicznych to wprost przeklada sie
        # na to, czy artykul jest traktowany jako pisany przez fachowca.
        "alumniOf": {
            "@type": "CollegeOrUniversity",
            "name": "Politechnika Łódzka",
            "sameAs": "https://p.lodz.pl/",
        },
        "hasCredential": {
            "@type": "EducationalOccupationalCredential",
            "credentialCategory": "degree",
            "educationalLevel": "inżynier",
        },
        "knowsAbout": [
            "diagnostyka magistral pojazdowych CAN, LIN, FlexRay, J1939",
            "diagnostyka UDS ISO 14229",
            "elektromechanika pojazdowa",
            "spawanie MIG/MAG i TIG, w tym aluminium",
            "budowa i retrofit maszyn CNC",
            "systemy alarmowe, monitoring i audyty zabezpieczeń",
            "automatyka bram i sterowniki przemysłowe",
            "programowanie sterowników na ESP32",
            "programowanie obiektowe i strukturalne: Kotlin, Python, C++",
            "druk 3D i skanowanie 3D",
            "żywica epoksydowa",
        ],
        "award": [
            "Mechanik Roku powiatu pułtuskiego — plebiscyt Mistrzowie Motoryzacji (dwukrotnie)",
            "2. miejsce w województwie mazowieckim — plebiscyt Mistrzowie Motoryzacji",
        ],
    }


def autor_id():
    """Odwolanie do autora dla pola `author` — z odwrotem do firmy."""
    return {"@id": SITE + ("/#autor" if AUTOR["imie"] else "/#organizacja")}


# Google Analytics 4 — identyfikator pomiaru z panelu GA (format "G-XXXXXXXXXX").
# Pusty ciag = zaden kod sledzacy nie trafia na strone. Podmien tu jedna linie
# i zbuduj serwis od nowa; nie ma potrzeby dotykac zadnej podstrony z osobna.
GA4_ID = os.environ.get("GA4_ID", "G-FH5BBFCEMV").strip()


def analytics():
    """Skrypt GA4 albo pusty ciag, gdy identyfikator nie zostal jeszcze podany.

    Laduje sie asynchronicznie, wiec nie opoznia pierwszego wyswietlenia.
    `anonymize_ip` obcina ostatni oktet adresu — przy samym pomiarze ruchu
    nie trzeba wtedy pytac o zgode na profilowanie.
    """
    if not GA4_ID:
        return ""
    return (
        '\n<script async src="https://www.googletagmanager.com/gtag/js?id='
        + GA4_ID + '"></script>\n'
        '<script>\n'
        'window.dataLayer=window.dataLayer||[];\n'
        'function gtag(){dataLayer.push(arguments);}\n'
        'gtag("js",new Date());\n'
        'gtag("config","' + GA4_ID + '",{"anonymize_ip":true});\n'
        '</script>'
    )


FB = "https://www.facebook.com/profile.php?id=61591837903022"
IG = "https://www.instagram.com/fwdrucik/"
YT = "https://www.youtube.com/channel/UC25ZHkjkLUoSwsr7bfzIRjw"

# ---------------------------------------------------------------- JSON-LD

# Węzeł firmy — powtarzany na każdej podstronie, spięty stałym @id.
ORGANIZACJA = {
    "@type": ["LocalBusiness", "ProfessionalService"],
    "@id": SITE + "/#organizacja",
    "name": FIRMA,
    "alternateName": "FW Drucik",
    # Opis czyta i wyszukiwarka, i model jezykowy budujacy odpowiedz o firmie.
    # Bez niego wizytowka w wynikach skladala sie z samej nazwy i adresu.
    "description": (
        "Warsztat elektromechaniczny w Domosławiu pod Winnicą, powiat pułtuski. "
        "Elektryka samochodowa, instalacje maszyn, serwis elektronarzędzi i diagnostyka magistral "
        "pojazdowych CAN, LIN i J1939, obsługa klimatyzacji R134a i R1234yf, spawanie "
        "MIG/MAG, TIG i MMA, lutowanie twarde, remonty silników, budowa maszyn CNC, "
        "druk i skan 3D oraz odlewy z żywicy epoksydowej. Obsługujemy auta osobowe, "
        "dostawcze, ciężarowe oraz maszyny budowlane, rolnicze i produkcyjne. Programujemy falowniki, "
        "prototypujemy na Arduino i ESP32, piszemy oprogramowanie i wdrażamy automatyzacje z agentami AI. "
        "Montujemy sterowniki bram, centrale alarmowe i monitoring, integrujemy smart home oraz wykonujemy audyty bezpieczeństwa."
    ),
    "url": SITE + "/",
    "logo": {"@type": "ImageObject", "url": SITE + "/assets/fwdrucik-znak-256.png", "width": 256, "height": 256},
    "image": OG_IMAGE,
    "telephone": TELEFON,
    "email": EMAIL,
    "vatID": "PL8882921900",
    "taxID": NIP,
    "priceRange": "$$",
    "currenciesAccepted": "PLN",
    "paymentAccepted": "Gotówka, przelew bankowy",
    "geo": {"@type": "GeoCoordinates", "latitude": LAT, "longitude": LON},
    "address": {
        "@type": "PostalAddress",
        "streetAddress": ULICA,
        "postalCode": KOD,
        "addressLocality": MIASTO,
        "addressRegion": "mazowieckie",
        "addressCountry": "PL",
    },
    "hasMap": MAPA,
    "openingHoursSpecification": [
        {
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "opens": "08:00",
            "closes": "17:00",
        },
        {
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Saturday"],
            "opens": "09:00",
            "closes": "13:00",
        },
    ],
    "areaServed": [
        {"@type": "City", "name": n}
        for n in [
            "Winnica", "Pułtusk", "Nasielsk", "Serock", "Płońsk", "Ciechanów",
            "Maków Mazowiecki", "Nowy Dwór Mazowiecki", "Legionowo", "Warszawa",
        ]
    ],
    "sameAs": [FB, IG, YT],
}


def organizacja_z_zalozycielem():
    """Dopina zalozyciela do wezla firmy, gdy nazwisko jest juz podane."""
    if AUTOR["imie"]:
        ORGANIZACJA["founder"] = {"@id": SITE + "/#autor"}
    return ORGANIZACJA

WEBSITE = {
    "@type": "WebSite",
    "@id": SITE + "/#strona",
    "url": SITE + "/",
    "name": FIRMA,
    "inLanguage": "pl-PL",
    "publisher": {"@id": SITE + "/#organizacja"},
}


def breadcrumbs_ld(sciezka):
    """sciezka: lista par (nazwa, url względny). Zwraca węzeł BreadcrumbList."""
    items = []
    for i, (nazwa, url) in enumerate(sciezka, start=1):
        items.append(
            {
                "@type": "ListItem",
                "position": i,
                "name": nazwa,
                "item": SITE + url,
            }
        )
    return {"@type": "BreadcrumbList", "@id": SITE + "/#okruszki", "itemListElement": items}


def faq_ld(pytania):
    """pytania: lista par (pytanie, odpowiedź w czystym tekście)."""
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": p,
                "acceptedAnswer": {"@type": "Answer", "text": o},
            }
            for p, o in pytania
        ],
    }


def service_ld(nazwa, opis, url, typ="Service"):
    return {
        "@type": typ,
        "name": nazwa,
        "description": opis,
        "url": SITE + url,
        "serviceType": nazwa,
        "provider": {"@id": SITE + "/#organizacja"},
        "areaServed": {"@type": "AdministrativeArea", "name": "powiat pułtuski, województwo mazowieckie"},
        "availableChannel": {
            "@type": "ServiceChannel",
            "serviceUrl": SITE + "/kontakt/",
            "servicePhone": TELEFON,
        },
    }


# ---------------------------------------------------------------- szablony

NAWIGACJA = [
    ("/uslugi/", "Usługi"),
    ("/blog/", "Blog"),
    ("/forum/", "Forum"),
    ("/narzedzia/", "Narzędzia"),
    ("/kompendium-ai/", "Kompendium AI"),
    ("/realizacje/", "Realizacje"),
    ("/sklep/", "Sklep"),
    ("/o-nas/", "O nas"),
    ("/kontakt/", "Kontakt"),
    ("/konto/", "Konto"),
]

FONTS = ("https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600;700"
         "&family=Hanken+Grotesk:wght@400;500;600;700&display=swap")


def head(p):
    url = SITE + p["url"]
    ld = {"@context": "https://schema.org", "@graph": p["graph"]}
    ld_json = json.dumps(ld, ensure_ascii=False, separators=(",", ":"))
    robots = p.get("robots", "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1")
    # Obraz hero jest elementem LCP tylko na stronie głównej — tylko tam ma sens preload.
    preload = ('\n<link rel="preload" as="image" href="/assets/mechanizm-1100.webp"'
               f' imagesrcset="{HERO_SRCSET_WEBP}" imagesizes="{HERO_SIZES}" fetchpriority="high">'
               if p["url"] == "/" else "")
    # Wpis bloga ma własną ilustrację. Bez tego każdy link do artykułu
    # w komunikatorze i na Facebooku pokazywał to samo zdjęcie warsztatu —
    # podgląd nie mówił nic o treści, więc nie zachęcał do kliknięcia.
    og = p.get("og_obraz") or {}
    og_img = SITE + og["src"] if og.get("src") else OG_IMAGE
    og_w = og.get("width", "1200")
    og_h = og.get("height", "630")
    og_alt = og.get("alt") or "Warsztat F.W. DRUCIK — elektromechanika, spawanie i obróbka metalu"
    # Chrome ściska klatki przejścia między długą mapą i kompendium.
    przejscie = "\n<style>@view-transition{navigation:none}</style>" if p["url"].startswith("/pracownia/") else ""
    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{p['title']}</title>
<meta name="description" content="{p['desc']}">
<link rel="canonical" href="{url}">
<meta name="robots" content="{robots}">
<meta name="author" content="{FIRMA}">
<meta name="geo.region" content="PL-MZ">
<meta name="geo.placename" content="Winnica, powiat pułtuski">
<meta name="geo.position" content="{LAT:.6f};{LON:.6f}">
<meta name="ICBM" content="{LAT:.6f}, {LON:.6f}">
<link rel="alternate" type="text/markdown" title="LLM Context Data" href="/llms.txt">
<link rel="alternate" type="application/rss+xml" title="Blog techniczny F.W. DRUCIK" href="/rss.xml">
<meta property="og:type" content="{p.get('og_type', 'website')}">
<meta property="og:locale" content="pl_PL">
<meta property="og:site_name" content="{FIRMA}">
<meta property="og:title" content="{p['title']}">
<meta property="og:description" content="{p['desc']}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="{og_w}">
<meta property="og:image:height" content="{og_h}">
<meta property="og:image:alt" content="{og_alt}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{p['title']}">
<meta name="twitter:description" content="{p['desc']}">
<meta name="twitter:image" content="{og_img}">
<meta name="theme-color" content="#101716">
<link rel="icon" href="/assets/fwdrucik-znak-64.png" type="image/png" sizes="64x64">
<link rel="apple-touch-icon" href="/assets/fwdrucik-znak-192.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>{preload}
<link rel="stylesheet" href="/assets/style.css">{przejscie}
<link rel="stylesheet" href="/assets/spolecznosc.css">
<link rel="stylesheet" href="/assets/warsztat.css">
<link rel="stylesheet" href="{FONTS}" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="{FONTS}"><style>.reveal{{opacity:1;transform:none}}</style></noscript>
<script type="application/ld+json">{ld_json}</script>{analytics()}
</head>
<body data-slug="{p['url'].replace('/', '-').strip('-')}" data-scenes-module="/assets/warsztat3d.js">
<a class="skip-link" href="#tresc">Przejdź do treści</a>
"""


def header(aktywny):
    def is_act(url):
        return ' aria-current="page" class="active"' if (aktywny.startswith(url) and url != "/") or (aktywny == url) else ""

    def is_cat_act(prefix):
        return ' active' if aktywny.startswith(prefix) else ''

    return f"""<header>
  <div class="header-top-bar">
    <div class="container header-top-inner">
      <div class="header-status" id="workshop-status" title="Godziny otwarcia: Pn-Pt 8:00-17:00, Sob 9:00-13:00">
        <span class="status-indicator"></span>
        <span class="status-label">Warsztat czynny: <b>pn–pt 8:00–17:00, sob 9:00–13:00</b></span>
      </div>
      <div class="header-quick-links">
        <a href="/narzedzia/" class="quick-link">⚙ Kalkulatory inżynierskie</a>
        <a href="/kompendium-ai/" class="quick-link">🤖 Baza AI</a>
        <a href="/konto/" class="quick-link">👤 Strefa Klienta</a>
      </div>
    </div>
  </div>
  <div class="nav">
    <a href="/" class="brand" aria-label="{FIRMA} — strona główna">
      <img src="/assets/fwdrucik-naglowek.webp" width="352" height="106" alt="">
    </a>
    <nav class="nav-menu" id="primary-nav" aria-label="Menu główne">
      <div class="mobile-drawer-header">
        <div class="mobile-drawer-brand">F.W. <b>DRUCIK</b></div>
        <div class="mobile-quick-actions">
          <a class="mobile-quick-btn mobile-call-btn" href="tel:{TELEFON}">📞 Zadzwoń: {TELEFON_TXT}</a>
          <a class="mobile-quick-btn mobile-quote-btn" href="/kontakt/#formularz">⚡ Bezpłatna wycena</a>
        </div>
      </div>
      <ul class="nav-list">
        <li class="nav-item has-dropdown{is_cat_act('/uslugi/')}">
          <a href="/uslugi/"{is_act('/uslugi/')} class="nav-link dropdown-toggle" aria-haspopup="true" aria-expanded="false">
            Usługi <span class="nav-arrow" aria-hidden="true">▾</span>
          </a>
          <div class="dropdown-panel mega-menu" role="region" aria-label="Usługi warsztatowe i produkcyjne">
            <div class="mega-grid">
              <div class="mega-col">
                <p class="mega-title">Pojazdy & Elektryka</p>
                <a href="/uslugi/elektromechanika/"{is_act('/uslugi/elektromechanika/')} class="mega-item">
                  <span class="mega-icon">⚡</span>
                  <div class="mega-meta">
                    <b>Elektromechanika pojazdowa</b>
                    <span>Samochody, ciężarówki, maszyny i elektronarzędzia</span>
                  </div>
                </a>
                <a href="/uslugi/klimatyzacja-samochodowa/"{is_act('/uslugi/klimatyzacja-samochodowa/')} class="mega-item">
                  <span class="mega-icon">❄</span>
                  <div class="mega-meta">
                    <b>Klimatyzacja samochodowa</b>
                    <span>Czynniki R134a i R1234yf, szczelność, odgrzybianie</span>
                  </div>
                </a>
                <a href="/uslugi/remonty-silnikow/"{is_act('/uslugi/remonty-silnikow/')} class="mega-item">
                  <span class="mega-icon">🔧</span>
                  <div class="mega-meta">
                    <b>Remonty silników</b>
                    <span>Diagnostyka, rozrządy, głowice, osprzęt</span>
                  </div>
                </a>
              </div>
              <div class="mega-col">
                <p class="mega-title">Obróbka & Produkcja</p>
                <a href="/uslugi/spawanie/"{is_act('/uslugi/spawanie/')} class="mega-item">
                  <span class="mega-icon">🔥</span>
                  <div class="mega-meta">
                    <b>Spawanie MIG / MAG / TIG</b>
                    <span>Stal, aluminium, lutowanie twarde, konstrukcje</span>
                  </div>
                </a>
                <a href="/uslugi/maszyny-cnc/"{is_act('/uslugi/maszyny-cnc/')} class="mega-item">
                  <span class="mega-icon">⚙</span>
                  <div class="mega-meta">
                    <b>Budowa maszyn CNC & Retrofit</b>
                    <span>Frezarki, plotery, automatyzacja napędów</span>
                  </div>
                </a>
                <a href="/uslugi/druk-3d/"{is_act('/uslugi/druk-3d/')} class="mega-item">
                  <span class="mega-icon">🖨</span>
                  <div class="mega-meta">
                    <b>Druk 3D, Skan & Żywica</b>
                    <span>Prototypowanie FDM/SLA, żywica epoksydowa</span>
                  </div>
                </a>
              </div>
              <div class="mega-col mega-col--it">
                <p class="mega-title">IT & Automatyzacja</p>
                <a href="/uslugi/programowanie-aplikacje/"{is_act('/uslugi/programowanie-aplikacje/')} class="mega-item">
                  <span class="mega-icon">💻</span>
                  <div class="mega-meta">
                    <b>Programowanie Android & Python</b>
                    <span>Aplikacje Kotlin, skrypty diagnostyczne, C++ ESP32</span>
                  </div>
                </a>
                <a href="/automatyzacje/"{is_act('/automatyzacje/')} class="mega-item">
                  <span class="mega-icon">🤖</span>
                  <div class="mega-meta">
                    <b>Automatyzacje procesów</b>
                    <span>n8n, agenci AI, integracje i szkolenia</span>
                  </div>
                </a>
              </div>
              <div class="mega-col">
                <p class="mega-title">Nadruki, instalacje i maszyny</p>
                <a href="/uslugi/nadruki-i-sublimacja/"{is_act('/uslugi/nadruki-i-sublimacja/')} class="mega-item">
                  <div class="mega-meta">
                    <b>Nadruki i sublimacja</b>
                    <span>Znakowanie</span>
                  </div>
                </a>
                <a href="/uslugi/bezpieczenstwo-obiektow/"{is_act('/uslugi/bezpieczenstwo-obiektow/')} class="mega-item">
                  <div class="mega-meta">
                    <b>Bezpieczeństwo obiektów</b>
                    <span>Systemy niskoprądowe</span>
                  </div>
                </a>
                <a href="/uslugi/budowa-maszyn/"{is_act('/uslugi/budowa-maszyn/')} class="mega-item">
                  <div class="mega-meta">
                    <b>Budowa maszyn na zamówienie</b>
                    <span>Konstrukcja i obróbka</span>
                  </div>
                </a>
                <div class="mega-footer-link">
                  <a href="/uslugi/" class="btn-mega-all">Wszystkie usługi warsztatu &rarr;</a>
                </div>
              </div>
            </div>
          </div>
        </li>
        <li class="nav-item has-dropdown{is_cat_act('/blog/') or is_cat_act('/filmy/') or is_cat_act('/forum/') or is_cat_act('/narzedzia/') or is_cat_act('/kompendium-ai/')}">
          <a href="/blog/" class="nav-link dropdown-toggle" aria-haspopup="true" aria-expanded="false">
            Wiedza & Narzędzia <span class="nav-arrow" aria-hidden="true">▾</span>
          </a>
          <div class="dropdown-panel dropdown-simple" role="region" aria-label="Wiedza i narzędzia">
            <a href="/blog/"{is_act('/blog/')} class="dropdown-item">
              <span class="item-ico">📝</span>
              <div><b>Blog techniczny</b><span>Poradniki, oscyloskop, CAN, spawanie</span></div>
            </a>
            <a href="/filmy/"{is_act('/filmy/')} class="dropdown-item">
              <span class="item-ico">🎬</span>
              <div><b>Filmy z warsztatu</b><span>Rolki i poradniki wideo</span></div>
            </a>
            <a href="/forum/"{is_act('/forum/')} class="dropdown-item">
              <span class="item-ico">💬</span>
              <div><b>Forum dyskusyjne</b><span>Wymiana wiedzy, schematy i dyskusje</span></div>
            </a>
            <a href="/narzedzia/"{is_act('/narzedzia/')} class="dropdown-item">
              <span class="item-ico">⚙</span>
              <div><b>Narzędzia online</b><span>Kalkulatory CNC, spadków napięć, drutu</span></div>
            </a>
            <a href="/pracownia/"{is_act('/pracownia/')} class="dropdown-item">
              <span class="item-ico">⚡</span>
              <div><b>Pracownia Drucika</b><span>Elektronika, Arduino i druk 3D dla najmłodszych</span></div>
            </a>
            <a href="/kompendium-ai/"{is_act('/kompendium-ai/')} class="dropdown-item">
              <span class="item-ico">🧠</span>
              <div><b>Kompendium AI</b><span>Sztuczna inteligencja w inżynierii</span></div>
            </a>
          </div>
        </li>
        <li class="nav-item has-dropdown{is_cat_act('/sklep/') or is_cat_act('/koszulki/') or is_cat_act('/realizacje/')}">
          <a href="/sklep/" class="nav-link dropdown-toggle" aria-haspopup="true" aria-expanded="false">
            Sklep & Realizacje <span class="nav-arrow" aria-hidden="true">▾</span>
          </a>
          <div class="dropdown-panel dropdown-simple" role="region" aria-label="Sklep i realizacje">
            <a href="/sklep/"{is_act('/sklep/')} class="dropdown-item">
              <span class="item-ico">🛍</span>
              <div><b>Sklep & Rękodzieło</b><span>Patery drewno/żywica, świeczniki, części</span></div>
            </a>
            <a href="/koszulki/" class="dropdown-item"{' aria-current="page"' if aktywny == '/koszulki/' else ''}>
              <span class="item-ico">👕</span>
              <div><b>Koszulki z nadrukiem</b><span>Pierwsza seria w przygotowaniu</span></div>
            </a>
            <a href="/realizacje/"{is_act('/realizacje/')} class="dropdown-item">
              <span class="item-ico">⭐</span>
              <div><b>Portfolio realizacji</b><span>Zdjęcia wykonanych zleceń i maszyn</span></div>
            </a>
            <a href="/#opinie" class="dropdown-item"><span class="item-ico">★</span><div><b>Opinie klientów</b><span>Oceny sklepu i strony</span></div></a>
          </div>
        </li>
        <li class="nav-item"><a href="/o-nas/"{is_act('/o-nas/')} class="nav-link">O nas</a></li>
        <li class="nav-item"><a href="/kontakt/"{is_act('/kontakt/')} class="nav-link">Kontakt</a></li>
      </ul>
    </nav>
    <div class="nav-actions">
      <a class="nav-action-btn nav-koszyk" href="/koszyk/" aria-label="Koszyk">
        <span class="nav-ico" aria-hidden="true">🛒</span>
        <span class="koszyk-licznik" data-koszyk-licznik hidden>0</span>
      </a>
      <a class="nav-action-btn nav-konto" href="/konto/" aria-label="Moje konto / Zaloguj">
        <span class="nav-ico" aria-hidden="true">👤</span>
      </a>
      <a class="nav-cta-wycena" href="/kontakt/#formularz" aria-label="Bezpłatna wycena zlecenia">Wycena</a>
      <a class="nav-tel" href="tel:{TELEFON}" aria-label="Zadzwoń {TELEFON_TXT}">
        <span class="nav-tel-ico" aria-hidden="true">📞</span>
        <span class="nav-tel-txt">{TELEFON_TXT}</span>
      </a>
      <button class="burger" aria-label="Rozwiń menu" aria-expanded="false" aria-controls="primary-nav">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>
"""


def okruszki(sciezka):
    """Widoczne okruszki nawigacyjne (bez strony głównej w tekście linku ostatniego elementu)."""
    if len(sciezka) < 2:
        return ""
    czesci = []
    for i, (nazwa, url) in enumerate(sciezka):
        if i == len(sciezka) - 1:
            czesci.append(f'<span aria-current="page">{nazwa}</span>')
        else:
            czesci.append(f'<a href="{url}">{nazwa}</a>')
    return ('<nav class="breadcrumbs" aria-label="Okruszki nawigacyjne"><div class="container">'
            + '<span class="sep">/</span>'.join(czesci)
            + "</div></nav>\n")


FOOTER = f"""<footer>
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <img src="/assets/logo.webp" width="80" height="44" alt="{FIRMA}" loading="lazy">
        <span class="brand-text">F.W. <b>DRUCIK</b></span>
      </div>
      <div class="footer-cols">
        <div class="footer-col">
          <p class="footer-col-title">Usługi</p>
          <a href="/uslugi/elektromechanika/">Elektromechanika</a>
          <a href="/uslugi/klimatyzacja-samochodowa/">Klimatyzacja samochodowa</a>
          <a href="/uslugi/spawanie/">Spawanie MIG/MAG/TIG/MMA</a>
          <a href="/uslugi/lutowanie-twarde/">Lutowanie twarde</a>
          <a href="/uslugi/remonty-silnikow/">Remonty silników</a>
        </div>
        <div class="footer-col">
          <p class="footer-col-title">Produkcja</p>
          <a href="/uslugi/maszyny-cnc/">Budowa maszyn CNC</a>
          <a href="/uslugi/druk-3d/">Druk i skan 3D</a>
          <a href="/uslugi/zywica-epoksydowa/">Żywica epoksydowa</a>
          <a href="/realizacje/">Realizacje</a>
          <a href="/sklep/">Sklep</a>
        </div>
        <div class="footer-col">
          <p class="footer-col-title">Firma & Społeczność</p>
          <a href="/o-nas/">O nas</a>
          <a href="/blog/">Blog techniczny</a>
          <a href="/forum/">Forum dyskusyjne</a>
          <a href="/narzedzia/">Narzędzia online</a>
          <a href="/kursy/">Kursy techniczne</a>
          <a href="/automatyzacje/">Automatyzacja AI dla firm</a>
          <a href="/konsultacje/">Konsultacje telefoniczne</a>
          <a href="/kompendium-ai/">Kompendium wiedzy AI</a>
          <a href="/konto/">Moje konto / Zaloguj</a>
          <a href="/obszar-dzialania/">Obszar działania</a>
          <a href="/kontakt/">Kontakt</a>
          <a href="/regulamin/">Regulamin sklepu</a>
          <a href="/odstapienie/">Odstąpienie od umowy</a>
          <a href="/polityka-prywatnosci/">Polityka prywatności</a>
        </div>
        <div class="footer-col">
          <p class="footer-col-title">Kontakt</p>
          <a href="tel:{TELEFON}">{TELEFON_TXT}</a>
          <a href="mailto:{EMAIL}">{EMAIL}</a>
          <a href="{MAPA}" target="_blank" rel="noopener">{ULICA}, {KOD} {MIASTO}</a>
          <a href="{FB}" target="_blank" rel="noopener">Facebook</a>
          <a href="{IG}" target="_blank" rel="noopener">Instagram</a>
          <a href="{YT}" target="_blank" rel="noopener">YouTube</a>
        </div>
      </div>
    </div>
    <div class="footer-bottom">© <span id="year">2026</span> {FIRMA} — {ULICA}, {KOD} {MIASTO}, NIP {NIP}. Wszelkie prawa zastrzeżone.</div>
  </div>
<p class="container"><a href="/#opinie">Opinie klientów</a><br>
<button type="button" data-open-cabinet aria-haspopup="dialog" aria-controls="detonator-modal" hidden>Zagraj w „Rozbrój instalację”</button></p>
</footer>

<!-- Easter egg: rozbrój instalację -->
<button type="button" id="detonator-btn" class="detonator-btn" title="Panel serwisowy" aria-label="Panel serwisowy" aria-haspopup="dialog" aria-controls="detonator-modal"><svg class="icon-svg" aria-hidden="true"><use href="/assets/icons.svg#icon-electro"/></svg></button>
<div class="lightbox" id="detonator-modal" role="dialog" aria-modal="true" aria-labelledby="detonator-title">
  <div class="lightbox-inner detonator-inner">
    <button class="lightbox-close" id="detonator-close" aria-label="Zamknij">&times;</button>
    <h2 id="detonator-title">Rozbrój instalację</h2>
    <p id="detonator-text">Gra losowa. Wybierz jeden z przewodów w wirtualnej rozdzielnicy.</p>
    <div class="workbench-cabinet" data-scene="cabinet"><canvas aria-hidden="true"></canvas></div>
    <div class="wire-cut-row">
      <button class="wire-btn" data-wire="red" type="button"><span class="wire-line red"></span>Czerwony</button>
      <button class="wire-btn" data-wire="blue" type="button"><span class="wire-line blue"></span>Niebieski</button>
      <button class="wire-btn" data-wire="yellow" type="button"><span class="wire-line yellow"></span>Żółty</button>
      <button class="wire-btn" data-wire="green" type="button"><span class="wire-line green"></span>Zielony</button>
    </div>
    <p id="detonator-result" role="status"></p>
    <a href="/kontakt/" class="workbench-link" id="detonator-offer" hidden>Skontaktuj się w sprawie rabatu</a>
    <button type="button" class="workbench-control" id="detonator-reset" hidden>Zresetuj bezpiecznik</button>
  </div>
</div>

<button type="button" id="assistant-launch" class="robot" aria-expanded="false" aria-controls="assistant-panel" data-script="/assets/asystent.js"><svg class="robot-svg" viewBox="0 0 120 140" width="96" height="112" aria-hidden="true" focusable="false"><defs><linearGradient id="rb-mosiadz" x1="0" y1="0" x2="1" y2="1"><stop class="robot-stop-jasny" offset="0" stop-color="#f0c46e"/><stop class="robot-stop-metal" offset=".55" stop-color="#c38a3a"/><stop class="robot-stop-cien" offset="1" stop-color="#7a5320"/></linearGradient><linearGradient id="rb-helm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a4766"/><stop offset="1" stop-color="#1b2338"/></linearGradient><filter id="rb-blask" x="-50%" y="-200%" width="200%" height="500%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><ellipse cx="60" cy="134" rx="30" ry="4" fill="#000" opacity=".35"/><g class="robot-nogi"><rect class="robot-noga-l" x="40" y="106" width="12" height="22" rx="4" fill="url(#rb-mosiadz)" stroke="#3b2a12"/><rect class="robot-noga-p" x="68" y="106" width="12" height="22" rx="4" fill="url(#rb-mosiadz)" stroke="#3b2a12"/><rect x="36" y="124" width="20" height="8" rx="3" fill="#1b2338"/><rect x="64" y="124" width="20" height="8" rx="3" fill="#1b2338"/></g><g class="robot-cialo"><g class="robot-reka-l"><rect x="16" y="64" width="12" height="34" rx="5" fill="url(#rb-mosiadz)" stroke="#3b2a12"/><circle cx="22" cy="100" r="6" fill="#1b2338"/></g><g class="robot-reka-p"><rect x="92" y="64" width="12" height="30" rx="5" fill="url(#rb-mosiadz)" stroke="#3b2a12"/><rect x="96" y="90" width="18" height="6" rx="2" fill="#2b3550" stroke="#0b1020"/><rect x="112" y="91.5" width="5" height="3" fill="#c9d3ea"/><g class="robot-iskry" fill="#ffd27a"><circle cx="120" cy="92" r="1.6"/><circle cx="117" cy="86" r="1.1"/><circle cx="119" cy="99" r="1.2"/><circle cx="113" cy="84" r=".9"/></g></g><rect x="28" y="58" width="64" height="52" rx="12" fill="url(#rb-mosiadz)" stroke="#3b2a12" stroke-width="1.5"/><circle cx="34" cy="64" r="1.6" fill="#3b2a12"/><circle cx="86" cy="64" r="1.6" fill="#3b2a12"/><circle cx="34" cy="104" r="1.6" fill="#3b2a12"/><circle cx="86" cy="104" r="1.6" fill="#3b2a12"/><circle cx="60" cy="82" r="13" fill="#0d1a36" stroke="#3b2a12" stroke-width="2"/><path d="M50 86a10 10 0 0 1 20 0" fill="none" stroke="#5ff3e6" stroke-width="1.4" opacity=".7"/><line class="robot-iglica" x1="60" y1="84" x2="60" y2="73" stroke="#ff5a4e" stroke-width="2" stroke-linecap="round"/><polyline points="36,98 46,98 50,94 70,94 74,98 84,98" fill="none" stroke="#5ff3e6" stroke-width="1.6" filter="url(#rb-blask)"/></g><g class="robot-glowa"><line x1="60" y1="10" x2="60" y2="2" stroke="#c9d3ea" stroke-width="2"/><circle class="robot-antena" cx="60" cy="2.5" r="2.6" fill="#ff5a4e"/><path d="M30 34c0-15 13-24 30-24s30 9 30 24v12c0 7-6 12-13 12H43c-7 0-13-5-13-12z" fill="url(#rb-helm)" stroke="#0b1020" stroke-width="1.5"/><circle cx="30" cy="38" r="4.5" fill="url(#rb-mosiadz)" stroke="#3b2a12"/><circle cx="90" cy="38" r="4.5" fill="url(#rb-mosiadz)" stroke="#3b2a12"/><rect x="38" y="26" width="44" height="20" rx="5" fill="#050b12" stroke="#5ff3e6" stroke-opacity=".35"/><rect class="robot-oczy" x="43" y="34" width="34" height="4" rx="2" fill="#5ff3e6" filter="url(#rb-blask)"/></g></svg><span class="robot-etykieta">Zapytaj DRUCIKA · AI</span></button>
<script src="/assets/drucik.js" defer></script>
<script src="/assets/script.js" defer></script>
<script src="/assets/spolecznosc.js" defer></script>
</body>
</html>
"""


USLUGI_LISTA = [
    ("/uslugi/elektromechanika/", "Elektromechanika"),
    ("/uslugi/klimatyzacja-samochodowa/", "Klimatyzacja samochodowa"),
    ("/uslugi/spawanie/", "Spawanie MIG/MAG/TIG/MMA"),
    ("/uslugi/lutowanie-twarde/", "Lutowanie twarde"),
    ("/uslugi/remonty-silnikow/", "Remonty silników"),
    ("/uslugi/maszyny-cnc/", "Budowa maszyn CNC"),
    ("/uslugi/druk-3d/", "Druk i skan 3D"),
    ("/uslugi/zywica-epoksydowa/", "Żywica epoksydowa"),
]


def aside(biezacy):
    """Panel boczny: karta kontaktowa + linkowanie wewnętrzne do pozostałych usług."""
    linki = "".join(
        f'<li><a href="{u}">{n}</a></li>' if u != biezacy
        else f'<li><span aria-current="page">{n}</span></li>'
        for u, n in USLUGI_LISTA
    )
    return f"""<aside class="sidebar">
  <div class="side-card side-card--kontakt">
    <h2>Szybka wycena</h2>
    <p>Opisz zlecenie. Wstępną wycenę przygotujemy bezpłatnie w ciągu 24 h roboczych.</p>
    <a class="btn btn-primary" href="tel:{TELEFON}">{TELEFON_TXT}</a>
    <a class="btn btn-outline" href="/kontakt/">Formularz kontaktowy</a>
    <dl class="side-dane">
      <dt>Warsztat</dt><dd>{ULICA}, {KOD} {MIASTO}</dd>
      <dt>Godziny</dt><dd>Pon–Pt 8:00–17:00<br>Sob 9:00–13:00</dd>
      <dt>E-mail</dt><dd><a href="mailto:{EMAIL}">{EMAIL}</a></dd>
    </dl>
  </div>
  <nav class="side-card" aria-label="Pozostałe usługi">
    <h2>Pozostałe usługi</h2>
    <ul class="side-lista">{linki}</ul>
  </nav>
</aside>"""


CTA = f"""<section class="cta-band">
  <div class="container">
    <h2>Opisz zlecenie — wycenimy je bezpłatnie</h2>
    <p>Pon–Pt 8:00–17:00, sobota 9:00–13:00. Odpowiadamy w ciągu 24 godzin roboczych.</p>
    <div class="hero-cta">
      <a href="tel:{TELEFON}" class="btn btn-primary">Zadzwoń: {TELEFON_TXT}</a>
      <a href="/kontakt/" class="btn btn-outline">Wyślij zapytanie</a>
    </div>
  </div>
</section>"""


def wersja_zasobu(nazwa):
    """Skrót treści pliku z assets/ doklejany do adresu jako ?v=...

    .htaccess podaje CSS i JS z `max-age=31536000, immutable`, a nazwy plików
    się nie zmieniają — bez tego stały odwiedzający dostawałby starą wersję
    przez rok po każdej poprawce (forum i konta przestawały u niego działać).
    HTML ma `max-age=0`, więc nowy adres z nowym skrótem dociera od razu.
    """
    sciezka = os.path.join(ASSETS, nazwa)
    if not os.path.isfile(sciezka):
        return ""
    with open(sciezka, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:10]


def wersjonuj(html):
    for nazwa in ("style.css", "warsztat.css", "warsztat3d.js", "script.js", "drucik.js", "pracownia.js", "pracownia-generatory.js", "pracownia-obwody.js", "narzedzia.js", "sklep.js", "admin-sklep.js", "spolecznosc.css", "spolecznosc.js", "asystent.js", "czat-admin.js", "tresci-admin.js"):
        wersja = wersja_zasobu(nazwa)
        if wersja:
            html = html.replace(f"/assets/{nazwa}", f"/assets/{nazwa}?v={wersja}")
    return html


def owin_tabele(html):
    """Każdą <table> bez opakowania wkłada w <div class="tabela-wrap">.

    Tabela techniczna ma `min-width`, więc na telefonie musi się przewijać
    w poziomie w swoim pudełku. Agent bloga potrafi wygenerować gołą <table>
    i wtedy tabela wychodziła poza ekran — opakowanie robimy przy budowaniu,
    żeby nie zależeć od tego, co napisze model.
    """
    wynik, ostatni = [], 0
    for m in re.finditer(r"<table[\s>]", html):
        start = m.start()
        przed = html[:start]
        # już opakowana? sprawdzamy najbliższy poprzedzający otwarty <div>
        otwarcie = przed.rfind('<div class="tabela-wrap">')
        if otwarcie != -1 and "</div>" not in przed[otwarcie:]:
            continue
        koniec = html.find("</table>", start)
        if koniec == -1:
            continue
        koniec += len("</table>")
        wynik.append(html[ostatni:start])
        wynik.append('<div class="tabela-wrap">' + html[start:koniec] + "</div>")
        ostatni = koniec
    wynik.append(html[ostatni:])
    return "".join(wynik)


def zrodlo_strony(p):
    """Surowa treść podstrony — z pliku w src/ albo gotowa, podana w metadanych.

    Podstrony kompendium nie mają pliku źródłowego: ich HTML powstaje z modułu
    `kompendium` przy budowaniu. Wszystkie miejsca czytające treść przechodzą
    przez tę funkcję, żeby nie trzeba było ich rozgałęziać osobno.
    """
    if p.get("html") is not None:
        return p["html"]
    with open(os.path.join(SRC, p["src"]), encoding="utf-8") as plik:
        html = plik.read()
    if p["src"] == "pracownia.html":
        return render_kurs(html, SRC)
    if p["src"] == "pracownia-kompendium.html":
        return render_kompendium(html)
    return html


def render(p, wpisy=(), indeks=None):
    ciało = zrodlo_strony(p)
    indeks = indeks or {}

    if p["url"] in indeks:
        meta = indeks[p["url"]]
        ciało = popraw_czas_czytania(ciało)
        ciało = wzbogac_blogposting(ciało, meta, wpisy)
        blok = blok_powiazane(
            powiazane(meta, wpisy),
            "Przeczytaj również",
            "Materiały z tego samego obszaru — diagnostyka, pomiary i praktyka warsztatowa.")
        blok = blok_autora() + blok
        usluga = KATEGORIA_USLUGA.get(meta["kategoria"])
        if usluga:
            blok += (f'\n<p class="powiazane-usluga">Potrzebujesz tego w praktyce? '
                     f'Zobacz, jak to robimy: <a href="{usluga}">nasza oferta w tym zakresie</a>.</p>\n')
        forum = KATEGORIA_FORUM.get(meta["kategoria"])
        if forum:
            kat, nazwa = forum
            blok += (f'\n<p class="powiazane-usluga">Masz przypadek, którego nie opisuje '
                     f'ten poradnik? Opisz go na forum w dziale '
                     f'<a href="/forum/?kat={kat}">{nazwa}</a> — odpowiadamy tam osobiście.</p>\n')
        # Sekcja komentarzy zamyka artykuł — powiązane wpisy mają być tuż nad nią.
        if '<section class="comments-section">' in ciało:
            ciało = ciało.replace('<section class="comments-section">',
                                  blok + '\n  <section class="comments-section">', 1)
        else:
            ciało += blok

    elif p["url"] == "/blog/":
        ciało = ciało.replace("{{SPIS-BLOGA}}", spis_tresci_bloga(wpisy))

    elif p["url"] == "/forum/":
        # Forum bez tresci statycznej nie mialo czego zaindeksowac ani czym
        # przytrzymac czytelnika, gdy zaden watek go akurat nie interesowal.
        ciało += blok_powiazane(
            wpisy[:6],
            "Zanim zapytasz — sprawdź poradniki",
            "Najnowsze artykuły z warsztatu. Odpowiedź na Twoje pytanie może już tam być.")
        ciało += ('\n<p class="powiazane-usluga">Wolisz od razu zlecić robotę? '
                  'Zobacz <a href="/uslugi/">pełną listę usług warsztatu</a> '
                  'albo napisz przez <a href="/kontakt/">formularz kontaktowy</a>.</p>\n')

    elif p["url"] in USLUGA_KATEGORIE and p["url"] != "/automatyzacje/":
        wybrane = [w for w in wpisy if w["kategoria"] in USLUGA_KATEGORIE[p["url"]]][:3]
        blok = blok_powiazane(
            wybrane,
            "Poradniki z naszego warsztatu",
            "Sprawdź wskazówki przed zleceniem naprawy.")
        if "{{CTA}}" in ciało:
            ciało = ciało.replace("{{CTA}}", blok + "\n{{CTA}}", 1)
        else:
            ciało += blok

    ciało = river_table(ciało).replace("{{ASIDE}}", aside(p["url"])).replace("{{CTA}}", CTA)
    ciało = community_body(ciało, p["url"])
    ciało = owin_tabele(ciało)
    return wersjonuj(
        head(p)
        + header(p["url"])
        + okruszki(p.get("okruszki", []))
        + '<main id="tresc">\n'
        + ciało
        + "\n</main>\n"
        + FOOTER
    )



# ---------------------------------------------------------------- wpisy bloga

DATY = os.path.join(BASE, "daty.json")

# Kategoria wpisu wskazuje usługę, przy której warto ten poradnik pokazać.
# Czytelnik, który szuka wykonawcy, ma trafić z artykułu do oferty, a ze
# strony oferty do dowodu, że wiemy o czym mówimy.
KATEGORIA_USLUGA = {
    "AI i automatyzacja": "/automatyzacje/",
    "Znakowanie": "/uslugi/nadruki-i-sublimacja/",
    "Systemy niskoprądowe": "/uslugi/bezpieczenstwo-obiektow/",
    "Konstrukcja i obróbka": "/uslugi/budowa-maszyn/",
    "Elektromechanika": "/uslugi/elektromechanika/",
    "Elektronika i magistrale": "/uslugi/elektromechanika/",
    "Klimatyzacja": "/uslugi/klimatyzacja-samochodowa/",
    "Spawanie & CNC": "/uslugi/maszyny-cnc/",
    "Programowanie i kursy": "/uslugi/programowanie-aplikacje/",
    "Druk 3D": "/uslugi/druk-3d/",
}

# Dzial bloga wskazuje tez dzial forum. Czytelnik, ktory po artykule ma pytanie,
# ma gdzie je zadac, a watki forum dostaja linki z tresci zamiast wisiec bez
# zadnego odnosnika poza menu glownym.
KATEGORIA_FORUM = {
    "Elektromechanika": ("elektro", "Elektromechanika"),
    "Elektronika i magistrale": ("elektro", "Elektromechanika"),
    "Klimatyzacja": ("klimatyzacja", "Klimatyzacja"),
    "Spawanie & CNC": ("spawanie", "Spawanie & CNC"),
    "Programowanie i kursy": ("spawanie", "Spawanie & CNC"),
    "Druk 3D": ("spawanie", "Spawanie & CNC"),
}

# Odwrotnie: która usługa ma pokazać wpisy z których działów bloga.
USLUGA_KATEGORIE = {}
for _kat, _usl in KATEGORIA_USLUGA.items():
    USLUGA_KATEGORIE.setdefault(_usl, []).append(_kat)
USLUGA_KATEGORIE["/uslugi/spawanie/"] = ["Spawanie & CNC"]


def _pole(html, wzor, dom=""):
    m = re.search(wzor, html, re.S)
    return m.group(1).strip() if m else dom


def meta_wpisu(p):
    """Dane wpisu potrzebne kanalowi RSS, blokom powiazanych wpisow i og:image.

    Zrodlem jest sam plik wpisu w src/ — nie ma osobnego rejestru, ktory moglby
    sie z nim rozjechac po recznej poprawce.
    """
    html = zrodlo_strony(p)
    obraz = None
    m = re.search(r'<img[^>]+src="(/assets/blog/[^"]+)"[^>]*>', html)
    if m:
        tag = m.group(0)
        obraz = {
            "src": m.group(1),
            "width": _pole(tag, r'width="(\d+)"', "1200"),
            "height": _pole(tag, r'height="(\d+)"', "675"),
            "alt": _pole(tag, r'alt="([^"]*)"'),
        }
    else:
        # Wpis bez wlasnej ilustracji dostaje karte tytulowa z og-obrazki.py.
        # Wczesniej wszystkie takie wpisy podstawialy jedno zdjecie warsztatu,
        # wiec kazdy link w komunikatorze wygladal tak samo.
        # Slug bierzemy z nazwy pliku zrodlowego, bo adres wpisu bywa inny
        # niz nazwa pliku (np. blog-spawanie-tig-aluminium.html leci pod
        # /blog/spawanie-tig-aluminium-vs-mig/).
        slug = re.sub(r"^blog-|\.html$", "", p.get("src") or "")
        karta = os.path.join(ASSETS, "og", slug + ".jpg")
        if os.path.isfile(karta):
            obraz = {
                "src": f"/assets/og/{slug}.jpg",
                "width": "1200",
                "height": "630",
                "alt": re.sub(r"<[^>]+>", "", _pole(html, r"<h1[^>]*>(.*?)</h1>")).strip()
                       + " — F.W. DRUCIK",
            }
    return {
        "url": p["url"],
        "title": p["title"],
        "desc": p["desc"],
        "h1": re.sub(r"<[^>]+>", "", _pole(html, r"<h1[^>]*>(.*?)</h1>")).strip(),
        "kategoria": _pole(html, r'<span class="badge[^"]*">([^<]+)</span>').replace("&amp;", "&"),
        "data": _pole(html, r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"'),
        "obraz": obraz,
    }


def wpisy_bloga(strony):
    """Opublikowane wpisy, od najnowszego. Szkice pomijamy — maja noindex."""
    lista = [meta_wpisu(p) for p in strony
             if p["url"].startswith("/blog/") and p["url"] != "/blog/"
             and not p.get("noindex")]
    lista.sort(key=lambda w: w["data"] or "", reverse=True)
    return lista


def powiazane(wpis, wpisy, ile=3):
    """Wybiera pokrewne wpisy: najpierw ten sam dzial, potem wspolne slowa
    w tytule, na koncu swiezsza data."""
    def slowa(tekst):
        return set(re.findall(r"[a-ząćęłńóśźż]{5,}", tekst.lower()))
    moje = slowa(wpis["h1"] or wpis["title"])
    kandydaci = [k for k in wpisy if k["url"] != wpis["url"]]
    kandydaci.sort(key=lambda k: k["data"] or "", reverse=True)
    kandydaci.sort(key=lambda k: -((3 if k["kategoria"] == wpis["kategoria"] else 0)
                                   + len(moje & slowa(k["h1"] or k["title"]))))
    return kandydaci[:ile]


def blok_autora():
    """Krotka wizytowka pod wpisem — kto to napisal i dlaczego mozna mu wierzyc."""
    if not AUTOR["imie"]:
        return ""
    return (
        '\n<aside class="wizytowka-autora">\n'
        f'  <img src="/assets/logo.webp" width="80" height="44" alt="Logo {FIRMA} — elektromechanika i spawanie, Winnica" loading="lazy">\n'
        '  <div>\n'
        f'    <p class="wizytowka-kto">{AUTOR["imie"]}<span>{AUTOR["rola"]}</span></p>\n'
        f'    <p class="wizytowka-opis">{AUTOR["opis"]}</p>\n'
        '    <p class="wizytowka-opis"><strong>Ten materiał sprawdziłem przed publikacją</strong>'
        ' — wartości, kolejność czynności i to, czy według tego opisu da się pracować'
        ' przy warsztacie. Masz inne doświadczenie albo pytanie do konkretnego punktu?'
        ' Napisz, odpowiadam osobiście.</p>\n'
        '    <p class="wizytowka-linki"><a href="/kontakt/">Zadaj pytanie</a>'
        ' <a href="/o-nas/">O warsztacie</a>'
        ' <a href="/uslugi/">Zobacz usługi</a></p>\n'
        '  </div>\n'
        '</aside>\n'
    )


def blok_powiazane(wybrane, naglowek, opis):
    """Sekcja z linkami do pokrewnych wpisow.

    Powod: 25 z 28 artykulow nie mialo ani jednego linku przychodzacego poza
    lista /blog/. Wyszukiwarka docierala do nich jedna sciezka, a czytelnik po
    przeczytaniu artykulu nie mial dokad pojsc.
    """
    if not wybrane:
        return ""
    poz = "\n".join(
        '        <li><a href="{u}">'
        '<span class="powiazane-kat">{k}</span>'
        '<span class="powiazane-tytul">{t}</span></a></li>'.format(
            u=w["url"], k=w["kategoria"], t=w["h1"] or w["title"])
        for w in wybrane
    )
    return (
        '\n<section class="powiazane" aria-labelledby="powiazane-naglowek">\n'
        '  <div class="container">\n'
        '    <h2 id="powiazane-naglowek">' + naglowek + '</h2>\n'
        '    <p class="powiazane-opis">' + opis + '</p>\n'
        '    <ul class="powiazane-lista">\n' + poz + '\n    </ul>\n'
        '  </div>\n'
        '</section>\n'
    )


def wzbogac_blogposting(html, meta, wpisy):
    """Uzupelnia wezel BlogPosting o pola, ktorych Google uzywa przy artykulach.

    Brakowalo obrazka, dzialu i przypisania do bloga, a wydawca i autor byli
    powtarzana kopia firmy zamiast odwolania do wezla /#organizacja. Robimy to
    przy budowaniu, zeby objelo takze wpisy napisane wczesniej.
    """
    wzor = re.compile(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', re.S)
    for m in wzor.finditer(html):
        try:
            d = json.loads(m.group(1))
        except ValueError:
            continue
        if d.get("@type") != "BlogPosting":
            continue
        d["@type"] = ["BlogPosting", "TechArticle"]
        d["@id"] = SITE + meta["url"] + "#wpis"
        d["url"] = SITE + meta["url"]
        d["author"] = autor_id()
        d["publisher"] = {"@id": SITE + "/#organizacja"}
        d["isPartOf"] = {"@id": SITE + "/blog/#blog"}
        d.setdefault("dateModified", d.get("datePublished", ""))
        if meta["kategoria"]:
            d["articleSection"] = meta["kategoria"]
        if meta["obraz"]:
            d["image"] = {
                "@type": "ImageObject",
                "url": SITE + meta["obraz"]["src"],
                "width": int(meta["obraz"]["width"]),
                "height": int(meta["obraz"]["height"]),
            }
        else:
            d["image"] = OG_IMAGE
        tekst = re.sub(r"<[^>]+>", " ", _pole(html, r'<div id="blog-full-content"[^>]*>(.*)') or html)
        d["wordCount"] = len(tekst.split())
        d["timeRequired"] = "PT{}M".format(czas_czytania(tekst))
        nowy = ('<script type="application/ld+json">\n'
                + json.dumps(d, ensure_ascii=False, indent=2)
                + '\n</script>')
        return html[:m.start()] + nowy + html[m.end():]
    return html


def blog_ld(wpisy):
    """Wezel Blog na /blog/ — wyszukiwarka widzi liste artykulow jako calosc."""
    return {
        "@type": "Blog",
        "@id": SITE + "/blog/#blog",
        "name": "Blog techniczny F.W. DRUCIK",
        "description": "Poradniki warsztatowe: elektromechanika, diagnostyka magistral, "
                       "spawanie, obrobka CNC, druk 3D i programowanie sterownikow.",
        "url": SITE + "/blog/",
        "inLanguage": "pl-PL",
        "publisher": {"@id": SITE + "/#organizacja"},
        "blogPost": [
            {
                "@type": "BlogPosting",
                "@id": SITE + w["url"] + "#wpis",
                "headline": w["h1"] or w["title"],
                "url": SITE + w["url"],
                "datePublished": w["data"],
                "articleSection": w["kategoria"],
            }
            for w in wpisy
        ],
    }


def faq_ze_strony(p):
    """Pary pytanie-odpowiedz z sekcji <div class="faq"> w tresci podstrony.

    Wpisy bloga maja sekcje "Najczestsze pytania" widoczna dla czytelnika,
    ale niewidoczna dla wyszukiwarki — dane strukturalne FAQ mialy tylko
    strony uslug, gdzie pytania wpisano recznie. Czytamy je wprost ze
    znacznikow, wiec opis dla wyszukiwarki nie moze rozjechac sie z trescia.
    """
    html = zrodlo_strony(p)
    blok = re.search(r'(?s)<div class="faq">(.*?)</div>', html)
    if not blok:
        return None
    pary = []
    for d in re.findall(r"(?s)<details>(.*?)</details>", blok.group(1)):
        pytanie = _pole(d, r"(?s)<summary>(.*?)</summary>")
        odpowiedz = " ".join(re.findall(r"(?s)<p>(.*?)</p>", d))
        pytanie = re.sub(r"<[^>]+>", "", pytanie).strip()
        odpowiedz = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", odpowiedz)).strip()
        if pytanie and odpowiedz:
            pary.append((pytanie, odpowiedz))
    return faq_ld(pary) if pary else None


def indeks_szukania(strony, rendery, indeks_wpisow):
    """Indeks dla wyszukiwarki w /narzedzia/.

    Wyszukiwanie dzieje sie w przegladarce, wiec serwer nie musi nic liczyc,
    a plik idzie tak samo jak reszta serwisu — jednym wgraniem. Trzymamy tylko
    poczatek tresci, zeby indeks nie urosl do rozmiaru calego serwisu.
    """
    pozycje = []
    for p, html in zip(strony, rendery):
        if p.get("noindex"):
            continue
        m = re.search(r"(?s)<main[^>]*>(.*?)</main>", html)
        body = re.sub(r"(?s)<script.*?</script>", " ", m.group(1) if m else "")
        # unescape, bo w indeksie ma byc tekst do czytania, a nie &nbsp;
        tekst = re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", body))).strip()
        pozycja = {"u": p["url"], "t": unescape(p["title"]), "o": unescape(p["desc"]),
                   "s": tekst[:900]}
        wpis = indeks_wpisow.get(p["url"])
        if wpis and wpis["kategoria"]:
            pozycja["k"] = wpis["kategoria"]
        pozycje.append(pozycja)
    return json.dumps(pozycje, ensure_ascii=False, separators=(",", ":"))


def spis_tresci_bloga(wpisy):
    """Spis tresci nad lista wpisow: dzialy i tytuly, wszystko na jednym ekranie.

    Lista kart jest wygodna do przegladania, ale przy trzydziestu wpisach nie
    da sie z niej odczytac, o czym w ogole jest ten blog. Spis pokazuje to
    od razu i daje skok wprost do artykulu.
    """
    if not wpisy:
        return ""
    dzialy = {}
    for w in wpisy:
        dzialy.setdefault(w["kategoria"] or "Pozostałe", []).append(w)
    kolumny = []
    for dzial, lista in sorted(dzialy.items(), key=lambda x: -len(x[1])):
        pozycje = "".join(
            f'<li><a href="{w["url"]}">{w["h1"] or w["title"]}</a>'
            f'<span class="spis-data">{w["data"]}</span></li>'
            for w in lista
        )
        usluga = KATEGORIA_USLUGA.get(dzial)
        odnosnik = (f'      <p class="spis-usluga"><a href="{usluga}">'
                    f'Zobacz usługę z tego zakresu</a></p>\n' if usluga else "")
        kolumny.append(
            f'    <div class="spis-dzial">\n'
            f'      <h3>{dzial} <span class="spis-ile">{len(lista)}</span></h3>\n'
            f'      <ol>{pozycje}</ol>\n'
            f'{odnosnik}'
            f'    </div>'
        )
    # Rozwinięty spis ma na telefonie blisko trzy tysiące pikseli wysokości
    # i spycha karty wpisów poza zasięg kciuka. Stąd <details>: na szerokim
    # ekranie zostaje otwarty, na wąskim script.js zamyka go przy wczytaniu.
    return (
        '<details class="spis-bloga" open>\n'
        '  <summary class="spis-glowa">\n'
        '    <h2 id="spis-bloga-naglowek">Spis treści bloga</h2>\n'
        f'    <span class="spis-podpis">{len(wpisy)} artykułów w {len(dzialy)} działach</span>\n'
        '  </summary>\n'
        '  <p class="spis-wskazowka">Szukasz konkretnej rzeczy? '
        '<a href="/narzedzia/#szukaj">Użyj wyszukiwarki serwisu</a>.</p>\n'
        '  <div class="spis-siatka">\n' + "\n".join(kolumny) + '\n  </div>\n'
        '</details>\n'
    )


# Szablony PHP: plik zrodlowy w php/ -> sciezka w dist/ oraz adres, ktorego
# uzywa naglowek do zbudowania odsylaczy wzglednych i aktywnej pozycji w menu.
SZABLONY_PHP = [
    ("forum-watek.php",  "forum/watek.php",  "/forum/watek/", "/forum/", "Forum dyskusyjne"),
    ("forum-mapa.php",   "forum/mapa.php",   "/forum/",       "/forum/", "Forum dyskusyjne"),
    ("sklep-lista.php",  "sklep/index.php",  "/sklep/",       "/sklep/", "Sklep"),
    ("sklep-produkt.php", "sklep/produkt.php", "/sklep/",      "/sklep/", "Sklep"),
]


def river_table(html):
    if "{{RIVER_TABLE}}" in html:
        with open(os.path.join(SRC, "river-table-fragment.html"), encoding="utf-8") as f:
            return html.replace("{{RIVER_TABLE}}", f.read())
    return html


def strony_php():
    """Sklada podstrony serwowane przez PHP z tym samym ukladem co reszta serwisu.

    Strona renderowana po stronie serwera ma wygladac jak kazda inna podstrona,
    a jednoczesnie miec wlasny tytul, opis i adres kanoniczny. Naglowek
    generujemy wiec raz, ze znacznikami do podmiany, zamiast utrzymywac drugi
    szablon ukladu strony.
    """
    strony = {}
    for zrodlo, cel, adres, aktywny, nazwaOkruszka in SZABLONY_PHP:
        sciezka = os.path.join(BASE, "php", zrodlo)
        if not os.path.isfile(sciezka):
            continue

        p = {
            "url": adres,
            "title": "{{TYTUL}}",
            "desc": "{{OPIS}}",
            "robots": "{{ROBOTS}}",
            "graph": [ORGANIZACJA, WEBSITE,
                      breadcrumbs_ld([("Strona główna", "/"), (nazwaOkruszka, aktywny)])],
        }
        glowa = wersjonuj(head(p) + header(aktywny))
        # head() wstawia adres strony w canonical i og:url — tam ma trafic adres
        # konkretnej podstrony, wiec zamieniamy go na znacznik.
        glowa = glowa.replace(SITE + adres, "{{URL}}")
        stopka = wersjonuj(FOOTER)

        # Wersjonujemy takze tresc szablonu, nie tylko glowe i stopke —
        # inaczej skrypt dolaczony w samym szablonie zostawalby w pamieci
        # przegladarki po kazdej poprawce.
        tresc = wersjonuj(river_table(open(sciezka, encoding="utf-8").read()))
        if zrodlo == "sklep-lista.php":
            tresc = tresc.replace("</main>", REVIEWS + "\n</main>")
        strony[cel] = tresc.replace("{{GLOWA}}", glowa).replace("{{STOPKA}}", stopka)
    return strony


# ------------------------------------------------------------- kompendium AI

def kompendium_html(tekst):
    """Zamienia uproszczony Markdown treści kompendium na HTML serwisu.

    Obsługiwany podzbiór: nagłówki ### i ####, akapity, listy punktowane
    i numerowane, tabele, cytaty jako ramki z uwagą, blok kodu w potrójnych
    apostrofach oraz pogrubienia i kod w linii. Pełny parser byłby tu zbędną
    zależnością — a ten podzbiór pokrywa całą treść.

    Nagłówki ### stają się <h2>, bo <h1> na podstronie jest tytułem artykułu.
    """
    def w_linii(s):
        s = escape(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<em>\1</em>", s)
        return s

    wynik = []
    linie = tekst.strip().split("\n")
    i = 0
    while i < len(linie):
        linia = linie[i]
        goła = linia.strip()

        if not goła or goła == "---":
            i += 1
            continue

        # blok kodu
        if goła.startswith("```"):
            i += 1
            kod = []
            while i < len(linie) and not linie[i].strip().startswith("```"):
                kod.append(linie[i])
                i += 1
            i += 1
            wynik.append("<pre><code>" + escape("\n".join(kod)) + "</code></pre>")
            continue

        # nagłówki
        if goła.startswith("#### "):
            wynik.append(f"<h3>{w_linii(goła[5:])}</h3>")
            i += 1
            continue
        if goła.startswith("### "):
            wynik.append(f"<h2>{w_linii(goła[4:])}</h2>")
            i += 1
            continue

        # cytat jako ramka z uwagą
        if goła.startswith("> "):
            akapit = []
            while i < len(linie) and linie[i].strip().startswith(">"):
                akapit.append(linie[i].strip().lstrip(">").strip())
                i += 1
            wynik.append('<div class="uwaga"><p>' + w_linii(" ".join(akapit)) + "</p></div>")
            continue

        # tabela
        if goła.startswith("|"):
            wiersze = []
            while i < len(linie) and linie[i].strip().startswith("|"):
                wiersze.append(linie[i].strip())
                i += 1
            komorki = [[c.strip() for c in w.strip("|").split("|")] for w in wiersze]
            # druga linia to separator wyrównania — pomijamy ją
            naglowek = komorki[0]
            tresc = komorki[2:] if len(komorki) > 1 and set("-: ") >= set("".join(komorki[1])) else komorki[1:]
            thead = "".join(f"<th>{w_linii(c)}</th>" for c in naglowek)
            tbody = "".join(
                "<tr>" + "".join(f"<td>{w_linii(c)}</td>" for c in wiersz) + "</tr>"
                for wiersz in tresc
            )
            wynik.append(f"<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>")
            continue

        # listy
        if re.match(r"^[-*] ", goła) or re.match(r"^\d+\. ", goła):
            numerowana = bool(re.match(r"^\d+\. ", goła))
            pozycje = []
            while i < len(linie):
                bieżąca = linie[i].strip()
                if re.match(r"^[-*] ", bieżąca) or re.match(r"^\d+\. ", bieżąca):
                    pozycje.append(re.sub(r"^([-*]|\d+\.) ", "", bieżąca))
                elif bieżąca and linie[i].startswith("  ") and pozycje:
                    pozycje[-1] += " " + bieżąca
                else:
                    break
                i += 1
            znacznik = "ol" if numerowana else "ul"
            środek = "".join(f"<li>{w_linii(x)}</li>" for x in pozycje)
            wynik.append(f"<{znacznik}>{środek}</{znacznik}>")
            continue

        # akapit
        akapit = []
        while i < len(linie) and linie[i].strip() and not re.match(
                r"^(#{3,4} |[-*] |\d+\. |\||> |```|---$)", linie[i].strip()):
            akapit.append(linie[i].strip())
            i += 1
        if akapit:
            wynik.append("<p>" + w_linii(" ".join(akapit)) + "</p>")

    return "\n".join(wynik)


def popraw_czas_czytania(html):
    """Podmienia zadeklarowany czas czytania na policzony z tresci wpisu.

    W plikach zrodlowych czasy byly wpisane recznie i rozjechaly sie z tekstem:
    wpis na 900 slow deklarowal trzynascie minut, a kilkanascie innych mialo
    wpisane rowne osiem niezaleznie od dlugosci. Czytelnik, ktory raz sprawdzi,
    ze liczba klamie, przestaje ufac reszcie strony.
    """
    if "min czytania" not in html:
        return html
    tresc = _pole(html, r'<div id="blog-full-content"[^>]*>(.*)') or html
    minuty = czas_czytania(re.sub(r"<[^>]+>", " ", tresc))
    return re.sub(r"\d+\s*min czytania", f"{minuty} min czytania", html)


def czas_czytania(tekst):
    """Minuty czytania liczone z rzeczywistej liczby słów.

    W pierwotnej bazie czasy były wpisane ręcznie i zawyżone kilkukrotnie —
    artykuł na 203 słowa deklarował dwanaście minut. Przy 200 słowach na minutę
    liczba wychodzi sama i nie da się jej rozjechać z treścią.
    """
    slowa = len(re.sub(r"[#*|`>-]", " ", tekst).split())
    return max(1, round(slowa / 200))


def daty_stron(strony):
    """lastmod ma znaczyc: wtedy tresc naprawde sie zmienila.

    Wczesniej kazda budowa wpisywala dzisiejsza date do wszystkich adresow
    w sitemapie. Mapa, w ktorej wszystko zmienilo sie dzis, nie niesie zadnej
    informacji — wyszukiwarki przestaja brac lastmod pod uwage. Trzymamy wiec
    skrot tresci kazdej podstrony w daty.json i podbijamy date tylko wtedy, gdy
    skrot sie zmieni. Plik lezy w repozytorium, wiec dziala takze przy plytkim
    klonie w GitHub Actions, gdzie `git log` nie zna historii pliku.
    """
    stare = {}
    if os.path.isfile(DATY):
        with open(DATY, encoding="utf-8") as f:
            stare = json.load(f)
    dzis = date.today().isoformat()
    nowe = {}
    for p in strony:
        zrodlo = zrodlo_strony(p)
        skrot = hashlib.sha1((p["title"] + p["desc"] + zrodlo).encode("utf-8")).hexdigest()[:16]
        byl = stare.get(p["url"])
        if byl and byl.get("skrot") == skrot:
            nowe[p["url"]] = byl
            continue
        data = dzis
        if not byl:
            # Pierwsze poznanie strony: wpis bloga zna wlasna date publikacji,
            # wiec nie udajemy, ze powstal dzisiaj.
            m = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"', zrodlo)
            if m:
                data = m.group(1)
        nowe[p["url"]] = {"skrot": skrot, "data": data}
    with open(DATY, "w", encoding="utf-8", newline="\n") as f:
        json.dump(nowe, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    return {u: v["data"] for u, v in nowe.items()}


def rss(wpisy, daty):
    """Kanal RSS bloga.

    Czytniki, agregatory i automaty publikujace na Facebooku i Instagramie
    potrzebuja jednego adresu, pod ktorym widac nowe wpisy. Bez kanalu kazdy
    z nich musi parsowac HTML listy.
    """
    from datetime import datetime, timezone
    from email.utils import format_datetime

    def rfc822(d):
        try:
            chwila = datetime.strptime(d, "%Y-%m-%d").replace(hour=8, tzinfo=timezone.utc)
        except (ValueError, TypeError):
            chwila = datetime.now(timezone.utc)
        return format_datetime(chwila)

    pozycje = []
    for w in wpisy[:30]:
        pozycje.append(
            "    <item>\n"
            f"      <title>{escape(w['h1'] or w['title'])}</title>\n"
            f"      <link>{SITE}{w['url']}</link>\n"
            f'      <guid isPermaLink="true">{SITE}{w["url"]}</guid>\n'
            f"      <category>{escape(w['kategoria'])}</category>\n"
            f"      <pubDate>{rfc822(w['data'])}</pubDate>\n"
            f"      <description>{escape(w['desc'])}</description>\n"
            "    </item>"
        )
    ostatnia = rfc822(wpisy[0]["data"]) if wpisy else rfc822(None)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>Blog techniczny {FIRMA}</title>\n"
        f"    <link>{SITE}/blog/</link>\n"
        "    <description>Poradniki warsztatowe: elektromechanika, diagnostyka magistral, "
        "spawanie, obrobka CNC, druk 3D i programowanie sterownikow.</description>\n"
        "    <language>pl-pl</language>\n"
        f"    <lastBuildDate>{ostatnia}</lastBuildDate>\n"
        f'    <atom:link href="{SITE}/rss.xml" rel="self" type="application/rss+xml"/>\n'
        + "\n".join(pozycje)
        + "\n  </channel>\n</rss>\n"
    )


def llms_full(wpisy):
    """Pelny kontekst dla modeli jezykowych.

    llms-full.txt byl znak w znak kopia llms.txt — dwa adresy, jedna tresc,
    zero dodatkowej wiedzy. Tutaj dopisujemy caly spis artykulow, bo to jest
    ta czesc serwisu, ktorej krotki plik nie opisuje.
    """
    linie = [LLMS_TXT.rstrip(), "", "## Pelna lista artykulow bloga", ""]
    for w in wpisy:
        linie.append(f"### {w['h1'] or w['title']}")
        linie.append(f"- Adres: {SITE}{w['url']}")
        linie.append(f"- Dzial: {w['kategoria']}")
        linie.append(f"- Data publikacji: {w['data']}")
        linie.append(f"- Streszczenie: {w['desc']}")
        linie.append("")
    return "\n".join(linie)


# ---------------------------------------------------------------- zapis

def zapisz(sciezka_wzgledna, tresc):
    cel = os.path.join(DIST, sciezka_wzgledna.lstrip("/"))
    os.makedirs(os.path.dirname(cel), exist_ok=True)
    with open(cel, "w", encoding="utf-8", newline="\n") as f:
        f.write(tresc)


def sciezka_pliku(url):
    if url == "/":
        return "index.html"
    return url.strip("/") + "/index.html"


def sitemap(strony, daty):
    dzis = date.today().isoformat()
    wpisy = []
    for p in strony:
        if p.get("noindex"):
            continue
        wpisy.append(
            "  <url>\n"
            f"    <loc>{SITE}{p['url']}</loc>\n"
            f"    <lastmod>{daty.get(p['url'], dzis)}</lastmod>\n"
            f"    <changefreq>{p.get('changefreq', 'monthly')}</changefreq>\n"
            f"    <priority>{p.get('priority', '0.7')}</priority>\n"
            "  </url>"
        )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(wpisy)
            + "\n</urlset>\n")


# Manifest aplikacji webowej. Bez niego przegladarka mobilna nie proponuje
# dodania serwisu do ekranu glownego, a po dodaniu skrot dostaje przyciety
# zrzut ekranu zamiast ikony i otwiera sie z paskiem adresu.
MANIFEST = json.dumps({
    "name": FIRMA + " — elektromechanika, spawanie, CNC",
    "short_name": "F.W. DRUCIK",
    "description": ORGANIZACJA["description"],
    "lang": "pl-PL",
    "start_url": "/?zrodlo=pwa",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#0b0d10",
    "theme_color": "#0b0d10",
    "categories": ["business", "utilities"],
    "icons": [
        {"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "/assets/icon-maskable-512.png", "sizes": "512x512", "type": "image/png",
         "purpose": "maskable"},
    ],
    "shortcuts": [
        {"name": "Kontakt i wycena", "url": "/kontakt/"},
        {"name": "Blog techniczny", "url": "/blog/"},
        {"name": "Forum", "url": "/forum/"},
    ],
}, ensure_ascii=False, indent=2)


ROBOTS = f"""# robots.txt — {SITE}
# Wspólne reguły dla publicznej treści i ograniczenia dla wszystkich robotów.
User-agent: *
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: Claude-SearchBot
User-agent: Claude-User
User-agent: PerplexityBot
User-agent: Google-Extended
User-agent: GPTBot
User-agent: ClaudeBot
Allow: /

# Pozostałości po starej instalacji Joomla — nie indeksować
Disallow: /administrator/
Disallow: /autoinstalator/
Disallow: /cache/
Disallow: /tmp/
Disallow: /logs/
Disallow: /*?wyslano=

# Panele zarządzania i narzędzia warsztatowe — nie indeksować
Disallow: /admin/
Disallow: /kreator/

# Backend serwisu — same odpowiedzi JSON, nie ma tam treści dla wyszukiwarek
Disallow: /api/

Sitemap: {SITE}/sitemap.xml
Sitemap: {SITE}/rss.xml
Sitemap: {SITE}/forum/mapa.xml
"""

LLMS_TXT = f"""# F.W. DRUCIK — Elektromechanika, Spawanie, CNC, Klimatyzacja, Programowanie

> Warsztat elektromechaniczny i produkcyjny w Domosławiu 13A, 06-120 Winnica (powiat pułtuski, woj. mazowieckie).
> Telefon kontaktowy: +48 601 726 924 | Email: fwdrucik@gmail.com | NIP: 888-292-19-00

## O firmie
F.W. DRUCIK specjalizuje się w usługach elektromechanicznych, spawalniczych MIG/MAG/TIG, klimatyzacji samochodowej, budowie maszyn CNC, druku 3D oraz dedykowanym programowaniu aplikacji Android w języku Kotlin, Python, C++ i HTML. Obsługujemy klientów z Winnicy, Pułtuska, Nasielska, Serocka, Ciechanowa i Płońska.

## Kluczowe Podstrony i Oferta
- Elektromechanika pojazdowa i przemysłowa: {SITE}/uslugi/elektromechanika/
- Serwis klimatyzacji R134a i R1234yf: {SITE}/uslugi/klimatyzacja-samochodowa/
- Spawanie MIG/MAG/TIG Aluminium: {SITE}/uslugi/spawanie/
- AI-native engineering, czyli aplikacje i automatyzacje budowane z agentami AI (Android, Python, WWW): {SITE}/uslugi/programowanie-aplikacje/
- Budowa maszyn CNC na zamówienie: {SITE}/uslugi/maszyny-cnc/
- Druk 3D i skanowanie 3D: {SITE}/uslugi/druk-3d/
- Remonty silników spalinowych: {SITE}/uslugi/remonty-silnikow/
- Lutowanie twarde miedzi i mosiądzu: {SITE}/uslugi/lutowanie-twarde/
- Wyroby z żywicy epoksydowej: {SITE}/uslugi/zywica-epoksydowa/

- Nadruki i sublimacja: {SITE}/uslugi/nadruki-i-sublimacja/
- Bezpieczeństwo obiektów: {SITE}/uslugi/bezpieczenstwo-obiektow/
- Budowa maszyn na zamówienie: {SITE}/uslugi/budowa-maszyn/

## Automatyzacja i narzędzia AI dla firm
- [Wdrożenia n8n i agenci AI]({SITE}/automatyzacje/): integracja CRM, ERP, poczty i dokumentów, szkolenia pracowników, opieka po wdrożeniu oraz przykłady dla firm różnej wielkości.
- [Pierwsza automatyzacja n8n w firmie]({SITE}/blog/n8n-pierwsza-automatyzacja-w-firmie/): zapytania, błędy, duplikaty i akceptacja odpowiedzi.
- [Kompendium AI]({SITE}/kompendium-ai/): poradniki i pojęcia.

## Wiedza i społeczność
- [Blog techniczny]({SITE}/blog/)
- Forum Dyskusyjne: {SITE}/forum/
- Bezpłatna Wycena & Kontakt: {SITE}/kontakt/
"""



HTACCESS = r"""# ------------------------------------------------------------------
# fwdrucik.pl — konfiguracja Apache pod SEO i wydajność
# ------------------------------------------------------------------

Options -Indexes
DirectoryIndex index.html index.php

# Wymagane przez hosting-home.pl — wybór wersji PHP dla plików .php.
# Blok pochodzi z oryginalnego .htaccess tego katalogu, nie usuwać.
<FilesMatch "\.php$">
SetEnv CGI_HANDLER php84
</FilesMatch>

<IfModule mod_rewrite.c>
  RewriteEngine On

  # 1. Wymuszenie HTTPS
  RewriteCond %{HTTPS} !=on
  RewriteCond %{HTTP:X-Forwarded-Proto} !https
  RewriteRule ^(.*)$ https://fwdrucik.pl/$1 [R=301,L]

  # 2. Wersja bez www jako kanoniczna
  RewriteCond %{HTTP_HOST} ^www\.fwdrucik\.pl$ [NC]
  RewriteRule ^(.*)$ https://fwdrucik.pl/$1 [R=301,L]

  # 3. Watki forum: /forum/watek/12-tytul/ obsluguje skrypt PHP.
  #    Regula stoi przed doklejaniem ukosnika, bo sama przyjmuje oba warianty,
  #    a strona i tak przekieruje na wersje kanoniczna z pelnym tytulem.
  RewriteRule ^forum/watek/([0-9]+)(-[a-z0-9-]*)?/?$ forum/watek.php?id=$1 [L,QSA]
  RewriteRule ^forum/mapa\.xml$ forum/mapa.php [L]

  # 4. Karta produktu: /sklep/<slug>/ obsluguje skrypt PHP. Regula stoi przed
  #    doklejaniem ukosnika i przed katalogiem /sklep/, ktory ma wlasny index.php.
  RewriteRule ^sklep/([a-z0-9][a-z0-9-]*)/?$ sklep/produkt.php?slug=$1 [L,QSA]

  # 5. index.html w adresie -> adres katalogu (jeden URL = jedna treść).
  #    Adres docelowy podany w całości, bo TLS kończy się przed Apache
  #    i względne przekierowanie wychodziłoby na http:// (zbędny dodatkowy skok).
  RewriteCond %{THE_REQUEST} \s/+(.*/)?index\.html[\s?] [NC]
  RewriteRule ^(.*/)?index\.html$ https://fwdrucik.pl/$1 [R=301,L]

  # 6. Ukośnik na końcu adresu katalogu
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_URI} !(\.[a-zA-Z0-9]{1,5}|/)$
  RewriteRule ^(.*)$ https://fwdrucik.pl/$1/ [R=301,L]

  # 7. Stary adres jednostronicowej wersji z kotwicami
  RewriteRule ^uslugi\.html$ https://fwdrucik.pl/uslugi/ [R=301,L]
  RewriteRule ^kontakt\.html$ https://fwdrucik.pl/kontakt/ [R=301,L]

</IfModule>

# Strona błędu 404
ErrorDocument 404 /404.html

# ------------------------------------------------------------------
# Kompresja
# ------------------------------------------------------------------
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript
  AddOutputFilterByType DEFLATE application/javascript application/x-javascript
  AddOutputFilterByType DEFLATE application/json application/xml application/rss+xml
  AddOutputFilterByType DEFLATE image/svg+xml application/vnd.ms-fontobject
  AddOutputFilterByType DEFLATE font/ttf font/otf font/woff font/woff2
</IfModule>

<IfModule mod_brotli.c>
  AddOutputFilterByType BROTLI_COMPRESS text/html text/css text/javascript
  AddOutputFilterByType BROTLI_COMPRESS application/javascript application/json
  AddOutputFilterByType BROTLI_COMPRESS image/svg+xml
</IfModule>

# ------------------------------------------------------------------
# Cache przeglądarki
# ------------------------------------------------------------------
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresDefault                          "access plus 1 month"
  ExpiresByType text/html                 "access plus 0 seconds"
  ExpiresByType text/xml                  "access plus 0 seconds"
  ExpiresByType application/xml           "access plus 0 seconds"
  ExpiresByType text/css                  "access plus 1 year"
  ExpiresByType application/javascript    "access plus 1 year"
  ExpiresByType image/jpeg                "access plus 1 year"
  ExpiresByType image/png                 "access plus 1 year"
  ExpiresByType image/webp                "access plus 1 year"
  ExpiresByType image/avif                "access plus 1 year"
  ExpiresByType image/svg+xml             "access plus 1 year"
  ExpiresByType video/mp4                 "access plus 1 year"
  ExpiresByType image/x-icon              "access plus 1 year"
</IfModule>

<IfModule mod_headers.c>
  <FilesMatch "\.(css|js|jpg|jpeg|png|webp|avif|svg|mp4|woff2?)$">
    Header set Cache-Control "public, max-age=31536000, immutable"
  </FilesMatch>
  <FilesMatch "\.html$">
    Header set Cache-Control "public, max-age=0, must-revalidate"
  </FilesMatch>

  # Ochrona zaplecza i narzędzi web przed indeksowaniem w robotach
  SetEnvIf Request_URI "^/(admin|kreator)/" NOINDEX_TOOL=1
  Header always set X-Robots-Tag "noindex, nofollow, noarchive" env=NOINDEX_TOOL

  # Nagłówki bezpieczeństwa
  # Tryb raportowania. Przed wymuszaniem sprawdź sklep, formularz, mapy, filmy i panel.
  Header always set Content-Security-Policy-Report-Only "base-uri 'self'; object-src 'none'; frame-ancestors 'self'; form-action 'self' https://formsubmit.co; script-src 'self' https://www.googletagmanager.com"
  Header always set X-Content-Type-Options "nosniff"
  Header always set X-Frame-Options "SAMEORIGIN"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set Permissions-Policy "geolocation=(self), microphone=(), camera=()"
  # 180 dni, bez includeSubDomains — gdyby kiedyś wygasł certyfikat, skutek jest odwracalny szybciej
  Header always set Strict-Transport-Security "max-age=15552000"
  Header unset X-Powered-By
</IfModule>

# Poprawne typy MIME
<IfModule mod_mime.c>
  AddType image/svg+xml    .svg
  AddType image/webp       .webp
  AddType image/avif       .avif
  AddType video/mp4        .mp4
  AddType text/vtt         .vtt
  AddType font/woff2       .woff2
  AddType application/manifest+json .webmanifest
</IfModule>

# Blokada dostępu do plików wrażliwych
<FilesMatch "^(\.htaccess|\.htpasswd|\.git.*|.*\.py|.*\.md|.*\.sql|.*\.log|.*\.env|.*konfiguracja.*\.php|_.*\.php)$">
  <IfModule mod_authz_core.c>
    Require all denied
  </IfModule>
  <IfModule !mod_authz_core.c>
    Order allow,deny
    Deny from all
  </IfModule>
</FilesMatch>
"""


def main():
    from pages import STRONY  # import po zdefiniowaniu pomocników

    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)

    wpisy = wpisy_bloga(STRONY)
    indeks = {w["url"]: w for w in wpisy}

    for p in STRONY:
        if p["url"] in indeks:
            p["og_obraz"] = indeks[p["url"]]["obraz"]
            p.setdefault("og_type", "article")
        if p["url"] == "/blog/":
            p["graph"] = list(p["graph"]) + [blog_ld(wpisy)]
        # Wezel autora dokladamy tam, gdzie sie do niego odwolujemy: przy wpisach
        # bloga i na stronie "O nas". Bez niego `author` wskazywalby w prozne.
        osoba = autor_ld()
        if osoba and (p["url"] in indeks or p["url"] == "/o-nas/"):
            p["graph"] = list(p["graph"]) + [osoba]

        # FAQ dopisujemy tylko tam, gdzie nikt nie wpisal go recznie w pages.py.
        if not any(w.get("@type") == "FAQPage" for w in p["graph"]):
            faq = faq_ze_strony(p)
            if faq:
                p["graph"] = list(p["graph"]) + [faq]

    daty = daty_stron(STRONY)

    rendery = [render(p, wpisy, indeks) for p in STRONY]
    for p, html in zip(STRONY, rendery):
        # Podstrona z kluczem "php" jest skladana przez skrypt na serwerze.
        # Zapisanie obok niej index.html przykrylo by ja — DirectoryIndex
        # bierze index.html przed index.php.
        if p.get("php"):
            continue
        zapisz(sciezka_pliku(p["url"]), html)

    # 404 jako plik w katalogu głównym
    p404 = next(x for x in STRONY if x["url"] == "/404")
    zapisz("404.html", render(p404, wpisy, indeks))
    shutil.rmtree(os.path.join(DIST, "404"), ignore_errors=True)

    # Plik potwierdzający własność witryny w Google Search Console.
    # Nie usuwać — bez niego usługa traci weryfikację.
    zapisz("googlef582bb402e008585.html",
           "google-site-verification: googlef582bb402e008585.html\n")

    zapisz("api/_wiedza_publiczna.json", public_knowledge(STRONY, BASE))
    zapisz("api/_tresci_manifest.json", json.dumps(sorted(n for n in os.listdir(os.path.join(BASE,"src")) if n.endswith(".html") and n not in {"admin.html","konto.html","logowanie.html","rejestracja.html","reset-hasla.html"}), ensure_ascii=False))
    zapisz("robots.txt", ROBOTS)
    # Klucz weryfikacyjny IndexNow jest z definicji publiczny.
    indexnow = "5208cda6c552c267bd614a7dd177606d"
    zapisz(f"{indexnow}.txt", indexnow)
    zapisz("site.webmanifest", MANIFEST)
    zapisz("llms.txt", LLMS_TXT)
    zapisz("llms-full.txt", llms_full(wpisy))
    zapisz("sitemap.xml", sitemap(STRONY, daty))
    zapisz("rss.xml", rss(wpisy, daty))
    zapisz("szukaj.json", indeks_szukania(STRONY, rendery, indeks))

    # Watki forum i sklep: HTML sklada PHP, bo tresc powstaje w bazie
    # miedzy jednym budowaniem serwisu a drugim.
    for cel, tresc in strony_php().items():
        zapisz(cel, tresc)
    zapisz(".htaccess", HTACCESS)

    if os.path.isdir(ASSETS):
        # hero-bg.jpg to plik źródłowy dla optymalizatora — na serwer idą tylko warianty
        shutil.copytree(ASSETS, os.path.join(DIST, "assets"), dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("hero-bg.jpg"))

    # Backend PHP (konta, forum, komentarze). Świadomie pomijane:
    #   konfiguracja.php  — dane do bazy, tworzone ręcznie na serwerze,
    #   schemat.sql       — DDL wklejany raz w phpMyAdmin, nie ma czego szukać na WWW.
    if os.path.isdir(API):
        shutil.copytree(API, os.path.join(DIST, "api"), dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("konfiguracja.php", "*.sql", "__pycache__"))
        # Spis wpisów bloga dla panelu admina (moderacja.php?akcja=tresci&typ=wpis).
        # Serwer nie ma src/ ani pages.py, a nazwa pliku źródłowego ręcznych
        # wpisów różni się od sluga. Prefiks _ blokuje odczyt po HTTP (api/.htaccess).
        spis = [{"slug": p["url"].strip("/").split("/", 1)[1], "tytul": p["title"],
                 "src": p["src"], "ukryty": bool(p.get("noindex"))}
                for p in STRONY if re.fullmatch(r"/blog/[a-z0-9-]+/", p["url"]) and p.get("src")]
        zapisz("api/_blog.php", "<?php\nreturn json_decode(" + repr(
            json.dumps(spis, ensure_ascii=False)) + ", true);\n")

    # Zdalny kreator PWA dla sklepu i Allegro
    if os.path.isfile(os.path.join(SRC, "kreator.html")):
        os.makedirs(os.path.join(DIST, "kreator"), exist_ok=True)
        shutil.copy2(os.path.join(SRC, "kreator.html"), os.path.join(DIST, "kreator", "index.html"))

    ile = len([1 for _, _, f in os.walk(DIST) for _ in f])
    print(f"Gotowe: {len(STRONY)} podstron, {ile} plików w {DIST}")


if __name__ == "__main__":
    main()
