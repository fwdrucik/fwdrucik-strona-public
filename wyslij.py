# -*- coding: utf-8 -*-
"""
Wysyłka zawartości dist/ na serwer fwdrucik.pl przez FTPS.

    py wyslij.py           — pokazuje plan wysyłki, nic nie zmienia
    py wyslij.py --wykonaj — faktycznie wysyła pliki

Dane logowania czytane tak samo jak w skillu ftp-serwer:
C:\\Users\\Computer\\.claude\\.ftp-fwdrucik.json
"""

import json
import os
import ssl
import sys
import time
from ftplib import FTP, FTP_TLS

BASE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(BASE, "dist")
# UWAGA: domena fwdrucik.pl jest wskazana na ten katalog, a nie na public_html.
# Sprawdzone 2026-08-08: plik serwowany pod adresem / to autoinstalator/joomla/index.html.
ZDALNY_ROOT = "public_html/autoinstalator/joomla"
CONFIG = os.path.expanduser(r"~\.claude\.ftp-fwdrucik.json")


class FTPS(FTP_TLS):
    """Pure-FTPd na hosting-home.pl wymaga wznowienia sesji TLS na kanale
    danych. Bez tego serwer zrywa każdy transfer (WinError 10054)."""

    def ntransfercmd(self, cmd, rest=None):
        conn, size = FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.sock.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session)
        return conn, size


