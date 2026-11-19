# -*- coding: utf-8 -*-
"""Kursy online — katalog i strony poszczególnych kursów.

Strony powstają z danych, nie z plików w src/. Cztery kursy mają identyczną
budowę (dla kogo, program, co dostajesz, zapisy, pytania), więc trzymanie ich
jako czterech kopii HTML znaczyłoby cztery miejsca do poprawienia przy każdej
zmianie ceny albo terminu.

Uwaga o uczciwości sprzedaży: nagrania jeszcze nie istnieją. Strony mówią to
wprost i prowadzą zapisy na pierwszą edycję w niższej cenie, zamiast udawać, że
kurs jest gotowy do pobrania od ręki. Po nagraniu materiału wystarczy zmienić
`GOTOWY` na True i uzupełnić `data_startu`.
"""

from build import SITE, breadcrumbs_ld, faq_ld

GLOWNA = ("Strona główna", "/")
SEKCJA = ("Kursy", "/kursy/")

# Dopóki nagrania nie są gotowe, wszystkie strony prowadzą zapisy, a nie sprzedaż.
GOTOWY = False


KURSY = [
    {
        "slug": "diagnostyka-magistral-pojazdowych",
        "tytul": "Diagnostyka magistral pojazdowych",
        "podtytul": "CAN, LIN, FlexRay, J1939 i UDS — od oscylogramu do naprawionego pojazdu",
        "title_seo": "Kurs diagnostyki magistral CAN i J1939 | F.W. DRUCIK",
        "opis": "Kurs online diagnostyki magistral pojazdowych: CAN, LIN, FlexRay, J1939 "
                "i UDS ISO 14229. Pomiary oscyloskopem, kody NRC, praktyka warsztatowa.",
        "cena": 899,
        "cena_zapisy": 649,
        "godzin": 12,
        "poziom": "Średnio zaawansowany",
        "dla_kogo": [
            "Mechanik, który chce diagnozować błędy komunikacji U.",
            "Diagnosta pracujący na pojazdach ciężarowych i maszynach, gdzie J1939 jest normą.",
            "Elektryk samochodowy, który chce potwierdzać usterki sterowników pomiarami.",
        ],
        "wymagania": "Podstawy elektrotechniki i umiejętność obsługi multimetru. "
                     "Oscyloskop bardzo pomaga, ale pierwsze moduły da się przejść bez niego.",
        "program": [
            ("Jak działa magistrala",
             "Dlaczego dwa przewody zastąpiły sto. Topologia, terminacja 120 Ω, "
             "poziomy napięć CAN High i CAN Low, co widać na oscyloskopie przy sprawnej sieci."),
            ("CAN od podstaw",
             "Budowa ramki, arbitraż, bit stuffing, licznik błędów i przejście w bus-off. "
             "Skąd się biorą błędy komunikacji, które znikają po restarcie."),
            ("Pomiary na żywym pojeździe",
             "Podpięcie oscyloskopu, odczyt przebiegu, rozpoznanie zwarcia do masy, do plusa "
             "i przerwy w linii. Typowe uszkodzenia wiązki i miejsca, gdzie występują."),
            ("LIN — prosta sieć lokalna",
             "Master i slave, ramka LIN, po co w ogóle druga magistrala. Diagnostyka lusterek, "
             "foteli, klimatyzacji postojowej i modułów drzwi."),
            ("J1939 w pojazdach ciężarowych",
             "PGN, SPN i FMI — jak czytać kody z ciężarówki i maszyny budowlanej. "
             "Adresowanie, komunikaty rozgłoszeniowe, praca z dokumentacją SAE."),
            ("FlexRay i Automotive Ethernet",
             "Gdzie się je spotyka i czym różnią się od CAN-a. Czego nie da się zmierzyć "
             "zwykłym oscyloskopem i kiedy trzeba oddać pojazd do ASO."),
            ("UDS ISO 14229 w praktyce",
             "Sesje diagnostyczne, usługi, security access. Kody NRC — co znaczy odmowa "
             "sterownika i jak znaleźć jej przyczynę."),
            ("Sterowniki i sieć w komplecie",
             "ECU, VECU, EBS, ECAS, BCM. Które sterowniki rozmawiają z którymi i co się dzieje, "
             "gdy jeden przestanie odpowiadać."),
            ("Trzy przypadki od początku do końca",
             "Trzy realne usterki z warsztatu: objaw, pomiary, ślepe uliczki i rozwiązanie. "
             "Z oscylogramami i zrzutami ze skanera."),
        ],
        "pytania": [
            ("Czy potrzebuję drogiego sprzętu?",
             "Nie na start. Multimetr i tani oscyloskop USB wystarczą na osiem z dziewięciu "
             "modułów. W kursie jest osobny odcinek o doborze sprzętu w różnych budżetach — "
             "od 400 zł do sprzętu warsztatowego."),
            ("Czy to kurs pod konkretną markę?",
             "Nie. Magistrale działają tak samo niezależnie od logo na masce. Przykłady są "
             "z pojazdów ciężarowych, dostawczych i maszyn, bo tam pracuję na co dzień, "
             "ale zasady przenoszą się na osobowe."),
            ("Co jeśli utknę w trakcie?",
             "Do kursu jest dołączona jedna konsultacja telefoniczna 30 minut. Można też "
             "pytać na forum warsztatu."),
        ],
    },
    {
        "slug": "klimatyzacja-samochodowa",
        "tytul": "Klimatyzacja samochodowa",
        "podtytul": "Serwis, diagnostyka i czynniki R134a oraz R1234yf bez zgadywania",
        "title_seo": "Kurs serwisu klimatyzacji samochodowej | F.W. DRUCIK",
        "opis": "Kurs online serwisu klimatyzacji samochodowej: ciśnienia robocze, "
                "diagnostyka usterek, R134a i R1234yf, procedury po naprawie.",
        "cena": 499,
        "cena_zapisy": 349,
        "godzin": 7,
        "poziom": "Podstawowy",
        "dla_kogo": [
            "Warsztat, który ma stację do nabijania i chce robić na niej coś więcej niż wymianę czynnika.",
            "Mechanik, który słyszy „nie chłodzi” i nie wie, od czego zacząć.",
            "Każdy, kto wchodzi w R1234yf i chce uniknąć kosztownych pomyłek.",
        ],
        "wymagania": "Brak. Kurs zaczyna się od obiegu chłodniczego wytłumaczonego od zera.",
        "program": [
            ("Obieg chłodniczy bez wzorów",
             "Sprężarka, skraplacz, zawór rozprężny, parownik, osuszacz. Co się dzieje "
             "z czynnikiem na każdym odcinku i dlaczego to ma znaczenie przy diagnozie."),
            ("Ciśnienia mówią wszystko",
             "Odczyt manometrów: niskie i wysokie ciśnienie w normie, za niskie, za wysokie "
             "i rozbieżne. Tabela objawów i przyczyn, którą można powiesić w warsztacie."),
            ("R134a kontra R1234yf",
             "Czym się różnią, dlaczego nie wolno ich mieszać, wymagania sprzętowe, "
             "palność R1234yf i co to zmienia w procedurze."),
            ("Nieszczelności",
             "Metody wykrywania: barwnik UV, detektor elektroniczny, azot pod ciśnieniem. "
             "Gdzie ucieka najczęściej i jak nie stracić dnia na szukaniu."),
            ("Sprężarka",
             "Sprzęgło, sterowanie zaworem, sprężarki bezsprzęgłowe. Kiedy do wymiany, kiedy "
             "wystarczy naprawa i dlaczego po wymianie trzeba przepłukać układ."),
            ("Elektryka i sterowanie",
             "Czujniki ciśnienia i temperatury, sterowanie z BCM, magistrala w układzie komfortu. "
             "Dlaczego klimatyzacja potrafi przestać działać po wymianie akumulatora."),
            ("Procedury po naprawie",
             "Próżnia, czas trzymania, dawkowanie oleju, napełnianie, kontrola wydajności. "
             "Lista kontrolna do wydruku."),
        ],
        "pytania": [
            ("Czy potrzebuję stacji do nabijania?",
             "Do wykonywania serwisu tak, do przejścia kursu nie. Moduły o diagnostyce "
             "i elektryce są przydatne nawet bez własnej stacji."),
            ("Czy kurs daje uprawnienia f-gazowe?",
             "Nie. Uprawnienia f-gazowe wydaje jednostka certyfikująca po egzaminie państwowym. "
             "Ten kurs uczy roboty, nie zastępuje certyfikatu."),
        ],
    },
    {
        "slug": "spawanie-tig-aluminium",
        "tytul": "Spawanie TIG aluminium",
        "podtytul": "Prąd zmienny, balans, częstotliwość i elektroda — czyli dlaczego spoina wychodzi brudna",
        "title_seo": "Kurs spawania TIG aluminium — AC, balans | F.W. DRUCIK",
        "opis": "Kurs online spawania aluminium metodą TIG AC: dobór elektrody, balans "
                "i częstotliwość, przygotowanie materiału, porowatość i jej przyczyny.",
        "cena": 599,
        "cena_zapisy": 449,
        "godzin": 6,
        "poziom": "Średnio zaawansowany",
        "dla_kogo": [
            "Spawacz, który dobrze radzi sobie ze stalą, a przy aluminium spoina wychodzi szara i porowata.",
            "Warsztat, który kupił spawarkę AC/DC i nie wykorzystuje połowy jej możliwości.",
            "Każdy, kto naprawia chłodnice, zbiorniki, obudowy i elementy maszyn z aluminium.",
        ],
        "wymagania": "Umiejętność spawania TIG na stali. Spawarka z prądem zmiennym (AC).",
        "program": [
            ("Dlaczego aluminium jest inne",
             "Tlenek glinu topi się w 2050 °C, a samo aluminium w 660 °C. Cała reszta kursu "
             "wynika z tego jednego zdania."),
            ("Prąd zmienny i co robi balans",
             "Faza czyszcząca i faza wtapiania. Co się dzieje przy 30%, 50% i 70% balansu — "
             "z pokazaniem spoin i przekrojów."),
            ("Częstotliwość AC",
             "Od 50 do 250 Hz. Jak zmienia się szerokość jeziorka i skupienie łuku, "
             "kiedy podbić, a kiedy zejść niżej."),
            ("Elektrody wolframowe",
             "Zielona, złota, fioletowa — czym się różnią przy AC. Szlifowanie, kulka na końcu, "
             "średnica dobrana do prądu."),
            ("Przygotowanie materiału",
             "Odtłuszczenie, szczotka do aluminium wyłącznie do aluminium, usuwanie tlenku, "
             "czas między czyszczeniem a spawaniem."),
            ("Porowatość i pozostałe wady",
             "Skąd bierze się porowatość, pęknięcia na gorąco i czarny nalot. Diagnoza po wyglądzie "
             "spoiny, z galerią wad i przyczyn."),
            ("Podajnik spool gun i gruby materiał",
             "Kiedy TIG przestaje mieć sens i lepiej wziąć MIG z podajnikiem. Dobór drutu, "
             "ustawienia, spawanie grubszych przekrojów."),
        ],
        "pytania": [
            ("Czy nauczę się spawać z samego wideo?",
             "Nie. Wideo skraca drogę i oszczędza materiał, ale rękę wyrabia się przy stole. "
             "Kurs mówi, co ustawić i co znaczy to, co widzisz — resztę robi praktyka."),
            ("Czy mogę przysłać zdjęcia swoich spoin do oceny?",
             "Tak, w pierwszej edycji jest ocena spoin ze zdjęć — do trzech kompletów na osobę."),
        ],
    },
    {
        "slug": "esp32-w-warsztacie",
        "tytul": "ESP32 w warsztacie",
        "podtytul": "Automatyka, pomiary i własne narzędzia — od pierwszego skryptu do działającego urządzenia",
        "title_seo": "Kurs ESP32 dla warsztatu — automatyka i pomiary | F.W. DRUCIK",
        "opis": "Kurs online ESP32 dla warsztatu: czujniki, RS485 i Modbus, MQTT, "
                "monitorowanie maszyn, własne narzędzia pomiarowe i sterujące.",
        "cena": 449,
        "cena_zapisy": 329,
        "godzin": 8,
        "poziom": "Podstawowy",
        "dla_kogo": [
            "Mechanik albo technik, który chce zbudować własne narzędzie zamiast kupować gotowe za tysiące.",
            "Utrzymanie ruchu — monitorowanie maszyn, temperatur, drgań i czasu pracy.",
            "Każdy, kto ma pomysł na automatyzację czegoś w warsztacie i nie wie, od czego zacząć.",
        ],
        "wymagania": "Brak doświadczenia w programowaniu. Zaczynamy od instalacji środowiska.",
        "program": [
            ("Pierwsze uruchomienie",
             "ESP32 w pigułce, instalacja środowiska, wgranie programu, migająca dioda. "
             "Dobór modułu i zasilania do warunków warsztatowych."),
            ("Czujniki, które faktycznie się przydają",
             "DS18B20, DHT22 i AHT20, BME280. Temperatura, wilgotność, ciśnienie — podpięcie, "
             "odczyt, kalibracja i typowe pułapki."),
            ("Wejścia i wyjścia w brudnym środowisku",
             "Przekaźniki, optoizolacja, ochrona wejść, zasilanie 24 V w otoczeniu przemysłowym. "
             "Jak nie spalić modułu po tygodniu."),
            ("RS485 i Modbus RTU",
             "Rozmowa z falownikami, licznikami i sterownikami przemysłowymi. Adresacja, "
             "rejestry, terminacja magistrali."),
            ("Wi-Fi i MQTT",
             "Wysyłanie pomiarów na serwer, prosty panel z podglądem, powiadomienia. "
             "Co zrobić, gdy w hali nie ma zasięgu."),
            ("Bluetooth i telefon",
             "BLE i komunikacja z telefonem — własna aplikacja do odczytu urządzenia bez chmury."),
            ("Trzy gotowe projekty",
             "Rejestrator temperatury z pamięcią, licznik czasu pracy maszyny, "
             "kontrola warunków w lakierni. Kod do skopiowania i schematy."),
        ],
        "pytania": [
            ("Ile kosztuje sprzęt do kursu?",
             "Komplet do wszystkich projektów mieści się w 150–250 zł. Lista zakupowa "
             "z linkami jest w pierwszym module."),
            ("Czy to kurs programowania?",
             "Na tyle, na ile trzeba. Nie uczę informatyki — uczę zbudować urządzenie, "
             "które działa w warsztacie."),
        ],
    },
]


