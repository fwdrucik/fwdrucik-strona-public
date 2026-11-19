# -*- coding: utf-8 -*-
"""
Ustawia wspólny sekret agenta bloga w obu miejscach naraz.

Po co: `api/wpisy.php` przyjmuje zgłoszenie szkicu tylko wtedy, gdy token
z nagłówka `X-Agent-Token` zgadza się z `agent_token` w konfiguracji na
serwerze. Ten sam token musi siedzieć jako sekret `AGENT_TOKEN` w
repozytorium GitHuba, bo stamtąd woła go workflow. Gdy któregokolwiek
brakuje, agent kończy pracę na:

    HTTP 503 {"ok":false,"blad":"Zgłaszanie wpisów nieskonfigurowane."}

Skrypt robi obie rzeczy w jednym przebiegu i sprawdza wynik.

Jak użyć:

    py ustaw-token-agenta.py --generuj
        Losuje mocny token, wstawia go na serwer i do sekretów GitHuba.
        Niczego nie musisz wklejać ani nigdzie zapisywać.

    py ustaw-token-agenta.py --wklej
        Pyta o token agenta w ukrytym monicie — wklejasz go w konsoli,
        nic nie widać na ekranie i nic nie zostaje w historii poleceń
        ani na dysku. Użyj, gdy masz już swoją wartość.

    py ustaw-token-agenta.py D:\\claude\\token-agenta.txt
        To samo, ale token bierze z pliku (jedna linia, nic więcej).
        Plik jest kasowany po udanym ustawieniu.

    py ustaw-token-agenta.py --generuj --tylko-serwer
        Pomija GitHuba (np. gdy `gh` nie jest zalogowany).

    py ustaw-token-agenta.py --tylko-serwer --github-wklej
        Pyta w ukrytym monicie o PAT-a GitHuba i wstawia go do konfiguracji
        serwera razem z `github_repo`. Tokenu agenta nie rusza.

    py ustaw-token-agenta.py --generuj --github-token D:\\claude\\pat.txt
        Przy okazji ustawia `github_token` i `github_repo` w konfiguracji
        serwera — panel administratora woła nimi `repository_dispatch`,
        żeby opublikować zatwierdzony wpis. Bez obu kluczy akceptacja
        zapisuje status w bazie i na tym się kończy.

        PAT musi być drobnoziarnisty (fine-grained), ograniczony do
        repozytorium fwdrucik/fwdrucik-strona, z uprawnieniem
        Contents: Read and write — tyle wymaga POST /repos/.../dispatches.

Token nie jest wypisywany ani logowany — skrypt pokazuje wyłącznie jego
długość. Dane logowania FTP czyta z ~/.claude/.ftp-fwdrucik.json, tak samo
jak wyslij.py i ustaw-haslo-bazy.py.
"""

import argparse
import getpass
import io
import json
import os
import re
import secrets
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from ftplib import FTP, FTP_TLS

CONFIG_FTP = os.path.expanduser(r"~\.claude\.ftp-fwdrucik.json")
KOPIE = os.path.expanduser(r"~\AppData\Local\Temp\claude\ftp-backup")
REPO = "fwdrucik/fwdrucik-strona"
PROBA_URL = "https://fwdrucik.pl/api/wpisy.php?akcja=zglos"

# Kolejność ta sama co w api/_lib.php: plik spoza katalogu WWW wygrywa,
# więc łatamy ten, który backend faktycznie czyta.
KANDYDACI = (
    "public_html/autoinstalator/fw-konfiguracja.php",
    "public_html/autoinstalator/joomla/api/konfiguracja.php",
)


class FTPS(FTP_TLS):
    """Pure-FTPd na home.pl wymaga wznowienia sesji TLS na kanale danych."""

    def ntransfercmd(self, cmd, rest=None):
        conn, size = FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.sock.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session)
        return conn, size


def blad(tekst):
    print("BŁĄD:", tekst, file=sys.stderr)
    sys.exit(1)