def dane_logowania():
    """Zmienne środowiskowe mają pierwszeństwo — tak działa to w Actions,
    gdzie nie ma pliku z hasłem, tylko sekrety repozytorium."""
    if os.environ.get("FTP_HOST") and os.environ.get("FTP_USER"):
        return {
            "host": os.environ["FTP_HOST"],
            "user": os.environ["FTP_USER"],
            "password": os.environ.get("FTP_PASSWORD", ""),
            "port": os.environ.get("FTP_PORT", 21),
        }
    if not os.path.isfile(CONFIG):
        print(f"Brak danych logowania: ustaw FTP_HOST/FTP_USER/FTP_PASSWORD "
              f"albo utwórz {CONFIG}", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


# Hosting potrafi odrzucić logowanie bez powodu leżącego po naszej stronie:
# limit równoległych sesji, chwilowe przeciążenie, sesja z poprzedniego
# przebiegu jeszcze niezamknięta. Jedna taka odmowa wywracała cały przebieg
# (wachdog 2026-08-28) i przychodził mail o awarii, choć minutę później
# wszystko działało.
PROBY_LOGOWANIA = 4


def _polacz_raz(c):
    """Połączenie FTPS z weryfikacją certyfikatu przed podaniem danych."""
    ftp = FTPS(context=ssl.create_default_context())
    try:
        ftp.connect(c["host"], int(c.get("port", 21)), timeout=60)
        ftp.auth()
        ftp.login(c["user"], c["password"])
        ftp.prot_p()
        ftp.set_pasv(True)
    except Exception:
        ftp.close()
        raise
    print("połączenie: FTPS (szyfrowane)")
    return ftp


def polacz():
    c = dane_logowania()
    for proba in range(1, PROBY_LOGOWANIA + 1):
        try:
            return _polacz_raz(c)
        except Exception as e:
            if proba == PROBY_LOGOWANIA:
                print(f"Logowanie nie powiodło się po {PROBY_LOGOWANIA} próbach.",
                      file=sys.stderr)
                raise
            # 10 s, 20 s, 40 s — tyle wystarcza, żeby zwolniła się sesja
            # po poprzednim przebiegu.
            czekaj = 2 ** proba * 5
            print(f"Logowanie odrzucone ({type(e).__name__}: {e}) — "
                  f"ponawiam za {czekaj} s (próba {proba}/{PROBY_LOGOWANIA - 1})",
                  file=sys.stderr)
            time.sleep(czekaj)


def utworz_katalog(ftp, sciezka):
    czesci = sciezka.split("/")
    biezaca = ""
    for cz in czesci:
        if not cz:
            continue
        biezaca = f"{biezaca}/{cz}" if biezaca else cz
        try:
            ftp.mkd(biezaca)
        except Exception:
            pass  # katalog już istnieje


def pliki_do_wyslania():
    lista = []
    for korzen, _, pliki in os.walk(DIST):
        for p in pliki:
            lokalny = os.path.join(korzen, p)
            wzgledny = os.path.relpath(lokalny, DIST).replace(os.sep, "/")
            lista.append((lokalny, f"{ZDALNY_ROOT}/{wzgledny}", os.path.getsize(lokalny)))
    return sorted(lista, key=lambda x: x[1])


def usun_zdalne(sciezki, wykonaj):
    """Kasuje wskazane pliki na serwerze.

    Wysyłka sama z siebie niczego nie usuwa — nadpisuje tylko to, co jest
    w dist/. Odrzucony szkic zostałby więc na serwerze na zawsze, mimo że
    zniknął z repozytorium. Stąd ta operacja, celowo wąska: kasuje wyłącznie
    podane ścieżki, nigdy całych katalogów i nigdy niczego spoza dist/.
    """
    sciezki = [s.strip().lstrip("/") for s in sciezki if s.strip()]
    if not sciezki:
        print("Nic do skasowania.")
        return

    print(f"{'KASOWANIE' if wykonaj else 'PLAN (próba na sucho)'}: {len(sciezki)} plików\n")
    for s in sciezki:
        print("  " + ZDALNY_ROOT + "/" + s)
    if not wykonaj:
        print("\nNic nie skasowano. Aby skasować naprawdę: py wyslij.py --usun plik --wykonaj")
        return

    ftp = polacz()
    for s in sciezki:
        cel = ZDALNY_ROOT + "/" + s
        try:
            ftp.delete(cel)
            print("skasowano:", cel)
        except Exception as e:
            # Brak pliku to nie błąd — szkic mógł nigdy nie dojechać na serwer.
            print("pominięto:", cel, "-", e)
    ftp.quit()
    print(f"\nGotowe — sprzątnięto {len(sciezki)} pozycji.")


def main():
    wykonaj = "--wykonaj" in sys.argv

    if "--usun" in sys.argv:
        i = sys.argv.index("--usun")
        argumenty = [a for a in sys.argv[i + 1:] if not a.startswith("--")]
        if len(argumenty) == 1 and os.path.isfile(argumenty[0]):
            with open(argumenty[0], encoding="utf-8") as f:
                argumenty = f.read().splitlines()
        usun_zdalne(argumenty, wykonaj)
        return

    lista = pliki_do_wyslania()
    if "--tylko" in sys.argv:
        i = sys.argv.index("--tylko")
        filtry = [a.replace("\\", "/").lower() for a in sys.argv[i + 1:] if not a.startswith("--")]
        if filtry:
            lista = [x for x in lista if any(f in x[1].lower() for f in filtry)]
    razem = sum(x[2] for x in lista)

    print(f"{'WYSYŁKA' if wykonaj else 'PLAN (próba na sucho)'}: "
          f"{len(lista)} plików, {razem // 1024} kB\n")
    for _, zdalny, rozmiar in lista:
        print(f"  {zdalny:52} {rozmiar // 1024:5} kB")

    if not wykonaj:
        print("\nNic nie wysłano. Aby wysłać naprawdę: py wyslij.py --wykonaj")
        return

    # Pure-FTPd na hosting-home.pl potrafi zerwać połączenie w środku przebiegu
    # (WinError 10054). Bez ponawiania kończyło się to serwisem zaktualizowanym
    # w połowie: część podstron nowa, część stara, a `dist/` niezgodny z tym,
    # co widzi klient. Dlatego każdy plik ma własne podejścia, a zerwana sesja
    # jest odtwarzana zamiast przerywać całość.
    MAKS_PROB = 4

    ftp = polacz()
    katalogi = sorted({os.path.dirname(z) for _, z, _ in lista})
    for k in katalogi:
        utworz_katalog(ftp, k)

    wyslane = 0
    nieudane = []

    for lokalny, zdalny, _ in lista:
        for proba in range(1, MAKS_PROB + 1):
            try:
                with open(lokalny, "rb") as f:
                    ftp.storbinary(f"STOR {zdalny}", f)
                print("wysłano:", zdalny)
                wyslane += 1
                break
            except FileNotFoundError:
                # Plik zniknął spod nóg (antywirus, równoległa przebudowa).
                # Ponawianie nic tu nie da — zgłaszamy i idziemy dalej.
                print("BRAK PLIKU:", lokalny)
                nieudane.append(zdalny)
                break
            except Exception as e:
                if proba == MAKS_PROB:
                    print(f"NIE UDAŁO SIĘ ({proba} próby): {zdalny} — {e}")
                    nieudane.append(zdalny)
                    break
                print(f"  ponawiam {zdalny} (próba {proba + 1}/{MAKS_PROB}): {e}")
                time.sleep(2 * proba)
                try:
                    ftp.quit()
                except Exception:
                    pass
                ftp = polacz()
                utworz_katalog(ftp, os.path.dirname(zdalny))

    try:
        ftp.quit()
    except Exception:
        pass

    print(f"\nGotowe — {wyslane} z {len(lista)} plików na serwerze.")
    if nieudane:
        print(f"\nNIE WYSŁANO {len(nieudane)} plików — serwis jest niespójny!")
        for z in nieudane:
            print("  -", z)
        print("\nUruchom wysyłkę ponownie: py wyslij.py --wykonaj")
        sys.exit(1)


if __name__ == "__main__":
    main()