def _cena_html(k):
    if GOTOWY:
        return (f'<p class="price">{k["cena"]} zł <span>/ dostęp bezterminowy</span></p>')
    return (f'<p class="price">{k["cena_zapisy"]} zł '
            f'<span>w zapisach, potem {k["cena"]} zł</span></p>')


def _karta_kursu(k):
    return (
        '<article class="product-card">\n'
        '  <div class="product-info">\n'
        f'    <p class="cat">{k["poziom"]} · {k["godzin"]} godzin</p>\n'
        f'    <h2><a href="/kursy/{k["slug"]}/">{k["tytul"]}</a></h2>\n'
        f'    <p>{k["podtytul"]}</p>\n'
        f'    {_cena_html(k)}\n'
        f'    <a href="/kursy/{k["slug"]}/" class="btn btn-primary">Zobacz program</a>\n'
        '  </div>\n'
        '</article>\n'
    )


def _formularz(k):
    """Zapisy idą tą samą drogą co reszta formularzy — mailem, bez nowego zaplecza."""
    temat = f"KURS {k['tytul']} — zapis"
    return (
        f'<form class="contact-form reveal" action="https://formsubmit.co/fwdrucik@gmail.com" method="POST">\n'
        f'  <input type="hidden" name="_subject" value="{temat}">\n'
        '  <input type="hidden" name="_template" value="table">\n'
        '  <input type="hidden" name="_captcha" value="false">\n'
        f'  <input type="hidden" name="_next" value="{SITE}/kursy/{k["slug"]}/?wyslano=1">\n'
        f'  <input type="hidden" name="Kurs" value="{k["tytul"]}">\n'
        '  <input type="text" name="_honey" tabindex="-1" autocomplete="off" style="display:none" aria-hidden="true">\n'
        '  <label for="z-name">Imię i nazwisko</label>\n'
        '  <input type="text" id="z-name" name="Imię i nazwisko" required autocomplete="name">\n'
        '  <label for="z-email">Email</label>\n'
        '  <input type="email" id="z-email" name="Email" required autocomplete="email">\n'
        '  <label for="z-tel">Telefon (opcjonalnie)</label>\n'
        '  <input type="tel" id="z-tel" name="Telefon" autocomplete="tel">\n'
        '  <label for="z-uwagi">Czego najbardziej potrzebujesz z tego kursu?</label>\n'
        '  <textarea id="z-uwagi" name="Czego potrzebuję" placeholder="Piszę program pod realne problemy — napisz, co Cię blokuje w robocie. To realnie wpływa na kolejność modułów."></textarea>\n'
        '  <label class="checkbox">\n'
        '    <input type="checkbox" name="Zgoda RODO" value="tak" required>\n'
        '    <span>Zgadzam się na kontakt w sprawie tego kursu.</span>\n'
        '  </label>\n'
        '  <button type="submit" class="btn btn-primary">Zapisz mnie na pierwszą edycję</button>\n'
        '  <p class="form-note">Zapis nie jest płatnością ani zobowiązaniem. Odezwę się, '
        'gdy materiał będzie gotowy — z ceną z zapisów i terminem startu.</p>\n'
        '</form>\n'
    )


