# -*- coding: utf-8 -*-
"""Zasoby kompendium: schematy workflow, dobór sprzętu i szablony promptów.

Zawartość przeniesiona z lokalnej bazy wiedzy i uzupełniona. Twierdzenia
w rodzaju „poziom zbliżony do GPT-4o na Twoim biurku” zostały sprowadzone
do tego, co da się obronić — model 32B w kwantyzacji 4-bitowej jest bardzo
dobry, ale porównanie z czołowymi modelami komercyjnymi nie broni się
w zadaniach wymagających szerokiej wiedzy.
"""

# --------------------------------------------------------------- workflowy

WORKFLOWY = [
    {
        "slug": "sdxl-podstawowy",
        "tytul": "Podstawowy workflow SDXL 1024×1024",
        "poziom": "Podstawowy",
        "vram": "6–8 GB",
        "opis": "Podstawowy schemat ComfyUI: rozmiar obrazu i ustawienia KSamplera. "
                "Punkt wyjścia do dalszych zmian.",
        "wezly": [
            ("Load Checkpoint", "Wczytanie modelu", "wyjścia: MODEL, CLIP, VAE"),
            ("Empty Latent Image", "Latent", "1024×1024, batch 1"),
            ("CLIP Text Encode (pozytywny)", "Warunek", "opis sceny"),
            ("CLIP Text Encode (negatywny)", "Warunek", "czego unikać"),
            ("KSampler", "Sampling", "steps 25, cfg 6.5, dpmpp_2m, karras, denoise 1.0"),
            ("VAE Decode → Save Image", "Wyjście", "zapis PNG z metadanymi grafu"),
        ],
        "polaczenia": [
            "Load Checkpoint [MODEL] → KSampler [model]",
            "Load Checkpoint [CLIP] → oba węzły CLIP Text Encode [clip]",
            "CLIP Text Encode pozytywny [CONDITIONING] → KSampler [positive]",
            "CLIP Text Encode negatywny [CONDITIONING] → KSampler [negative]",
            "Empty Latent Image [LATENT] → KSampler [latent_image]",
            "KSampler [LATENT] → VAE Decode [samples]",
            "Load Checkpoint [VAE] → VAE Decode [vae]",
            "VAE Decode [IMAGE] → Save Image [images]",
        ],
    },
    {
        "slug": "flux-dev",
        "tytul": "Flux.1 Dev — GGUF lub FP8 z podwójnym enkoderem",
        "poziom": "Zaawansowany",
        "vram": "8–16 GB",
        "opis": "Zalecana architektura dla Flux.1: podwójny enkoder tekstu (CLIP-L do prostych "
                "haseł, T5XXL do długich opisów), węzeł FluxGuidance i dedykowany "
                "szesnastokanałowy VAE. Model ładuje się osobno, nie jako checkpoint.",
        "wezly": [
            ("Unet Loader (GGUF) lub UNETLoader", "Wczytanie modelu", "flux1-dev-fp8 albo plik GGUF"),
            ("DualCLIPLoader", "Enkodery", "clip_l + t5xxl_fp8, typ: flux"),
            ("VAELoader", "VAE", "ae.safetensors"),
            ("CLIP Text Encode", "Warunek", "opis w zdaniach, nie w hasłach"),
            ("FluxGuidance", "Prowadzenie", "guidance 3.5"),
            ("Empty Latent Image", "Latent", "1024×1024"),
            ("KSampler", "Sampling", "steps 20, cfg 1.0, euler, simple"),
            ("VAE Decode → Save Image", "Wyjście", ""),
        ],
        "polaczenia": [
            "Unet Loader [MODEL] → KSampler [model]",
            "DualCLIPLoader [CLIP] → CLIP Text Encode [clip]",
            "CLIP Text Encode [CONDITIONING] → FluxGuidance [conditioning]",
            "FluxGuidance [CONDITIONING] → KSampler [positive]",
            "Empty Latent Image [LATENT] → KSampler [latent_image]",
            "KSampler [LATENT] → VAE Decode [samples]",
            "VAELoader [VAE] → VAE Decode [vae]",
        ],
        "uwaga": "CFG w KSamplerze musi wynosić dokładnie 1,0. Prompt negatywny przy tej "
                 "wartości nie działa — to zachowanie modelu, nie błąd konfiguracji.",
    },
    {
        "slug": "lora-stacking",
        "tytul": "Łączenie LoRA postaci i stylu z ochroną twarzy",
        "poziom": "Średniozaawansowany",
        "vram": "8 GB",
        "opis": "Połączenie co najmniej dwóch LoRA. Osobne wagi modelu i enkodera "
                "pomagają ograniczyć wpływ LoRA stylu na twarz.",
        "wezly": [
            ("Load Checkpoint", "Wczytanie modelu", ""),
            ("Load LoRA (postać)", "LoRA", "strength_model 0.80, strength_clip 0.90"),
            ("Load LoRA (styl)", "LoRA", "strength_model 0.55, strength_clip 0.40"),
            ("CLIP Text Encode (pozytywny)", "Warunek", "trigger stylu na początku"),
            ("CLIP Text Encode (negatywny)", "Warunek", ""),
            ("Empty Latent Image", "Latent", ""),
            ("KSampler", "Sampling", ""),
            ("VAE Decode → Save Image", "Wyjście", ""),
        ],
        "polaczenia": [
            "Checkpoint [MODEL] → LoRA postać [model]",
            "Checkpoint [CLIP] → LoRA postać [clip]",
            "LoRA postać [MODEL] → LoRA styl [model]",
            "LoRA postać [CLIP] → LoRA styl [clip]",
            "LoRA styl [MODEL] → KSampler [model]",
            "LoRA styl [CLIP] → oba węzły CLIP Text Encode [clip]",
        ],
        "uwaga": "Kolejność nie jest przemienna — LoRA wpięta jako ostatnia wpływa na wynik "
                 "najsilniej. Trzymaj stałą kolejność: najpierw postać, potem styl.",
    },
    {
        "slug": "hires-i-upscale",
        "tytul": "Dwuetapowe powiększanie do 4K z kafelkowaniem",
        "poziom": "Zaawansowany",
        "vram": "8–12 GB",
        "opis": "Obraz powstaje w rozdzielczości natywnej, zostaje powiększony modelem "
                "powiększającym, a następnie przerysowany kafelkowo z niskim denoise. "
                "Daje ostry obraz 4K bez klonowania obiektów.",
        "wezly": [
            ("Podstawowy rurociąg generacji", "Etap 1", "1024×1024"),
            ("Upscale Model Loader", "Model powiększający", "np. 4x-UltraSharp"),
            ("Upscale Image (using Model)", "Powiększenie", "×4 w przestrzeni pikseli"),
            ("Ultimate SD Upscale", "Sampling kafelkowy", "kafel 1024, denoise 0.35, mask_blur 8"),
            ("Save Image", "Wyjście", ""),
        ],
        "polaczenia": [
            "Etap 1 [IMAGE] → Upscale Image [image]",
            "Upscale Model Loader [UPSCALE_MODEL] → Upscale Image [upscale_model]",
            "Upscale Image [IMAGE] → Ultimate SD Upscale [image]",
            "Checkpoint [MODEL] → Ultimate SD Upscale [model]",
            "Warunki [CONDITIONING] → Ultimate SD Upscale [positive / negative]",
        ],
        "uwaga": "Denoise powyżej 0,5 przy kafelkowaniu sprawia, że sąsiednie kafle zaczynają "
                 "rysować różne rzeczy i pojawiają się widoczne szwy.",
    },
    {
        "slug": "inpainting-maska",
        "tytul": "Inpainting z maską — poprawa fragmentu obrazu",
        "poziom": "Średniozaawansowany",
        "vram": "6–8 GB",
        "opis": "Przerysowanie zaznaczonego obszaru z zachowaniem spójności z tłem. Najczęstsze "
                "zastosowanie to poprawa dłoni i twarzy oraz podmiana pojedynczego elementu "
                "sceny bez ruszania reszty kadru.",
        "wezly": [
            ("Load Image", "Wejście", "obraz do poprawy"),
            ("Load Image (MASK) lub MaskEditor", "Maska", "obszar do przerysowania"),
            ("VAE Encode (for Inpainting)", "Latent", "grow_mask_by 12"),
            ("CLIP Text Encode", "Warunek", "opis tego, co ma się pojawić"),
            ("KSampler", "Sampling", "denoise 0.6–0.9"),
            ("VAE Decode → Save Image", "Wyjście", ""),
        ],
        "polaczenia": [
            "Load Image [IMAGE] → VAE Encode for Inpainting [pixels]",
            "Maska [MASK] → VAE Encode for Inpainting [mask]",
            "Checkpoint [VAE] → VAE Encode for Inpainting [vae]",
            "VAE Encode [LATENT] → KSampler [latent_image]",
        ],
        "uwaga": "Parametr grow_mask_by rozszerza maskę o kilka pikseli i wyraźnie zmniejsza "
                 "ryzyko widocznej granicy. Zaznaczaj obszar z zapasem — maska po samej "
                 "krawędzi problemu daje modelowi za mało kontekstu.",
    },
]

