# -*- coding: utf-8 -*-
"""Dział Fooocus i SD WebUI Forge — generowanie obrazów na sprzęcie konsumenckim."""

ARTYKULY = [
    {
        "slug": "fooocus-przewodnik",
        "tytul": "Fooocus — jakość SDXL bez konfigurowania czegokolwiek",
        "dzial": "obrazy",
        "poziom": "Podstawowy",
        "tagi": ["Fooocus", "SDXL", "Inpaint", "FaceSwap", "Style"],
        "zajawka": "Tryby wydajności, cztery tryby Image Prompt i inpainting, który nie "
                   "zostawia szwów. Program dla osób, które chcą obrazu, a nie budowania grafu.",
        "tresc": """
### Dla kogo jest Fooocus

Fooocus autorstwa **lllyasviel**, twórcy ControlNet i Forge, upraszcza obsługę SDXL do pola tekstowego. Automatycznie dobiera prompt negatywny, wagi stylu i sampler.

Fooocus ułatwia generowanie bez nauki grafu, ale daje mniej kontroli nad nietypowymi procesami niż ComfyUI.

Wymagania są łagodne — działa na kartach od 4 GB pamięci, bo sam zarządza przenoszeniem wag
między kartą a pamięcią operacyjną.

---

### Trzy tryby wydajności

1. **Quality** — 60 kroków, pełny model bazowy plus automatyczny refiner. Najostrzejszy detal,
   najdłuższy czas.
2. **Speed** — 30 kroków. Codzienny tryb pracy, wynik gotowy w kilkanaście sekund.
3. **Extreme Speed** — model destylowany (LCM albo SDXL Lightning), **4–8 kroków**, obraz
   w 2–4 sekundy. Do szukania kompozycji, nie do finalnego renderu.

Praktyczny nawyk: szukaj kadru w trybie Extreme Speed, a gdy prompt już działa, przełącz na
Quality z tym samym ziarnem.

---

### Image Prompt i jego cztery tryby

Po zaznaczeniu **Input Image → Image Prompt** dochodzą cztery różne sposoby wykorzystania zdjęcia
referencyjnego:

| Tryb | Co przenosi ze zdjęcia | Typowe użycie |
| :--- | :--- | :--- |
| **ImagePrompt** | Klimat, paletę barw, ogólną kompozycję | Utrzymanie stylu serii obrazów |
| **FaceSwap** | Geometrię twarzy | Ta sama osoba w różnych scenach |
| **PyraCanny** | Krawędzie i kontury | Zachowanie kształtu mebla, pojazdu, budynku |
| **CPDS** | Głębię i układ przestrzenny | Zmiana tekstur i światła przy tej samej scenie |

Suwak **Stop At** decyduje, do którego momentu generacji obowiązuje referencja — niższa wartość
daje luźniejsze nawiązanie. **Weight** ustala siłę wpływu. Przy FaceSwap warto zacząć od wartości
domyślnych i schodzić w dół, jeśli twarz „przykleja się" zbyt dosłownie razem z oświetleniem
ze zdjęcia źródłowego.

Można używać kilku obrazów referencyjnych naraz, w różnych trybach — na przykład PyraCanny na
kształt i ImagePrompt na kolorystykę.

---

### Inpainting bez szwów

Fooocus ma własny silnik inpaintingu, który rozwiązuje najbardziej dokuczliwy problem tej techniki:
widoczną granicę między obszarem oryginalnym a domalowanym.

Trzy tryby:

- **Improve Detail** — zaznaczasz obszar i nie piszesz nic. Program podnosi rozdzielczość fragmentu
  i poprawia anatomię. Podstawowe narzędzie do dłoni i twarzy.
- **Modify Content** — zaznaczasz i opisujesz, co ma się tam pojawić.
- **Outpaint** — rozszerza kadr w wybranym kierunku, dorysowując otoczenie.

Przy inpaintingu obowiązuje zasada odwrotna do intuicji: **zaznacz nieco więcej niż sam problem**.
Maska obejmująca tylko zniekształcony palec daje modelowi za mało kontekstu; maska obejmująca całą
dłoń z nadgarstkiem daje dobry wynik.

---

### Style zamiast długich promptów

Zakładka **Style** to ponad sto gotowych zestawów modyfikatorów. Włączenie „Fooocus Photograph"
albo „SAI Cinematic" dokłada do promptu sprawdzoną formułkę, której nie trzeba pisać ręcznie.

Ostrzeżenie z praktyki: **włączenie pięciu stylów naraz zwykle daje gorszy wynik niż jednego**.
Style nakładają się i zaczynają walczyć o ten sam obszar opisu. Dwa, wyjątkowo trzy.

---

### Tryb Developer Debug Mode

Zaznaczenie pola **Developer Debug Mode** odsłania parametry, które normalnie są ukryte:

- **Guidance Scale (CFG)** — domyślnie dynamiczne w zakresie 4,0–7,0. Zejście do 3,0 daje miękki,
  filmowy obraz; podniesienie do 8,0 wzmacnia nasycenie i kontrast, kosztem naturalności.
- **Positive ADM Guidance** — waga estetyczna. Wartości 1,2–1,8 wyraźnie poprawiają realizm skóry
  i światła.
- **FreeU** — wzmocnienie struktur przy jednoczesnym tłumieniu szumu. Punkt wyjścia:
  `b1: 1,01`, `b2: 1,02`, `s1: 0,99`, `s2: 0,95`. Usuwa charakterystyczną „mgłę" i mdłe kolory
  modeli bazowych SDXL.
- **Sampler i scheduler** — do ręcznego wyboru, gdy domyślny `dpmpp_2m_sde_gpu` z `karras`
  nie daje oczekiwanego charakteru.
- **Seed** — do powtórzenia dokładnie tego samego kadru.

Debug Mode wyświetla też podgląd kroków pośrednich, co bardzo pomaga przy diagnozowaniu,
w którym momencie kompozycja się psuje.
""",
    },
    {
        "slug": "sd-webui-forge",
        "tytul": "SD WebUI Forge — Flux i SDXL na karcie 6–8 GB",
        "dzial": "obrazy",
        "poziom": "Średniozaawansowany",
        "tagi": ["Forge", "Flux", "VRAM", "Automatic1111", "NF4"],
        "zajawka": "Przebudowany silnik pamięci, który pozwala uruchomić modele wcześniej "
                   "zarezerwowane dla kart 16 GB. Z konfiguracją Flux.1 krok po kroku "
                   "i porównaniem do klasycznego Automatic1111.",
        "tresc": """
### Skąd wziął się Forge

Forge to przebudowa Automatic1111 autorstwa **lllyasviel**. **Przenosi warstwy między GPU a RAM podczas generowania**, zamiast trzymać cały model na karcie.

Pozwala uruchamiać modele przekraczające VRAM. Sprawniejsze zarządzanie transferem może też skrócić generowanie.

---

### Porównanie z klasycznym Automatic1111

| Cecha | Automatic1111 | Forge |
| :--- | :--- | :--- |
| Zarządzanie pamięcią | Częste `CUDA out of memory` | Przenoszenie warstw bez przerywania pracy |
| Szybkość SDXL | Odniesienie | Zwykle o 30–75% szybciej |
| Obsługa Flux.1 | Brak albo bardzo wolno | Natywna: NF4, FP8, GGUF |
| Narzędzia wbudowane | Przez rozszerzenia | ControlNet, FreeU, DeepShrink, StyleAlign w zestawie |
| Minimalna pamięć dla SDXL | 8–12 GB | Od 4–6 GB |

Interfejs pozostaje ten sam, więc przesiadka nie wymaga uczenia się niczego od nowa. Rozszerzenia
pisane pod Automatic1111 w większości działają, choć nie wszystkie.

---

### Flux.1 w Forge krok po kroku

1. Pobierz model w wariancie zoptymalizowanym: `flux1-dev-bnb-nf4.safetensors` albo plik GGUF.
2. Umieść go w katalogu `webui/models/Stable-diffusion/`.
3. Wybierz model z listy w lewym górnym rogu. Forge sam rozpozna, że to Flux, i przełączy tryb.
4. Ustaw parametry generacji:
   - **Sampling steps:** 20
   - **Sampler:** Euler
   - **Schedule type:** Simple
   - **CFG Scale:** 1,0
   - **Distilled CFG Scale:** 3,5
   - **Rozdzielczość:** 1024×1024 albo 896×1152
5. Enkodery T5 i CLIP Forge obsługuje w tle — nie trzeba konfigurować ścieżek jak w ComfyUI.

Rozróżnienie dwóch pól CFG jest tu kluczowe. **CFG Scale** to klasyczne guidance i przy Fluxie
musi zostać na 1,0. **Distilled CFG Scale** to parametr wbudowany w model — nim się steruje siłą
trzymania się promptu, a sensowny zakres to 2,5–4,0.

---

### Tryby pamięci

W ustawieniach jest przełącznik strategii:

- **Never OOM** — najbezpieczniejszy, przenosi agresywnie, wolniejszy.
- **Shared** — kompromis, dobry punkt wyjścia.
- **Full VRAM** — wszystko na karcie, najszybszy, tylko przy dużym zapasie pamięci.

Do tego suwak określający, ile pamięci karty zostawić dla innych aplikacji. Przy 8 GB warto
zostawić około 1 GB, jeśli w tle pracuje przeglądarka.

---

### Wbudowane moduły

#### Kohya DeepShrink

Rozwiązuje problem generowania od razu w wysokiej rozdzielczości. Model SDXL proszony
o 1536×1536 zwykle rysuje dwie głowy albo zdublowany horyzont, bo nie zna kompozycji w tej skali.

DeepShrink przez pierwsze kilkanaście procent kroków **kompresuje wewnętrzne bloki uwagi**,
zmuszając sieć do ustalenia globalnej kompozycji tak, jakby obraz był mały. Potem wraca do pełnej
rozdzielczości i dorysowuje detal. Efekt: duży obraz w jednym przebiegu, bez etapu powiększania.

#### StyleAlign

Współdzieli mapy samouwagi w obrębie jednej partii obrazów. Generując cztery obrazy naraz,
otrzymujesz je w tej samej palecie, z tym samym charakterem światła i podobnym typem postaci.
Nieocenione przy przygotowywaniu spójnej serii.

#### Self-Attention Guidance (SAG)

Wykorzystuje wewnętrzne mapy uwagi do wykrycia obszarów rozmytych lub zniekształconych i kieruje
tam więcej „uwagi" podczas odszumiania. Największą różnicę widać na oczach, rzęsach, biżuterii
i drobnych napisach.

#### FreeU

Przeważa wagi między ścieżką główną a połączeniami pomijającymi w sieci. Wzmacnia strukturę
i tłumi szum wysokoczęstotliwościowy. Wartości wyjściowe takie jak w Fooocus: `b1: 1,01`,
`b2: 1,02`, `s1: 0,99`, `s2: 0,95`.

---

### Kiedy Forge, a kiedy ComfyUI

Forge wygrywa, gdy potrzebna jest szybka praca w znanym interfejsie, generowanie seriami
i dostęp do modułów bez konfigurowania. ComfyUI wygrywa, gdy rurociąg ma wyglądać inaczej niż
przewidział autor programu: wieloetapowe powiększanie, warunkowe gałęzie, własne łączenie modeli,
przetwarzanie wsadowe według reguł.

W praktyce wiele osób trzyma oba: Forge do codziennej pracy, ComfyUI do rzeczy nietypowych.
Modele i LoRA można współdzielić przez dowiązania symboliczne albo wpis w pliku konfiguracyjnym,
żeby nie trzymać dwóch kopii tych samych kilkunastu gigabajtów.
""",
    },
]
