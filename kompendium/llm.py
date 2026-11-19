# -*- coding: utf-8 -*-
"""Dział modeli językowych uruchamianych lokalnie: LM Studio, GGUF, sampling, API."""

ARTYKULY = [
    {
        "slug": "lm-studio-od-a-do-z",
        "tytul": "LM Studio od A do Z — instalacja, dobór modelu GGUF i ustawienia GPU",
        "tytul_seo": "LM Studio od A do Z — Modele LLM lokalnie | F.W. DRUCIK",
        "dzial": "llm",
        "poziom": "Podstawowy",
        "tagi": ["LM Studio", "GGUF", "VRAM", "Kwantyzacja", "llama.cpp"],
        "zajawka": "Jak dobrać model do posiadanej karty, co naprawdę znaczą oznaczenia "
                   "Q4_K_M i Q8_0, ile warstw przenieść na GPU i skąd biorą się nagłe "
                   "spadki prędkości generowania.",
        "tresc": """
### Po co uruchamiać model lokalnie

Lokalny model działa bez internetu, opłat za token i limitu zapytań usługi. **Dane pozostają na komputerze.** Ograniczeniem jest sprzęt: mały model zwykle ustępuje największym modelom chmurowym.

Sprawdza się przy notatkach, ekstrakcji danych, tłumaczeniu, kodzie i dokumentach firmy. Zadania wymagające szerokiej wiedzy lub długiego rozumowania mogą być trudniejsze.

---

### Format GGUF i kwantyzacja

LM Studio korzysta z silnika **llama.cpp** i formatu **GGUF**. To jeden plik zawierający wagi
modelu w skwantyzowanej postaci — czyli zapisane z mniejszą precyzją niż oryginalne 16 bitów
na parametr.

Oznaczenia w nazwie pliku znaczą konkretne rzeczy:

| Oznaczenie | Bity na wagę | Jakość | Kiedy sięgać |
| :--- | :--- | :--- | :--- |
| `Q2_K` | ~2,6 | Wyraźnie gorsza | Ostateczność przy bardzo małej pamięci |
| `Q3_K_M` | ~3,9 | Zauważalnie gorsza | Gdy Q4 się nie mieści |
| `Q4_K_M` | ~4,8 | Dobra | **Domyślny wybór** — najlepszy stosunek jakości do rozmiaru |
| `Q5_K_M` | ~5,7 | Bardzo dobra | Gdy jest zapas pamięci |
| `Q6_K` | ~6,6 | Prawie jak oryginał | Zapas pamięci i zależy na precyzji |
| `Q8_0` | ~8,5 | Praktycznie bez straty | Rzadko potrzebne poniżej modeli 7B |

Litera `K` oznacza nowszą metodę kwantyzacji (k-quants), która rozdziela precyzję nierównomiernie
— więcej bitów dla warstw wrażliwych. `_M` to wariant średni, `_S` mniejszy, `_L` większy.

**Reguła praktyczna:** większy model w mocniejszej kwantyzacji zwykle bije mniejszy model
w słabszej. Model 13B w Q4_K_M da lepsze wyniki niż 7B w Q8_0 przy podobnym rozmiarze pliku.

---

### Ile pamięci potrzeba

Przybliżenie, które wystarcza do planowania: **rozmiar pliku GGUF plus 1–2 GB na okno kontekstu
i bufory**. Model 7B w Q4_K_M to około 4,4 GB pliku, czyli komfortowo mieści się na karcie 8 GB
razem z kontekstem 8192 tokenów.

| Pamięć karty | Rozsądny wybór |
| :--- | :--- |
| 6 GB | 7B w Q4_K_M, kontekst do 4096 |
| 8 GB | 7–8B w Q4_K_M lub Q5_K_M, kontekst 8192 |
| 12 GB | 13–14B w Q4_K_M, kontekst 16384 |
| 16 GB | 14B w Q5_K_M albo 22B w Q4_K_M |
| 24 GB | 32B w Q4_K_M, kontekst 32768 |

---

### GPU Offload — najważniejszy suwak

W ustawieniach modelu jest pozycja **GPU Offload** (`n_gpu_layers`) określająca, ile warstw sieci
trafi do pamięci karty. Reszta zostaje w pamięci operacyjnej i liczy ją procesor.

Różnica jest dramatyczna. Model w całości na karcie generuje kilkadziesiąt tokenów na sekundę.
Ten sam model z dwiema warstwami na procesorze potrafi zwolnić do kilku tokenów na sekundę —
bo każdy token musi przejść przez wolniejszą ścieżkę.

**Stąd praktyczna zasada: albo model mieści się w całości, albo warto wziąć mniejszy.** Częściowe
przeniesienie ma sens tylko wtedy, gdy naprawdę zależy nam na konkretnym dużym modelu i godzimy
się czekać.

Ustawienie `-1` przenosi wszystkie warstwy. Jeśli model się nie mieści, LM Studio zgłosi błąd
pamięci — wtedy schodzi się w dół, aż zadziała.

---

### Okno kontekstu kosztuje pamięć

Parametr **Context Length** określa, ile tokenów model pamięta. Każde podwojenie kontekstu zwiększa
zużycie pamięci na **KV Cache** — bufor przechowujący stany pośrednie dla wszystkich dotychczasowych
tokenów.

Przy modelu 7B kontekst 32768 tokenów potrafi zająć kilka gigabajtów samego bufora. Dlatego model,
który ładował się bez problemu przy kontekście 4096, może nie zmieścić się przy 32768.

Jeśli silnik na to pozwala, warto włączyć **kwantyzację KV Cache** (często oznaczaną jako `q8_0`
dla klucza i wartości) — zmniejsza zapotrzebowanie o połowę przy niewielkiej stracie.

---

### Dlaczego generowanie nagle zwalnia

Cztery najczęstsze przyczyny, w kolejności występowania:

- **Model nie mieści się w całości** i część warstw liczy procesor. Sprawdź `n_gpu_layers`
  i faktyczne zużycie pamięci karty w menedżerze zadań.
- **Kontekst się zapełnił.** Im dłuższa rozmowa, tym więcej tokenów model przetwarza przy każdej
  odpowiedzi. Spowolnienie narastające w trakcie długiej sesji to normalne zachowanie.
- **Sterownik przeniósł nadmiar do pamięci systemowej.** Nowsze sterowniki NVIDIA robią to zamiast
  zgłosić błąd — model działa, ale wielokrotnie wolniej. Można to wyłączyć w panelu sterownika.
- **Zbyt duża liczba wątków procesora.** Ustawienie większe niż liczba rdzeni fizycznych zwykle
  szkodzi zamiast pomagać.

---

### Szablon rozmowy ma znaczenie

Każda rodzina modeli oczekuje innego formatu wiadomości: ChatML, Llama 3, Mistral, Alpaca. LM Studio
zwykle wykrywa go z metadanych pliku, ale przy modelach składanych ręcznie potrafi trafić źle.

Objaw jest charakterystyczny: model odpowiada sensownie, ale **nie przestaje pisać** — dokleja
kolejne wymyślone tury rozmowy albo powtarza pytanie użytkownika. To znak, że znacznik końca
wypowiedzi nie zgadza się z szablonem. Poprawia się to ręcznie w ustawieniach modelu.
""",
    },
    {
        "slug": "parametry-samplingu-llm",
        "tytul": "Parametry samplingu w modelach językowych — temperatura, Top-P, Min-P, kary",
        "dzial": "llm",
        "poziom": "Średniozaawansowany",
        "tagi": ["Sampling", "Temperature", "Top-P", "Min-P", "LLM"],
        "zajawka": "Co robi każdy suwak, w jakiej kolejności są stosowane i jakie zestawy "
                   "sprawdzają się do kodu, do rozmowy i do pisania. Z wyjaśnieniem, "
                   "dlaczego przy Min-P nie ustawia się Top-P.",
        "tresc": """
### Jak model wybiera kolejne słowo

Model oblicza **prawdopodobieństwa kolejnego tokenu** w słowniku. Sampling określa, które tokeny dopuścić i jak wybrać jeden z nich.

Filtry działają kolejno: temperatura zmienia rozkład, dalsze filtry ograniczają kandydatów, potem następuje losowanie.

---

### Temperature — jak bardzo model ryzykuje

Temperatura skaluje różnice między prawdopodobieństwami. Niska wyostrza rozkład (najlepszy token
staje się jeszcze bardziej dominujący), wysoka go spłaszcza (mniej prawdopodobne tokeny dostają
szansę).

| Zakres | Zachowanie | Zastosowanie |
| :--- | :--- | :--- |
| 0,0–0,2 | Praktycznie deterministyczne | Kod, matematyka, wyciąganie danych do JSON |
| 0,3–0,5 | Ostrożne, powtarzalne | Streszczenia, tłumaczenia, odpowiedzi faktograficzne |
| 0,7–0,8 | Naturalne, zrównoważone | Rozmowa, pisanie artykułów, asystent ogólny |
| 1,0–1,3 | Kreatywne | Burza mózgów, warianty tekstu, fabuła |
| powyżej 1,5 | Chaotyczne | Rzadko użyteczne |

Temperatura 0 nie oznacza, że model zawsze odpowie identycznie — przy obliczeniach na GPU drobne
różnice w kolejności operacji potrafią zmienić wynik. Do pełnej powtarzalności potrzebne jest
jeszcze ustawione ziarno losowe.

---

### Top-P (nucleus sampling) — obcięcie ogona po sumie

Top-P sortuje tokeny od najbardziej do najmniej prawdopodobnego i **sumuje ich prawdopodobieństwa,
aż suma przekroczy zadaną wartość**. Wszystko poza tym zbiorem jest odrzucane.

Przy `top_p = 0,9` model bierze pod uwagę tyle najlepszych tokenów, ile trzeba, żeby objąć 90%
masy prawdopodobieństwa. Jeśli rozkład jest ostry — jeden token ma 95% — zbiór ma jeden element
i wybór jest przesądzony. Jeśli rozkład jest płaski, w grze zostaje kilkadziesiąt tokenów.

- **0,9–0,95** — wartości typowe, bezpieczne przy większości zastosowań.
- **0,5–0,7** — bardziej zachowawczo, gdy model zbacza z tematu.
- **1,0** — filtr wyłączony, decyduje sama temperatura.

Słabość Top-P polega na tym, że **nie odróżnia sytuacji pewnej od niepewnej w sposób, jakiego
byśmy chcieli**. Gdy najlepszy token ma 40%, a kolejne po 10%, próg 0,9 wpuszcza do losowania
tokeny wyraźnie gorsze od lidera.

---

### Min-P — nowszy filtr względem lidera

Min-P odrzuca tokeny, których prawdopodobieństwo jest **niższe niż zadany ułamek prawdopodobieństwa
najlepszego tokena**. Przy `min_p = 0,05` i liderze o prawdopodobieństwie 60% odpada wszystko
poniżej 3%.

To zachowanie jest bardziej intuicyjne: gdy model jest pewny, próg rośnie razem z liderem i filtr
działa ostro; gdy model się waha, próg spada i zostaje więcej opcji. Dokładnie tego oczekujemy.

- Wartości typowe: **0,05–0,10**.
- Wyższe (0,15+) mocno zawężają wybór i usztywniają styl.

> **Nie stosuj Top-P i Min-P jednocześnie.** Oba robią to samo zadanie różnymi metodami,
> a nałożone na siebie dają zawężenie trudne do przewidzenia. Wybierz jeden i wyłącz drugi:
> `top_p = 1,0` przy pracy z Min-P.

---

### Top-K — najprostszy filtr

Top-K zostawia po prostu K najlepszych tokenów, niezależnie od ich prawdopodobieństw. Jest
najstarszy z tej trójki i najmniej elastyczny — przy ostrym rozkładzie wpuszcza niepotrzebne
tokeny, przy płaskim odcina za dużo. Zwykle zostawia się go wyłączonego (`0`) albo na dużej
wartości (40–100) jako zabezpieczenie.

---

### Repetition Penalty — kara za powtórzenia

Zmniejsza prawdopodobieństwo tokenów, które już wystąpiły. Zapobiega zapętleniom, w których model
w kółko powtarza to samo zdanie.

- **1,0** — kara wyłączona.
- **1,05–1,15** — zakres praktyczny.
- **powyżej 1,25** — psuje kod. Model „boi się" użyć drugi raz tej samej nazwy zmiennej albo
  słowa kluczowego, przez co generuje składniowo błędne fragmenty.

Przy zadaniach programistycznych warto trzymać wartość blisko 1,0 i walczyć z powtórzeniami
promptem, a nie karą.

Pokrewne parametry to **frequency penalty** (kara rosnąca z liczbą wystąpień) i **presence penalty**
(stała kara za samo wystąpienie). Ta druga bywa lepsza do wymuszenia różnorodności tematów
bez psucia składni.

---

### Gotowe zestawy

| Zadanie | Temp | Min-P | Top-P | Rep. penalty |
| :--- | :--- | :--- | :--- | :--- |
| Kod, dane, JSON | 0,1 | 0,05 | 1,0 | 1,0 |
| Odpowiedzi faktograficzne | 0,3 | 0,05 | 1,0 | 1,05 |
| Rozmowa, asystent | 0,7 | 0,05 | 1,0 | 1,1 |
| Pisanie, warianty | 1,0 | 0,08 | 1,0 | 1,1 |
| Burza mózgów | 1,2 | 0,10 | 1,0 | 1,15 |

---

### Okno kontekstu to nie parametr samplingu

**Context Length** bywa mylony z suwakami samplingu, bo leży w tym samym panelu. Określa, ile
tokenów wstecz model widzi — a nie jak wybiera kolejny.

Każde podwojenie kontekstu zwiększa zużycie pamięci na KV Cache i wydłuża czas odpowiedzi. Jeśli
model ma odpowiadać na podstawie długiego dokumentu, zwykle lepiej wyciągnąć z niego istotny
fragment i podać w promptcie, niż wrzucać całość i podnosić kontekst do maksimum.
""",
    },
    {
        "slug": "lokalny-serwer-api-llm",
        "tytul": "Lokalny serwer API modelu językowego — podpięcie pod własne aplikacje",
        "dzial": "llm",
        "poziom": "Średniozaawansowany",
        "tagi": ["API", "LM Studio", "OpenAI", "Integracja", "Python"],
        "zajawka": "Model uruchomiony lokalnie wystawia interfejs zgodny z API OpenAI. "
                   "Wystarczy to, żeby podpiąć go pod edytor kodu, własny skrypt "
                   "albo narzędzie warsztatowe — bez wysyłania czegokolwiek do chmury.",
        "tresc": """
### Na czym polega zgodność z API OpenAI

LM Studio, Ollama i llama.cpp udostępniają HTTP API zgodne z formatem OpenAI. Zgodne biblioteki można skierować do modelu lokalnego, zmieniając adres serwera.

W LM Studio wybierz **Developer** lub *Local Server* i **Start Server**. Domyślny adres: `http://localhost:1234/v1`.

Dostępne końcówki:

- `POST /v1/chat/completions` — rozmowa, najczęściej używana
- `POST /v1/completions` — uzupełnianie tekstu bez struktury rozmowy
- `POST /v1/embeddings` — wektory do wyszukiwania semantycznego
- `GET /v1/models` — lista załadowanych modeli

---

### Najprostsze wywołanie

Sprawdzenie, czy serwer odpowiada, zajmuje jedno polecenie:

```
curl http://localhost:1234/v1/models
```

Właściwe zapytanie z Pythona, bez żadnej dodatkowej biblioteki:

```
import json, urllib.request

zapytanie = {
    "model": "lokalny",
    "messages": [
        {"role": "system", "content": "Odpowiadasz krótko i konkretnie."},
        {"role": "user", "content": "Wypisz trzy przyczyny spadku ciśnienia w układzie."}
    ],
    "temperature": 0.3,
    "max_tokens": 400,
}

req = urllib.request.Request(
    "http://localhost:1234/v1/chat/completions",
    data=json.dumps(zapytanie).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=120) as odp:
    wynik = json.load(odp)

print(wynik["choices"][0]["message"]["content"])
```

Pole `model` przy serwerze lokalnym jest zwykle ignorowane — liczy się to, co faktycznie jest
załadowane w programie. Klucz API też nie jest wymagany, choć niektóre biblioteki upierają się
przy jego obecności; wystarczy wtedy dowolny ciąg znaków.

---

### Odpowiedź strumieniowa

Ustawienie `"stream": true` sprawia, że serwer odsyła odpowiedź kawałkami, w formacie
server-sent events. Dla interfejsu użytkownika to duża różnica: tekst pojawia się od razu, zamiast
po kilkunastu sekundach ciszy.

Każda linia zaczyna się od `data: ` i zawiera fragment JSON z polem `delta`. Strumień kończy się
linią `data: [DONE]`.

---

### Wymuszenie odpowiedzi w formacie JSON

Gdy odpowiedź ma trafić prosto do programu, a nie do człowieka, parsowanie swobodnego tekstu jest
proszeniem się o kłopoty. Dwa mechanizmy to rozwiązują:

- **`response_format`** z typem `json_schema` — serwer pilnuje, żeby wynik pasował do podanego
  schematu. Obsługa zależy od wersji programu.
- **Gramatyka GBNF** w llama.cpp — ograniczenie na poziomie samplingu, przez co model
  fizycznie nie może wygenerować tokenu łamiącego format.

Bez żadnego z nich zostaje trzeci sposób, prosty i skuteczny: bardzo dokładny system prompt plus
temperatura 0,1 plus walidacja po stronie programu z jedną ponowną próbą.

---

### Do czego to podpiąć

- **Edytor kodu.** Wtyczki typu Continue dla VS Code przyjmują dowolny adres zgodny z OpenAI —
  podpowiedzi działają wtedy bez wysyłania kodu na zewnątrz.
- **Własne narzędzia.** Skrypt porządkujący notatki, generator opisów, klasyfikator wiadomości.
- **Pętla narzędziowa.** Model może zwrócić żądanie wywołania funkcji, a program je wykona
  i odeśle wynik — to podstawa działania agenta.
- **Wyszukiwanie semantyczne.** Końcówka `embeddings` pozwala zbudować wyszukiwarkę po własnych
  dokumentach, która rozumie znaczenie, a nie tylko dopasowanie znaków.

---

### Bezpieczeństwo: serwer bez uwierzytelniania

Domyślnie serwer nie ma żadnej kontroli dostępu. Dopóki nasłuchuje na `localhost`, jest widoczny
tylko dla programów na tym samym komputerze — i tak powinno zostać.

Zmiana adresu nasłuchu na `0.0.0.0` udostępnia model **całej sieci lokalnej**. Bywa to potrzebne
(model na komputerze stacjonarnym, korzystanie z telefonu), ale wtedy trzeba świadomie ograniczyć
dostęp: reguła zapory dopuszczająca konkretne adresy albo pośrednik wymagający hasła. Nigdy nie
należy wystawiać takiego serwera bezpośrednio do internetu.

---

### Typowe problemy

| Objaw | Przyczyna |
| :--- | :--- |
| Połączenie odrzucone | Serwer nie wystartował albo inny port |
| Odpowiedź obcięta w połowie | Zbyt małe `max_tokens` |
| Model dopisuje kolejne tury rozmowy | Niedopasowany szablon rozmowy |
| Bardzo długi czas pierwszej odpowiedzi | Ładowanie modelu do pamięci — dotyczy tylko pierwszego zapytania |
| Błąd braku klucza API | Biblioteka wymaga pola; wpisz dowolny ciąg |
""",
    },
]
