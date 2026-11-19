# -*- coding: utf-8 -*-
"""
Wpisywanie kluczy API i danych dostępowych do konfiguracji serwera.

    py ustaw-klucze.py                — przechodzi po wszystkich pozycjach
    py ustaw-klucze.py platnosci      — tylko grupa „platnosci"
    py ustaw-klucze.py --klucz numer_konta   — jedna wskazana pozycja
    py ustaw-klucze.py --pokaz        — wypisuje, co jest już ustawione (bez wartości)
    py ustaw-klucze.py --grupy        — lista dostępnych grup

Jak to działa: program pyta po kolei o każdą pozycję, a Ty wklejasz wartość
i naciskasz Enter. Pusty Enter zostawia to, co jest, i przechodzi dalej.
Na końcu wszystko idzie jednym zapisem do pliku konfiguracyjnego na serwerze
(`public_html/autoinstalator/fw-konfiguracja.php`), poza katalogiem WWW.

Czego program NIE robi:

  * nie wypisuje wartości na ekran — sekrety wpisujesz „w ciemno", tak jak
    hasło w terminalu, żeby nie zostały w historii konsoli ani na zrzucie
    ekranu udostępnionym komuś do pomocy,
  * nie zapisuje ich na dysku lokalnym,
  * nie dotyka pozycji, o które nie pytał — hasło do bazy leży w tym samym
    pliku i ma zostać nietknięte.

Przed każdym zapisem powstaje kopia dotychczasowej konfiguracji
w `C:\\Users\\<Ty>\\AppData\\Local\\Temp\\claude\\ftp-backup\\`.
"""

import argparse
import getpass
import io
import os
import re
import ssl
import sys
from datetime import datetime
from ftplib import FTP, FTP_TLS

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FTP = os.path.expanduser(r"~\.claude\.ftp-fwdrucik.json")
ZDALNA_KONFIGURACJA = "public_html/autoinstalator/fw-konfiguracja.php"
KATALOG_KOPII = os.path.expanduser(
    r"~\AppData\Local\Temp\claude\ftp-backup")


# --------------------------------------------------------------------- pozycje
# `tajne` decyduje o tym, czy wpisywana wartość ma być niewidoczna na ekranie.
# Identyfikatory sklepu czy adresy serwerów nie są tajemnicą i wygodniej
# je sprawdzić wzrokiem; klucze, hasła i sekrety — już tak.
POZYCJE = [
    # ---------------------------------------------------------- płatności
    ("platnosci", "p24_merchant_id", "Przelewy24 — Merchant ID (numer sprzedawcy)", False),
    ("platnosci", "p24_pos_id", "Przelewy24 — POS ID (zwykle taki sam jak Merchant ID)", False),
    ("platnosci", "p24_crc", "Przelewy24 — klucz CRC", True),
    ("platnosci", "p24_api_key", "Przelewy24 — klucz do REST API", True),
    ("platnosci", "p24_sandbox", "Przelewy24 — tryb testowy? wpisz 1 albo 0", False),
    ("platnosci", "payu_pos_id", "PayU — POS ID", False),
    ("platnosci", "payu_md5", "PayU — drugi klucz (MD5)", True),
    ("platnosci", "payu_oauth_client_id", "PayU — OAuth client_id", False),
    ("platnosci", "payu_oauth_secret", "PayU — OAuth client_secret", True),
    ("platnosci", "tpay_id", "Tpay — ID sprzedawcy", False),
    ("platnosci", "tpay_kod", "Tpay — kod bezpieczeństwa", True),
    ("platnosci", "numer_konta", "Numer konta do przelewów tradycyjnych (IBAN)", False),

    # ---------------------------------------------------------------- poczta
    ("poczta", "smtp_host", "SMTP — serwer poczty wychodzącej (np. smtp.home.pl)", False),
    ("poczta", "smtp_port", "SMTP — port (587 dla TLS, 465 dla SSL)", False),
    ("poczta", "smtp_szyfrowanie", "SMTP — szyfrowanie: tls albo ssl", False),
    ("poczta", "smtp_uzytkownik", "SMTP — login (zwykle pełny adres e-mail)", False),
    ("poczta", "smtp_haslo", "SMTP — hasło do skrzynki", True),
    ("poczta", "smtp_nadawca", "Adres, z którego wychodzą wiadomości", False),
    ("poczta", "email_zamowien", "Adres, na który mają przychodzić zamówienia", False),

    # ---------------------------------------------------------------- google
    ("google", "google_api_key", "Google — klucz API", True),
    ("google", "google_maps_key", "Google Maps — klucz API", True),
    ("google", "ga4_pomiar", "Google Analytics 4 — identyfikator pomiaru (G-...)", False),
    ("google", "google_site_verification", "Google Search Console — kod weryfikacyjny", False),

    # ----------------------------------------------------------------- sklep
    ("sklep", "sklep_otwarty", "Sklep otwarty dla wszystkich? 1 = tak, 0 = tylko admin", False),
    ("sklep", "sklep_regulamin_wersja", "Wersja regulaminu sklepu (np. 2026-08-22)", False),

    # ----------------------------------------------------------------- agent
    ("agent", "agent_token", "Token agenta publikującego", True),
    ("agent", "github_token", "GitHub — token dostępowy (PAT)", True),
    ("agent", "github_repo", "GitHub — repozytorium w formacie wlasciciel/nazwa", False),
]

