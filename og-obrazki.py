# -*- coding: utf-8 -*-
"""Generator grafik pomocniczych: kart Open Graph i ikon aplikacji webowej.

Uruchomienie:
    py og-obrazki.py

Karty OG powstaja tylko dla tych wpisow bloga, ktore nie maja wlasnej
ilustracji w tresci. Wczesniej kazdy taki wpis podstawial pod og:image to samo
zdjecie warsztatu — link do artykulu w komunikatorze wygladal identycznie jak
link do strony glownej i nie mowil nic o tresci.

Ikony (192/512 px) sa potrzebne manifestowi web-app; w assets nie bylo zadnej
kwadratowej ikony w tych rozmiarach.
"""

import glob
import os
import re
from html import unescape

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "src")
OG_DIR = os.path.join(BASE, "assets", "og")
ASSETS = os.path.join(BASE, "assets")

BG = (11, 13, 16)
PANEL = (26, 30, 36)
BLUE = (46, 194, 255)
ORANGE = (255, 138, 61)
TEXT = (231, 235, 240)
MUTED = (154, 164, 178)

FONTS = "C:/Windows/Fonts/"


def font(rozmiar, wariant="Bold"):
    """Bahnschrift ma waskie, techniczne litery — blisko Oswalda ze strony."""
    sciezka = FONTS + "bahnschrift.ttf"
    if os.path.isfile(sciezka):
        f = ImageFont.truetype(sciezka, rozmiar)
        try:
            f.set_variation_by_name("SemiBold Condensed" if wariant == "Bold" else "Condensed")
        except Exception:
            pass
        return f
    return ImageFont.truetype(FONTS + ("arialbd.ttf" if wariant == "Bold" else "arial.ttf"), rozmiar)


def bez_znacznikow(tekst):
    return unescape(re.sub(r"<[^>]+>", "", tekst)).strip()


def lam(rysunek, tekst, czcionka, szerokosc):
    linie, biezaca = [], ""
    for slowo in tekst.split():
        proba = (biezaca + " " + slowo).strip()
        if rysunek.textlength(proba, font=czcionka) <= szerokosc:
            biezaca = proba
        else:
            if biezaca:
                linie.append(biezaca)
            biezaca = slowo
    if biezaca:
        linie.append(biezaca)
    return linie


def karta(tytul, kategoria, plik):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # tlo: skos w kolorze panelu + akcent, zeby karta nie byla plaska plama
    d.polygon([(W * 0.80, 0), (W, 0), (W, H), (W * 0.66, H)], fill=PANEL)
    d.polygon([(W * 0.795, 0), (W * 0.815, 0), (W * 0.675, H), (W * 0.655, H)], fill=BLUE)
    d.rectangle([0, H - 12, W, H], fill=BLUE)
    d.rectangle([0, H - 12, W * 0.28, H], fill=ORANGE)

    marg = 72
    # nadkreslenie z kategoria
    f_kat = font(30)
    kat = (kategoria or "Poradnik warsztatowy").upper()
    d.text((marg, marg), kat, font=f_kat, fill=BLUE)
    d.line([(marg, marg + 52), (marg + d.textlength(kat, font=f_kat), marg + 52)], fill=BLUE, width=3)

    # tytul — rozmiar dobierany tak, zeby zmiescil sie w czterech linijkach
    for rozmiar in (72, 64, 58, 52, 46, 40):
        f_tyt = font(rozmiar)
        linie = lam(d, tytul, f_tyt, W * 0.58)
        if len(linie) <= 4:
            break
    y = marg + 110
    for linia in linie[:4]:
        d.text((marg, y), linia, font=f_tyt, fill=TEXT)
        y += int(rozmiar * 1.22)

    # stopka: firma i adres serwisu
    f_firma = font(40)
    f_adres = font(28, "Regular")
    d.text((marg, H - 132), "F.W. DRUCIK", font=f_firma, fill=TEXT)
    d.text((marg, H - 82), "fwdrucik.pl  ·  warsztat w Domosławiu pod Winnicą",
           font=f_adres, fill=MUTED)

    img.save(plik, "JPEG", quality=88, optimize=True, progressive=True)
    return W, H


def ikona(rozmiar, plik, maskowalna=False):
    img = Image.new("RGB", (rozmiar, rozmiar), BG)
    d = ImageDraw.Draw(img)
    # maskowalna ikona ma bezpieczny margines — system moze przyciac rogi
    pad = rozmiar * (0.22 if maskowalna else 0.1)
    d.rounded_rectangle([pad, pad, rozmiar - pad, rozmiar - pad],
                        radius=int(rozmiar * 0.06), outline=BLUE, width=max(2, rozmiar // 64))
    f = font(int(rozmiar * (0.3 if maskowalna else 0.36)))
    tekst = "FW"
    w = d.textlength(tekst, font=f)
    d.text(((rozmiar - w) / 2, rozmiar * (0.36 if maskowalna else 0.30)), tekst, font=f, fill=TEXT)
    f2 = font(int(rozmiar * (0.12 if maskowalna else 0.14)))
    t2 = "DRUCIK"
    w2 = d.textlength(t2, font=f2)
    d.text(((rozmiar - w2) / 2, rozmiar * (0.55 if maskowalna else 0.55)), t2, font=f2, fill=BLUE)
    img.save(plik, "PNG", optimize=True)


def main():
    os.makedirs(OG_DIR, exist_ok=True)
    zrobione = 0
    for plik in sorted(glob.glob(os.path.join(SRC, "blog-*.html"))):
        html = open(plik, encoding="utf-8").read()
        if re.search(r'<img[^>]+src="/assets/blog/', html):
            continue  # wpis ma wlasna ilustracje, karta nie jest potrzebna
        slug = os.path.basename(plik)[len("blog-"):-len(".html")]
        h1 = bez_znacznikow(re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1))
        m = re.search(r'<span class="badge[^"]*">([^<]+)</span>', html)
        kat = bez_znacznikow(m.group(1)) if m else ""
        cel = os.path.join(OG_DIR, slug + ".jpg")
        karta(h1, kat, cel)
        zrobione += 1
        print("karta OG:", os.path.relpath(cel, BASE))

    for r in (192, 512):
        ikona(r, os.path.join(ASSETS, f"icon-{r}.png"))
    ikona(512, os.path.join(ASSETS, "icon-maskable-512.png"), maskowalna=True)
    print(f"Gotowe: {zrobione} kart OG, 3 ikony aplikacji.")


if __name__ == "__main__":
    main()