def polacz():
    if not os.path.isfile(CONFIG_FTP):
        blad(f"brak danych logowania FTP — utwórz {CONFIG_FTP}")
    with open(CONFIG_FTP, encoding="utf-8") as f:
        c = json.load(f)
    kontekst = ssl.create_default_context()
    kontekst.check_hostname = False
    kontekst.verify_mode = ssl.CERT_NONE
    ftp = FTPS(context=kontekst)
    ftp.connect(c["host"], int(c.get("port", 21)), timeout=60)
    ftp.login(c["user"], c["password"])
    ftp.prot_p()
    ftp.set_pasv(True)
    return ftp


def pobierz(ftp, sciezka):
    """Zwraca treść pliku albo None, jeśli go nie ma."""
    bufor = io.BytesIO()
    try:
        ftp.retrbinary("RETR " + sciezka, bufor.write)
    except Exception:
        return None
    return bufor.getvalue().decode("utf-8")


def php_string(wartosc):
    """Bezpieczny literał PHP w apostrofach — token może zawierać ' albo \\."""
    return "'" + str(wartosc).replace("\\", "\\\\").replace("'", "\\'") + "'"


def wstaw_klucz(tresc, klucz, wartosc):
    """Podmienia wartość klucza w tablicy PHP albo dopisuje go przed `];`.

    Łatamy istniejący plik zamiast generować go od nowa z szablonu: obok
    tokenu leży tam hasło bazy, którego skrypt nie zna i nie ma prawa nadpisać.
    """
    literal = php_string(wartosc)
    wzorzec = re.compile(r"(['\"]" + re.escape(klucz) + r"['\"]\s*=>\s*)(.*?)(\s*,)", re.S)
    if wzorzec.search(tresc):
        return wzorzec.sub(lambda m: m.group(1) + literal + m.group(3), tresc, count=1), "podmieniony"

    zamkniecie = tresc.rfind("];")
    if zamkniecie == -1:
        blad("plik konfiguracyjny nie wygląda jak tablica PHP (brak `];`)")
    wstawka = f"    '{klucz}'{' ' * max(1, 14 - len(klucz))}=> {literal},\n"
    return tresc[:zamkniecie] + wstawka + tresc[zamkniecie:], "dopisany"


def zapisz_kopie(sciezka_zdalna, tresc):
    os.makedirs(KOPIE, exist_ok=True)
    nazwa = sciezka_zdalna.replace("/", "_")
    stempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    cel = os.path.join(KOPIE, f"{stempel}_{nazwa}")
    with open(cel, "w", encoding="utf-8", newline="\n") as f:
        f.write(tresc)
    return cel


def oczysc_sekret(wartosc, opis):
    """Usuwa znaki sterujące i ostrzega, skąd się wzięły.

    Ctrl+V wpisany jako skrót klawiszowy w oknie z ukrytym echem (getpass)
    w niektórych terminalach nie wywołuje wklejenia — wysyła surowy bajt
    0x16 (SYN, czyli sam kod Ctrl+V) wprost do wejścia. Token z takim bajtem
    w środku łamie nagłówek HTTP (kontrolne znaki są w nim niedozwolone) i
    serwer odrzuca żądanie zanim dotrze do PHP — API odpowiada wtedy pustym
    `400 Bad Request`, bez żadnego komunikatu o złym tokenie.
    """
    sterujace = [c for c in wartosc if ord(c) < 32 and c not in "\t"]
    if not sterujace:
        return wartosc
    oczyszczona = "".join(c for c in wartosc if ord(c) >= 32 or c == "\t")
    print(f"UWAGA: w {opis} znalazłem {len(sterujace)} znak(ów) sterujących (np. Ctrl+V"
          " wysłany jako bajt zamiast wywołać wklejenie) — usuwam je.")
    print("       Jeśli wynikowy token wygląda krótszy niż powinien, wklej go jeszcze raz")
    print("       przez PRAWY PRZYCISK MYSZY zamiast Ctrl+V.")
    return oczyszczona


