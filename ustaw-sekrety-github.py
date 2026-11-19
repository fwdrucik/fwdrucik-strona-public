# -*- coding: utf-8 -*-
"""
Przeniesienie danych FTP z lokalnej konfiguracji do sekretów repozytorium.

    py ustaw-sekrety-github.py            — pokazuje, co jest rozjechane
    py ustaw-sekrety-github.py --wykonaj  — zapisuje sekrety w GitHubie

Po co: GitHub Actions wysyła serwis na serwer, korzystając z sekretów
`FTP_HOST`, `FTP_USER` i `FTP_PASSWORD`. Gdy hasło do hostingu zmieni się
lokalnie, a sekret zostanie stary, codzienny przegląd przestaje wysyłać
cokolwiek — i wygląda to na awarię serwera, choć jest to rozjazd haseł.
Dokładnie to zdarzyło się między 15 a 17 sierpnia 2026.

Wartości idą z pliku prosto na wejście `gh secret set`. Nie pojawiają się
ani na ekranie, ani w argumentach polecenia (a więc i na liście procesów),
ani w historii powłoki.

Wymaga zalogowanego `gh` (`gh auth status`).
"""

import argparse
import json
import os
import subprocess
import sys

CONFIG_FTP = os.path.expanduser(r"~\.claude\.ftp-fwdrucik.json")

# Nazwa sekretu w GitHubie -> klucz w lokalnym pliku konfiguracyjnym.
MAPA = {
    "FTP_HOST": "host",
    "FTP_USER": "user",
    "FTP_PASSWORD": "password",
}


def blad(tekst):
    print("BŁĄD:", tekst, file=sys.stderr)
    sys.exit(1)


def zamaskuj(wartosc):
    """Podgląd wartości bez jej zdradzania: długość i pierwszy znak.

    Wystarcza, żeby stwierdzić „to jest to, co myślę", a nie wystarcza,
    żeby cokolwiek odtworzyć.
    """
    wartosc = str(wartosc)
    if len(wartosc) <= 2:
        return "•" * len(wartosc)
    return wartosc[0] + "•" * (len(wartosc) - 1) + f" ({len(wartosc)} znaków)"


def gh(*argumenty, wejscie=None):
    wynik = subprocess.run(
        ["gh", *argumenty],
        input=wejscie,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if wynik.returncode != 0:
        blad(f"gh {' '.join(argumenty[:2])}: {wynik.stderr.strip()[:200]}")
    return wynik.stdout


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--wykonaj", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    args = ap.parse_args()

    if args.help:
        print(__doc__)
        return 0

    if not os.path.isfile(CONFIG_FTP):
        blad(f"brak lokalnej konfiguracji FTP: {CONFIG_FTP}")

    with open(CONFIG_FTP, encoding="utf-8") as f:
        cfg = json.load(f)

    brakujace = [k for k in MAPA.values() if not cfg.get(k)]
    if brakujace:
        blad("w konfiguracji brakuje pól: " + ", ".join(brakujace))

    gh("auth", "status")

    print("Sekrety do zapisania w repozytorium:\n")
    for sekret, klucz in MAPA.items():
        print(f"  {sekret:14s} {zamaskuj(cfg[klucz])}")

    print("\nData ostatniej zmiany sekretów w GitHubie:")
    for linia in gh("secret", "list").splitlines():
        if linia.startswith("FTP_"):
            print("  " + linia.replace("\t", "  "))

    czas_pliku = os.path.getmtime(CONFIG_FTP)
    from datetime import datetime
    print(f"\nLokalna konfiguracja zmieniona: "
          f"{datetime.fromtimestamp(czas_pliku):%Y-%m-%d %H:%M}")

    if not args.wykonaj:
        print("\nPróba na sucho — nic nie zapisano.")
        print("Aby zapisać naprawdę: py ustaw-sekrety-github.py --wykonaj")
        return 0

    print()
    for sekret, klucz in MAPA.items():
        # Wartosc idzie wejsciem standardowym, a nie argumentem polecenia —
        # argumenty widac na liscie procesow systemu.
        gh("secret", "set", sekret, wejscie=str(cfg[klucz]))
        print(f"  zapisano {sekret}")

    print("\nGotowe. Sprawdź, uruchamiając przegląd serwisu:")
    print("  gh workflow run wachdog.yml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
