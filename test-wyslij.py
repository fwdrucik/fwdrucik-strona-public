# -*- coding: utf-8 -*-
"""Testy ponawiania logowania w wyslij.py — bez sieci i bez serwera FTP.

    py test-wyslij.py

Chodzą w workflow „Kontrola" przy każdym pushu. Serwer FTP zastępuje atrapa,
a odczekiwanie między próbami jest podmienione, żeby testy nie trwały minuty.
"""

import importlib.util
import os
import ssl
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

spec = importlib.util.spec_from_file_location("wyslij", os.path.join(BASE, "wyslij.py"))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

zaliczone, oblane = [], []


def sprawdz(nazwa, warunek, szczegol=""):
    (zaliczone if warunek else oblane).append(nazwa)
    print(("  OK   " if warunek else "  BLAD ") + nazwa + (f" — {szczegol}" if szczegol else ""))


# Dane logowania i odczekiwanie podmieniamy raz na całe testy: żaden test nie
# ma prawa dotknąć prawdziwego serwera ani czekać 10 sekund.
w.dane_logowania = lambda: {"host": "atrapa", "user": "u", "password": "p", "port": 21}
odczekania = []
w.time.sleep = lambda s: odczekania.append(s)


class Polaczenie:
    """Minimalna atrapa połączenia — wystarczy, że da się ją zwrócić."""


def podstaw_proby(zachowania):
    """Kolejne próby logowania zwracają to, co poda lista.

    Element to wyjątek (próba pada) albo obiekt połączenia (próba się udaje).
    """
    stan = {"licznik": 0}

    def raz(c):
        wynik = zachowania[stan["licznik"]]
        stan["licznik"] += 1
        if isinstance(wynik, Exception):
            raise wynik
        return wynik

    w._polacz_raz = raz
    return stan


print("\nWeryfikacja FTPS:")

class SerwerFTPS:
    def __init__(self, context, awaria_tls=False):
        self.context = context
        self.awaria_tls = awaria_tls
        self.kroki = []

    def connect(self, host, port, timeout):
        self.kroki.append("connect")

    def auth(self):
        self.kroki.append("auth")
        if self.awaria_tls:
            raise ssl.SSLCertVerificationError("niezaufany certyfikat")

    def login(self, user, password):
        self.kroki.append("login")

    def prot_p(self):
        self.kroki.append("prot_p")

    def set_pasv(self, flag):
        self.kroki.append("pasv")

    def close(self):
        self.kroki.append("close")


def test_tls(awaria_tls):
    utworzone = []

    def atrapa(context):
        serwer = SerwerFTPS(context, awaria_tls)
        utworzone.append(serwer)
        return serwer

    w.FTPS = atrapa
    try:
        w._polacz_raz(w.dane_logowania())
        wynik = True
    except ssl.SSLCertVerificationError:
        wynik = False
    return wynik, utworzone[0]


wynik, serwer = test_tls(False)
sprawdz("weryfikacja certyfikatu i nazwy serwera",
        serwer.context.verify_mode == ssl.CERT_REQUIRED and serwer.context.check_hostname)
sprawdz("TLS przed loginem i szyfrowany kanał danych",
        wynik and serwer.kroki == ["connect", "auth", "login", "prot_p", "pasv"])
wynik, serwer = test_tls(True)
sprawdz("niezaufany certyfikat kończy próbę przed logowaniem",
        not wynik and serwer.kroki == ["connect", "auth", "close"])

print("\nPonawianie logowania:")

odczekania.clear()
polaczenie = Polaczenie()
stan = podstaw_proby([polaczenie])
sprawdz("udane logowanie za pierwszym razem", w.polacz() is polaczenie)
sprawdz("bez odczekiwania, gdy nie było odmowy", odczekania == [], str(odczekania))

odczekania.clear()
polaczenie = Polaczenie()
stan = podstaw_proby([OSError("530 Login incorrect"), OSError("421 too many connections"),
                      polaczenie])
sprawdz("dwie odmowy, trzecia próba udana", w.polacz() is polaczenie)
sprawdz("trzy podejścia w sumie", stan["licznik"] == 3, f"było {stan['licznik']}")
sprawdz("odczekiwanie rośnie: 10 s, 20 s", odczekania == [10, 20], str(odczekania))

odczekania.clear()
stan = podstaw_proby([OSError("1"), OSError("2"), OSError("3"), OSError("4")])
try:
    w.polacz()
    poddal_sie = False
except OSError:
    poddal_sie = True
sprawdz("cztery odmowy pod rząd przerywają wysyłkę", poddal_sie)
sprawdz("tyle podejść, ile mówi PROBY_LOGOWANIA",
        stan["licznik"] == w.PROBY_LOGOWANIA, f"było {stan['licznik']}")
sprawdz("po ostatniej odmowie nie ma już odczekiwania", odczekania == [10, 20, 40],
        str(odczekania))

print(f"\nZaliczone: {len(zaliczone)}, oblane: {len(oblane)}")
if oblane:
    print("OBLANE:", ", ".join(oblane))
sys.exit(1 if oblane else 0)
