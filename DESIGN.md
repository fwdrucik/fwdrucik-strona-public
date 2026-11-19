---
name: "F.W. DRUCIK"
description: "Interfejs warsztatowy w zielonym graficie, z czytelnymi scenami 3D i diagramami procesu."
colors:
  primary: "#80edf0"
  primary-hover: "#b3f8f9"
  secondary: "#e5a87e"
  graphite: "#101716"
  panel: "#192321"
  paper: "#e8ece2"
  muted: "#b7c6be"
  line: "#34453e"
  paper-ink: "#1a2621"
  action-ink: "#0b2425"
  field-navy: "#0a1530"
typography:
  display:
    fontFamily: "Barlow Condensed, Jost, sans-serif"
    fontSize: "clamp(3.35rem, 5.8vw, 5.35rem)"
    fontWeight: 700
    lineHeight: 0.91
    letterSpacing: "-.018em"
  headline:
    fontFamily: "Barlow Condensed, Jost, sans-serif"
    fontSize: "clamp(2.15rem, 4.1vw, 3.65rem)"
    fontWeight: 700
    lineHeight: 0.98
    letterSpacing: "0"
  title:
    fontFamily: "Barlow Condensed, Jost, sans-serif"
    fontSize: "clamp(1.5rem, 2.5vw, 2.05rem)"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0"
  body:
    fontFamily: "Hanken Grotesk, Segoe UI, Arial, sans-serif"
    fontSize: "17px"
    lineHeight: 1.55
  label:
    fontFamily: "Hanken Grotesk, Segoe UI, Arial, sans-serif"
    fontSize: ".88rem"
    fontWeight: 700
    letterSpacing: ".08em"
rounded:
  control: "2px"
  button: "3px"
  field: "6px"
spacing:
  controls: "7px"
  actions: "10px"
  section-inset: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.action-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.button}"
    padding: "14px 28px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.action-ink}"
  button-outline:
    textColor: "{colors.paper}"
    typography: "{typography.label}"
    rounded: "{rounded.button}"
    padding: "14px 28px"
  scene-control:
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    height: "40px"
    padding: "7px 10px"
  contact-field:
    backgroundColor: "{colors.field-navy}"
    textColor: "{colors.paper}"
    rounded: "{rounded.field}"
    padding: "12px 14px"
  service-link:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.paper-ink}"
    padding: "14px 17px 17px"
  navigation-link:
    textColor: "{colors.muted}"
    rounded: "{rounded.field}"
    padding: "10px 8px"
---

# Design System: F.W. DRUCIK

## Overview

**Creative North Star: "Stół warsztatowy"**

Stalowe mechanizmy, miedziana wiązka i sygnał świetlny nadają stronie charakter stanowiska pracy. Ciemne ramy scen i jasne pasy z ofertą porządkują przejście między oglądaniem a wyborem usługi.

Skrócone nagłówki i opisowe etykiety zostawiają miejsce na właściwy model albo kolejność kroków. Punktowa animacja pomaga obejrzeć mechanizm lub rozpoznać stan interakcji.

**Key Characteristics:**
- Zielony grafit, jasny papier, sygnał cyjanowy i ciepły akcent miedzi.
- Wyraziste nagłówki skondensowane i spokojny tekst użytkowy.
- Cienkie ramy, oszczędne zaokrąglenia i siatka wewnątrz sceny.
- Modele usług rozpoznawalne dzięki własnej geometrii.

## Colors

### Primary

- **Sygnał cyjanowy** prowadzi do głównego przycisku, aktywnego sterowania, zaznaczenia i obrysu fokusu. Jasny cyjan rozjaśnia przycisk po najechaniu.

### Secondary

- **Ciepła miedź** wyróżnia lokalizację na stronie głównej i krok akceptacji w diagramie. W modelach pojawia się jako przewód, detal albo cieplejsze światło.

### Neutral

- **Zielony grafit** stanowi tło strony, a jaśniejszy **panel warsztatowy** oddziela większą powierzchnię roboczą.
- **Jasny papier** jest kolorem głównego tekstu na ciemnej powierzchni oraz tłem bloków porównawczych. **Atrament na papierze** pozostaje ciemny.
- **Przygaszona jasna zieleń** służy opisom na ciemnym tle. **Linia ramy** rozdziela sekcje i pola sterowania.
- **Pole formularza** zachowuje ciemnogranatowe wypełnienie i jasny tekst.

**The Signal Rule.** Cyjan wskazuje akcję, stan wyboru lub przepływ. Miedź odróżnia pomocniczą informację oraz cieplejsze światło w scenie.

