# Płatności online — co trzeba zrobić, żeby ruszyły

Sklep jest gotowy: katalog, koszyk, zamówienia, konta z adresem do wysyłki
i panel do zarządzania. Brakuje jednego elementu — **umowy z operatorem
płatności**. Tego nie da się obejść kodem: BLIK, Google Pay i karty wymagają
licencjonowanego pośrednika, który weryfikuje sprzedawcę i rozlicza pieniądze.

Do czasu podpisania umowy klient płaci przelewem tradycyjnym albo przy
odbiorze w warsztacie. Obie te drogi już działają.

---

## 1. Co musisz mieć, zanim zaczniesz

| Wymóg | Stan |
|---|---|
| Działalność gospodarcza z wpisem do CEIDG | masz |
| Rachunek firmowy | masz |
| Certyfikat SSL na domenie | masz (HTTPS wymuszony w `.htaccess`) |
| Regulamin sklepu | **do napisania** |
| Polityka prywatności z klauzulą o płatnościach | do uzupełnienia |
| Formularz odstąpienia od umowy (14 dni) | **do przygotowania** |

Trzy ostatnie pozycje operator sprawdza przy weryfikacji sklepu. Bez nich
wniosek zostaje odrzucony — to najczęstszy powód przeciągania się rejestracji.

---

## 2. Wybór operatora

Stawki dla małego sklepu, stan na 2026 rok:

| Operator | BLIK | Karta | Opłata startowa | Uwagi |
|---|---|---|---|---|
| **Tpay** | 1,78% + 0,39 zł | 1,59% + 0,39 zł | brak | Najprostsza rejestracja, konto zwykle w dobę |
| **PayU** | 1,19% + 0,09 zł | 1,9% + 0,25 zł | 199 zł | Najtańszy BLIK, ale opłata startowa |
| **Przelewy24** | 1,2–1,9% | ok. 1,9% | brak | Najszersza obsługa banków, BLIK One Click |
| **Autopay** | od 1,19% | — | brak | Promocje na start dla nowych sklepów |

**Rekomendacja przy Twojej skali:** zacznij od **Tpay** albo **Przelewy24**.
Przy kilku–kilkunastu zamówieniach miesięcznie różnica w prowizji to złotówki,
a liczy się to, jak szybko ruszysz i jak łatwo się to konfiguruje. PayU zaczyna
się opłacać dopiero przy większym obrocie, bo 199 zł na start trzeba odrobić.

---

## 3. Co zrobić po podpisaniu umowy

Operator da Ci komplet identyfikatorów i kluczy. Wpisujesz je programem:

```bash
py ustaw-klucze.py platnosci
```

Program pyta po kolei o każdą pozycję. Klucze i sekrety wpisujesz „w ciemno" —
nie pojawiają się na ekranie ani w historii konsoli. Wszystko idzie prosto do
pliku konfiguracyjnego na serwerze, poza katalogiem WWW.

Potrzebne pozycje zależą od operatora:

- **Przelewy24** — `p24_merchant_id`, `p24_pos_id`, `p24_crc`, `p24_api_key`
- **PayU** — `payu_pos_id`, `payu_md5`, `payu_oauth_client_id`, `payu_oauth_secret`
- **Tpay** — `tpay_id`, `tpay_kod`

Sama obecność któregokolwiek z tych kluczy **automatycznie dokłada opcję
„Płatność online — BLIK, Google Pay, karta"** do listy sposobów zapłaty
(patrz `fw_platnosci()` w `api/_sklep.php`). Nie trzeba niczego przełączać.

---

## 4. Czego jeszcze brakuje w kodzie

Sam moduł rozmowy z operatorem trzeba dopisać — to jeden plik i dwie ścieżki:

1. **Utworzenie transakcji.** Po zapisaniu zamówienia wywołanie API operatora
   z kwotą, numerem zamówienia i adresem powrotnym, a potem przekierowanie
   klienta na stronę płatności.
2. **Odbiór potwierdzenia.** Osobna końcówka przyjmująca powiadomienie od
   operatora, sprawdzająca podpis i ustawiająca zamówieniu status `oplacone`.

**Krok drugi jest tym, na którym łatwo się pomylić.** Statusu nie wolno zmieniać
na podstawie tego, że klient wrócił na stronę „dziękujemy" — ten adres można
otworzyć ręcznie. Jedynym wiarygodnym źródłem jest powiadomienie serwer-serwer
z poprawnym podpisem, zweryfikowanym Twoim kluczem CRC.

Miejsce na to jest przygotowane: tabela `fw_zamowienia` ma kolumnę `status`
ze stanem `oplacone`, a `numer` jest unikalny i nadaje się na identyfikator
transakcji u operatora.

---

## 5. Terminal płatniczy w warsztacie

Osobna sprawa od sklepu — dotyczy klientów płacących na miejscu.

**Program Polska Bezgotówkowa** daje terminal za 0 zł przez pierwsze
12 miesięcy i 0% prowizji od kart do 100 000 zł obrotu. Warunki:

- brak terminala i umowy o przyjmowanie płatności bezgotówkowych
  przez ostatnie 12 miesięcy,
- obrót do 100 000 zł w skali roku,
- sektor MŚP — jednoosobowa działalność kwalifikuje się na tych samych zasadach
  co większe firmy.

Program prowadzi fundacja wspierana przez Ministerstwo Finansów, Związek Banków
Polskich oraz Visa i Mastercard, więc nie jest to promocja jednego banku.
Wniosek składa się przez wybranego agenta rozliczeniowego.

**Czy jest potrzebny do sklepu?** Nie — sklep internetowy działa na bramce
płatności, nie na terminalu. Terminal ma sens wtedy, gdy klienci odbierają
towar w warsztacie i chcą płacić kartą; sposób zapłaty „gotówka lub karta przy
odbiorze" już jest w sklepie i właśnie tego dotyczy.

---

## 6. Kolejność, w jakiej to robić

1. Napisz regulamin sklepu i uzupełnij politykę prywatności.
2. Złóż wniosek u operatora (Tpay albo Przelewy24) — weryfikacja trwa
   od doby do kilku dni.
3. Wpisz klucze: `py ustaw-klucze.py platnosci`.
4. Dopisz moduł transakcji i odbioru potwierdzenia.
5. Przetestuj w trybie piaskownicy (`p24_sandbox = 1`).
6. Otwórz sklep dla wszystkich: `py ustaw-klucze.py sklep`
   i ustaw `sklep_otwarty` na `1`.
7. Usuń `noindex=True` z wpisu `/sklep/` w `pages.py` i przebuduj serwis —
   dopiero wtedy sklep trafi do mapy serwisu i do wyszukiwarki. Linia jest tam
   opisana komentarzem, żeby nie dało się jej przeoczyć.

Do punktu szóstego sklep widzi wyłącznie administrator — pozostali dostają
stronę z informacją o przebudowie.
