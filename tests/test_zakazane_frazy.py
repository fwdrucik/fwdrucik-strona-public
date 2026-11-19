# -*- coding: utf-8 -*-
"""py tests/test_zakazane_frazy.py — blokada nazwy partnera i deklaracji własnego przezwajania.

Nazwy partnera celowo tu nie ma: test podmienia zestaw skrótów na skrót słowa testowego.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import sprawdz  # noqa: E402

assert len(sprawdz.SKROTY_PARTNERA) == 3

sprawdz.SKROTY_PARTNERA = {hashlib.sha256(s.encode()).hexdigest() for s in ("testfirma", "ab-cd", "abcd")}
for zle in ("Serwis TESTFIRMA sp. z o.o.", "https://testfirma.com.pl/", "firma AB-CD", "firma ab cd",
            "przezwajamy silniki", "Przezwijamy", "podłączanie i przezwajanie na inne napięcie zasilania"):
    assert sprawdz.zakazana_fraza(zle), zle

for dobre in ("Czy przezwajacie silniki elektryczne?", "przezwojenie zlecamy pracowni nawojowej",
              "wirnik", "uzwojenie stojana", "abecadło"):
    assert sprawdz.zakazana_fraza(dobre) is None, dobre

print("OK")
