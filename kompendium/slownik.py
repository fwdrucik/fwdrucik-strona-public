# -*- coding: utf-8 -*-
"""Słownik pojęć.

Interfejs pierwotnej bazy obiecywał „65+ haseł", a haseł było 40. Lista poniżej
domyka tę obietnicę: zachowuje wszystkie pierwotne definicje i dokłada pojęcia,
bez których poprzedni zestaw się nie domykał — ziarno losowe, kroki, harmonogram
szumu, wagi w promptcie, szablon rozmowy, mieszanka ekspertów i pozostałe.
"""

SLOWNIK = [
    # ---------------------------------------------------------- modele i wagi
    {
        "termin": "Checkpoint (.safetensors)",
        "dzial": "Modele i wagi",
        "definicja": "Kompletny model generatywny zawierający wszystkie wagi: UNet albo DiT, "
                     "enkoder tekstu i VAE. Rozmiar od ok. 2 GB (SD 1.5) przez 6,5 GB (SDXL) "
                     "po 12–24 GB (Flux.1).",
    },
    {
        "termin": "Safetensors",
        "dzial": "Modele i wagi",
        "definicja": "Format wag bez mechanizmu wykonywania kodu przy odczycie, "
                     "w odróżnieniu od `.ckpt` opartego na pickle.",
    },
    {
        "termin": "LoRA (Low-Rank Adaptation)",
        "dzial": "Modele i wagi",
        "definicja": "Lekka nakładka na model bazowy, zwykle 10–300 MB, trenowana na małym "
                     "zbiorze w celu nauczenia sieci konkretnego stylu, postaci, ubioru albo "
                     "koncepcji — bez modyfikowania pliku modelu.",
    },
    {
        "termin": "Rank (LoRA)",
        "dzial": "Modele i wagi",
        "definicja": "Rozmiar macierzy LoRA, zwykle 8, 16, 32 lub 64. Wyższy rank "
                     "zwiększa pojemność i plik, ale też ryzyko przeuczenia na tle zamiast obiekcie.",
    },
    {
        "termin": "LyCORIS / LoCon / DoRA",
        "dzial": "Modele i wagi",
        "definicja": "Rozszerzone architektury treningu niskorzędowego. LoCon obejmuje także "
                     "warstwy splotowe, a DoRA rozdziela kierunek wektora wag od jego długości, "
                     "co daje wyższą wierność detalu.",
    },
    {
        "termin": "Textual Inversion (embedding)",
        "dzial": "Modele i wagi",
        "definicja": "Niewielki plik wektorowy definiujący jedno nowe słowo w przestrzeni "
                     "enkodera tekstu. Nie zmienia modelu — dokłada mu pojęcie.",
    },
    {
        "termin": "Trigger word",
        "dzial": "Modele i wagi",
        "definicja": "Słowo albo fraza, którą trzeba umieścić w promptcie, żeby LoRA "
                     "zadziałała. Ustala je osoba trenująca model; bez niego nakładka "
                     "wpływa na obraz słabo albo wcale.",
    },
    {
        "termin": "Fine-tuning (dostrajanie)",
        "dzial": "Modele i wagi",
        "definicja": "Dalsze trenowanie całego modelu na własnym zbiorze danych. W odróżnieniu "
                     "od LoRA zmienia wszystkie wagi, wymaga znacznie więcej pamięci i czasu, "
                     "a wynikiem jest pełnowymiarowy nowy model.",
    },
    {
        "termin": "Destylacja modelu",
        "dzial": "Modele i wagi",
        "definicja": "Trenowanie mniejszego lub szybszego modelu tak, by naśladował wyniki "
                     "większego. Stąd biorą się warianty generujące obraz w 4 krokach zamiast "
                     "w 30 — kosztem części różnorodności.",
    },
    {
        "termin": "MoE (Mixture of Experts)",
        "dzial": "Modele i wagi",
        "definicja": "Architektura, w której model składa się z wielu podsieci, a dla każdego "
                     "tokena aktywowana jest tylko część z nich. Daje jakość dużego modelu przy "
                     "koszcie obliczeniowym mniejszego — ale pamięć musi pomieścić całość.",
    },

    # ------------------------------------------------------ architektura sieci
    {
        "termin": "VAE (Variational AutoEncoder)",
        "dzial": "Architektura sieci",
        "definicja": "Sieć tłumacząca między przestrzenią pikseli a skompresowaną przestrzenią "
                     "ukrytą. Odpowiada za czystość barw i kontrast — niedopasowany VAE daje "
                     "obraz blady albo w dziwnych kolorach.",
    },
    {
        "termin": "Latent Space (przestrzeń ukryta)",
        "dzial": "Architektura sieci",
        "definicja": "Reprezentacja obrazu o ośmiokrotnie zmniejszonej rozdzielczości — obraz "
                     "1024×1024 to macierz 128×128 o 4 lub 16 kanałach. Cały kosztowny proces "
                     "odszumiania toczy się właśnie tam.",
    },
    {
        "termin": "UNet",
        "dzial": "Architektura sieci",
        "definicja": "Klasyczna architektura sieci odszumiającej w SD 1.5 i SDXL: ścieżka "
                     "zwężająca, wąskie gardło i ścieżka rozszerzająca, spięte połączeniami "
                     "pomijającymi. W nowszych modelach zastępowana przez DiT.",
    },
    {
        "termin": "DiT (Diffusion Transformer)",
        "dzial": "Architektura sieci",
        "definicja": "Architektura zastępująca UNet blokami transformera. Używana m.in. "
                     "w Flux.1 i SD3. Lepiej skaluje się z rozmiarem i wyraźnie lepiej rozumie "
                     "złożone opisy tekstowe.",
    },
    {
        "termin": "Attention (mechanizm uwagi)",
        "dzial": "Architektura sieci",
        "definicja": "Operacja, w której każdy element sekwencji waży, jak bardzo interesują go "
                     "pozostałe. W modelach obrazu wiąże słowa promptu z obszarami kadru; "
                     "to na niej opiera się większość technik sterowania generacją.",
    },

    # ----------------------------------------------------- enkodery tekstu
    {
        "termin": "CLIP",
        "dzial": "Enkodery tekstu",
        "definicja": "Model zamieniający prompt na wektory zrozumiałe dla sieci generującej. "
                     "Jego okno jest krótkie — 77 tokenów na fragment — dlatego bardzo długie "
                     "prompty w SD są dzielone i tracą część precyzji.",
    },
    {
        "termin": "CLIP-Vision",
        "dzial": "Enkodery tekstu",
        "definicja": "Odmiana CLIP przetwarzająca obraz zamiast tekstu. Na niej opiera się "
                     "IP-Adapter i wszystkie mechanizmy „promptu obrazkowego”.",
    },
    {
        "termin": "T5XXL",
        "dzial": "Enkodery tekstu",
        "definicja": "Duży enkoder językowy (część kodująca ma ok. 4,7 mld parametrów) używany "
                     "w Flux.1 i SD3. Odpowiada za rozumienie relacji przestrzennych i napisów, "
                     "ale potrafi zająć więcej pamięci niż sam model obrazu.",
    },
    {
        "termin": "Clip Skip",
        "dzial": "Enkodery tekstu",
        "definicja": "Określa, na której warstwie od końca zatrzymać przetwarzanie tekstu. "
                     "W modelach anime standardem jest 2, w fotorealistycznych SDXL — 1.",
    },
    {
        "termin": "Wagi w promptcie",
        "dzial": "Enkodery tekstu",
        "definicja": "Składnia podbijająca albo osłabiająca fragment opisu, w ComfyUI zapisywana "
                     "jako `(czerwony płaszcz:1.3)`. Wartości powyżej ok. 1,5 zwykle psują obraz "
                     "zamiast wzmacniać efekt.",
    },
    {
        "termin": "Positive / Negative Prompt",
        "dzial": "Enkodery tekstu",
        "definicja": "Dwa warunki generacji: pozytywny opisuje, co ma się pojawić, negatywny — "
                     "kierunek, od którego model ma się odsuwać. W modelach z CFG równym 1,0, "
                     "jak Flux.1 Dev, prompt negatywny nie działa.",
    },

    # ------------------------------------------------- parametry generacji
    {
        "termin": "CFG Scale",
        "dzial": "Parametry generacji",
        "definicja": "Jak ściśle model trzyma się promptu kosztem swobody. 3–5 daje efekt miękki, "
                     "7 to standard dla SD 1.5 i SDXL, powyżej 12 pojawia się przepalenie barw. "
                     "We Flux.1 zastąpione osobnym parametrem guidance.",
    },
    {
        "termin": "Guidance Scale (Flux)",
        "dzial": "Parametry generacji",
        "definicja": "Wbudowany w model odpowiednik CFG, sterowany osobnym węzłem. Wartość "
                     "wyjściowa 3,5; sensowny zakres 2,5–4,0. Klasyczne CFG musi wtedy "
                     "pozostać na 1,0.",
    },
    {
        "termin": "Steps (liczba kroków)",
        "dzial": "Parametry generacji",
        "definicja": "Ile razy sampler wykona odszumianie. Powyżej pewnej wartości obraz "
                     "przestaje się poprawiać — 20–30 dla SDXL, 4–8 dla modeli destylowanych. "
                     "Podnoszenie do 150 marnuje czas, nie dodaje jakości.",
    },
    {
        "termin": "Seed (ziarno losowe)",
        "dzial": "Parametry generacji",
        "definicja": "Liczba wyznaczająca początkowy szum. To samo ziarno przy tych samych "
                     "ustawieniach daje ten sam obraz — dlatego ustalenie ziarna jest warunkiem "
                     "sensownego porównywania zmian w promptcie.",
    },
    {
        "termin": "Denoising Strength",
        "dzial": "Parametry generacji",
        "definicja": "Ile szumu dodać do istniejącego obrazu przed ponownym odszumianiem. "
                     "1,0 to generacja od zera; 0,3–0,5 to typowy zakres przy powiększaniu, "
                     "gdy kompozycja ma zostać zachowana.",
    },
    {
        "termin": "Batch size i batch count",
        "dzial": "Parametry generacji",
        "definicja": "Batch size to liczba obrazów liczonych równolegle — szybciej, ale zużywa "
                     "wielokrotnie więcej pamięci. Batch count to liczba powtórzeń jeden po "
                     "drugim, bez dodatkowego kosztu pamięci.",
    },

    # --------------------------------------------- samplery i harmonogramy
    {
        "termin": "Sampler",
        "dzial": "Samplery i harmonogramy",
        "definicja": "Algorytm numeryczny rozwiązujący równanie procesu dyfuzji — krok po kroku "
                     "usuwa szum z przestrzeni ukrytej, odsłaniając obraz zgodny z promptem.",
    },
    {
        "termin": "Scheduler (harmonogram szumu)",
        "dzial": "Samplery i harmonogramy",
        "definicja": "Rozkład poziomów szumu między kolejnymi krokami. Sampler mówi „jak” "
                     "odszumiać, scheduler — „ile na każdym kroku”. Popularne: normal, karras, "
                     "exponential, simple, sgm_uniform.",
    },
    {
        "termin": "Karras",
        "dzial": "Samplery i harmonogramy",
        "definicja": "Harmonogram przesuwający większość kroków w obszar niskiego szumu, gdzie "
                     "powstaje detal. Zwykle daje ostrzejszy wynik przy tej samej liczbie kroków "
                     "niż harmonogram liniowy.",
    },
    {
        "termin": "Euler a (Euler Ancestral)",
        "dzial": "Samplery i harmonogramy",
        "definicja": "Sampler stochastyczny — dokłada świeży szum w każdym kroku. Daje miękkie, "
                     "malarskie kompozycje, ale wynik zmienia się nawet przy dużej liczbie "
                     "kroków, więc nie zbiega do jednego obrazu.",
    },
    {
        "termin": "DPM++ 2M Karras",
        "dzial": "Samplery i harmonogramy",
        "definicja": "Deterministyczny sampler drugiego rzędu z harmonogramem Karras. Uznawany "
                     "za punkt odniesienia dla fotorealizmu — pełną ostrość osiąga już przy "
                     "20–30 krokach.",
    },
    {
        "termin": "UniPC",
        "dzial": "Samplery i harmonogramy",
        "definicja": "Szybki sampler typu predyktor-korektor. Potrafi dać poprawny obraz "
                     "w 12–15 krokach, co czyni go dobrym wyborem do szybkiego szukania kadru.",
    },
    {
        "termin": "LCM (Latent Consistency Model)",
        "dzial": "Samplery i harmonogramy",
        "definicja": "Technika destylacji pozwalająca wygenerować pełny obraz w 4–8 krokach, "
                     "praktycznie w czasie rzeczywistym. Kosztem jest mniejsza różnorodność "
                     "i słabszy detal.",
    },

    # ----------------------------------------------------- kontrola i edycja
    {
        "termin": "ControlNet",
        "dzial": "Kontrola i edycja",
        "definicja": "Sieć pomocnicza narzucająca układ przestrzenny generacji na podstawie "
                     "mapy krawędzi, mapy głębi, pozy szkieletu albo segmentacji. Najpewniejszy "
                     "sposób na powtórzenie konkretnej kompozycji.",
    },
    {
        "termin": "IP-Adapter",
        "dzial": "Kontrola i edycja",
        "definicja": "Mechanizm używający obrazu jako promptu. W odróżnieniu od ControlNetu "
                     "przenosi cechy semantyczne — twarz, styl ubioru, kolorystykę — a nie "
                     "geometrię kadru.",
    },
    {
        "termin": "Inpainting",
        "dzial": "Kontrola i edycja",
        "definicja": "Przerysowanie zaznaczonego maską fragmentu obrazu z zachowaniem spójności "
                     "z otoczeniem. Zaznaczenie nieco większego obszaru niż sam problem zwykle "
                     "daje lepszy wynik niż maska dokładnie po krawędzi.",
    },
    {
        "termin": "Outpainting",
        "dzial": "Kontrola i edycja",
        "definicja": "Rozszerzenie kadru poza pierwotne granice z domalowaniem otoczenia — "
                     "na przykład zamiana zdjęcia pionowego na panoramiczne.",
    },
    {
        "termin": "img2img",
        "dzial": "Kontrola i edycja",
        "definicja": "Generacja rozpoczynana od istniejącego obrazu zamiast czystego szumu. "
                     "Siłę przekształcenia ustala parametr denoise — to nim decyduje się, "
                     "ile z oryginału ma zostać.",
    },
    {
        "termin": "Regional prompting",
        "dzial": "Kontrola i edycja",
        "definicja": "Przypisanie różnych fragmentów promptu do różnych obszarów kadru. "
                     "Rozwiązuje typowy problem mieszania się cech, gdy w scenie ma być "
                     "kilka różnych postaci albo obiektów.",
    },

    # ------------------------------------------------- powiększanie i jakość
    {
        "termin": "Hires Fix",
        "dzial": "Powiększanie i jakość",
        "definicja": "Dwuetapowa generacja: obraz powstaje w rozdzielczości natywnej modelu, "
                     "zostaje powiększony i przechodzi drugie odszumianie o mocy 0,35–0,55. "
                     "Standardowy sposób na duży obraz bez zdublowanych elementów.",
    },
    {
        "termin": "Upscaler",
        "dzial": "Powiększanie i jakość",
        "definicja": "Model powiększający obraz. Powiększanie w przestrzeni ukrytej jest szybsze "
                     "i lepiej łączy się z kolejnym samplingiem; powiększanie pikselowe "
                     "(np. ESRGAN) daje ostrzejsze krawędzie, ale nie dorysuje brakującego detalu.",
    },
    {
        "termin": "Tiled VAE / Tiled Diffusion",
        "dzial": "Powiększanie i jakość",
        "definicja": "Przetwarzanie obrazu kafelkami zamiast w całości. Pozwala wygenerować "
                     "albo zdekodować obraz, który nie zmieściłby się w pamięci karty — wolniej, "
                     "za to bez błędu braku pamięci.",
    },
    {
        "termin": "Refiner (SDXL)",
        "dzial": "Powiększanie i jakość",
        "definicja": "Drugi model SDXL przejmujący ostatnie kilkanaście procent kroków i "
                     "dopracowujący detal. Przy dobrych modelach społecznościowych coraz częściej "
                     "pomijany — bywa, że pogarsza wynik zamiast go poprawiać.",
    },
    {
        "termin": "FreeU",
        "dzial": "Powiększanie i jakość",
        "definicja": "Przeważenie wag między ścieżką główną a połączeniami pomijającymi. "
                     "Wzmacnia strukturę i usuwa charakterystyczną mgłę modeli SDXL bez "
                     "dodatkowego kosztu obliczeniowego.",
    },
    {
        "termin": "Kohya DeepShrink",
        "dzial": "Powiększanie i jakość",
        "definicja": "Tymczasowe zawężenie bloków uwagi w pierwszych krokach generacji "
                     "w wysokiej rozdzielczości. Zapobiega klonowaniu postaci i podwójnym "
                     "głowom przy obrazach większych niż rozdzielczość natywna modelu.",
    },
    {
        "termin": "Self-Attention Guidance (SAG)",
        "dzial": "Powiększanie i jakość",
        "definicja": "Wykorzystuje wewnętrzne mapy uwagi do wykrycia obszarów rozmytych "
                     "i skierowania tam większej uwagi przy odszumianiu. Największą różnicę "
                     "widać na oczach, rzęsach i drobnych napisach.",
    },
    {
        "termin": "StyleAlign",
        "dzial": "Powiększanie i jakość",
        "definicja": "Współdzielenie map samouwagi w obrębie jednej partii obrazów. Cała seria "
                     "wychodzi wtedy w tej samej palecie i z tym samym charakterem światła.",
    },

    # ------------------------------------------------------ modele językowe
    {
        "termin": "Token i tokenizer",
        "dzial": "Modele językowe",
        "definicja": "Podstawowa jednostka tekstu. W angielskim jeden token to średnio ok. 4 "
                     "znaki; w polskim, przez znaki diakrytyczne i odmianę, jedno słowo potrafi "
                     "zająć 2–3 tokeny. Ma to wpływ na koszt i na okno kontekstu.",
    },
    {
        "termin": "Context Window (okno kontekstu)",
        "dzial": "Modele językowe",
        "definicja": "Maksymalna liczba tokenów, jaką model utrzymuje naraz: prompt, historia "
                     "rozmowy i generowana odpowiedź. Po jego przekroczeniu początek rozmowy "
                     "wypada z pamięci.",
    },
    {
        "termin": "KV Cache",
        "dzial": "Modele językowe",
        "definicja": "Bufor przechowujący wektory Key i Value dla dotychczasowych tokenów. "
                     "Pozwala generować kolejne słowa bez przeliczania całej historii, ale "
                     "rośnie liniowo z długością kontekstu i zjada pamięć karty.",
    },
    {
        "termin": "Kwantyzacja (GGUF, AWQ, EXL2)",
        "dzial": "Modele językowe",
        "definicja": "Zapis wag z mniejszą precyzją — na przykład 4 bity zamiast 16. Zmniejsza "
                     "model o 60–75% przy niewielkiej stracie jakości. Q4_K_M jest zwykle "
                     "najlepszym kompromisem.",
    },
    {
        "termin": "GGUF",
        "dzial": "Modele językowe",
        "definicja": "Format pliku modelu używany przez llama.cpp i oparte na nim programy. "
                     "Jeden plik zawiera wagi, tokenizer i metadane, w tym szablon rozmowy.",
    },
    {
        "termin": "Model instruowany a bazowy",
        "dzial": "Modele językowe",
        "definicja": "Model bazowy jedynie kontynuuje tekst. Model instruowany (z dopiskiem "
                     "Instruct albo Chat) przeszedł dodatkowe trenowanie na parach polecenie–"
                     "odpowiedź i dopiero on nadaje się do rozmowy.",
    },
    {
        "termin": "Szablon rozmowy (chat template)",
        "dzial": "Modele językowe",
        "definicja": "Format znaczników oddzielających role w rozmowie: ChatML, Llama 3, Mistral. "
                     "Niedopasowany szablon objawia się tym, że model nie przestaje pisać "
                     "i dokleja wymyślone kolejne tury.",
    },
    {
        "termin": "Halucynacja",
        "dzial": "Modele językowe",
        "definicja": "Odpowiedź brzmiąca wiarygodnie, ale nieprawdziwa. Model nie odróżnia "
                     "wiedzy od prawdopodobnego brzmienia — dlatego przy faktach sprawdzalnych "
                     "zawsze potrzebne jest źródło albo weryfikacja.",
    },
    {
        "termin": "GPU Offload (n_gpu_layers)",
        "dzial": "Modele językowe",
        "definicja": "Liczba warstw modelu przeniesionych do pamięci karty. Model w całości "
                     "na karcie działa wielokrotnie szybciej niż ten sam model z kilkoma "
                     "warstwami po stronie procesora.",
    },
    {
        "termin": "FlashAttention",
        "dzial": "Modele językowe",
        "definicja": "Zoptymalizowany pod pamięć podręczną GPU sposób liczenia mechanizmu uwagi. "
                     "Zmniejsza zużycie pamięci i przyspiesza pracę — najbardziej przy długim "
                     "kontekście, gdzie uwaga jest głównym kosztem.",
    },
    {
        "termin": "Speculative decoding",
        "dzial": "Modele językowe",
        "definicja": "Mały model proponuje kilka kolejnych tokenów, duży weryfikuje je jednym "
                     "przebiegiem. Gdy propozycje trafiają, generowanie przyspiesza bez zmiany "
                     "jakości wyniku.",
    },
    {
        "termin": "VRAM Offloading",
        "dzial": "Modele językowe",
        "definicja": "Dynamiczne przenoszenie nieużywanych w danej chwili warstw z pamięci karty "
                     "do pamięci operacyjnej i z powrotem. Na tym opiera się działanie dużych "
                     "modeli obrazu na kartach 6–8 GB.",
    },

    # --------------------------------------------------------- parametry LLM
    {
        "termin": "Temperature",
        "dzial": "Parametry samplingu",
        "definicja": "Skaluje różnice między prawdopodobieństwami tokenów. 0,1 to ścisła "
                     "powtarzalność, 0,7 styl konwersacyjny, powyżej 1,2 wysoka kreatywność "
                     "i rosnące ryzyko bzdur.",
    },
    {
        "termin": "Top-P (nucleus sampling)",
        "dzial": "Parametry samplingu",
        "definicja": "Ogranicza wybór do najmniejszego zbioru tokenów, których skumulowane "
                     "prawdopodobieństwo przekracza próg P. Wartość 1,0 wyłącza filtr.",
    },
    {
        "termin": "Top-K",
        "dzial": "Parametry samplingu",
        "definicja": "Zostawia K najlepszych tokenów niezależnie od ich prawdopodobieństw. "
                     "Najprostszy i najmniej elastyczny z filtrów — zwykle zostawia się go "
                     "wyłączonego albo na dużej wartości jako zabezpieczenie.",
    },
    {
        "termin": "Min-P",
        "dzial": "Parametry samplingu",
        "definicja": "Odcina tokeny słabsze niż zadany ułamek prawdopodobieństwa najlepszego "
                     "tokena. Dostosowuje się do pewności modelu, przez co jest stabilniejszy "
                     "od Top-P. Obu naraz się nie używa.",
    },
    {
        "termin": "Repetition penalty",
        "dzial": "Parametry samplingu",
        "definicja": "Obniża prawdopodobieństwo słów, które już wystąpiły. Zakres praktyczny "
                     "1,05–1,15; powyżej 1,25 psuje kod, bo model unika powtórzenia nazwy "
                     "zmiennej.",
    },
    {
        "termin": "Frequency i presence penalty",
        "dzial": "Parametry samplingu",
        "definicja": "Frequency penalty rośnie z liczbą wystąpień tokena, presence penalty jest "
                     "stała od pierwszego wystąpienia. Ta druga lepiej wymusza różnorodność "
                     "tematów bez psucia składni.",
    },
    {
        "termin": "Stop sequence",
        "dzial": "Parametry samplingu",
        "definicja": "Ciąg znaków, po którego wygenerowaniu model kończy odpowiedź. Ratuje "
                     "sytuacje, w których model dokleja kolejne tury rozmowy mimo poprawnego "
                     "szablonu.",
    },

    # ------------------------------------------------ prompt engineering
    {
        "termin": "System prompt",
        "dzial": "Prompt engineering",
        "definicja": "Instrukcja nadrzędna definiująca rolę, ton, format odpowiedzi i "
                     "ograniczenia asystenta, obowiązująca przez całą rozmowę.",
    },
    {
        "termin": "Few-shot prompting",
        "dzial": "Prompt engineering",
        "definicja": "Podanie w promptcie dwóch–czterech przykładów w formie wejście → "
                     "oczekiwane wyjście przed właściwym pytaniem. Wyraźnie podnosi poprawność "
                     "przy zadaniach o ustalonym formacie.",
    },
    {
        "termin": "Chain of Thought",
        "dzial": "Prompt engineering",
        "definicja": "Poproszenie modelu o wypisanie toku rozumowania przed odpowiedzią. "
                     "Pomaga przy matematyce, kodzie i analizie logicznej; przy prostych "
                     "pytaniach tylko wydłuża wynik.",
    },

    # -------------------------------------------------- agenci i architektury
    {
        "termin": "RAG (Retrieval-Augmented Generation)",
        "dzial": "Agenci i architektury",
        "definicja": "Model najpierw wyszukuje fragmenty własnych dokumentów, potem odpowiada "
                     "na ich podstawie. Sposób na wiedzę firmową bez trenowania modelu.",
    },
    {
        "termin": "Osadzenie wektorowe (embedding)",
        "dzial": "Agenci i architektury",
        "definicja": "Reprezentacja fragmentu tekstu jako wektora liczb, w której bliskość "
                     "oznacza podobieństwo znaczeniowe. Podstawa wyszukiwania semantycznego "
                     "i pamięci długoterminowej agentów.",
    },
    {
        "termin": "Baza wektorowa",
        "dzial": "Agenci i architektury",
        "definicja": "Magazyn osadzeń z szybkim wyszukiwaniem najbliższych sąsiadów. Do kilkuset "
                     "tysięcy fragmentów wystarczają rozwiązania plikowe działające lokalnie.",
    },
    {
        "termin": "Tool calling / function calling",
        "dzial": "Agenci i architektury",
        "definicja": "Zdolność modelu do rozpoznania, że potrzebne jest zewnętrzne narzędzie, "
                     "i wygenerowania ustrukturyzowanego wywołania. Model proponuje — wykonuje "
                     "zawsze program.",
    },
    {
        "termin": "ReAct (Reasoning + Acting)",
        "dzial": "Agenci i architektury",
        "definicja": "Wzorzec pracy agenta: myśl, działanie, obserwacja, ocena — w pętli aż do "
                     "osiągnięcia celu albo wyczerpania limitu kroków.",
    },
    {
        "termin": "Model Context Protocol (MCP)",
        "dzial": "Agenci i architektury",
        "definicja": "Otwarty standard połączeń między aplikacjami AI a narzędziami, plikami "
                     "i bazami. Jeden serwer napisany raz działa z każdym klientem obsługującym "
                     "protokół.",
    },
    {
        "termin": "Wstrzykiwanie poleceń (prompt injection)",
        "dzial": "Agenci i architektury",
        "definicja": "Atak polegający na umieszczeniu instrukcji w treści, którą model czyta jako "
                     "dane — na stronie, w dokumencie, w wiadomości. Obrona polega na traktowaniu "
                     "wszystkiego spoza rozmowy jako danych, nigdy jako poleceń.",
    },
]
