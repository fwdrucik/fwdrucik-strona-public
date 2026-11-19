# -*- coding: utf-8 -*-
"""
Przygotowanie lekkich wersji grafik do assets/ — uruchamiane ręcznie, nie przy każdym buildzie.

    py optymalizuj-grafike.py

Wymaga: Pillow oraz ffmpeg w PATH (do wyciągnięcia klatek-plakatów z filmów).
Filmy .mp4 pobierane są wcześniej z serwera do katalogu ZRODLA_WIDEO.
"""

import os
import subprocess

from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")
ZRODLA_WIDEO = r"C:\Users\Computer\AppData\Local\Temp\claude\ftp-backup"

SZEROKOSCI_HERO = [640, 1024, 1600, 1920]


def hero():
    src = os.path.join(ASSETS, "hero-bg.jpg")
    org = Image.open(src).convert("RGB")
    for w in SZEROKOSCI_HERO:
        h = round(org.height * w / org.width)
        mniejszy = org.resize((w, h), Image.LANCZOS)
        mniejszy.save(os.path.join(ASSETS, f"hero-bg-{w}.webp"), "WEBP", quality=78, method=6)
        mniejszy.save(os.path.join(ASSETS, f"hero-bg-{w}.jpg"), "JPEG",
                      quality=80, optimize=True, progressive=True)
        print(f"hero-bg-{w}: webp+jpg")


def logo():
    src = os.path.join(ASSETS, "favicon.png")
    org = Image.open(src).convert("RGBA")
    org.save(os.path.join(ASSETS, "logo.webp"), "WEBP", quality=88, method=6)
    # favicon 64x64 wycięty ze środka logo — kwadratowy, jak wymagają przeglądarki
    bok = min(org.size)
    lewo = (org.width - bok) // 2
    gora = (org.height - bok) // 2
    org.crop((lewo, gora, lewo + bok, gora + bok)).resize((64, 64), Image.LANCZOS).save(
        os.path.join(ASSETS, "favicon-64.png"), "PNG", optimize=True)
    print("logo.webp + favicon-64.png")


PLAKATY = {
    "promo.mp4": ("promo-poster", "00:00:01.5"),
    "matrix-industrial.mp4": ("matrix-poster", "00:00:02.0"),
    "logo-animated.mp4": ("logo-poster", "00:00:01.0"),
}


def plakaty():
    for plik, (nazwa, czas) in PLAKATY.items():
        zrodlo = os.path.join(ZRODLA_WIDEO, plik)
        if not os.path.isfile(zrodlo):
            print(f"pominięto {plik} — brak pliku w {ZRODLA_WIDEO}")
            continue
        tmp = os.path.join(ASSETS, f"{nazwa}.png")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", czas, "-i", zrodlo,
             "-frames:v", "1", "-vf", "scale=1280:-2", tmp],
            check=True,
        )
        klatka = Image.open(tmp).convert("RGB")
        klatka.save(os.path.join(ASSETS, f"{nazwa}.webp"), "WEBP", quality=72, method=6)
        klatka.save(os.path.join(ASSETS, f"{nazwa}.jpg"), "JPEG",
                    quality=74, optimize=True, progressive=True)
        os.remove(tmp)
        print(f"{nazwa}: webp+jpg")


if __name__ == "__main__":
    hero()
    logo()
    plakaty()
    print("\nRozmiary w assets/:")
    for f in sorted(os.listdir(ASSETS)):
        print(f"  {f:26} {os.path.getsize(os.path.join(ASSETS, f)) // 1024:5} kB")
