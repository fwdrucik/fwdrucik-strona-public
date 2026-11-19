# -*- coding: utf-8 -*-
"""
Pobiera ilustracje do wpisów blogowych z Wikimedia Commons.

Bierzemy wyłącznie pliki na licencjach pozwalających na użycie komercyjne
(CC0, CC BY, CC BY-SA, domena publiczna) i zapisujemy dane do podpisu:
autor, licencja, adres strony pliku. Podpis musi znaleźć się pod obrazem —
to warunek licencji, nie ozdobnik.

Uruchomienie:
    python pobierz-grafiki.py            # pobiera brakujące
    python pobierz-grafiki.py --od-nowa  # nadpisuje wszystkie
"""

import argparse
import html
import json
import os
import re
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
CEL = os.path.join(BASE, "assets", "blog")
DANE = os.path.join(BASE, "assets", "blog", "zrodla.json")
API = "https://commons.wikimedia.org/w/api.php"
UA = "fwdrucik.pl-site-builder/1.0 (fwdrucik@gmail.com)"
SZEROKOSC = 1200

# nazwa_lokalna -> tytuł pliku na Commons
PLIKI = {
    "can-zlacze-obd2":      "File:2016-07 ODB-II connector 01.JPG",
    "rs485-okablowanie":    "File:RS-485 wiring.png",
    "esp32-plytka":         "File:ESP32 Dev Board.jpg",
    "arduino-uno":          "File:Arduino Uno board.jpg",
    "klimatyzacja-manometry": "File:Cool under pressure- 386th ECES HVAC technicians in action (9047740).jpg",
    "cnc-frezarka":         "File:CNC milling machine.jpg",
}

LICENCJE_OK = ("cc0", "cc by", "cc by-sa", "public domain", "pd")


def bez_html(tekst):
    return html.unescape(re.sub(r"<[^>]+>", "", tekst or "")).strip()


def format_i_wymiary(dane):
    """Rozpoznaje format i rozmiar z samych bajtów — API bywa niezgodne z tym,
    co realnie zwraca serwer miniatur, a width/height w HTML muszą się zgadzać."""
    if dane[:8] == b"\x89PNG\r\n\x1a\n":
        szer = int.from_bytes(dane[16:20], "big")
        wys = int.from_bytes(dane[20:24], "big")
        return ".png", szer, wys
    if dane[:2] == b"\xff\xd8":
        i = 2
        while i < len(dane) - 9:
            if dane[i] != 0xFF:
                i += 1
                continue
            znacznik = dane[i + 1]
            if znacznik in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                            0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                wys = int.from_bytes(dane[i + 5:i + 7], "big")
                szer = int.from_bytes(dane[i + 7:i + 9], "big")
                return ".jpg", szer, wys
            i += 2 + int.from_bytes(dane[i + 2:i + 4], "big")
        return ".jpg", 0, 0
    raise ValueError("nieznany format obrazu")


def pobierz_json(adres):
    req = urllib.request.Request(adres, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as odp:
        return json.load(odp)


def metadane(tytuly):
    adres = API + "?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "titles": "|".join(tytuly),
        "prop": "imageinfo", "iiprop": "url|extmetadata",
        "iiurlwidth": str(SZEROKOSC),
    })
    strony = pobierz_json(adres)["query"]["pages"]
    return {p["title"]: p for p in strony.values() if "imageinfo" in p}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--od-nowa", action="store_true")
    args = ap.parse_args()

    os.makedirs(CEL, exist_ok=True)
    strony = metadane(list(PLIKI.values()))
    zrodla = {}

    for nazwa, tytul in PLIKI.items():
        p = strony.get(tytul)
        if not p:
            print(f"POMINIĘTO {nazwa}: nie znaleziono {tytul}")
            continue
        ii = p["imageinfo"][0]
        meta = ii["extmetadata"]
        licencja = bez_html(meta.get("LicenseShortName", {}).get("value", ""))
        if not licencja.lower().startswith(LICENCJE_OK):
            print(f"POMINIĘTO {nazwa}: licencja „{licencja}” wymaga sprawdzenia ręcznego")
            continue

        req = urllib.request.Request(ii["thumburl"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as odp:
            dane = odp.read()
        rozszerzenie, szerokosc, wysokosc = format_i_wymiary(dane)
        plik = os.path.join(CEL, nazwa + rozszerzenie)
        if args.od_nowa or not os.path.exists(plik):
            with open(plik, "wb") as f:
                f.write(dane)
            print(f"{nazwa}{len(dane)//1024} kB")

        zrodla[nazwa] = {
            "plik": f"/assets/blog/{nazwa}{rozszerzenie}",
            "szerokosc": szerokosc,
            "wysokosc": wysokosc,
            "tytul": p["title"].replace("File:", ""),
            "autor": bez_html(meta.get("Artist", {}).get("value", "")) or "autor nieznany",
            "licencja": licencja,
            "licencja_url": meta.get("LicenseUrl", {}).get("value", ""),
            "strona": ii["descriptionurl"],
        }

    with open(DANE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(zrodla, f, ensure_ascii=False, indent=2)
    print(f"\nZapisano dane {len(zrodla)} plików do {DANE}")
    for n, z in zrodla.items():
        print(f"  {n}: {z['szerokosc']}x{z['wysokosc']}, {z['autor'][:40]}, {z['licencja']}")


if __name__ == "__main__":
    main()
