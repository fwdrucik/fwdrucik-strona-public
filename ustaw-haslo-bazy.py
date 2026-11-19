# -*- coding: utf-8 -*-
"""
Wstawia hasło bazy do pliku konfiguracyjnego backendu na serwerze.

Po co: plik `fw-konfiguracja.php` leży poza katalogiem WWW i trzeba w nim
uzupełnić jedno pole — hasło bazy `42047126_fwdrucik`. Ten skrypt robi to
za Ciebie, żebyś nie musiał edytować pliku przez WebFTP.

Jak użyć:

    1. Utwórz plik tekstowy z samym hasłem bazy (jedna linia, nic więcej), np.
       D:\\claude\\haslo-bazy.txt
    2. py ustaw-haslo-bazy.py D:\\claude\\haslo-bazy.txt
    3. Skrypt wyśle gotową konfigurację, sprawdzi połączenie z bazą
       i skasuje plik z hasłem z dysku.

Hasło nie jest nigdzie wypisywane ani logowane — skrypt pokazuje wyłącznie
jego długość. Dane logowania FTP czyta z ~/.claude/.ftp-fwdrucik.json.
"""

import io
import json
import os
import ssl
import sys
import urllib.request
from ftplib import FTP, FTP_TLS

CONFIG_FTP = os.path.expanduser(r"~\.claude\.ftp-fwdrucik.json")
CEL = "public_html/autoinstalator/fw-konfiguracja.php"
SPRAWDZ_URL = "https://fwdrucik.pl/api/forum.php?akcja=watki"

DB_HOST = "mysql8"
DB_PORT = 3306
DB_NAZWA = "42047126_fwdrucik"
DB_UZYTKOWNIK = "42047126_fwdrucik"
PREFIKS = "fw_"

SZABLON = """<?php
// Konfiguracja backendu fwdrucik.pl (konta, forum, komentarze).
// Plik leży POZA katalogiem serwowanym przez WWW — domena wskazuje na
// public_html/autoinstalator/joomla, więc z internetu jest nieosiągalny.
// Wygenerowane przez ustaw-haslo-bazy.py. Nie wrzucaj tego pliku do repozytorium.

return [
    'db_host'       => {host},
    'db_port'       => {port},
    'db_nazwa'      => {nazwa},
    'db_uzytkownik' => {uzytkownik},
    'db_haslo'      => {haslo},

    'prefiks'       => {prefiks},
];
"""


def php_string(wartosc):
    """Bezpieczny literał PHP w apostrofach — hasło może zawierać ' albo \\."""
    return "'" + str(wartosc).replace("\\", "\\\\").replace("'", "\\'") + "'"


class FTPS(FTP_TLS):
    """Pure-FTPd na home.pl wymaga wznowienia sesji TLS na kanale danych."""

    def ntransfercmd(self, cmd, rest=None):
        conn, size = FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.sock.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session)
        return conn, size


def polacz():
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


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    sciezka = sys.argv[1]
    if not os.path.isfile(sciezka):
        print("Nie ma takiego pliku:", sciezka)
        sys.exit(1)

    with open(sciezka, encoding="utf-8-sig") as f:
        haslo = f.read().strip()

    if not haslo:
        print("Plik jest pusty — wpisz w nim samo hasło bazy.")
        sys.exit(1)
    if haslo == "TUTAJ_WPISZ_HASLO_BAZY":
        print("W pliku siedzi placeholder, nie prawdziwe hasło.")
        sys.exit(1)

    print(f"Wczytano hasło: {len(haslo)} znaków (treści nie pokazuję).")

    tresc = SZABLON.format(
        host=php_string(DB_HOST),
        port=DB_PORT,
        nazwa=php_string(DB_NAZWA),
        uzytkownik=php_string(DB_UZYTKOWNIK),
        haslo=php_string(haslo),
        prefiks=php_string(PREFIKS),
    )

    ftp = polacz()
    ftp.storbinary("STOR " + CEL, io.BytesIO(tresc.encode("utf-8")))
    rozmiar = ftp.size(CEL)
    ftp.quit()
    print(f"Wgrano {CEL} ({rozmiar} bajtów).")

    # Kontrola: końcówka forum odpytuje bazę, więc od razu widać, czy hasło gra.
    try:
        with urllib.request.urlopen(SPRAWDZ_URL, timeout=45) as r:
            odp = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print("Nie udało się sprawdzić API:", e)
        odp = None

    if odp and odp.get("ok"):
        print("API łączy się z bazą — backend działa.")
        usun = True
    else:
        blad = (odp or {}).get("blad", "brak odpowiedzi")
        print("API nadal nie łączy się z bazą:", blad)
        print("Plik z hasłem ZOSTAJE na dysku, żebyś mógł poprawić i powtórzyć.")
        usun = False

    if usun:
        os.remove(sciezka)
        print("Skasowano plik z hasłem:", sciezka)


if __name__ == "__main__":
    main()
