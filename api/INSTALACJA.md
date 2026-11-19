# Backend fwdrucik.pl — uruchomienie krok po kroku

Katalog `api/` zawiera backend kont, forum i komentarzy: kilka plików PHP
rozmawiających z bazą MySQL. Frontend (`assets/script.js`) woła je przez `fetch`.

Poniższe kroki wykonujesz raz. Kroki 1–3 robisz ręcznie w panelu hostingu,
bo z tej maszyny nie ma dostępu do MySQL z zewnątrz ani do shella.

---

## Stan na 2026-08-08 — zrobione

Kroki 1–5 są już wykonane na produkcji. Zostało tylko wpisanie hasła bazy
(patrz koniec kroku 3) i krok 6.

Hosting to **home.pl**, panel: <https://cp.home.pl>. Nazwa `hosting-home.pl`
z adresu FTP to tylko nazewnictwo serwerów home.pl — domena `hosting-home.pl`
sama w sobie nie istnieje i nie ma tam żadnego panelu.

| Co | Wartość |
|---|---|
| Serwer | SERWER2631699 (Hosting Biznes Apache) |
| Host bazy | `mysql8` |
| Nazwa bazy | `42047126_fwdrucik` |
| Użytkownik bazy | `42047126_fwdrucik` |
| Wersja MySQL | 8.0.33, utf8mb4 |
| phpMyAdmin | z panelu: Usługi WWW → Bazy danych → *Panel* |
| WebFTP | <https://serwer0000000.hosting-home.pl/homeftp/index.php> |

## 1. Załóż nową bazę MySQL

W panelu **home.pl** (Usługi WWW → OPCJE → *Nowa baza danych*) utwórz
**nową, pustą bazę** — nie używaj bazy Joomli. Zapisz cztery rzeczy: host,
nazwę bazy, użytkownika i hasło.

## 2. Wgraj strukturę tabel

W panelu wejdź w **phpMyAdmin**, wybierz nową bazę, zakładka **SQL**, wklej
całą zawartość pliku `api/schemat.sql` i wykonaj. Powstanie sześć tabel
z prefiksem `fw_`: `fw_uzytkownicy`, `fw_sesje`, `fw_watki`, `fw_odpowiedzi`,
`fw_komentarze`, `fw_limity`.

## 3. Utwórz plik konfiguracyjny na serwerze

Skopiuj `api/konfiguracja.przyklad.php` i wgraj go przez FTP jako:

```
public_html/autoinstalator/fw-konfiguracja.php
```

Ten katalog leży **piętro wyżej niż katalog serwowany przez WWW** (domena
wskazuje na `public_html/autoinstalator/joomla`), więc pliku nie da się pobrać
z internetu. Uzupełnij w nim dane z kroku 1.

Wariant awaryjny — gdyby hosting nie pozwolił czytać z tamtego katalogu —
to `.../joomla/api/konfiguracja.php`. Wtedy chroni go już tylko reguła
z `api/.htaccess`, więc traktuj to jako rozwiązanie tymczasowe.

Pliku konfiguracyjnego **nie ma w repozytorium** i `build.py` celowo go nie
kopiuje do `dist/`, więc `wyslij.py` go nie nadpisze.

## 4. Wyślij serwis

```bash
python build.py
python sprawdz.py
python wyslij.py --wykonaj
```

`build.py` kopiuje `api/` do `dist/api/` z pominięciem `konfiguracja.php`
i `schemat.sql`.

## 5. Sprawdź, czy API odpowiada

W przeglądarce otwórz:

```
https://fwdrucik.pl/api/auth.php?akcja=ja
```

Poprawna odpowiedź to JSON: `{"ok":true,"uzytkownik":null,"csrf":"..."}`.

- `{"ok":false,"blad":"Brak pliku konfiguracyjnego API."}` — krok 3 nie doszedł do skutku.
- `{"ok":false,"blad":"Baza danych jest chwilowo niedostępna."}` — złe dane w konfiguracji.
- Pobieranie pliku zamiast JSON-a — hosting nie wykonał PHP; sprawdź blok
  `SetEnv CGI_HANDLER php84` w `api/.htaccess`.

## 6. Zrób sobie konto administratora

1. Wejdź na https://fwdrucik.pl/konto/ i zarejestruj się normalnie
   (e-mail `fwdrucik@gmail.com`, własne mocne hasło — minimum 10 znaków).
