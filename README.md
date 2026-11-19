# fwdrucik.pl — kod serwisu (wersja publiczna do portfolio)

Serwis firmy F.W. DRUCIK: statyczny generator w Pythonie (ok. 140 podstron, blog, kompendium AI,
Pracownia Pana Drucika dla dzieci), backend PHP dla kont, forum, komentarzy i sklepu oraz
interaktywne sceny Three.js. Na żywo: https://fwdrucik.pl

**Jak powstał:** kod napisały agenty AI (Claude Code, Codex, Antigravity). Dawid Tutak opisywał
wymagania, dzielił pracę na zadania, testował i odbierał wynik. To przykład podejścia
*AI-native engineering*.

## Co tu jest
- `build.py`, `pages.py`, `src/` — generator stron, metadane i treść
- `sprawdz.py` — bramka jakości (tytuły, opisy, nagłówki, dane strukturalne, mapa serwisu); błąd zatrzymuje wdrożenie
- `api/`, `php/` — backend PHP (konta, forum, sklep, panel administratora)
- `assets/` — style, skrypty, sceny 3D
- `kompendium/`, `pracownia*/` — treści edukacyjne

## Czego tu nie ma
To kopia bez historii commitów. Usunięte są: zbudowany `dist/`, workflowy wdrożeń, notatki
wewnętrzne agentów, szkice wpisów. Klucze i hasła nigdy nie były w kodzie (konfiguracja serwera
żyje poza repozytorium, wzór w `api/konfiguracja.przyklad.php`).

## Uruchomienie
```
python build.py     # generuje dist/
python sprawdz.py   # kontrola jakości
```

## Licencja
Kod udostępniony do wglądu jako portfolio. Wszelkie prawa zastrzeżone © F.W. DRUCIK Dawid Tutak.