GRUPY = {
    "platnosci": "Operatorzy płatności (BLIK, Google Pay, karta) i numer konta",
    "poczta": "Wysyłka wiadomości e-mail (potwierdzenia, zamówienia)",
    "google": "Usługi Google (API, Mapy, Analytics, Search Console)",
    "sklep": "Ustawienia sklepu",
    "agent": "Publikowanie treści i integracja z GitHubem",
}


def blad(tekst):
    print("BŁĄD:", tekst, file=sys.stderr)
    sys.exit(1)


# ------------------------------------------------------------------------ FTPS

class FTPS(FTP_TLS):
    """Pure-FTPd na hosting-home.pl wymaga wznowienia sesji TLS na kanale
    danych. Bez tego serwer zrywa każdy transfer."""

    def ntransfercmd(self, cmd, rest=None):
        conn, size = FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.sock.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session)
        return conn, size


def dane_logowania():
    """Zmienne środowiskowe mają pierwszeństwo, potem plik obok konfiguracji
    Claude Code — dokładnie tak jak w wyslij.py."""
    host = os.environ.get("FTP_HOST")
    user = os.environ.get("FTP_USER")
    haslo = os.environ.get("FTP_PASSWORD")
    if host and user and haslo:
        return host, user, haslo

    if not os.path.isfile(CONFIG_FTP):
        blad(f"brak pliku z danymi FTP: {CONFIG_FTP}")
    import json
    with open(CONFIG_FTP, encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg["host"], cfg["user"], cfg["password"]


def polacz():
    host, user, haslo = dane_logowania()
    # hosting-home.pl przedstawia na FTPS certyfikat samopodpisany, wiec pelna
    # weryfikacja lancucha odrzuca polaczenie. Wylaczamy ja tak samo jak robi to
    # wyslij.py: kanal zostaje zaszyfrowany, ale tozsamosc serwera nie jest
    # potwierdzana certyfikatem — polegamy na tym, ze adres hosta pochodzi
    # z lokalnej konfiguracji, a nie z sieci.
    kontekst = ssl.create_default_context()
    kontekst.check_hostname = False
    kontekst.verify_mode = ssl.CERT_NONE
    ftp = FTPS(context=kontekst)
    ftp.connect(host, 21, timeout=30)
    ftp.login(user, haslo)
    ftp.prot_p()
    ftp.encoding = "utf-8"
    return ftp


def pobierz(ftp, sciezka):
    bufor = io.BytesIO()
    ftp.retrbinary("RETR " + sciezka, bufor.write)
    return bufor.getvalue().decode("utf-8")


def wyslij(ftp, sciezka, tresc):
    ftp.storbinary("STOR " + sciezka, io.BytesIO(tresc.encode("utf-8")))


# ----------------------------------------------------------- praca na tekście

def php_string(wartosc):
    """Wartość jako literał PHP w apostrofach — z ucieczką dla apostrofu
    i odwrotnego ukośnika."""
    return "'" + wartosc.replace("\\", "\\\\").replace("'", "\\'") + "'"


def wstaw_klucz(tresc, klucz, wartosc):
    """Podmienia wartość klucza w tablicy PHP albo dopisuje go przed `];`.

    Łatamy istniejący plik zamiast generować go od nowa z szablonu: obok
    kluczy leży tam hasło bazy, którego ten program nie zna i nie ma prawa
    nadpisać.
    """
    literal = php_string(wartosc)
    wzorzec = re.compile(r"(['\"]" + re.escape(klucz) + r"['\"]\s*=>\s*)(.*?)(\s*,)", re.S)
    if wzorzec.search(tresc):
        return wzorzec.sub(lambda m: m.group(1) + literal + m.group(3), tresc, count=1)

    zamkniecie = tresc.rfind("];")
    if zamkniecie == -1:
        blad("plik konfiguracyjny nie wygląda jak tablica PHP (brak `];`)")
    wstawka = f"    '{klucz}'{' ' * max(1, 26 - len(klucz))}=> {literal},\n"
    return tresc[:zamkniecie] + wstawka + tresc[zamkniecie:]


def obecne_klucze(tresc):
    """Nazwy kluczy, które już mają niepustą wartość. Same nazwy — nigdy
    wartości, żeby nic wrażliwego nie trafiło na ekran."""
    ustawione = set()
    for m in re.finditer(r"['\"]([a-z0-9_]+)['\"]\s*=>\s*(.*?),", tresc, re.S):
        wartosc = m.group(2).strip()
        if wartosc not in ("''", '""', "null", "NULL", ""):
            ustawione.add(m.group(1))
    return ustawione


def oczysc(wartosc):
    """Usuwa znaki sterujące i białe znaki z brzegów.

    Wklejenie przez Ctrl+V w niektórych terminalach dokłada bajt 0x16.
    Taki znak w nagłówku HTTP albo w kluczu API kończy się błędem, którego
    nie da się zobaczyć — wartość „wygląda dobrze", a nie działa.
    """
    return "".join(z for z in wartosc if z.isprintable()).strip()


# ------------------------------------------------------------------- interfejs

def zapytaj(opis, klucz, tajne, juz_ustawione):
    stan = " [ustawione]" if juz_ustawione else ""
    print(f"\n  {opis}{stan}")
    print(f"  klucz: {klucz}")
    if tajne:
        print("  (wpisywane znaki nie będą widoczne)")
        wartosc = getpass.getpass("  > ")
    else:
        wartosc = input("  > ")
    return oczysc(wartosc)


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("grupa", nargs="?", default=None)
    ap.add_argument("--klucz", default=None,
                    help="ustaw pojedyncza pozycje po jej nazwie technicznej")
    ap.add_argument("--pokaz", action="store_true")
    ap.add_argument("--grupy", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    args = ap.parse_args()

    if args.help:
        print(__doc__)
        return 0

    if args.grupy:
        print("Dostępne grupy:\n")
        for nazwa, opis in GRUPY.items():
            ile = len([p for p in POZYCJE if p[0] == nazwa])
            print(f"  {nazwa:12s} {opis} ({ile} pozycji)")
        return 0

    if args.grupa and args.grupa not in GRUPY:
        blad('nie znam grupy ' + args.grupa + '. Lista: py ustaw-klucze.py --grupy')

    if args.klucz and args.klucz not in {k for _, k, _, _ in POZYCJE}:
        podobne = [k for _, k, _, _ in POZYCJE if args.klucz.lower() in k]
        wskazowka = (
            'Podobne: ' + ', '.join(podobne) if podobne
            else 'Pelna lista pozycji: py ustaw-klucze.py --pokaz'
        )
        blad('nie znam pozycji ' + args.klucz + '. ' + wskazowka)

    print("Łączę się z serwerem...")
    ftp = polacz()
    try:
        try:
            tresc = pobierz(ftp, ZDALNA_KONFIGURACJA)
        except Exception as e:
            blad(f"nie mogę pobrać {ZDALNA_KONFIGURACJA}: {e}")

        ustawione = obecne_klucze(tresc)

        if args.pokaz:
            print("\nStan konfiguracji na serwerze (same nazwy, bez wartości):\n")
            for grupa, opis in GRUPY.items():
                print(f"  {opis}")
                for g, klucz, etykieta, _ in POZYCJE:
                    if g == grupa:
                        znak = "✓" if klucz in ustawione else "·"
                        print(f"    {znak} {klucz:26s} {etykieta}")
                print()
            return 0

        if args.klucz:
            do_zapytania = [p for p in POZYCJE if p[1] == args.klucz]
        else:
            do_zapytania = [p for p in POZYCJE if args.grupa is None or p[0] == args.grupa]

        print("\n" + "=" * 68)
        print("Wklejaj wartości i naciskaj Enter.")
        print("Sam Enter = zostaw bez zmian i przejdź dalej.")
        print("Ctrl+C = przerwij bez zapisywania czegokolwiek.")
        print("=" * 68)

        zmiany = {}
        biezaca_grupa = None
        for grupa, klucz, etykieta, tajne in do_zapytania:
            if grupa != biezaca_grupa:
                biezaca_grupa = grupa
                print(f"\n\n### {GRUPY[grupa].upper()}")
            wartosc = zapytaj(etykieta, klucz, tajne, klucz in ustawione)
            if wartosc:
                zmiany[klucz] = wartosc

        if not zmiany:
            print("\nNic nie podano — konfiguracja została bez zmian.")
            return 0

        print("\n" + "=" * 68)
        print(f"Do zapisania: {len(zmiany)} pozycji")
        for klucz in zmiany:
            print(f"  • {klucz}")
        print("=" * 68)
        if input("\nZapisać na serwerze? wpisz TAK: ").strip() != "TAK":
            print("Przerwane. Nic nie zostało zmienione.")
            return 0

        # Kopia zapasowa przed jakąkolwiek zmianą — plik zawiera hasło bazy
        # i pomyłka w tym miejscu potrafi zdjąć serwis z sieci.
        os.makedirs(KATALOG_KOPII, exist_ok=True)
        stempel = datetime.now().strftime("%Y%m%d-%H%M%S")
        kopia = os.path.join(KATALOG_KOPII, f"fw-konfiguracja-{stempel}.php")
        with open(kopia, "w", encoding="utf-8", newline="\n") as f:
            f.write(tresc)
        print(f"Kopia poprzedniej wersji: {kopia}")

        nowa = tresc
        for klucz, wartosc in zmiany.items():
            nowa = wstaw_klucz(nowa, klucz, wartosc)

        wyslij(ftp, ZDALNA_KONFIGURACJA, nowa)
        print(f"Zapisano {len(zmiany)} pozycji w {ZDALNA_KONFIGURACJA}.")

        if "sklep_otwarty" in zmiany:
            print("\nUwaga: zmiana `sklep_otwarty` działa natychmiast — sprawdź")
            print("https://fwdrucik.pl/sklep/ w oknie prywatnym przeglądarki.")
    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nPrzerwane. Nic nie zostało zapisane.")
        sys.exit(130)