2. W phpMyAdmin wykonaj:

```sql
UPDATE fw_uzytkownicy SET rola = 'admin', zaufany = 1
  WHERE email = 'fwdrucik@gmail.com';
```

3. Wyloguj się i zaloguj ponownie. `/admin/` pokaże kolejkę moderacji.

W repozytorium nie ma i nie może być hasła administratora ani jego skrótu —
dlatego konto powstaje tą drogą.

---

## Jak to działa

**Sesje.** Po zalogowaniu serwer losuje 32-bajtowy token, w bazie trzyma tylko
jego skrót SHA-256, a sam token wkłada do ciasteczka `fw_sesja`
(`HttpOnly`, `Secure`, `SameSite=Lax`, 30 dni). JavaScript nie ma do niego
dostępu, więc XSS nie wykrada sesji.

**CSRF.** Drugie ciasteczko `fw_csrf` (zwykłe, czytelne dla JS) musi zostać
powtórzone w nagłówku `X-FW-CSRF` przy każdym POST. Obca strona nie odczyta
ciasteczka z domeny fwdrucik.pl, więc nagłówka nie podrobi.

**Hasła.** `password_hash()` z `PASSWORD_DEFAULT` (obecnie bcrypt).
Przy logowaniu `password_needs_rehash()` przelicza skrót, jeśli PHP podniesie
domyślny algorytm. Nieistniejące konto też przechodzi przez `password_verify()`
na atrapie skrótu — po czasie odpowiedzi nie da się zgadnąć, które adresy są
zarejestrowane.

**Moderacja.** Nowe konto ma `zaufany = 0` i jego pierwsza treść dostaje status
`oczekuje` — widzi ją tylko autor i administrator. Zatwierdzenie w panelu
ustawia `zaufany = 1`, więc kolejne wpisy tego autora publikują się od razu.

**Limity tempa** (na adres IP): rejestracja 5/godz., logowanie 10/15 min,
nowy wątek 5/godz., odpowiedzi i komentarze po 20/godz. Formularz rejestracji
ma dodatkowo ukryte pole-pułapkę na boty.

**SQL.** Wyłącznie `PDO` z prawdziwymi zapytaniami parametryzowanymi
(`ATTR_EMULATE_PREPARES = false`). Nazwy tabel składane są z prefiksu
sprawdzanego wyrażeniem regularnym, nigdy z danych użytkownika.

**Escapowanie.** Backend zapisuje treść bez zmian, a przeglądarka wypisuje ją
przez funkcję `esc()` w `assets/script.js`. Nie usuwaj jej — bez niej wraca
podatność XSS w komentarzach i wątkach.

## Końcówki API

| Adres | Metoda | Opis |
|---|---|---|
| `/api/auth.php?akcja=ja` | GET | kto jest zalogowany + token CSRF |
| `/api/auth.php?akcja=rejestracja` | POST | `nick`, `email`, `haslo` |
| `/api/auth.php?akcja=logowanie` | POST | `login`, `haslo` |
| `/api/auth.php?akcja=wylogowanie` | POST | — |
| `/api/forum.php?akcja=watki` | GET | `kategoria` = `all`/`elektro`/`spawanie`/`klimatyzacja` |
| `/api/forum.php?akcja=watek` | GET | `id` |
| `/api/forum.php?akcja=nowy-watek` | POST | `kategoria`, `tytul`, `tresc` |
| `/api/forum.php?akcja=odpowiedz` | POST | `watek_id`, `tresc` |
| `/api/komentarze.php?akcja=lista` | GET | `slug` |
| `/api/komentarze.php?akcja=dodaj` | POST | `slug`, `tresc` |
| `/api/moderacja.php?akcja=kolejka` | GET | tylko admin |
| `/api/moderacja.php?akcja=uzytkownicy` | GET | tylko admin |
| `/api/moderacja.php?akcja=zatwierdz\|odrzuc\|usun` | POST | `typ`, `id` |
| `/api/moderacja.php?akcja=blokuj` | POST | `id`, `zablokowany` |

Wszystkie odpowiedzi to JSON. Sukces ma `"ok": true`, błąd `"ok": false`
i pole `blad` z komunikatem po polsku, gotowym do pokazania użytkownikowi.