def wklej_sekret(opis):
    """Ukryty monit — wklejona wartość nie pojawia się na ekranie ani
    w historii poleceń, w odróżnieniu od podania jej w argumencie."""
    wartosc = getpass.getpass(f"Wklej {opis} (wpisywanie jest niewidoczne), Enter zatwierdza: ").strip()
    if not wartosc:
        blad(f"nic nie wklejono — {opis} nie może być pusty")
    return oczysc_sekret(wartosc, opis)


def wczytaj_sekret(sciezka, opis):
    if not os.path.isfile(sciezka):
        blad(f"nie ma takiego pliku: {sciezka}")
    with open(sciezka, encoding="utf-8-sig") as f:
        wartosc = f.read().strip()
    if not wartosc:
        blad(f"plik {sciezka} jest pusty — wpisz w nim sam {opis}")
    if wartosc.upper().startswith("TUTAJ"):
        blad(f"w pliku {sciezka} siedzi placeholder, nie prawdziwa wartość")
    return oczysc_sekret(wartosc, opis)


def ustaw_sekret_github(token):
    """Przekazuje token przez stdin, żeby nie trafił do listy procesów."""
    try:
        wynik = subprocess.run(
            ["gh", "secret", "set", "AGENT_TOKEN", "-R", REPO],
            input=token, text=True, capture_output=True, timeout=120,
        )
    except FileNotFoundError:
        print("  gh nie znaleziony — sekret w GitHubie ustaw sam:")
        print(f"  gh secret set AGENT_TOKEN -R {REPO}")
        return False
    if wynik.returncode != 0:
        print("  gh zwrócił błąd:", (wynik.stderr or "").strip()[:300])
        return False
    return True


