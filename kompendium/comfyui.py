# -*- coding: utf-8 -*-
"""Dział ComfyUI: graf węzłowy, Flux.1, LoRA i praca z interfejsem."""

ARTYKULY = [
    {
        "slug": "comfyui-architektura-wezlowa",
        "tytul": "Architektura węzłowa ComfyUI — graf, złącza i rurociąg generacji",
        "tytul_seo": "Architektura węzłowa ComfyUI — Budowa workflow | F.W. DRUCIK",
        "dzial": "comfyui",
        "poziom": "Podstawowy",
        "tagi": ["ComfyUI", "Podstawy", "Węzły", "Latent", "KSampler", "VAE", "CLIP"],
        "zajawka": "Od załadowania checkpointu, przez kodowanie promptu w CLIP i przestrzeń "
                   "ukrytą, po odszumianie w KSamplerze i dekodowanie pikseli w VAE — z typami "
                   "złączy, kolejnością wykonania i błędami, które łapie każdy początkujący.",
        "tresc": """
### Czym jest ComfyUI

ComfyUI przedstawia generowanie jako **graf skierowany bez cykli (DAG)**. Obsługuje SD 1.5, SD 2.1, SDXL, SD3, Flux.1, Stable Cascade i wideo. Każdy etap jest węzłem, który można sprawdzić lub wymienić.

ComfyUI **przelicza węzły, których wejścia się zmieniły**. Zmiana ziarna uruchamia sampling bez ponownego ładowania modelu. To skraca kolejne próby.

---

### Typy złączy i ich kolory

Każde gniazdo ma ściśle określony typ danych. Interfejs blokuje połączenie niezgodnych typów,
więc pomyłka jest fizycznie niemożliwa — to jedna z mocniejszych stron tego podejścia.

| Typ złącza | Kolor | Co przenosi |
| :--- | :--- | :--- |
| **MODEL** | fioletowy | Wagi sieci: UNet w SD 1.5 i SDXL albo transformer DiT w Flux.1 |
| **CLIP** | żółty | Enkoder tekstu zamieniający prompt na wektory |
| **VAE** | czerwony | Koder i dekoder między pikselami RGB a przestrzenią ukrytą |
| **CONDITIONING** | jasnozielony | Prompt po przetworzeniu przez CLIP, z wagami |
| **LATENT** | różowy | Skompresowana reprezentacja obrazu, np. 128×128 dla 1024×1024 |
| **IMAGE** | niebieski | Zdekodowany obraz rastrowy RGB |
| **MASK** | biały | Maska jednokanałowa dla inpaintingu i outpaintingu |
| **CONTROL_NET** | pomarańczowy | Wagi modelu narzucającego ograniczenia przestrzenne |

Warto zapamiętać proporcję: latent jest **ośmiokrotnie mniejszy w każdym wymiarze** niż obraz
docelowy. Obraz 1024×1024 to latent 128×128. Dlatego cały kosztowny proces odszumiania toczy się
na małej macierzy, a dopiero na końcu VAE rozwija ją do pełnej rozdzielczości.

---

### Rurociąg generacji krok po kroku

1. **Load Checkpoint** — wczytuje plik `.safetensors` i wyprowadza trzy wyjścia: `MODEL`, `CLIP`, `VAE`.
2. **Empty Latent Image** — tworzy pustą macierz szumu o zadanych wymiarach. Dla SDXL punktem
   wyjścia jest 1024×1024, dla SD 1.5 — 512×512.
3. **CLIP Text Encode** — dwa węzły: prompt pozytywny i negatywny.
4. **KSampler** — właściwa generacja. Przyjmuje `MODEL`, oba `CONDITIONING` oraz `LATENT`
   i wykonuje iteracyjne odszumianie.
5. **VAE Decode** — zamienia gotowy latent na piksele.
6. **Save Image** — zapisuje PNG z całym grafem zaszytym w metadanych.

> **Sztuczka z metadanymi.** Przeciągnij dowolny PNG wygenerowany w ComfyUI na okno przeglądarki
> z otwartym programem, a odtworzy się cały workflow — te same węzły, wagi i ustawienia. To
> najprostszy sposób na dzielenie się konfiguracją i na odtworzenie własnej pracy sprzed miesiąca.

---

### Rozdzielczość: dlaczego „większe" nie znaczy „lepsze"

Model generuje sensownie w okolicach rozdzielczości, na której był trenowany. SD 1.5 uczono na
512×512, SDXL na około 1024×1024. Wpisanie od razu 2048×2048 nie daje ostrzejszego obrazu, tylko
**zdublowane elementy**: dwie głowy, cztery ręce, powtórzony horyzont. Sieć nie ma pojęcia
kompozycji w takiej skali.

Prawidłowa droga do dużego obrazu to dwa etapy:

1. Wygeneruj w rozdzielczości natywnej modelu.
2. Powiększ (`Upscale Latent` albo `Upscale Image`) i przepuść przez drugi KSampler
   z parametrem **denoise 0.35–0.55**. Niższa wartość zachowuje kompozycję, wyższa dorysowuje detal.

Przy bardzo dużych obrazach VAE potrafi wyczerpać pamięć karty przy samym dekodowaniu. Wtedy
zamiast `VAE Decode` używa się `VAE Decode (Tiled)` — dekoduje kafelkami, wolniej, ale mieści się
w pamięci.

---

### Kolejność wykonania i kolejka

ComfyUI nie wykonuje węzłów od lewej do prawej, tylko rozwiązuje zależności: liczy to, co jest
potrzebne wyjściu, i tylko to. Węzeł odłączony od żadnego wyjścia nie zostanie policzony w ogóle,
choćby stał na środku ekranu.

Kolejka (`Queue Prompt`) przyjmuje wiele zadań naraz. Można przygotować pięć wariantów promptu,
wrzucić je jedno po drugim i odejść od komputera — wykonają się po kolei. `Queue Front` wpycha
zadanie na początek, gdy trzeba coś sprawdzić bez czekania.

---

### Pięć błędów, które łapie prawie każdy początkujący

- **Podpięcie VAE z innego modelu.** Obraz wychodzi wtedy blady, przesycony albo w dziwnych
  barwach. VAE musi pasować do rodziny modelu.
- **Rozdzielczość spoza siatki 64 pikseli.** Wartości typu 1000×1000 dają artefakty na krawędziach.
  Trzymaj się wielokrotności 64.
- **CFG ustawione na 12–15 „bo mocniej".** Powyżej ok. 8 obraz zaczyna być przepalony: twarde
  kontury, plastikowa skóra, wypalone światła. Dla SDXL rozsądny zakres to 4–7.
- **Prompt negatywny przepisany z cudzego workflow.** Trzydzieści słów o „bad anatomy" przy modelu,
  który tego nie potrzebuje, zabiera tylko okno kontekstu enkodera.
- **Denoise 1.0 przy drugim przebiegu.** Powiększanie z pełnym odszumianiem generuje obraz od nowa,
  zamiast dopracować istniejący.

---

### Porządek w grafie

Przy dziesięciu węzłach graf jest czytelny sam z siebie. Przy pięćdziesięciu — już nie. Trzy
nawyki, które to ratują:

- **Reroute** — węzeł przekierowania, który pozwala poprowadzić długi kabel przez wyznaczony punkt
  zamiast na skos przez cały ekran.
- **Grupy** — zaznacz kilka węzłów i utwórz grupę (`Add Group`). Całą grupę można przesuwać
  i wyłączać jednym kliknięciem.
- **Bypass zamiast usuwania** — skrót `Ctrl+B` wyłącza węzeł, przepuszczając dane dalej.
  Idealne do sprawdzenia, co dana LoRA albo ControlNet faktycznie wnosi do obrazu.
""",
    },
    {
        "slug": "comfyui-laczenie-lora",
        "tytul": "Łączenie wielu modeli LoRA w ComfyUI — wagi, kolejność i konflikty",
        "dzial": "comfyui",
        "poziom": "Średniozaawansowany",
        "tagi": ["LoRA", "ComfyUI", "Wagi", "Styl", "Postać"],
        "zajawka": "Dwa suwaki wagi, trzy metody łączenia i sposób na najczęstszy konflikt: "
                   "LoRA postaci kontra LoRA stylu. Z metodą testowania wag, która zajmuje "
                   "jeden przebieg zamiast dwudziestu.",
        "tresc": """
### Czym jest LoRA

LoRA (Low-Rank Adaptation) to nakładka na model, zwykle 10–300 MB, ucząca go postaci, stylu, przedmiotu lub pozy bez ponownego trenowania wszystkich wag.

LoRA zapisuje zmianę wag jako iloczyn dwóch mniejszych macierzy. **Rank**, np. 8, 16, 32 lub 64, określa pojemność nakładki. Większy rank zwiększa plik i możliwość odwzorowania szczegółów, ale też ryzyko przeuczenia.

---

### Dwa suwaki, nie jeden

Węzeł **Load LoRA** ma dwie wagi i mylenie ich jest najczęstszym źródłem rozczarowań:

- **strength_model** — jak mocno LoRA wpływa na strukturę, kształty i anatomię.
- **strength_clip** — jak silnie enkoder tekstu reaguje na słowa wyzwalające (*trigger words*)
  powiązane z tą LoRA.

> **Reguła praktyczna.** Sensowny zakres to zwykle **0,6–0,85**. Wartość 1,0 przy łączeniu kilku
> LoRA prawie zawsze daje „przepalenie": nadmierny kontrast, plastikową skórę i zniekształcone
> krawędzie. Jeśli efekt jest za słaby, częściej pomaga poprawienie promptu niż podbicie wagi.

---

### Trzy metody łączenia

#### Łańcuch szeregowy

Wyjścia `MODEL` i `CLIP` z pierwszego węzła LoRA wpinasz w wejścia drugiego, i tak dalej.
Działa w czystym ComfyUI bez wtyczek. Przy czterech i więcej LoRA graf robi się nieczytelny.

#### LoRA Stacker

Węzły z paczek *rgthree* albo *Efficiency Nodes* pozwalają zdefiniować kilka modeli w jednym
panelu, z możliwością wyłączania pojedynczych pozycji jednym kliknięciem. Przy testowaniu
zestawów oszczędza mnóstwo czasu.

#### Wagi blokowe

Wtyczki typu *LoRA Block Weight* pozwalają zastosować LoRA tylko do wybranych bloków sieci.
To narzędzie na konkretny problem: gdy LoRA stylu psuje twarze, wyłączenie jej w blokach
odpowiadających za detal twarzy ratuje sytuację bez obniżania wagi całości.

---

### Kolejność ma znaczenie

Wbrew intuicji łączenie LoRA nie jest przemienne. Każda kolejna nakłada się na wagi już
zmodyfikowane przez poprzednią, więc **LoRA wpięta jako ostatnia ma zwykle silniejszy wpływ na
końcowy wygląd**. Przy zestawie postać + styl warto trzymać stałą kolejność: najpierw postać,
potem styl. Wtedy zmiana wagi stylu daje przewidywalny efekt, zamiast za każdym razem innego.

---

### Konflikt: postać kontra styl

Najczęstszy problem to LoRA postaci, która „gubi twarz" po dołożeniu LoRA stylu. Punkt wyjścia,
od którego warto zacząć strojenie:

| Rodzaj LoRA | strength_model | strength_clip |
| :--- | :--- | :--- |
| Postać | 0,75–0,85 | 0,90 |
| Styl | 0,50–0,65 | 0,40–0,50 |
| Przedmiot lub ubiór | 0,60–0,75 | 0,70 |
| Poza lub kompozycja | 0,40–0,60 | 0,30–0,50 |

Do tego dwie rzeczy w promptcie: słowo wyzwalające stylu na początku, słowo wyzwalające postaci
w części opisującej podmiot. Jeżeli obie LoRA mają to samo słowo wyzwalające — a zdarza się to
przy modelach z tego samego źródła — jedna z nich będzie systematycznie przegrywać. Wtedy trzeba
zmienić jedną z nich albo zaakceptować, że nie da się ich używać razem.

---

### Jak dobrać wagę w jednym przebiegu

Zamiast dwudziestu ręcznych prób użyj węzła **XY Plot** (z paczki *Efficiency Nodes*) albo
prostszego `LoraLoader` sterowanego z listy wartości. Ustaw jedną oś na `strength_model`
w zakresie 0,4–1,0 co 0,1 i wygeneruj siatkę. Otrzymasz siedem wariantów tego samego kadru
z tym samym ziarnem — różnicę widać od razu i nie trzeba niczego zapamiętywać.

Ta sama metoda działa do porównania samplerów, liczby kroków i wartości CFG. To najszybszy znany
sposób na przejście od zgadywania do wiedzy o konkretnym modelu.

---

### LoRA do Flux.1 to inna sprawa

Modele LoRA trenowane pod SD 1.5 albo SDXL **nie działają z Flux.1** — architektura jest inna.
Do Fluxa potrzebne są LoRA trenowane specjalnie pod niego, a węzeł ładujący bywa osobny
(`LoraLoaderModelOnly`), bo Flux nie ma pojedynczego złącza CLIP w tym samym sensie.
Wagi przy Fluxie działają zwykle łagodniej: 0,8–1,0 to typowy zakres, a przepalenie objawia się
raczej utratą detalu tła niż plastikową skórą.
""",
    },
    {
        "slug": "comfyui-flux-konfiguracja",
        "tytul": "Flux.1 w ComfyUI — konfiguracja Dev, Schnell, GGUF i FP8",
        "dzial": "comfyui",
        "poziom": "Zaawansowany",
        "tagi": ["Flux", "ComfyUI", "GGUF", "T5", "VRAM", "MMDiT"],
        "zajawka": "Jakie pliki pobrać, gdzie je położyć, jak spiąć węzły i dlaczego CFG "
                   "w KSamplerze musi wynosić dokładnie 1,0. Z porównaniem wariantów "
                   "skwantyzowanych pod konkretne ilości pamięci karty.",
        "tresc": """
### Co zmienia Flux.1

Flux.1 firmy Black Forest Labs ma architekturę **MMDiT** i około 12 miliardów parametrów. Lepiej radzi sobie ze złożonymi promptami, tekstem w obrazie i dłońmi niż wcześniejsze modele, choć nadal popełnia błędy.

Duży model i osobny enkoder tekstowy T5 wymagają odpowiedniej pamięci.

---

### Trzy warianty i po co są

1. **Flux.1 Schnell** (licencja Apache 2.0) — wersja destylowana, wymaga zaledwie **4 kroków**
   samplingu. Do szybkich szkiców i pracy komercyjnej bez ograniczeń licencyjnych.
2. **Flux.1 Dev** (licencja niekomercyjna) — najwyższa jakość, **20–28 kroków**, obsługuje
   LoRA i sterowanie parametrem guidance.
3. **Flux.1 Pro** — dostępny wyłącznie przez API producenta, nie do uruchomienia lokalnie.

---

### Warianty skwantyzowane pod pamięć karty

Pełny Dev w FP16 to ponad 23 GB — poza zasięgiem kart konsumenckich. Stąd wersje skwantyzowane:

| Wariant | Przybliżony rozmiar | Dla kart | Uwagi |
| :--- | :--- | :--- | :--- |
| FP16 | ~23 GB | 24 GB+ | Referencyjna jakość |
| FP8 (e4m3fn) | ~11 GB | 12–16 GB | Bardzo dobry kompromis, szybki |
| GGUF Q8 | ~12 GB | 12–16 GB | Jakość zbliżona do FP16 |
| GGUF Q5_K_M | ~8 GB | 8–12 GB | Rozsądny punkt dla 8 GB |
| GGUF Q4_K_S | ~6,5 GB | 6–8 GB | Widoczna utrata detalu |
| NF4 | ~6,5 GB | 6–8 GB | Szybki, gorzej trzyma tekst w obrazie |

Do wariantów GGUF potrzebna jest wtyczka **ComfyUI-GGUF** i węzeł `Unet Loader (GGUF)` zamiast
standardowego `UNETLoader`.

---

### Pliki i katalogi

- **Model:** `ComfyUI/models/unet/flux1-dev-fp8.safetensors` albo odpowiednik GGUF
- **Enkodery tekstu:** `ComfyUI/models/clip/`
  - `clip_l.safetensors` — klasyczny CLIP-L
  - `t5xxl_fp8_e4m3fn.safetensors` albo `t5xxl_fp16.safetensors`
- **VAE:** `ComfyUI/models/vae/ae.safetensors` — dedykowany, szesnastokanałowy

Uwaga na typowy błąd: model Flux **nie jest checkpointem** w rozumieniu SDXL. Nie ładuje się go
węzłem `Load Checkpoint`, tylko osobno — model, enkodery i VAE trzema różnymi węzłami.

---

### Schemat połączeń

1. **UNETLoader** (lub `Unet Loader (GGUF)`) — ładuje model.
2. **DualCLIPLoader** — ładuje `clip_l` jako pierwszy i `t5xxl` jako drugi, z typem `flux`.
3. **VAELoader** — ładuje `ae.safetensors`.
4. **CLIP Text Encode** dla promptu pozytywnego, a za nim węzeł **FluxGuidance**
   (wartość wyjściowa: **3,5**).
5. **KSampler** z ustawieniami:
   - Steps: **20–25** dla Dev, **4** dla Schnell
   - CFG: **1,0**
   - Sampler: **euler**
   - Scheduler: **simple** albo **sgm_uniform**
   - Denoise: **1,0**

---

### Dlaczego CFG musi wynosić 1,0

To pytanie wraca najczęściej. Flux.1 Dev jest modelem **destylowanym z prowadzeniem** — sterowanie,
które w SDXL realizuje classifier-free guidance, jest tu wbudowane w model i wystawione jako osobny
parametr `guidance` w węźle FluxGuidance.

Ustawienie CFG powyżej 1,0 w KSamplerze uruchamia klasyczny mechanizm guidance **na dodatek** do
wbudowanego. Efekt: obraz przepalony, kontrastowy i zniekształcony, a czas generacji dwukrotnie
dłuższy, bo model liczy dwa przebiegi zamiast jednego.

Z tego samego powodu **prompt negatywny w Fluxie Dev nie działa**. Węzeł można podpiąć, ale przy
CFG równym 1,0 jego zawartość nie ma wpływu na wynik. Zamiast wpisywać, czego nie chcesz, opisz
dokładniej to, czego chcesz.

---

### Gdy brakuje pamięci

Enkoder T5 potrafi zająć więcej niż sam model. Trzy sposoby, w kolejności od najmniej bolesnego:

- **T5 w FP8 zamiast FP16** — oszczędza kilka gigabajtów przy niewielkiej różnicy w jakości.
- **Przeniesienie enkodera na procesor** — parametr `device` w `DualCLIPLoader` ustawiony na `cpu`.
  Kodowanie promptu potrwa kilka sekund dłużej, ale dzieje się raz na prompt, a nie raz na krok.
- **Niższa kwantyzacja modelu** — zejście z Q8 na Q5_K_M zwykle daje różnicę widoczną dopiero
  przy porównaniu obok siebie.

---

### Typowe objawy i przyczyny

| Objaw | Najczęstsza przyczyna |
| :--- | :--- |
| Obraz przepalony, twarde kontury | CFG w KSamplerze różne od 1,0 |
| Szum zamiast obrazu | Podpięty VAE z SDXL zamiast `ae.safetensors` |
| Tekst w obrazie nieczytelny | Zbyt agresywna kwantyzacja (Q4, NF4) |
| Bardzo wolna generacja | T5 w FP16 przy karcie bez zapasu pamięci |
| Prompt negatywny bez efektu | Tak ma być — Dev go nie używa |
| Model się nie ładuje | Plik w `models/checkpoints` zamiast `models/unet` |
""",
    },
    {
        "slug": "comfyui-skroty-i-praktyki",
        "tytul": "ComfyUI szybciej — skróty klawiszowe i nawyki, które oszczędzają godziny",
        "tytul_seo": "Skróty klawiszowe i praktyki ComfyUI — Poradnik | F.W. DRUCIK",
        "dzial": "comfyui",
        "poziom": "Podstawowy",
        "tagi": ["ComfyUI", "Skróty", "Workflow", "Produktywność"],
        "zajawka": "Komplet skrótów, praca z szablonami i kolejką oraz kilka nawyków, "
                   "które odróżniają wygodną pracę od walki z plątaniną kabli.",
        "tresc": """
### Skróty, które warto znać na pamięć

| Skrót | Działanie |
| :--- | :--- |
| `Ctrl` + `Enter` | Dodaj bieżący graf do kolejki |
| `Ctrl` + `Shift` + `Enter` | Dodaj na początek kolejki |
| `Ctrl` + `S` | Zapisz workflow do pliku |
| `Ctrl` + `O` | Wczytaj workflow |
| `Ctrl` + `A` | Zaznacz wszystkie węzły |
| `Ctrl` + `M` | Wycisz węzeł (przestaje być liczony) |
| `Ctrl` + `B` | Bypass — węzeł przepuszcza dane dalej bez działania |
| `Delete` | Usuń zaznaczone węzły |
| `Ctrl` + `C` / `Ctrl` + `V` | Kopiuj i wklej węzły |
| `Ctrl` + `Shift` + `V` | Wklej z zachowaniem połączeń wejściowych |
| `Ctrl` + przeciągnięcie | Zaznaczenie prostokątem |
| `Shift` + przeciągnięcie | Przesuń kilka węzłów naraz |
| Dwuklik na pustym polu | Wyszukiwarka węzłów |
| `Alt` + `C` | Zwiń lub rozwiń węzeł |
| `.` (kropka) | Dopasuj widok do zaznaczenia |
| `Spacja` + ruch myszą | Przesuwanie płótna |

Przydatne skróty: **`Ctrl+B`** wyłącza węzeł do porównania wyniku, **`Ctrl+Shift+V`** kopiuje gałąź z połączeniami, a **dwuklik** otwiera wyszukiwanie.

---

### Wyszukiwarka węzłów zamiast menu

Dwuklik na pustym polu otwiera wyszukiwarkę. Wpisz `ksam` dla KSampler lub `vaed` dla VAE Decode; pełna nazwa nie jest potrzebna.

Jeszcze szybsza droga: **przeciągnij kabel z gniazda i puść na pustym polu**. ComfyUI pokaże
wyłącznie te węzły, które przyjmują ten typ danych. To zarazem podpowiedź, gdy nie wiadomo,
co dalej.

---

### Szablony zamiast budowania od zera

Workflow zapisany przez `Ctrl+S` to zwykły plik JSON. Warto trzymać kilka gotowych:

- podstawowy SDXL,
- Flux z GGUF,
- inpainting z maską,
- powiększanie dwuetapowe.

Do tego dochodzi funkcja **Save as Template** (menu po prawej), która zapisuje fragment grafu —
na przykład sam blok powiększania — do ponownego wstawienia w dowolnym miejscu.

I rzecz najmniej znana, a najwygodniejsza: **każdy PNG wygenerowany w ComfyUI zawiera cały
workflow w metadanych**. Przeciągnięcie obrazka na okno programu odtwarza konfigurację, która go
stworzyła. Archiwum obrazów jest jednocześnie archiwum ustawień.

---

### Kolejka jako narzędzie pracy

Pole `batch_count` przy przycisku kolejki mówi, ile razy wykonać ten sam graf. Ustawione na 10
z losowym ziarnem daje dziesięć wariantów bez dotykania klawiatury.

Sensowniejszy nawyk przy szukaniu kadru: wygeneruj serię z losowym ziarnem, wybierz najlepszy
obraz, odczytaj z niego ziarno (widać je w metadanych albo w węźle) i **przełącz ziarno na
`fixed`**. Od tego momentu zmiana promptu pokazuje wpływ samej zmiany, a nie loterię.

---

### Nawyki, które utrzymują graf w ryzach

- **Nazywaj węzły.** Prawy przycisk → Title. „Upscale ×2" mówi więcej niż „Upscale Image By"
  powtórzone trzy razy.
- **Grupuj etapy.** Blok generacji, blok powiększania, blok zapisu. Grupę można przesuwać
  i wyłączać w całości.
- **Używaj Reroute** do prowadzenia długich kabli. Graf z ośmioma kablami na skos jest nieczytelny
  po tygodniu przerwy.
- **Bypass zamiast usuwania.** Wyłączona LoRA albo ControlNet zostaje w grafie jako dokumentacja
  tego, co próbowałeś.
- **Zapisuj przed eksperymentem.** Rozbudowany graf łatwo zepsuć jedną zmianą, a cofnięcie nie
  zawsze obejmuje przepięcia.

---

### Menedżer węzłów

Wtyczka **ComfyUI-Manager** jest w praktyce obowiązkowa. Instaluje brakujące węzły jednym
kliknięciem, aktualizuje paczki i — co najważniejsze — po wczytaniu cudzego workflow wskazuje
dokładnie, których węzłów brakuje w Twojej instalacji. Bez niej ustawianie pobranego grafu bywa
godzinnym śledztwem.
""",
    },
]