# ------------------------------------------------------------------ sprzęt

SPRZET = [
    {
        "slug": "vram-4-6",
        "poziom": "4–6 GB pamięci karty",
        "karty": "RTX 3050, GTX 1660 Ti, GTX 1060 6 GB, laptopowe RTX 4050",
        "llm": [
            "Modele 3B w Q8_0 — całość na karcie, bardzo szybka odpowiedź",
            "Modele 7–8B w Q4_K_M — z częściowym przeniesieniem do pamięci operacyjnej, "
            "zauważalnie wolniej",
        ],
        "obraz": [
            "SD 1.5 w rozdzielczości 512×512 z powiększaniem do 1024×1024",
            "SDXL w Fooocus w trybie Speed",
            "Forge z trybem oszczędzania pamięci",
        ],
        "wskazowka": "Uruchamiaj ComfyUI z flagą `--lowvram` albo `--medvram`. Nie generuj obrazu "
                     "i nie trzymaj załadowanego modelu językowego jednocześnie.",
    },
    {
        "slug": "vram-8",
        "poziom": "8 GB — rozsądne minimum",
        "karty": "RTX 3070, RTX 4060, RTX 2070/2080, RX 6600 XT",
        "llm": [
            "Modele 7–8B w Q4_K_M lub Q5_K_M — całość na karcie, kontekst 8192",
            "Wyspecjalizowane modele do kodu tej samej wielkości",
        ],
        "obraz": [
            "SDXL w ComfyUI: 1024×1024, łączenie LoRA, ControlNet",
            "Flux.1 Schnell oraz Dev w wariancie NF4 albo GGUF Q4",
            "Fooocus w pełnym trybie Quality",
            "Krótkie animacje w SD 1.5",
        ],
        "wskazowka": "Przy Fluxie trzymaj się wariantów FP8 albo GGUF Q4–Q5 i enkodera T5 w FP8. "
                     "To granica, przy której wszystko mieści się bez przenoszenia do pamięci "
                     "operacyjnej.",
    },
    {
        "slug": "vram-12",
        "poziom": "12 GB — wygodne optimum",
        "karty": "RTX 3060 12 GB, RTX 4070, RTX 4070 SUPER, RX 6700 XT",
        "llm": [
            "Modele 13–14B w Q4_K_M — wyraźny skok jakości względem 8B",
            "Modele 7–8B w Q8_0 z długim kontekstem",
        ],
        "obraz": [
            "Flux.1 Dev FP8 w rozdzielczości natywnej z pełnym T5",
            "ControlNet i IP-Adapter równocześnie z powiększaniem",
            "Generowanie krótkiego wideo z obrazu",
        ],
        "wskazowka": "RTX 3060 w wersji 12 GB od lat pozostaje jedną z najbardziej opłacalnych "
                     "kart do pracy z modelami lokalnie — nie przez wydajność, tylko przez ilość "
                     "pamięci w tej cenie.",
    },
    {
        "slug": "vram-16-24",
        "poziom": "16–24 GB i więcej",
        "karty": "RTX 4080, RTX 4090, RTX 3090, Apple Silicon M-Max z pamięcią współdzieloną",
        "llm": [
            "Modele 32B w Q4_K_M — bardzo dobre w kodzie, analizie i pracy z dokumentami",
            "Modele 70B w Q3–Q4 z częściowym wsparciem pamięci operacyjnej",
            "Modele wyspecjalizowane w pracy na długim kontekście",
        ],
        "obraz": [
            "Flux.1 Dev w pełnej precyzji, czas generacji rzędu kilku sekund",
            "Trenowanie własnych modeli LoRA dla SDXL i Flux",
            "Serwer modelu językowego i ComfyUI uruchomione równolegle",
            "Nowsze modele generowania wideo",
        ],
        "wskazowka": "Model 32B w kwantyzacji 4-bitowej radzi sobie bardzo dobrze w zadaniach "
                     "technicznych i przy pracy z własnymi dokumentami. W zadaniach wymagających "
                     "szerokiej wiedzy o świecie i długiego rozumowania nadal przegrywa "
                     "z czołowymi modelami komercyjnymi — warto o tym pamiętać przy planowaniu "
                     "zastosowań.",
    },
]