## Typography

**Display Font:** Barlow Condensed, z zastępstwem Jost.
**Body Font:** Hanken Grotesk, z zastępstwem Segoe UI i Arial.

Zwarta, ciężka typografia nadaje nagłówkom rytm. Krój tekstowy pozwala szybko czytać opisy usług, formularze i podpisy.

- **Display** (700, od 3.35 do 5.35 rem na stronie głównej, interlinia .91). Dla nagłówków otwierających, z cyjanem akcentującym część treści.
- **Headline i Title** (700). Wyróżniają początek sekcji, podpis usług i tytuły sterowania.
- **Body** (17 px, interlinia 1.55). Opis rozpoczynający stronę główną ma miarę do 50 `ch`, a opisy przykładów automatyzacji do 78 `ch`.
- **Label** (700, .88 rem). Wielkie litery i odstępy między znakami dla głównych przycisków.

## Layout

Strona główna i konfigurator korzystają z dwóch kolumn. Bloki oparte na pokazie produktu dają więcej miejsca scenie. Obszar otwierający ma maksymalną szerokość 1310 px. Sekcja usług ma cztery pola o wspólnej linii podziału.

Przy 880 px zmniejszają się marginesy sceny otwierającej. Przy 760 px treść ustawia się w jednej kolumnie, a kafle usług przechodzą na dwie kolumny. Przy 420 px cztery przyciski przewodów układają się po dwa w wierszu.

## Elevation & Depth

Powierzchnie układają się warstwowo dzięki różnicy jasności i cienkim liniom podziału. Rama modelu i diagram procesu rzucają miękki cień w dół. Sterowanie pozostaje płaskie. Głębię wewnątrz sceny daje oświetlenie modelu i siatka tła.

**The Surface Rule.** Najpierw rozdziel powierzchnie kolorem i linią. Rozproszony cień zachowaj dla ramy modelu lub diagramu.

## Shapes

Pola usług i ramy obrazu mają proste krawędzie. Główne przyciski mają małe zaokrąglenie (3 px), a sterowanie sceną (2 px). Kółko identyfikuje próbkę żywicy, a prostokątna tabliczka numer porządkowy kroku.

## Components

### Buttons

Główne przyciski mają cyjanowe wypełnienie i ciemny tekst. Wariant obrysowy pozostawia tło widoczne. Po najechaniu rozjaśnia się wypełnienie lub pojawia się cyjanowy obrys. Fokus na ciemnym tle ma cyjanowy obrys (2 px) odsunięty od krawędzi (4 px).

### Cards / Containers

Jasny pas usług dzielą jednopikselowe linie. Każde pole pozostaje w całości linkiem i otrzymuje ciemniejszą zieloną powierzchnię po najechaniu lub przejściu fokusem. Wysokość miejsca na model skaluje się z ekranem.

### Inputs / Fields

Pola kontaktowe mają ciemne wypełnienie, jasny tekst, cienką ramkę i promień 6 px. Etykiety są nad kontrolkami. Próbki żywicy łączą nazwę koloru z wizualnym znacznikiem i obrysem zaznaczenia.

### Navigation

Górna belka używa ciemnego panelu, przygasowanych etykiet i wyraźnego przycisku wyceny. Linki rozjaśniają się na ciemniejszej zielonej podkładce. Nawigacja zachowuje menu mobilne.

### Ramy scen i diagram procesu

Sceny 3D mają własną powierzchnię, podpis i oddzielne sterowanie. Sterowanie pokazuje się po przygotowaniu sceny, a kluczowe ilustracje mają podglądy zastępcze. Sceny poza kadrem nie są renderowane. Preferencja ograniczonego ruchu oraz przełącznik animacji zatrzymują ruch ciągły. Diagram procesu numeruje rzeczywiste kroki i wyróżnia miejsce ludzkiej akceptacji.

## Do's and Don'ts

### Do

- Do umieszczaj sceny 3D w wyodrębnionej ramie z podpisem i zachowuj czytelny podgląd zastępczy.
- Do daj wyborom widoczny stan zaznaczenia i używaj czytelnych obrysów klawiaturowych.
- Do stosuj jasne pola dla przeglądu usług i porównań, zachowując ciemny kolor tekstu.

### Don't

- Don't stosuj tego samego kadru 3D do kilku różnych usług. Forma powinna wyjaśniać, czego dotyczy usługa.
- Don't oznaczaj stanu wyłącznie kolorem. Przy kolorach żywicy i przewodach zachowaj etykiety.
- Don't uzależniaj głównej nawigacji ani treści oferty od odtwarzania sceny.