def _strona_kursu(k):
    program = "".join(
        f'<li><strong>{tytul}.</strong> {opis}</li>\n'
        for tytul, opis in k["program"]
    )
    dla_kogo = "".join(f'<li>{x}</li>\n' for x in k["dla_kogo"])
    pytania = "".join(
        f'<h3>{p}</h3>\n<p>{o}</p>\n' for p, o in k["pytania"]
    )

    stan = (
        '' if GOTOWY else
        '<div class="produkt-zaufanie" style="margin-bottom:22px">\n'
        '  <li><strong>Kurs jest w produkcji — trwają zapisy na pierwszą edycję.</strong></li>\n'
        '  <li>Nagrania jeszcze nie powstały. Nie sprzedaję dostępu do czegoś, czego nie ma.</li>\n'
        '  <li>Zapis nic nie kosztuje i do niczego nie zobowiązuje — daje cenę z zapisów '
        'i wpływ na to, co znajdzie się w programie.</li>\n'
        '</div>\n'
    )

    return (
        '<section class="page-hero">\n  <div class="container">\n'
        f'    <p class="eyebrow">Kurs online · {k["poziom"]} · {k["godzin"]} godzin</p>\n'
        f'    <h1>{k["tytul"]}</h1>\n'
        f'    <p class="lead">{k["podtytul"]}</p>\n'
        '    <div class="hero-cta">\n'
        f'      <a href="#zapisy" class="btn btn-primary">Zapisz się na pierwszą edycję</a>\n'
        '      <a href="/konsultacje/" class="btn btn-outline">Wolę jednorazową konsultację</a>\n'
        '    </div>\n'
        '  </div>\n</section>\n\n'
        '<div class="wire-divider" aria-hidden="true"></div>\n\n'
        '<section class="diamond-bg">\n  <div class="container">\n'
        '    <div class="prose reveal">\n'
        f'      {stan}'
        '      <h2>Dla kogo to jest</h2>\n'
        f'      <ul class="check-list">\n{dla_kogo}      </ul>\n'
        f'      <p><strong>Czego potrzebujesz na start:</strong> {k["wymagania"]}</p>\n'
        '    </div>\n  </div>\n</section>\n\n'
        '<div class="wire-divider" aria-hidden="true"></div>\n\n'
        '<section>\n  <div class="container">\n'
        '    <div class="prose reveal">\n'
        '      <h2>Program</h2>\n'
        f'      <ol class="num-list">\n{program}      </ol>\n'
        '      <h2>Co dostajesz</h2>\n'
        '      <ul class="check-list">\n'
        f'        <li><strong>{k["godzin"]} godzin nagrań</strong> podzielonych na krótkie odcinki '
        '— do obejrzenia na telefonie w warsztacie.</li>\n'
        '        <li><strong>Materiały do wydruku</strong> — tabele, listy kontrolne i schematy, '
        'które można powiesić nad stanowiskiem.</li>\n'
        '        <li><strong>Dostęp bezterminowy</strong> razem z późniejszymi aktualizacjami.</li>\n'
        '        <li><strong>Faktura VAT</strong> — dla warsztatu to koszt uzyskania przychodu.</li>\n'
        '      </ul>\n'
        '    </div>\n  </div>\n</section>\n\n'
        '<div class="wire-divider" aria-hidden="true"></div>\n\n'
        '<section class="diamond-bg" id="zapisy">\n  <div class="container">\n'
        '    <div class="prose reveal">\n'
        '      <h2>Zapisy na pierwszą edycję</h2>\n'
        f'      {_cena_html(k)}\n'
        '    </div>\n'
        f'    {_formularz(k)}\n'
        '  </div>\n</section>\n\n'
        '<div class="wire-divider" aria-hidden="true"></div>\n\n'
        '<section>\n  <div class="container">\n'
        '    <div class="prose reveal">\n'
        '      <h2>Pytania</h2>\n'
        f'{pytania}'
        '    </div>\n  </div>\n</section>\n\n'
        '{{CTA}}\n'
    )