# ------------------------------------------------------------------ prompty

PROMPTY = [
    {
        "slug": "flux-fotorealizm",
        "tytul": "Flux.1 — kadr filmowy i fotografia surowa",
        "cel": "Flux.1 w ComfyUI albo Forge",
        "prompt": "A cinematic medium shot of a 35-year-old precision engineer inspecting "
                  "a machined steel component in a dimly lit, atmospheric workshop. Sparks "
                  "reflecting in safety goggles, natural skin pores, realistic imperfections, "
                  "volumetric lighting, 35mm film photography, Kodak Portra 400, shallow depth "
                  "of field, f/1.8",
        "uwagi": "Flux rozumie opis w zdaniach, jak polecenie dla operatora kamery. Nie dokładaj "
                 "słów-wypełniaczy w rodzaju „8k, octane render, masterpiece” — w tym modelu "
                 "nic nie wnoszą, a zabierają miejsce w opisie.",
    },
    {
        "slug": "sdxl-fotorealizm",
        "tytul": "SDXL — dokumentalne zdjęcie przemysłowe",
        "cel": "SDXL w ComfyUI, Fooocus albo Forge",
        "prompt": "Professional documentary photo of an industrial lathe operator in a modern "
                  "CNC workshop, highly detailed metal shavings, oil sheen on the machine bed, "
                  "dynamic perspective, rim lighting, sharp focus, raw photo",
        "uwagi": "W SDXL prompt negatywny nadal ma znaczenie — to on eliminuje plastikowy wygląd "
                 "skóry. Punkt wyjścia: „plastic skin, airbrushed, oversaturated, blurry, "
                 "deformed hands, watermark”.",
    },
    {
        "slug": "fooocus-faceswap",
        "tytul": "Fooocus — podmiana twarzy z zachowaniem sceny",
        "cel": "Fooocus",
        "prompt": "A confident specialist presenting a technical solution in a bright modern "
                  "conference hall, cinematic lighting, tailored suit, photorealistic",
        "uwagi": "Wczytaj zdjęcie twarzy do sekcji Image Prompt, zaznacz tryb FaceSwap "
                 "(waga ok. 0,85, stop ok. 0,9) i wpisz powyższy opis sceny. Jeśli twarz "
                 "przenosi się razem z oświetleniem ze zdjęcia źródłowego, obniż wagę.",
    },
    {
        "slug": "system-asystent-techniczny",
        "tytul": "System prompt — asystent techniczny",
        "cel": "Modele językowe uruchamiane lokalnie",
        "prompt": "Jesteś asystentem technicznym w warsztacie. Odpowiadasz zwięźle i konkretnie, "
                  "bez wstępów i podsumowań. Podajesz wartości z jednostkami. Jeśli brakuje "
                  "danych do jednoznacznej odpowiedzi, wypisujesz, czego brakuje, zamiast "
                  "zgadywać. Gdy pytanie dotyczy bezpieczeństwa, zaczynasz od ostrzeżenia.",
        "uwagi": "Zdanie o brakujących danych jest tu najważniejsze — bez niego model wypełnia "
                 "luki własnymi założeniami i podaje je z taką samą pewnością co fakty.",
    },
    {
        "slug": "system-wyciaganie-danych",
        "tytul": "System prompt — wyciąganie danych do JSON",
        "cel": "Modele językowe, integracja z programem",
        "prompt": "Zwracasz wyłącznie poprawny JSON zgodny z podanym schematem. Bez komentarzy, "
                  "bez bloków markdown, bez tekstu przed i po. Gdy wartości nie da się ustalić "
                  "z podanego tekstu, wstawiasz null. Nie wymyślasz danych.",
        "uwagi": "Do tego temperatura 0,1 i walidacja wyniku po stronie programu z jedną ponowną "
                 "próbą. Zdanie „bez bloków markdown” eliminuje najczęstszy problem: odpowiedź "
                 "owiniętą w potrójne apostrofy.",
    },
]
