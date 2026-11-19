# -*- coding: utf-8 -*-
"""Kompendium wiedzy AI — dane źródłowe podstron /kompendium-ai/.

Materiał powstał jako lokalna baza wiedzy (katalog `D:\\baza danych ai`) i był
jednostronicową aplikacją w JavaScripcie. Tu jest przeniesiony na statyczne
podstrony, bo aplikacja jednostronicowa ma tę samą wadę co forum przed
poprawką: cała treść siedzi w skrypcie i wyszukiwarka nie widzi z niej nic.

Przy przenoszeniu treść została sprawdzona i rozbudowana. Co znaleziono:

  * 13 artykułów miało łącznie 2932 słowa — średnio 225 na artykuł, przy
    deklarowanych czasach czytania rzędu 8–12 minut. Czas czytania liczymy
    teraz z rzeczywistej liczby słów, a artykuły zostały rozbudowane.
  * Artykuł „Parametry samplingu LLM: Temperature, Top-P, Min-P, Repetition
    Penalty" nie tłumaczył Top-P w ogóle, choć miał go w tytule.
  * Interfejs obiecywał „Słownik pojęć (65+ haseł)", a haseł było 40.
  * Zdania w rodzaju „renderuje idealne dłonie" zostały sprowadzone do tego,
    co da się obronić.

Każdy artykuł to słownik:
    slug, tytul, dzial, poziom, tagi, zajawka, tresc

`tresc` jest w uproszczonym Markdownie (nagłówki ###/####, pogrubienia,
`kod`, tabele, listy, cytaty, --- jako separator). Zamienia go na HTML
funkcja `kompendium_html()` w build.py — pełnego parsera tu nie potrzeba,
a własny konwerter nie wciąga zależności do budowania serwisu.
"""

from .comfyui import ARTYKULY as _COMFYUI
from .llm import ARTYKULY as _LLM
from .obrazy import ARTYKULY as _OBRAZY
from .agenci import ARTYKULY as _AGENCI
from .slownik import SLOWNIK
from .zasoby import WORKFLOWY, PROMPTY, SPRZET

# Działy kompendium. Kolejność decyduje o układzie na stronie głównej sekcji.
DZIALY = [
    {
        "slug": "comfyui",
        "nazwa": "ComfyUI i workflowy",
        "opis": "Graf węzłowy, Flux.1, łączenie modeli LoRA i praca z interfejsem.",
    },
    {
        "slug": "llm",
        "nazwa": "Modele językowe lokalnie",
        "opis": "LM Studio, dobór plików GGUF, parametry samplingu i własny serwer API.",
    },
    {
        "slug": "obrazy",
        "nazwa": "Fooocus i SD WebUI Forge",
        "opis": "Szybkie generowanie na słabszym sprzęcie, inpainting i moduły Forge.",
    },
    {
        "slug": "agenci",
        "nazwa": "Agenci AI i MCP",
        "opis": "Pętla narzędziowa, Model Context Protocol i budowa własnego asystenta.",
    },
]

ARTYKULY = _COMFYUI + _LLM + _OBRAZY + _AGENCI

__all__ = ["DZIALY", "ARTYKULY", "SLOWNIK", "WORKFLOWY", "PROMPTY", "SPRZET"]