def sprawdz_koncowke():
    """Puka do API celowo złym tokenem.

    401 „Zły token agenta" = konfiguracja jest wczytana i porównanie działa.
    503 = `agent_token` na serwerze nadal pusty. Sprawdzanie prawdziwym
    tokenem zapisałoby wpis w kolejce, a tego nie chcemy przy samym teście.
    """
    zadanie = urllib.request.Request(
        PROBA_URL, data=b"{}", method="POST",
        headers={"Content-Type": "application/json", "X-Agent-Token": "proba-" + secrets.token_hex(8)},
    )
    try:
        with urllib.request.urlopen(zadanie, timeout=45) as odp:
            return odp.status, odp.read().decode("utf-8", "replace")[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]
    except urllib.error.URLError as e:
        return None, str(e.reason)


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("plik", nargs="?", help="plik z tokenem agenta")
    ap.add_argument("--generuj", action="store_true", help="wylosuj token zamiast czytać z pliku")
    ap.add_argument("--wklej", action="store_true", help="zapytaj o token agenta w ukrytym monicie")
    ap.add_argument("--github-wklej", action="store_true", help="zapytaj o PAT GitHuba w ukrytym monicie")
    ap.add_argument("--tylko-serwer", action="store_true", help="nie ruszaj sekretów GitHuba")
    ap.add_argument("--github-token", metavar="PLIK", help="plik z PAT-em do publikacji z panelu")
    ap.add_argument("--github-repo", metavar="OWNER/REPO", default=REPO,
                    help=f"repozytorium wołane przez panel (domyślnie {REPO})")
    ap.add_argument("-h", "--help", action="store_true")
    args = ap.parse_args()

    zrodla = [z for z in (("--generuj", args.generuj), ("plik", bool(args.plik)),
                          ("--wklej", args.wklej)) if z[1]]
    chce_github = bool(args.github_token or args.github_wklej)

    if args.help or (not zrodla and not chce_github):
        print(__doc__)
        sys.exit(0 if args.help else 1)

    if len(zrodla) > 1:
        blad("wybierz jeden sposób podania tokenu agenta: " + ", ".join(z[0] for z in zrodla))
    if args.github_token and args.github_wklej:
        blad("wybierz jedno: --github-token PLIK albo --github-wklej")

    if args.generuj:
        token, skad = secrets.token_urlsafe(32), "wylosowany"
    elif args.wklej:
        token, skad = wklej_sekret("token agenta"), "wklejony"
    elif args.plik:
        token, skad = wczytaj_sekret(args.plik, "token agenta"), "z pliku"
    else:
        token, skad = None, None
        print("Tokenu agenta nie ruszam — ustawiam wyłącznie ustawienia GitHuba.")
    if token:
        print(f"Token agenta: {len(token)} znaków ({skad}), treści nie pokazuję.")

    if args.github_wklej:
        github_pat = wklej_sekret("PAT GitHuba")
    elif args.github_token:
        github_pat = wczytaj_sekret(args.github_token, "token GitHuba")
    else:
        github_pat = None
    if github_pat:
        print(f"Token GitHuba do panelu: {len(github_pat)} znaków.")

    print("\n1/4  Pobieranie konfiguracji z serwera")
    ftp = polacz()
    sciezka = tresc = None
    for kandydat in KANDYDACI:
        tresc = pobierz(ftp, kandydat)
        if tresc is not None:
            sciezka = kandydat
            break
    if sciezka is None:
        ftp.quit()
        blad("nie znalazłem pliku konfiguracyjnego na serwerze — sprawdź, czy backend jest wgrany:\n"
             + "\n".join("       " + k for k in KANDYDACI))

    kopia = zapisz_kopie(sciezka, tresc)
    print(f"     {sciezka} ({len(tresc)} B), kopia: {kopia}")

    print("\n2/4  Wstawianie tokenu do konfiguracji")
    nowa = tresc
    if token:
        nowa, jak = wstaw_klucz(nowa, "agent_token", token)
        print(f"     agent_token {jak}")
    if github_pat:
        nowa, jak_gh = wstaw_klucz(nowa, "github_token", github_pat)
        print(f"     github_token {jak_gh}")
        # moderacja.php wymaga obu kluczy naraz — sam token bez nazwy
        # repozytorium daje „Brak tokenu GitHuba w konfiguracji".
        nowa, jak_repo = wstaw_klucz(nowa, "github_repo", args.github_repo)
        print(f"     github_repo {jak_repo} ({args.github_repo})")

    if nowa == tresc:
        ftp.quit()
        blad("nic się nie zmieniło — przerywam, żeby nie nadpisywać pliku bez powodu")

    ftp.storbinary("STOR " + sciezka, io.BytesIO(nowa.encode("utf-8")))
    rozmiar = ftp.size(sciezka)
    ftp.quit()
    print(f"     wgrano ({rozmiar} B)")

    print("\n3/4  Sekret AGENT_TOKEN w repozytorium GitHuba")
    if not token:
        print("     pominięte — token agenta nie był zmieniany")
        github_ok = None
    elif args.tylko_serwer:
        print("     pominięte (--tylko-serwer)")
        github_ok = None
    else:
        github_ok = ustaw_sekret_github(token)
        print("     ustawiony" if github_ok else "     NIE ustawiony — patrz komunikat wyżej")

    print("\n4/4  Kontrola końcówki API (pukanie celowo złym tokenem)")
    kod, tresc_odp = sprawdz_koncowke()
    if kod == 401:
        print('     401 "Zły token agenta" — konfiguracja wczytana, porównanie działa.')
    elif kod == 503:
        print("     503 — serwer widzi pusty agent_token.")
        print("     Sprawdź, czy backend czyta ten plik:", sciezka)
        print("     Kopia sprzed zmiany:", kopia)
        sys.exit(1)
    else:
        print(f"     nieoczekiwana odpowiedź {kod}: {tresc_odp}")
        sys.exit(1)

    if args.plik and os.path.isfile(args.plik):
        os.remove(args.plik)
        print("\nSkasowano plik z tokenem:", args.plik)

    print("\nGotowe.")
    if not token:
        print("Sprawdzenie: zaakceptuj wpis w panelu i zobacz, czy w Actions pojawi się")
        print('przebieg "Decyzja o wpisie" uruchomiony przez repository_dispatch.')
    elif github_ok is False or args.tylko_serwer:
        print("Sekret w GitHubie ustaw jeszcze sam, inaczej workflow poda inny token niż serwer.")
    else:
        print("Sprawdzenie całości:")
        print(f"  gh workflow run agent-bloga.yml -R {REPO}")


if __name__ == "__main__":
    main()