def _kurs_ld(k):
    """Course dla wyszukiwarki.

    Cena i dostępność opisują to, co jest naprawdę: dopóki nagrania nie powstały,
    oferta jest przedsprzedażą (PreOrder), a nie towarem na stanie.
    """
    return {
        "@type": "Course",
        "@id": SITE + f"/kursy/{k['slug']}/#kurs",
        "name": k["tytul"],
        "description": k["opis"],
        "url": SITE + f"/kursy/{k['slug']}/",
        "inLanguage": "pl-PL",
        "educationalLevel": k["poziom"],
        "teaches": [tytul for tytul, _ in k["program"]],
        "provider": {"@id": SITE + "/#organizacja"},
        "offers": {
            "@type": "Offer",
            "price": str(k["cena_zapisy"] if not GOTOWY else k["cena"]),
            "priceCurrency": "PLN",
            "category": "Paid",
            "availability": "https://schema.org/InStock" if GOTOWY
                            else "https://schema.org/PreOrder",
            "url": SITE + f"/kursy/{k['slug']}/",
            "seller": {"@id": SITE + "/#organizacja"},
        },
        "hasCourseInstance": {
            "@type": "CourseInstance",
            "courseMode": "online",
            "courseWorkload": f"PT{k['godzin']}H",
        },
    }


def _strona(url, title, desc, html, okruszki, dodatkowe=None, priority="0.8"):
    from build import ORGANIZACJA, WEBSITE
    graph = [ORGANIZACJA, WEBSITE, breadcrumbs_ld([GLOWNA] + okruszki)]
    graph.extend(dodatkowe or [])
    return {
        "url": url,
        "src": None,
        "html": html,
        "title": title,
        "desc": desc,
        "graph": graph,
        "okruszki": [GLOWNA] + okruszki,
        "priority": priority,
        "changefreq": "monthly",
    }


def _katalog():
    karty = "".join(_karta_kursu(k) for k in KURSY)
    return (
        '<section class="page-hero">\n  <div class="container">\n'
        '    <p class="eyebrow">Kursy online</p>\n'
        '    <h1>Kursy techniczne dla warsztatów</h1>\n'
        '    <p class="lead">Cztery kursy: '
        'magistrale pojazdowe, klimatyzacja, spawanie aluminium i własna automatyka. '
        'Oparte na codziennej pracy warsztatu.</p>\n'
        '    <div class="hero-cta">\n'
        '      <a href="/konsultacje/" class="btn btn-outline">Potrzebuję pomocy od ręki</a>\n'
        '    </div>\n'
        '  </div>\n</section>\n\n'
        '<div class="wire-divider" aria-hidden="true"></div>\n\n'
        '<section class="diamond-bg">\n  <div class="container">\n'
        '    <div class="produkt-zaufanie reveal" style="margin-bottom:26px">\n'
        '      <li><strong>Kursy są w produkcji.</strong> Trwają zapisy na pierwszą edycję.</li>\n'
        '      <li>Zapis nic nie kosztuje, nie zobowiązuje i daje niższą cenę na starcie.</li>\n'
        '      <li>Piszę program pod realne problemy — przy zapisie można napisać, co blokuje '
        'Cię w robocie.</li>\n'
        '    </div>\n'
        f'    <div class="product-grid reveal">\n{karty}    </div>\n'
        '  </div>\n</section>\n\n'
        '<div class="wire-divider" aria-hidden="true"></div>\n\n'
        '<section>\n  <div class="container">\n'
        '    <div class="prose reveal">\n'
        '      <h2>Skąd te tematy</h2>\n'
        '      <p>Z <a href="/blog/">bloga</a>, na którym opisuję konkretne roboty, i z telefonów, '
        'które odbieram. Cztery zagadnienia wracają najczęściej i za każdym razem kończy się '
        'tak samo: materiału po polsku prawie nie ma, a to, co jest, to tłumaczenie ulotki '
        'producenta.</p>\n'
        '      <p>Jeśli szukasz odpowiedzi na jedno pytanie, a nie całego kursu — '
        '<a href="/konsultacje/">konsultacja telefoniczna</a> będzie szybsza i tańsza.</p>\n'
        '    </div>\n  </div>\n</section>\n\n'
        '{{CTA}}\n'
    )


STRONY = [
    _strona(
        "/kursy/",
        "Kursy techniczne online dla warsztatów | F.W. DRUCIK",
        "Kursy online: diagnostyka magistral CAN i J1939, serwis klimatyzacji, "
        "spawanie TIG aluminium, ESP32 w warsztacie. Zapisy na pierwszą edycję.",
        _katalog(),
        [SEKCJA],
        dodatkowe=[{
            "@type": "ItemList",
            "name": "Kursy techniczne F.W. DRUCIK",
            "numberOfItems": len(KURSY),
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "item": _kurs_ld(k)}
                for i, k in enumerate(KURSY)
            ],
        }],
        priority="0.9",
    ),
]

STRONY.extend(
    _strona(
        f"/kursy/{k['slug']}/",
        k["title_seo"],
        k["opis"],
        _strona_kursu(k),
        [SEKCJA, (k["tytul"], f"/kursy/{k['slug']}/")],
        dodatkowe=[_kurs_ld(k), faq_ld(k["pytania"])],
        priority="0.8",
    )
    for k in KURSY
)
