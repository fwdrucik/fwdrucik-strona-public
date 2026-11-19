# -*- coding: utf-8 -*-
"""Metadane wszystkich podstron fwdrucik.pl — tytuły, opisy, okruszki, dane strukturalne."""

from build import (
    ORGANIZACJA,
    WEBSITE,
    SITE,
    breadcrumbs_ld,
    faq_ld,
    service_ld,
)

GLOWNA = ("Strona główna", "/")


def strona(url, src, title, desc, okruszki=None, dodatkowe=None, priority="0.7",
           changefreq="monthly", **reszta):
    """Buduje wpis podstrony razem z pełnym grafem danych strukturalnych."""
    graph = [ORGANIZACJA, WEBSITE]
    sciezka = [GLOWNA] + (okruszki or [])
    if len(sciezka) > 1:
        graph.append(breadcrumbs_ld(sciezka))
    graph.extend(dodatkowe or [])
    wpis = {
        "url": url,
        "src": src,
        "title": title,
        "desc": desc,
        "graph": graph,
        "okruszki": sciezka,
        "priority": priority,
        "changefreq": changefreq,
    }
    wpis.update(reszta)
    return wpis


USLUGI = ("Usługi", "/uslugi/")


STRONY = [
    # ------------------------------------------------------------- główna
    strona(
        "/", "index.html",
        "Elektryka, automatyka, CNC — Winnica | F.W. DRUCIK",
        "Elektryka pojazdów i maszyn, serwis elektronarzędzi, falowniki, automatyzacje AI, alarmy i projekty CNC. "
        "Winnica k. Pułtuska, tel. 601 726 924.",
        priority="1.0", changefreq="weekly",
        dodatkowe=[
            faq_ld([
                ("Gdzie znajduje się warsztat F.W. DRUCIK?",
                 "Warsztat mieści się przy ul. Domosław 13A, 06-120 Winnica, w powiecie pułtuskim "
                 "w województwie mazowieckim. Obsługujemy Winnicę, Pułtusk, Nasielsk, Serock, Płońsk, "
                 "Ciechanów i okoliczne gminy, a przy większych zleceniach dojeżdżamy również dalej."),
                ("Ile kosztuje wycena zlecenia?",
                 "Wstępna wycena jest bezpłatna. Opisz zlecenie telefonicznie: "
                 "601 726 924, mailem na fwdrucik@gmail.com lub przez formularz kontaktowy — odpowiadamy "
                 "w ciągu 24 godzin roboczych."),
                ("Czy realizujecie zlecenia dla firm i osób prywatnych?",
                 "Tak. Obsługujemy osoby prywatne, firmy, gospodarstwa rolne i "
                 "zakłady produkcyjne. Wystawiamy faktury VAT, NIP 888-292-19-00."),
                ("Czy udzielacie gwarancji na wykonane usługi?",
                 "Tak, na każdą wykonaną usługę oraz na zastosowane materiały i podzespoły udzielamy "
                 "gwarancji. Działalność jest objęta ubezpieczeniem OC."),
            ]),
        ],
    ),

    # ------------------------------------------------------------- hub usług
    strona(
        "/uslugi/", "uslugi.html",
        "Usługi warsztatowe i produkcyjne | F.W. DRUCIK Winnica",
        "Elektromechanika, klimatyzacja, spawanie MIG/MAG/TIG/MMA, lutowanie twarde, remonty "
        "silników, maszyny CNC, druk 3D i żywica. Winnica, Pułtusk i okolice.",
        okruszki=[USLUGI], priority="0.9",
    ),

    strona(
        "/uslugi/nadruki-i-sublimacja/", "uslugi-nadruki-i-sublimacja.html",
        "Nadruki i sublimacja — Winnica, Pułtusk | F.W. DRUCIK",
        "Nadruki na odzieży, kubkach i gadżetach firmowych. Metodę dobieramy do materiału, projektu i sposobu użytkowania.",
        okruszki=[USLUGI, ("Nadruki i sublimacja", "/uslugi/nadruki-i-sublimacja/")], priority="0.9",
        dodatkowe=[
            service_ld("Nadruki i sublimacja", "Nadruki na odzieży, kubkach i gadżetach firmowych. Metodę dobieramy do materiału, projektu i sposobu użytkowania.", "/uslugi/nadruki-i-sublimacja/"),
            faq_ld([
                ("Czy można zrobić nadruk na bawełnie?", "Tak. Do bawełny dobieramy technikę odpowiednią do materiału i grafiki, na przykład folię flex lub flock."),
                ("Co nadaje się do sublimacji?", "Najczęściej jasny poliester oraz wyroby z powłoką przeznaczoną do sublimacji. Zgodność konkretnego produktu sprawdzamy przed wyceną."),
            ]),
        ],
    ),

    strona(
        "/uslugi/bezpieczenstwo-obiektow/", "uslugi-bezpieczenstwo-obiektow.html",
        "Bezpieczeństwo obiektów — Winnica, Pułtusk | F.W. DRUCIK",
        "Audyty bezpieczeństwa, centrale alarmowe, monitoring IP, automatyka bram i smart home.",
        okruszki=[USLUGI, ("Bezpieczeństwo obiektów", "/uslugi/bezpieczenstwo-obiektow/")], priority="0.9",
        dodatkowe=[
            service_ld("Bezpieczeństwo obiektów", "Audyty bezpieczeństwa, centrale alarmowe, monitoring IP, automatyka bram i smart home.", "/uslugi/bezpieczenstwo-obiektow/"),
            faq_ld([
                ("Czy można rozbudować istniejący alarm?", "Sprawdzamy centralę, okablowanie i zgodność urządzeń. Na tej podstawie ustalamy, które elementy można wykorzystać."),
                ("Czy audyt może poprzedzić montaż?", "Tak. Podczas audytu ustalamy, które strefy wymagają ochrony i jak ma wyglądać obsługa powiadomień."),
            ]),
        ],
    ),

    strona(
        "/uslugi/budowa-maszyn/", "uslugi-budowa-maszyn.html",
        "Budowa maszyn na zamówienie — Winnica, Pułtusk | F.W. DRUCIK",
        "Projektowanie i budowa pras, rębaków, pieców specjalistycznych i stanowisk zautomatyzowanych pod określony proces.",
        okruszki=[USLUGI, ("Budowa maszyn na zamówienie", "/uslugi/budowa-maszyn/")], priority="0.9",
        dodatkowe=[
            service_ld("Budowa maszyn na zamówienie", "Projektowanie i budowa pras, rębaków, pieców specjalistycznych i stanowisk zautomatyzowanych pod określony proces.", "/uslugi/budowa-maszyn/"),
            faq_ld([
                ("Kiedy powstaje wycena maszyny?", "Po uzgodnieniu wymagań i przygotowaniu projektu. Koszt zależy od konstrukcji, sterowania i zakresu odbioru."),
                ("Czy można zlecić samo toczenie?", "Tak. Na podstawie rysunku, materiału i liczby detali sprawdzamy możliwość wykonania i przygotowujemy wycenę."),
            ]),
        ],
    ),

    strona(
        "/uslugi/programowanie-aplikacje/", "uslugi-programowanie.html",
        "AI-native engineering: aplikacje z agentami AI — Winnica",
        "Aplikacje mobilne Android, automatyzacje w Pythonie, sterowniki ESP32 i serwisy WWW "
        "budowane z agentami AI i testowane na sprzęcie. Winnica, Pułtusk.",
        okruszki=[USLUGI, ("Programowanie & Aplikacje", "/uslugi/programowanie-aplikacje/")],
        priority="0.9",
        dodatkowe=[
            service_ld("Aplikacje mobilne, automatyzacje i sterowniki budowane z AI",
                       "Aplikacje Android, oprogramowanie w Pythonie, sterowniki mikrokontrolerów "
                       "i strony WWW budowane z agentami AI (Claude Code, Codex) i testowane na sprzęcie.",
                       "/uslugi/programowanie-aplikacje/"),
            faq_ld([
                ("Kto pisze kod waszych aplikacji?",
                 "Kod piszą agenci AI (Claude Code, Codex). My opisujemy wymagania, dzielimy pracę na zadania, "
                 "testujemy na urządzeniach i odbieramy tylko działające wersje. Aplikacje Android powstają "
                 "w Kotlinie, automatyzacje w Pythonie, oprogramowanie mikrokontrolerów w C++."),
                ("Czy budujecie oprogramowanie do sterowania maszynami?",
                 "Tak. Z agentami AI budujemy oprogramowanie łączące elektronikę, sterowniki CNC i aplikacje "
                 "Android z fizycznym sprzętem, a działanie sprawdzamy na maszynie."),
            ]),
        ],
    ),

    strona(
        "/uslugi/elektromechanika/", "uslugi-elektromechanika.html",
        "Elektryka pojazdów i maszyn — Winnica, Pułtusk",
        "Naprawa instalacji w samochodach, ciężarówkach i maszynach budowlanych oraz produkcyjnych. Serwis elektronarzędzi i programowanie falowników.",
        okruszki=[USLUGI, ("Elektromechanika", "/uslugi/elektromechanika/")], priority="0.9",
        dodatkowe=[
            service_ld("Elektromechanika pojazdowa i przemysłowa",
                       "Elektryka samochodowa, instalacje maszyn, naprawa elektronarzędzi i programowanie falowników.",
                       "/uslugi/elektromechanika/"),
            faq_ld([
                ("Czy naprawiacie alternatory i rozruszniki?",
                 "Nie przyjmujemy alternatorów ani rozruszników do naprawy lub regeneracji. Diagnozujemy instalacje elektryczne pojazdów."),
                ("Czy diagnozujecie usterki elektryczne w maszynach rolniczych?",
                 "Tak. Zajmujemy się instalacjami w ciągnikach, kombajnach, ładowaczach i przyczepach — "
                 "od przetartych wiązek i przepalonych bezpieczników po sterowniki i czujniki."),
                ("Czy przezwajacie silniki elektryczne?",
                 "Samego przezwojenia nie wykonujemy u siebie — zlecamy je wyspecjalizowanej pracowni "
                 "nawojowej. My diagnozujemy silnik, demontujemy go, a po przezwojeniu składamy, mierzymy "
                 "izolację i uruchamiamy pod obciążeniem. Koszt przezwojenia podajemy przed zleceniem."),
                ("Czy dojeżdżacie do awarii na miejscu?",
                 "Przy awariach maszyn stacjonarnych i instalacji przemysłowych dojeżdżamy na miejsce "
                 "w obrębie powiatu pułtuskiego i sąsiednich gmin. Zakres dojazdu ustalamy telefonicznie."),
                ("Ile trwa diagnostyka instalacji elektrycznej?",
                 "Typowa diagnostyka trwa od 30 do 90 minut. Po jej zakończeniu przedstawiamy zakres "
                 "naprawy i wycenę przed przystąpieniem do prac."),
            ]),
        ],
    ),

    strona(
        "/uslugi/klimatyzacja-samochodowa/", "uslugi-klimatyzacja.html",
        "Serwis klimatyzacji samochodowej — Winnica, Pułtusk",
        "Nabijanie czynnika R134a i R1234yf, wykrywanie nieszczelności, odgrzybianie układu, "
        "wymiana osuszacza i sprężarki. Winnica k. Pułtuska, tel. 601 726 924.",
        okruszki=[USLUGI, ("Klimatyzacja", "/uslugi/klimatyzacja-samochodowa/")],
        priority="0.9",
        dodatkowe=[
            service_ld("Serwis klimatyzacji samochodowej i przemysłowej",
                       "Montaż, serwis i naprawa klimatyzacji: uzupełnianie czynnika chłodniczego, "
                       "diagnostyka szczelności, odgrzybianie układu, wymiana osuszacza, "
                       "zaworu rozprężnego i sprężarki.",
                       "/uslugi/klimatyzacja-samochodowa/"),
            faq_ld([
                ("Jak często należy serwisować klimatyzację w samochodzie?",
                 "Uzupełnienie czynnika i kontrolę szczelności zaleca się raz na 1–2 lata, "
                 "a odgrzybianie układu raz w roku — najlepiej wiosną, przed sezonem."),
                ("Obsługujecie czynnik R1234yf?",
                 "Tak, obsługujemy zarówno starszy czynnik R134a, jak i R1234yf stosowany "
                 "w nowszych samochodach."),
                ("Skąd wiadomo, że klimatyzacja jest nieszczelna?",
                 "Najczęstsze objawy to stopniowy spadek wydajności chłodzenia i konieczność częstego "
                 "uzupełniania czynnika. Nieszczelność wykrywamy próbą ciśnieniową lub barwnikiem UV."),
                ("Nieprzyjemny zapach z nawiewu — co to znaczy?",
                 "To zwykle grzyby i bakterie na parowniku. Pomaga odgrzybianie układu połączone "
                 "z wymianą filtra kabinowego."),
            ]),
        ],
    ),

    strona(
        "/uslugi/spawanie/", "uslugi-spawanie.html",
        "Spawanie MIG, MAG, TIG i MMA — Winnica, Pułtusk",
        "Spawanie stali czarnej, nierdzewnej i aluminium metodami MIG/MAG, TIG i MMA. "
        "Konstrukcje, naprawy maszyn, elementy precyzyjne. Winnica k. Pułtuska.",
        okruszki=[USLUGI, ("Spawanie", "/uslugi/spawanie/")], priority="0.9",
        dodatkowe=[
            service_ld("Usługi spawalnicze MIG, MAG, TIG, MMA",
                       "Spawanie stali konstrukcyjnej, stali nierdzewnej i aluminium metodami "
                       "MIG, MAG, TIG i MMA. Konstrukcje spawane, naprawy maszyn i pojazdów, "
                       "elementy precyzyjne, prace na miejscu u klienta.",
                       "/uslugi/spawanie/"),
            faq_ld([
                ("Spawacie aluminium?",
                 "Tak. Aluminium spawamy metodą TIG (prąd przemienny) oraz MIG — od cienkich blach "
                 "i felg po elementy konstrukcyjne i zbiorniki."),
                ("Czy spawacie stal nierdzewną spożywczą?",
                 "Tak, stal nierdzewną spawamy metodą TIG w osłonie argonu, co pozwala uzyskać czyste, "
                 "gładkie spoiny bez przebarwień — również przy elementach kontaktujących się z żywnością."),
                ("Można przywieźć element do warsztatu?",
                 "Tak, mniejsze elementy przyjmujemy w warsztacie w Domosławiu 13A. Do konstrukcji "
                 "stacjonarnych i napraw maszyn dojeżdżamy na miejsce."),
                ("Jak wyceniane są usługi spawalnicze?",
                 "Wycena zależy od metody, materiału, grubości i długości spoiny oraz od przygotowania "
                 "elementu. Wstępną wycenę podajemy bezpłatnie po opisie lub zdjęciach zlecenia."),
            ]),
        ],
    ),

    strona(
        "/uslugi/lutowanie-twarde/", "uslugi-lutowanie.html",
        "Lutowanie twarde miedzi, mosiądzu i stali | F.W. DRUCIK",
        "Lutowanie twarde lutami srebrnymi: instalacje miedziane, chłodnice, wymienniki, "
        "przewody klimatyzacji. Szczelne połączenia. Winnica, powiat pułtuski.",
        okruszki=[USLUGI, ("Lutowanie twarde", "/uslugi/lutowanie-twarde/")], priority="0.8",
        dodatkowe=[
            service_ld("Lutowanie twarde",
                       "Łączenie elementów miedzianych, mosiężnych i stalowych metodą lutowania "
                       "twardego lutami srebrnymi i mosiężnymi — szczelne połączenia w instalacjach, "
                       "chłodnicach, wymiennikach i układach ciśnieniowych.",
                       "/uslugi/lutowanie-twarde/"),
            faq_ld([
                ("Czym lutowanie twarde różni się od spawania?",
                 "Przy lutowaniu twardym materiał łączonych elementów nie jest topiony — topi się tylko "
                 "spoiwo o temperaturze powyżej 450 °C. Dzięki temu łączy się materiały wrażliwe na "
                 "przegrzanie i różne metale ze sobą, bez odkształcania elementów."),
                ("Czy lutowane połączenie wytrzyma ciśnienie?",
                 "Tak. Prawidłowo wykonane złącze lutowane lutem srebrnym jest szczelne i wytrzymuje "
                 "ciśnienia robocze typowe dla instalacji chłodniczych i klimatyzacyjnych."),
                ("Naprawiacie chłodnice i przewody klimatyzacji?",
                 "Tak, lutujemy chłodnice, wymienniki, rurki miedziane i aluminiowe przewody układów "
                 "klimatyzacji — również w połączeniu z serwisem klimatyzacji."),
            ]),
        ],
    ),

    strona(
        "/uslugi/remonty-silnikow/", "uslugi-remonty-silnikow.html",
        "Remont i regeneracja silników — Winnica, Pułtusk",
        "Wymiana uszczelki pod głowicą, regeneracja głowic, wymiana rozrządu, remont "
        "kapitalny. Silniki osobowe, rolnicze i stacjonarne. Winnica k. Pułtuska.",
        okruszki=[USLUGI, ("Remonty silników", "/uslugi/remonty-silnikow/")], priority="0.9",
        dodatkowe=[
            service_ld("Remonty i regeneracja silników spalinowych",
                       "Naprawa i regeneracja silników spalinowych — od diagnostyki kompresji "
                       "i wymiany uszczelki pod głowicą po remont kapitalny z wymianą tłoków, "
                       "panewek i regeneracją głowicy.",
                       "/uslugi/remonty-silnikow/"),
            faq_ld([
                ("Jakie silniki remontujecie?",
                 "Silniki benzynowe i wysokoprężne w samochodach osobowych i dostawczych, ciągnikach "
                 "i maszynach rolniczych, a także silniki stacjonarne — agregaty, pompy, sprężarki."),
                ("Jak długo trwa remont silnika?",
                 "Prostsza naprawa, jak wymiana uszczelki pod głowicą, to zwykle 2–4 dni robocze. "
                 "Remont kapitalny trwa dłużej i zależy od dostępności części oraz zakresu obróbki."),
                ("Czy po remoncie jest gwarancja?",
                 "Tak, na wykonaną pracę i zastosowane części udzielamy gwarancji. Warunki ustalamy "
                 "indywidualnie w zależności od zakresu remontu."),
                ("Skąd wiadomo, że silnik kwalifikuje się do remontu?",
                 "Typowe objawy to spadek mocy, nadmierne spalanie oleju, dymienie, stukanie i niska "
                 "kompresja. Wykonujemy pomiar kompresji i próbę szczelności przed decyzją o zakresie prac."),
            ]),
        ],
    ),

    strona(
        "/uslugi/maszyny-cnc/", "uslugi-cnc.html",
        "Budowa maszyn CNC na zamówienie | F.W. DRUCIK",
        "Projektowanie i budowa maszyn CNC: frezarki, plotery, automatyka, modernizacja "
        "obrabiarek. Konstrukcja, elektronika, sterowanie i uruchomienie. Mazowieckie.",
        okruszki=[USLUGI, ("Budowa maszyn CNC", "/uslugi/maszyny-cnc/")], priority="0.9",
        dodatkowe=[
            service_ld("Projektowanie i budowa maszyn CNC",
                       "Budowa maszyn CNC na zamówienie: frezarki, plotery, obrabiarki i stanowiska "
                       "zautomatyzowane. Konstrukcja mechaniczna, elektronika, sterowanie, "
                       "uruchomienie i serwis. Modernizacja i retrofit istniejących maszyn.",
                       "/uslugi/maszyny-cnc/"),
            faq_ld([
                ("Budujecie maszyny od zera czy modernizujecie istniejące?",
                 "Robimy jedno i drugie. Budujemy maszyny od projektu po uruchomienie, a także "
                 "modernizujemy starsze obrabiarki — wymiana sterowania, napędów i elektroniki."),
                ("Ile kosztuje maszyna CNC na zamówienie?",
                 "Cena zależy od pola roboczego, sztywności konstrukcji, rodzaju napędów i sterowania. "
                 "Po rozmowie o zastosowaniu przygotowujemy koncepcję i wycenę bezpłatnie."),
                ("Czy szkolicie z obsługi gotowej maszyny?",
                 "Tak. Przy odbiorze przekazujemy dokumentację i przeprowadzamy szkolenie z obsługi "
                 "oraz podstawowej konserwacji maszyny."),
                ("Jak długo trwa budowa maszyny?",
                 "Od kilku tygodni przy prostszych ploterach do kilku miesięcy przy rozbudowanych "
                 "stanowiskach. Termin ustalamy na etapie wyceny."),
            ]),
        ],
    ),

    strona(
        "/brelok/", "brelok.html",
        "Brelok z imieniem lub rejestracją — druk 3D | F.W. DRUCIK",
        "Brelok w stylu tablicy rejestracyjnej z Twoim napisem do 8 znaków. Druk 3D w trzech "
        "kolorach, 19,99 zł, komplet 3 szt. 44,99 zł. Wysyłka do 2 dni roboczych.",
        okruszki=[("Brelok z imieniem", "/brelok/")], priority="0.7",
        dodatkowe=[
            faq_ld([
                ("Ile znaków zmieści się na breloku?",
                 "Do 8, razem ze spacją i myślnikiem."),
                ("Czy mogę zamówić różne napisy w komplecie?",
                 "Tak. Komplet to 3 breloki, każdy z innym napisem, wpisanym po przecinku."),
                ("Czy wystawiacie fakturę?",
                 "Sprzedawca jest zwolniony z VAT. Na życzenie wystawimy rachunek."),
                ("Jak szybko dostanę brelok?",
                 "Wysyłamy do 2 dni roboczych od potwierdzenia napisu."),
            ]),
        ],
    ),

    strona(
        "/uslugi/druk-3d/", "uslugi-druk-3d.html",
        "Druk 3D i skanowanie 3D na zamówienie | F.W. DRUCIK",
        "Druk 3D prototypów i części zamiennych oraz skanowanie 3D. Odtwarzamy części "
        "wycofane z produkcji. PLA, PETG, ABS, ASA. Wysyłka w całej Polsce.",
        okruszki=[USLUGI, ("Druk i skan 3D", "/uslugi/druk-3d/")], priority="0.9",
        dodatkowe=[
            service_ld("Druk 3D i skanowanie 3D",
                       "Druk 3D prototypów, części zamiennych, modeli i elementów użytkowych oraz "
                       "skanowanie 3D obiektów do dalszej obróbki cyfrowej i odtwarzania części.",
                       "/uslugi/druk-3d/"),
            faq_ld([
                ("Odtworzycie część, której nie ma już w sprzedaży?",
                 "Tak. Skanujemy oryginał lub odtwarzamy geometrię z pomiarów, przygotowujemy model 3D "
                 "i drukujemy część. Przy elementach obciążonych dobieramy materiał o odpowiedniej "
                 "wytrzymałości lub proponujemy wykonanie z metalu."),
                ("Z jakich materiałów drukujecie?",
                 "Standardowo z PLA, PETG, ABS i ASA. Do części pracujących na zewnątrz lub w wyższej "
                 "temperaturze dobieramy materiał odporny na UV i ciepło."),
                ("Nie mam modelu 3D — co wtedy?",
                 "Wystarczy fizyczny wzór, zdjęcia z wymiarami albo rysunek. Model przygotowujemy u siebie."),
                ("Ile kosztuje wydruk 3D?",
                 "Ceny prostych elementów zaczynają się od 30 zł. Koszt zależy od objętości, materiału, "
                 "wypełnienia i czasu druku — wycenę podajemy po otrzymaniu modelu lub wymiarów."),
            ]),
        ],
    ),

    strona(
        "/uslugi/zywica-epoksydowa/", "uslugi-zywica.html",
        "Żywica epoksydowa — stoły River Table i blaty na zamówienie",
        "Stoły River Table, blaty, podkładki, deski do serwowania i ozdoby z żywicy "
        "epoksydowej. Ręczne wykonanie, drewno łączone z żywicą. Winnica k. Pułtuska.",
        okruszki=[USLUGI, ("Żywica epoksydowa", "/uslugi/zywica-epoksydowa/")], priority="0.8",
        dodatkowe=[
            service_ld("Wyroby z żywicy epoksydowej na zamówienie",
                       "Odlewy artystyczne i użytkowe z żywicy epoksydowej: stoły River Table, blaty, "
                       "podkładki, deski do serwowania, ozdoby i elementy dekoracyjne wykonywane "
                       "na indywidualne zamówienie.",
                       "/uslugi/zywica-epoksydowa/"),
            faq_ld([
                ("Ile trwa wykonanie stołu River Table?",
                 "Zwykle 3–5 tygodni. Największą część czasu zajmuje sezonowanie drewna, utwardzanie "
                 "żywicy oraz szlifowanie i polerowanie blatu."),
                ("Czy blat z żywicy jest odporny na gorące naczynia?",
                 "Żywica epoksydowa dobrze znosi codzienne użytkowanie, ale nie należy stawiać na niej "
                 "bezpośrednio gorących garnków. Zalecamy podkładki — tak jak przy blatach lakierowanych."),
                ("Można zamówić blat w wybranym kolorze?",
                 "Tak. Dobieramy barwniki, pigmenty perłowe i efekty przejrzyste lub matowe pod projekt "
                 "wnętrza. Przed wykonaniem przygotowujemy próbkę koloru."),
                ("Wysyłacie gotowe wyroby?",
                 "Drobne wyroby wysyłamy kurierem. Duże blaty i stoły najlepiej odebrać osobiście lub "
                 "ustalić transport — zabezpieczamy je wtedy do przewozu."),
            ]),
        ],
    ),

    # ------------------------------------------------------------- koszulki, bez oferty do zatwierdzenia
    strona(
        "/koszulki/", "koszulki.html",
        "Koszulki z nadrukiem — w przygotowaniu | F.W. DRUCIK",
        "Autorskie koszulki z nadrukami F.W. DRUCIK. Pierwsza seria przechodzi próby jakości; sprzedaż nie jest jeszcze uruchomiona.",
        okruszki=[("Koszulki", "/koszulki/")],
        robots="noindex,follow", noindex=True,
    ),

    # ------------------------------------------------------------- firma
    strona(
        "/o-nas/", "o-nas.html",
        "Dawid Tutak — inżynier i mechanik roku | F.W. DRUCIK",
        "Dawid Tutak: inżynier Politechniki Łódzkiej, mechanik konstruktor i elektromechanik, "
        "dwukrotny Mechanik Roku powiatu pułtuskiego. Warsztat w Winnicy.",
        okruszki=[("O nas", "/o-nas/")], priority="0.8",
    ),

    strona(
        "/realizacje/", "realizacje.html",
        "Realizacje — konstrukcje, maszyny CNC, wydruki 3D | DRUCIK",
        "Konstrukcje i stelaże spawane, maszyny CNC na zamówienie, wydruki 3D, naprawy maszyn "
        "rolniczych i blaty z żywicy. Zobacz, co robimy w warsztacie w Winnicy.",
        okruszki=[("Realizacje", "/realizacje/")], priority="0.8", changefreq="weekly",
    ),

    strona(
        "/sklep/", "sklep.html",
        "Sklep — River Table, wydruki 3D, konstrukcje na zamówienie",
        "Stoły River Table od 890 zł, deski i podkładki od 120 zł, prototypy 3D od 30 zł, "
        "stelaże spawane i elementy CNC. Zamówienia telefonicznie lub mailem.",
        okruszki=[("Sklep", "/sklep/")], priority="0.8", changefreq="weekly",
        # Katalog powstaje w bazie, wiec strone sklada skrypt na serwerze —
        # build.py nie zapisuje dla tego adresu wlasnego index.html.
        php="sklep-lista.php",
        # Dopoki sklep jest w przebudowie, strona oddaje noindex. Zgloszenie
        # jej w mapie serwisu dawaloby w Search Console blad "adres oznaczony
        # jako noindex". Przy otwarciu sklepu skasuj te dwie linie —
        # opisane w api/PLATNOSCI.md, punkt 6.
        noindex=True,
        dodatkowe=[{
            "@type": "ItemList",
            "name": "Produkty F.W. DRUCIK",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "item": {
                    "@type": "Product", "name": "Stolik River Table — dąb i żywica epoksydowa",
                    "description": "Ręcznie wykonany stolik z blatem dębowym zalanym żywicą epoksydową.",
                    "brand": {"@type": "Brand", "name": "F.W. DRUCIK"},
                    "offers": {"@type": "Offer", "price": "890", "priceCurrency": "PLN",
                               "availability": "https://schema.org/InStock",
                               "url": SITE + "/sklep/",
                               "seller": {"@id": SITE + "/#organizacja"}}}},
                {"@type": "ListItem", "position": 2, "item": {
                    "@type": "Product", "name": "Podkładki i deski do serwowania z żywicy",
                    "description": "Deski i podkładki z drewna łączonego z żywicą epoksydową.",
                    "brand": {"@type": "Brand", "name": "F.W. DRUCIK"},
                    "offers": {"@type": "Offer", "price": "120", "priceCurrency": "PLN",
                               "availability": "https://schema.org/InStock",
                               "url": SITE + "/sklep/",
                               "seller": {"@id": SITE + "/#organizacja"}}}},
                {"@type": "ListItem", "position": 3, "item": {
                    "@type": "Product", "name": "Prototypy i części zamienne z druku 3D",
                    "description": "Wydruki 3D prototypów i części zamiennych na indywidualne zamówienie.",
                    "brand": {"@type": "Brand", "name": "F.W. DRUCIK"},
                    "offers": {"@type": "Offer", "price": "30", "priceCurrency": "PLN",
                               "availability": "https://schema.org/InStock",
                               "url": SITE + "/sklep/",
                               "seller": {"@id": SITE + "/#organizacja"}}}},
            ],
        }],
    ),

    strona(
        "/automatyzacje/", "automatyzacje.html",
        "Automatyzacja AI dla firm i wdrożenia n8n | F.W. DRUCIK",
        "Wdrożenia n8n, integracje CRM i ERP oraz agenci AI na zamówienie. "
        "Przykłady dla małych, średnich i dużych firm, szkolenie pracownika i opieka po wdrożeniu.",
        okruszki=[("Automatyzacja AI dla firm", "/automatyzacje/")],
        priority="0.9", changefreq="monthly",
        dodatkowe=[
            service_ld("Automatyzacja procesów, wdrożenia n8n i agenci AI dla firm",
                       "Audyt i pilotaż procesu, integracje CRM i ERP, agenci AI na zamówienie, "
                       "szkolenie pracowników oraz uzgodnione wsparcie techniczne i merytoryczne.",
                       "/automatyzacje/"),
        ],
    ),

    strona(
        "/blog/n8n-pierwsza-automatyzacja-w-firmie/", "blog-n8n-pierwsza-automatyzacja-w-firmie.html",
        "n8n w firmie. Pierwsza automatyzacja krok po kroku",
        "Jak zaprojektować pierwszą automatyzację n8n w firmie. Zbieranie zgłoszeń, zapis bez duplikatów, "
        "obsługa błędów i akceptacja odpowiedzi przez pracownika.",
        okruszki=[("Blog", "/blog/"), ("Pierwsza automatyzacja n8n", "/blog/n8n-pierwsza-automatyzacja-w-firmie/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/konsultacje/", "konsultacje.html",
        "Konsultacje techniczne przez telefon | F.W. DRUCIK",
        "Platna konsultacja telefoniczna dla mechanikow i warsztatow: magistrale CAN "
        "i J1939, UDS, sterowniki, klimatyzacja, spawanie aluminium. Od 120 zl.",
        okruszki=[("Konsultacje", "/konsultacje/")], priority="0.9", changefreq="monthly",
        dodatkowe=[
            service_ld("Konsultacje techniczne przez telefon",
                       "Platna konsultacja telefoniczna dla mechanikow, diagnostow i warsztatow "
                       "— diagnostyka magistral pojazdowych, sterownikow, klimatyzacji, "
                       "spawania aluminium i budowy maszyn CNC.",
                       "/konsultacje/"),
            faq_ld([
                ("Ile kosztuje konsultacja telefoniczna?",
                 "Trzydziesci minut kosztuje 120 zl, godzina 200 zl, a pakiet trzech godzin "
                 "do wykorzystania przez pol roku — 500 zl. Do kazdej konsultacji wystawiam fakture VAT."),
                ("Jak wyglada platnosc?",
                 "Najpierw opisujesz problem w formularzu. Potwierdzam termin i dopiero wtedy "
                 "wysylam dane do przelewu. Jesli widze, ze nie pomoge, mowie to od razu i nie biore pieniedzy."),
                ("Co jesli nie odbiore telefonu?",
                 "Dzwonie jeszcze dwa razy w ciagu godziny. Jesli nie uda sie w ogole, "
                 "przekladamy rozmowe na inny termin bez zadnej doplaty."),
                ("Czy dostane cos na pismie po rozmowie?",
                 "Tak. Po konsultacji wysylam mailem podsumowanie: kolejnosc pomiarow, wartosci "
                 "do sprawdzenia i linki do dokumentacji, zeby nie trzeba bylo notowac w trakcie."),
            ]),
        ],
    ),

    strona(
        "/obszar-dzialania/", "obszar-dzialania.html",
        "Obszar działania — Winnica, Pułtusk, Nasielsk, Serock",
        "Pracujemy w gminie Winnica, Pułtusku, Nasielsku, Serocku, Płońsku, Ciechanowie "
        "i okolicy. Warsztat w Domosławiu, dojazd do awarii w powiecie pułtuskim.",
        okruszki=[("Obszar działania", "/obszar-dzialania/")], priority="0.7",
    ),

    strona(
        "/kontakt/", "kontakt.html",
        "Kontakt — F.W. DRUCIK, Winnica | tel. 601 726 924",
        "Domosław 13A, 06-120 Winnica, tel. 601 726 924, fwdrucik@gmail.com. Pon–Pt 8–17, "
        "Sob 9–13. Bezpłatna wycena, odpowiedź w 24 h roboczych.",
        okruszki=[("Kontakt", "/kontakt/")], priority="0.9",
        dodatkowe=[{
            "@type": "ContactPage",
            "url": SITE + "/kontakt/",
            "name": "Kontakt — F.W. DRUCIK",
            "about": {"@id": SITE + "/#organizacja"},
        }],
    ),

    strona(
        "/polityka-prywatnosci/", "polityka-prywatnosci.html",
        "Polityka prywatności i cookies — F.W. DRUCIK",
        "Zasady przetwarzania danych osobowych i plików cookies w serwisie fwdrucik.pl. "
        "Administrator, cel przetwarzania, prawa użytkownika, kontakt.",
        okruszki=[("Polityka prywatności", "/polityka-prywatnosci/")], priority="0.2",
        changefreq="yearly",
    ),

    # ------------------------------------------------------------- Blog & Forum
    strona(
        "/blog/", "blog.html",
        "Blog techniczny i poradniki — F.W. DRUCIK Winnica",
        "Poradniki techniczne z elektromechaniki, diagnostyki alternatorów, spawalnictwa MIG/TIG, "
        "obróbki CNC i klimatyzacji w Winnicy i Pułtusku.",
        okruszki=[("Blog", "/blog/")], priority="0.8", changefreq="weekly",
    ),

    strona(
        "/blog/sublimacja-a-flex/", "blog-sublimacja-a-flex.html",
        "Sublimacja, flex i flock — dobór nadruku | F.W. DRUCIK",
        "Skład tkaniny i kształt projektu pomagają wybrać metodę jeszcze przed wyceną.",
        okruszki=[("Blog", "/blog/"), ("Sublimacja, flex czy flock? Jak dobrać nadruk do materiału", "/blog/sublimacja-a-flex/")],
        priority="0.8",
    ),

    strona(
        "/blog/audyt-alarmu-i-monitoringu/", "blog-audyt-alarmu-i-monitoringu.html",
        "Audyt alarmu i monitoringu przed montażem | F.W. DRUCIK",
        "Zacznij od stref i sposobu reagowania na alarm. To porządkuje wybór sprzętu.",
        okruszki=[("Blog", "/blog/"), ("Audyt alarmu i monitoringu. Co ustalić przed montażem", "/blog/audyt-alarmu-i-monitoringu/")],
        priority="0.8",
    ),

    strona(
        "/blog/zalozenia-do-budowy-maszyny/", "blog-zalozenia-do-budowy-maszyny.html",
        "Budowa maszyny — dane do wyceny | F.W. DRUCIK",
        "Opis materiału, cyklu i odbioru daje konstruktorowi więcej niż sama nazwa maszyny.",
        okruszki=[("Blog", "/blog/"), ("Założenia do budowy maszyny. Co opisać przed wyceną", "/blog/zalozenia-do-budowy-maszyny/")],
        priority="0.8",
    ),

    strona(
        "/blog/regeneracja-alternatorow-pultusk/", "blog-regeneracja-alternatorow.html",
        "Regeneracja alternatorów i rozruszników — poradnik",
        "Kiedy opłaca się regenerować alternator i rozrusznik? Poradnik elektromechanika "
        "z Winnicy k. Pułtuska. Pomiary, tętnienia i porównanie kosztów.",
        okruszki=[("Blog", "/blog/"), ("Regeneracja alternatorów", "/blog/regeneracja-alternatorow-pultusk/")],
        priority="0.8",
    ),

    strona(
        "/blog/spawanie-tig-aluminium-vs-mig/", "blog-spawanie-tig-aluminium.html",
        "Spawanie TIG aluminium vs MIG — poradnik i spoiny",
        "Porównanie technik spawalniczych TIG i MIG aluminium. Naprawa felg, misek "
        "olejowych i obudów w Winnicy k. Pułtuska.",
        okruszki=[("Blog", "/blog/"), ("Spawanie TIG aluminium", "/blog/spawanie-tig-aluminium-vs-mig/")],
        priority="0.8",
    ),

    strona(
        "/blog/klimatyzacja-samochodowa-r134a-vs-r1234yf/", "blog-klimatyzacja-r134a-r1234yf.html",
        "Serwis klimatyzacji: Czynnik R134a vs R1234yf — Winnica",
        "Poradnik serwisu klimatyzacji samochodowej. Nabijanie czynnika R134a i R1234yf, "
        "odgrzybianie i wykrywanie nieszczelności w Winnicy.",
        okruszki=[("Blog", "/blog/"), ("Serwis klimatyzacji R134a/R1234yf", "/blog/klimatyzacja-samochodowa-r134a-vs-r1234yf/")],
        priority="0.8",
    ),

    strona(
        "/blog/magistrala-can-diagnostyka/", "blog-magistrala-can-diagnostyka.html",
        "Magistrala CAN — jak działa i jak ją zdiagnozować",
        "Warstwa fizyczna CAN, ramka i arbitraż oraz pomiary warsztatowe: 60 Ω na złączu OBD, "
        "napięcia CAN_H i CAN_L, typowe usterki i czego przy magistrali nie robić.",
        okruszki=[("Blog", "/blog/"), ("Magistrala CAN", "/blog/magistrala-can-diagnostyka/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/sterowniki-ecu-vecu-ebs-ecas/", "blog-sterowniki-ecu-vecu-ebs-ecas.html",
        "ECU, VECU, EBS, ECAS i VDC — sterowniki w ciężarówce",
        "Co robi każdy moduł w pojeździe użytkowym, jak są spięte magistralą J1939 i ISO 11992 "
        "oraz dlaczego wymiana sterownika bez kalibracji nic nie daje.",
        okruszki=[("Blog", "/blog/"), ("Sterowniki w pojazdach użytkowych", "/blog/sterowniki-ecu-vecu-ebs-ecas/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/rs485-modbus-rtu/", "blog-rs485-modbus-rtu.html",
        "RS-485 i Modbus RTU — okablowanie, terminacja, błędy",
        "Topologia łańcucha, terminacja 120 Ω, rezystory polaryzujące i masa odniesienia. "
        "Do tego ramka Modbus RTU, kody funkcji i dziesięć typowych błędów instalacji.",
        okruszki=[("Blog", "/blog/"), ("RS-485 i Modbus RTU", "/blog/rs485-modbus-rtu/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/kurs-esp32-arduino-czesc-1/", "blog-kurs-esp32-arduino-czesc-1.html",
        "Kurs ESP32 i Arduino cz. 1 — wybór płytki i podstawy",
        "Porównanie Arduino Uno, Uno R4 i ESP32, pułapki napięć 3,3 V, pierwsze wejścia "
        "i wyjścia oraz zasilanie mikrokontrolera w pojeździe i w szafie sterowniczej.",
        okruszki=[("Blog", "/blog/"), ("Kurs ESP32 i Arduino, część 1", "/blog/kurs-esp32-arduino-czesc-1/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/klimatyzacja-cisnienia-procedura/", "blog-klimatyzacja-cisnienia-procedura.html",
        "Ciśnienia w klimatyzacji — tabela i procedura serwisu",
        "Tabela ciśnień nasycenia R134a, interpretacja wskazań manometrów, pełna procedura "
        "obsługi układu, dobór oleju oraz przepisy o czynnikach chłodniczych.",
        okruszki=[("Blog", "/blog/"), ("Ciśnienia w klimatyzacji", "/blog/klimatyzacja-cisnienia-procedura/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/ai-w-programowaniu-cnc/", "blog-ai-w-programowaniu-cnc.html",
        "AI w programowaniu maszyn CNC — co realnie działa",
        "Ścieżki adaptacyjne, monitorowanie zużycia narzędzia i modele językowe a G-code. "
        "Gdzie sztuczna inteligencja pomaga w obróbce, a gdzie tylko brzmi dobrze.",
        okruszki=[("Blog", "/blog/"), ("AI w programowaniu CNC", "/blog/ai-w-programowaniu-cnc/")],
        priority="0.8", og_type="article",
    ),

        strona(
        "/blog/magistrala-lin-w-pojazdach-diagnostyka/", "blog-magistrala-lin-w-pojazdach-diagnostyka.html",
        "Magistrala LIN w pojazdach: diagnostyka i rola - F.W. DRUCIK",
        "Dowiedz się, czym jest magistrala LIN, dlaczego uzupełnia sieć CAN i jak poprawnie diagnozować jej usterki w warsztacie samochodowym.",
        okruszki=[("Blog", "/blog/"), ("Magistrala LIN w pojazdach: rola i diagnostyka", "/blog/magistrala-lin-w-pojazdach-diagnostyka/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/flexray-i-automotive-ethernet-sieci-pokladowe/", "blog-flexray-i-automotive-ethernet-sieci-pokladowe.html",
        "FlexRay i Automotive Ethernet w diagnostyce | F.W. DRUCIK",
        "Analiza techniczna standardów FlexRay oraz Automotive Ethernet w nowoczesnych pojazdach. Dowiedz się, jak ewoluuje diagnostyka sieci pokładowych.",
        okruszki=[("Blog", "/blog/"), ("FlexRay i Automotive Ethernet", "/blog/flexray-i-automotive-ethernet-sieci-pokladowe/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/diagnostyka-j1939-ciezarowki/", "blog-diagnostyka-j1939-ciezarowki.html",
        "Diagnostyka J1939 w ciężarówkach — PGN, SPN, FMI",
        "Techniczne wprowadzenie do diagnostyki magistrali CAN J1939. Wyjaśniamy strukturę PGN, SPN i FMI w ciężarówkach. Sprawdź jak czytać ramki danych.",
        okruszki=[("Blog", "/blog/"), ("Diagnostyka J1939 w ciężarówkach: PGN, SPN i FMI", "/blog/diagnostyka-j1939-ciezarowki/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/uds-iso-14229-diagnostyka-warsztatowa/", "blog-uds-iso-14229-diagnostyka-warsztatowa.html",
        "UDS (ISO 14229) — diagnostyka i kody NRC",
        "Praktyczny przewodnik po protokole UDS ISO 14229 dla mechaników. Zrozum sesje diagnostyczne, kody NRC i obsługę błędów w nowoczesnych sterownikach.",
        okruszki=[("Blog", "/blog/"), ("UDS (ISO 14229)", "/blog/uds-iso-14229-diagnostyka-warsztatowa/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/diagnostyka-czujnikow-oscyloskopem/", "blog-diagnostyka-czujnikow-oscyloskopem.html",
        "Diagnostyka czujników: indukcyjne, Halla, PWM, SENT | DRUCIK",
        "Analiza sygnałów czujników samochodowych na oscyloskopie. Jak odróżnić czujnik indukcyjny, Halla, PWM i SENT w praktyce warsztatowej F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("Diagnostyka czujników", "/blog/diagnostyka-czujnikow-oscyloskopem/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/sterowniki-bcm-i-siec-komfortu/", "blog-sterowniki-bcm-i-siec-komfortu.html",
        "Sterowniki BCM i sieć komfortu: diagnostyka usterek | DRUCIK",
        "Analiza techniczna usterek modułów BCM, zwarć w wiązkach i diagnostyki sieci komfortu. Wskazówki dla mechaników i techników utrzymania ruchu.",
        okruszki=[("Blog", "/blog/"), ("Sterowniki BCM i sieć komfortu", "/blog/sterowniki-bcm-i-siec-komfortu/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/retarder-tempomat-skrzynia-amt-komunikacja-can/", "blog-retarder-tempomat-skrzynia-amt-komunikacja-can.html",
        "Retarder, tempomat, skrzynia AMT: komunikacja CAN | DRUCIK",
        "Analiza techniczna wymiany danych w magistrali CAN między retarderem, tempomatem a skrzynią biegów AMT. Wskazówki diagnostyczne dla mechaników.",
        okruszki=[("Blog", "/blog/"), ("Retarder, tempomat, skrzynia AMT", "/blog/retarder-tempomat-skrzynia-amt-komunikacja-can/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/zasilanie-24v-pojazdy-ciezarowe/", "blog-zasilanie-24v-pojazdy-ciezarowe.html",
        "Zasilanie 24V w ciężarówkach: diagnostyka spadków napięć",
        "Poradnik techniczny dla mechaników: jak diagnozować spadki napięć w instalacjach 24V, rola masy i pomiary pod obciążeniem w pojazdach ciężarowych.",
        okruszki=[("Blog", "/blog/"), ("Diagnostyka instalacji 24V w pojazdach", "/blog/zasilanie-24v-pojazdy-ciezarowe/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/materialy-do-druku-3d-w-warsztacie/", "blog-materialy-do-druku-3d-w-warsztacie.html",
        "Materiały do druku 3D — PLA, PETG, ABS, ASA i PA-CF",
        "Analiza techniczna materiałów do druku 3D: PLA, PETG, ABS, ASA oraz PA-CF pod kątem zastosowań w warsztacie mechanicznym. Właściwości i dobór tworzyw.",
        okruszki=[("Blog", "/blog/"), ("Materiały do druku 3D w warsztacie", "/blog/materialy-do-druku-3d-w-warsztacie/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/modele-jezykowe-w-diagnostyce-pojazdow/", "blog-modele-jezykowe-w-diagnostyce-pojazdow.html",
        "Modele językowe w diagnostyce: możliwości i ograniczenia",
        "Analiza przydatności modeli językowych w pracy diagnosty. Sprawdź, w jakich zadaniach AI wspiera serwis, a gdzie stanowi zagrożenie dla bezpieczeństwa.",
        okruszki=[("Blog", "/blog/"), ("Modele językowe w serwisie", "/blog/modele-jezykowe-w-diagnostyce-pojazdow/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/skanowanie-3d-uszkodzonej-czesci/", "blog-skanowanie-3d-uszkodzonej-czesci.html",
        "Skanowanie 3D uszkodzonych części - F.W. DRUCIK",
        "Techniczne aspekty skanowania 3D uszkodzonych elementów maszyn. Od chmury punktów do modelu CAD. Dowiedz się jak odtworzyć geometrię w F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("Skanowanie 3D uszkodzonej części", "/blog/skanowanie-3d-uszkodzonej-czesci/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/dobor-parametrow-skrawania/", "blog-dobor-parametrow-skrawania.html",
        "Parametry skrawania — obroty, posuw i głębokość",
        "Techniczne aspekty doboru prędkości skrawania, posuwu na ostrze i zagłębienia. Wskazówki dla operatorów obrabiarek CNC w warsztacie F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("Dobór parametrów skrawania", "/blog/dobor-parametrow-skrawania/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/wizja-komputerowa-w-kontroli-jakosci/", "blog-wizja-komputerowa-w-kontroli-jakosci.html",
        "Wizja komputerowa w kontroli jakości detali | F.W. DRUCIK",
        "Sprawdź, jak wdrożyć podstawowe systemy wizyjne do kontroli jakości detali w warsztacie i produkcji, wykorzystując dostępne narzędzia i wiedzę techniczną.",
        okruszki=[("Blog", "/blog/"), ("Wizja komputerowa w kontroli jakości detali", "/blog/wizja-komputerowa-w-kontroli-jakosci/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/retrofit-frezarki-cnc-od-czego-zaczac/", "blog-retrofit-frezarki-cnc-od-czego-zaczac.html",
        "Retrofit frezarki na CNC: przewodnik techniczny | F.W. DRUCIK",
        "Dowiedz się, jak technicznie podejść do modernizacji starej frezarki na sterowanie CNC. Analiza napędów, sterowników i wymogów bezpieczeństwa w F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("Retrofit starej frezarki na sterowanie CNC", "/blog/retrofit-frezarki-cnc-od-czego-zaczac/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/predykcyjne-utrzymanie-ruchu-pomiary/", "blog-predykcyjne-utrzymanie-ruchu-pomiary.html",
        "Predykcyjne utrzymanie ruchu: pomiary drgań i temperatury",
        "Dowiedz się, jak diagnostyka drgań i temperatury pozwala na predykcyjne utrzymanie ruchu w maszynach. Unikaj awarii dzięki analizie danych technicznych.",
        okruszki=[("Blog", "/blog/"), ("Predykcyjne utrzymanie ruchu", "/blog/predykcyjne-utrzymanie-ruchu-pomiary/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/kurs-esp32-czesc-2-wifi-mqtt/", "blog-kurs-esp32-czesc-2-wifi-mqtt.html",
        "Kurs ESP32 cz. 2: Wi-Fi i MQTT w warsztacie | F.W. DRUCIK",
        "Druga część kursu ESP32. Konfiguracja Wi-Fi, protokół MQTT i przesyłanie danych z czujników w warsztacie. Praktyczne wskazówki dla automatyków.",
        okruszki=[("Blog", "/blog/"), ("Kurs ESP32 część 2", "/blog/kurs-esp32-czesc-2-wifi-mqtt/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/python-dla-mechanika-pierwszy-skrypt/", "blog-python-dla-mechanika-pierwszy-skrypt.html",
        "Python dla mechanika: pierwszy skrypt obliczeniowy | DRUCIK",
        "Wprowadzenie do Pythona dla mechaników i techników utrzymania ruchu. Naucz się pisać proste skrypty do obliczeń technicznych w warsztacie.",
        okruszki=[("Blog", "/blog/"), ("Python od zera dla mechanika", "/blog/python-dla-mechanika-pierwszy-skrypt/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/dht22-aht20-pomiar-temperatury-wilgotnosci/", "blog-dht22-aht20-pomiar-temperatury-wilgotnosci.html",
        "DHT22 i AHT20: Pomiar warunków w hali | F.W. DRUCIK",
        "Analiza techniczna czujników DHT22 i AHT20 w zastosowaniach warsztatowych. Sprawdź specyfikację, dokładność pomiarową i integrację z systemami kontroli.",
        okruszki=[("Blog", "/blog/"), ("DHT22 i AHT20", "/blog/dht22-aht20-pomiar-temperatury-wilgotnosci/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/ds18b20-wiele-czujnikow-na-jednym-przewodzie/", "blog-ds18b20-wiele-czujnikow-na-jednym-przewodzie.html",
        "DS18B20: magistrala 1-Wire w praktyce warsztatowej | DRUCIK",
        "Analiza techniczna czujników DS18B20. Jak poprawnie łączyć wiele sensorów na jednej magistrali 1-Wire, zasady zasilania i diagnostyka sygnału.",
        okruszki=[("Blog", "/blog/"), ("DS18B20", "/blog/ds18b20-wiele-czujnikow-na-jednym-przewodzie/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/spawanie-aluminium-mig-podajnik-spool-gun-drut/", "blog-spawanie-aluminium-mig-podajnik-spool-gun-drut.html",
        "Spawanie aluminium metodą MIG: podajnik i uchwyt spool gun",
        "Techniczne aspekty spawania aluminium metodą MIG. Wybór podajnika, rola uchwytu spool gun oraz specyfika prowadzenia drutu miękkiego w warsztacie.",
        okruszki=[("Blog", "/blog/"), ("Spawanie aluminium metodą MIG: wyzwania techn…", "/blog/spawanie-aluminium-mig-podajnik-spool-gun-drut/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/tig-ac-balans-i-czestotliwosc-aluminium/", "blog-tig-ac-balans-i-czestotliwosc-aluminium.html",
        "TIG AC: Dobór balansu i częstotliwości - F.W. DRUCIK",
        "Techniczne aspekty spawania aluminium metodą TIG AC. Jak ustawić balans i częstotliwość, aby uzyskać stabilny łuk i odpowiednie wtopienie.",
        okruszki=[("Blog", "/blog/"), ("TIG AC: Dobór balansu i częstotliwości przy s…", "/blog/tig-ac-balans-i-czestotliwosc-aluminium/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/elektrody-wolframowe-dobor-szlifowanie/", "blog-elektrody-wolframowe-dobor-szlifowanie.html",
        "Elektrody wolframowe: dobór i szlifowanie | F.W. DRUCIK",
        "Techniczne aspekty doboru elektrod wolframowych do spawania TIG. Wpływ szlifowania na stabilność łuku i zalecenia BHP dla warsztatu.",
        okruszki=[("Blog", "/blog/"), ("Elektrody wolframowe: dobór, szlifowanie i wp…", "/blog/elektrody-wolframowe-dobor-szlifowanie/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/klimatyzacja-po-wymianie-akumulatora/", "blog-klimatyzacja-po-wymianie-akumulatora.html",
        "Klimatyzacja nie działa po wymianie akumulatora - F.W. DRUCIK",
        "Sprawdź, dlaczego klimatyzacja przestaje działać po odłączeniu zasilania. Analiza techniczna przyczyn, procedury adaptacji i diagnostyka w F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("Klimatyzacja nie działa po wymianie akumulatora", "/blog/klimatyzacja-po-wymianie-akumulatora/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/bme280-czujnik-temperatury-wilgotnosci-cisnienia/", "blog-bme280-czujnik-temperatury-wilgotnosci-cisnienia.html",
        "BME280: Pomiar temperatury, wilgotności i ciśnienia | DRUCIK",
        "Analiza techniczna modułu BME280. Sprawdź parametry pracy, interfejsy komunikacyjne i zastosowania w diagnostyce środowiskowej w warsztacie F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("BME280", "/blog/bme280-czujnik-temperatury-wilgotnosci-cisnienia/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/kurs-esp32-czesc-5-ble-i-komunikacja-z-telefonem/", "blog-kurs-esp32-czesc-5-ble-i-komunikacja-z-telefonem.html",
        "Kurs ESP32 część 5: BLE i komunikacja z telefonem | DRUCIK",
        "Poznaj podstawy komunikacji BLE w układach ESP32. Dowiedz się, jak poprawnie skonfigurować serwer GATT i przesyłać dane do urządzeń mobilnych w warsztacie.",
        okruszki=[("Blog", "/blog/"), ("Kurs ESP32 część 5", "/blog/kurs-esp32-czesc-5-ble-i-komunikacja-z-telefonem/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/modul-nadwozia-bcm-diagnostyka/", "blog-modul-nadwozia-bcm-diagnostyka.html",
        "Moduł BCM: diagnostyka i typowe awarie | F.W. DRUCIK",
        "Analiza techniczna modułów BCM w pojazdach. Jak diagnozować usterki magistrali, zasilania i przekaźników. Porady techniczne dla mechaników.",
        okruszki=[("Blog", "/blog/"), ("Moduł nadwozia BCM", "/blog/modul-nadwozia-bcm-diagnostyka/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/frezarka-cnc-od-zera-poradnik/", "blog-frezarka-cnc-od-zera-poradnik.html",
        "Budowa frezarki CNC od podstaw - poradnik F.W. DRUCIK",
        "Jak zbudować frezarkę CNC? Techniczne zestawienie podzespołów, kolejność montażu i kluczowe parametry dla mechanika i technika utrzymania ruchu.",
        okruszki=[("Blog", "/blog/"), ("Frezarka CNC od zera", "/blog/frezarka-cnc-od-zera-poradnik/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/zajarzanie-hf-kontra-lift-arc/", "blog-zajarzanie-hf-kontra-lift-arc.html",
        "Zajarzanie HF a Lift Arc: różnice techniczne | F.W. DRUCIK",
        "Analiza techniczna metod zajarzania łuku w metodzie TIG. Porównanie HF oraz Lift Arc pod kątem zastosowań, zakłóceń elektromagnetycznych i trwałości elektrody.",
        okruszki=[("Blog", "/blog/"), ("Zajarzanie HF kontra Lift Arc", "/blog/zajarzanie-hf-kontra-lift-arc/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/sprezarka-klimatyzacji-nie-zalacza-sie/", "blog-sprezarka-klimatyzacji-nie-zalacza-sie.html",
        "Sprężarka klimatyzacji nie załącza się - F.W. DRUCIK",
        "Diagnostyka układu klimatyzacji: przyczyny braku załączenia sprężarki przy prawidłowym ciśnieniu czynnika. Poradnik techniczny F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("Sprężarka klimatyzacji nie załącza się", "/blog/sprezarka-klimatyzacji-nie-zalacza-sie/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/modele-jezykowe-w-diagnostyce/", "blog-modele-jezykowe-w-diagnostyce.html",
        "Modele językowe w diagnostyce: fakty i mity | F.W. DRUCIK",
        "Analiza wykorzystania modeli językowych w diagnostyce technicznej. Sprawdź, gdzie AI pomaga, a gdzie generuje błędy w pracy mechanika i elektronika.",
        okruszki=[("Blog", "/blog/"), ("Modele językowe w diagnostyce", "/blog/modele-jezykowe-w-diagnostyce/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/odczyt-danych-z-rejestratora-i-wykres/", "blog-odczyt-danych-z-rejestratora-i-wykres.html",
        "Odczyt danych z rejestratora i analiza wykresów | F.W. DRUCIK",
        "Techniczny poradnik odczytu danych z rejestratorów parametrów pracy maszyn i pojazdów. Jak interpretować wykresy i unikać błędów diagnostycznych.",
        okruszki=[("Blog", "/blog/"), ("Odczyt danych z rejestratora i analiza wykresów", "/blog/odczyt-danych-z-rejestratora-i-wykres/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/kurs-esp32-karta-sd-rejestrator-pomiarow/", "blog-kurs-esp32-karta-sd-rejestrator-pomiarow.html",
        "Kurs ESP32 cz. 6: Karta SD i rejestrator pomiarów | F.W.",
        "Dowiedz się, jak zaimplementować obsługę kart SD w ESP32 do rejestracji danych pomiarowych. Poradnik techniczny dla elektroników i automatyków.",
        okruszki=[("Blog", "/blog/"), ("Kurs ESP32 część 6", "/blog/kurs-esp32-karta-sd-rejestrator-pomiarow/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/lokalizacja-sterownikow-w-samochodzie/", "blog-lokalizacja-sterownikow-w-samochodzie.html",
        "Lokalizacja sterowników w aucie: poradnik techniczny F.W.",
        "Dowiedz się, gdzie szukać sterowników w samochodzie bez demontażu deski rozdzielczej. Wskazówki techniczne dla mechaników od F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("Gdzie w aucie siedzą sterowniki", "/blog/lokalizacja-sterownikow-w-samochodzie/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/mlx90614-bezdotykowy-pomiar-temperatury-lozyska/", "blog-mlx90614-bezdotykowy-pomiar-temperatury-lozyska.html",
        "MLX90614: Bezdotykowy pomiar temperatury łożysk | F.W. DRUCIK",
        "Analiza techniczna czujnika MLX90614 w diagnostyce łożysk. Jak poprawnie mierzyć temperaturę, na co uważać i jak interpretować dane w utrzymaniu ruchu.",
        okruszki=[("Blog", "/blog/"), ("MLX90614", "/blog/mlx90614-bezdotykowy-pomiar-temperatury-lozyska/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/retrofit-tokarki-na-cnc-silniki-enkodery-sterowanie/", "blog-retrofit-tokarki-na-cnc-silniki-enkodery-sterowanie.html",
        "Retrofit tokarki na CNC: silniki, enkodery, sterowanie",
        "Techniczny poradnik o modernizacji tokarki konwencjonalnej na CNC. Dobór silników, enkoderów i sterowania zgodnie z zasadami sztuki inżynierskiej.",
        okruszki=[("Blog", "/blog/"), ("Retrofit tokarki na CNC", "/blog/retrofit-tokarki-na-cnc-silniki-enkodery-sterowanie/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/kurs-esp32-oled-enkoder/", "blog-kurs-esp32-oled-enkoder.html",
        "Kurs ESP32: Wyświetlacz OLED i enkoder w warsztacie | DRUCIK",
        "Dowiedz się, jak zintegrować wyświetlacz OLED z mikrokontrolerem ESP32 i obsługiwać menu za pomocą enkodera obrotowego w projektach automatyki.",
        okruszki=[("Blog", "/blog/"), ("Kurs ESP32 część 7", "/blog/kurs-esp32-oled-enkoder/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/drukarka-fdm-w-warsztacie/", "blog-drukarka-fdm-w-warsztacie.html",
        "Drukarka FDM w warsztacie: zastosowania techniczne | F.W.",
        "Analiza techniczna wykorzystania druku 3D FDM w warsztacie. Sprawdź, jakie elementy możesz wykonać samodzielnie i na co zwrócić uwagę przy doborze materiałów.",
        okruszki=[("Blog", "/blog/"), ("Drukarka FDM w warsztacie", "/blog/drukarka-fdm-w-warsztacie/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/spawanie-cienkie-blachy-metody-techniczne/", "blog-spawanie-cienkie-blachy-metody-techniczne.html",
        "Spawanie cienkich blach: techniki i unikanie przepaleń",
        "Poradnik techniczny dla spawaczy: jak łączyć cienkie blachy bez przepaleń. Dobór parametrów, technika prowadzenia łuku i przygotowanie materiału.",
        okruszki=[("Blog", "/blog/"), ("Spawanie cienkich blach", "/blog/spawanie-cienkie-blachy-metody-techniczne/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/bramka-can-gateway-diagnostyka-i-usterki/", "blog-bramka-can-gateway-diagnostyka-i-usterki.html",
        "Bramka CAN Gateway: diagnostyka i skutki awarii | F.W. DRUCIK",
        "Analiza techniczna modułu Gateway w sieci CAN. Jak działa bramka, jakie są objawy jej awarii i jak przeprowadzić diagnostykę w warsztacie.",
        okruszki=[("Blog", "/blog/"), ("Bramka CAN (gateway)", "/blog/bramka-can-gateway-diagnostyka-i-usterki/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/termopara-typu-k-z-max6675/", "blog-termopara-typu-k-z-max6675.html",
        "Termopara typu K z MAX6675: Pomiar temperatur w F.W. Drucik",
        "Analiza techniczna układu termopary typu K z modułem MAX6675. Zasady pomiaru, parametry techniczne i zastosowanie w diagnostyce warsztatowej.",
        okruszki=[("Blog", "/blog/"), ("Termopara typu K z MAX6675", "/blog/termopara-typu-k-z-max6675/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/regeneracja-sprezarki-klimatyzacji-wyciek-na-wale/", "blog-regeneracja-sprezarki-klimatyzacji-wyciek-na-wale.html",
        "Regeneracja sprężarki klimatyzacji: wyciek na wale | F.W.",
        "Techniczne aspekty regeneracji sprężarek klimatyzacji. Jak zdiagnozować wyciek na wale i dlaczego wymiana uszczelniacza wymaga precyzji? Sprawdź w F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("Regeneracja sprężarki klimatyzacji", "/blog/regeneracja-sprezarki-klimatyzacji-wyciek-na-wale/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/jak-ustawic-migomat-mig-mag-stal/", "blog-jak-ustawic-migomat-mig-mag-stal.html",
        "Jak ustawić migomat do stali: prąd, napięcie, drut",
        "Kurs MIG/MAG cz. 1: dobór drutu i gazu, reguły prądu i napięcia, tabela nastaw dla blach 1–6 mm i diagnoza łuku po dźwięku.",
        okruszki=[("Blog", "/blog/"), ("Jak ustawić migomat do stali", "/blog/jak-ustawic-migomat-mig-mag-stal/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/technika-spawania-mig-mag-pchanie-ciagniecie-pozycje/", "blog-technika-spawania-mig-mag-pchanie-ciagniecie-pozycje.html",
        "Pchać czy ciągnąć? Technika spawania MIG/MAG",
        "Kurs MIG/MAG cz. 2: kąt uchwytu, pchanie i ciągnięcie, ruchy uchwytem, korekta prądu w pionie i na pułapie oraz ćwiczenia na złomie.",
        okruszki=[("Blog", "/blog/"), ("Pchać czy ciągnąć? Technika uchwytu MIG/MAG i", "/blog/technika-spawania-mig-mag-pchanie-ciagniecie-pozycje/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/spawanie-aluminium-migomatem-drut-gaz-technika/", "blog-spawanie-aluminium-migomatem-drut-gaz-technika.html",
        "Aluminium migomatem: drut, gaz, podawanie i technika",
        "Kurs MIG/MAG cz. 3: drut 4043 czy 5356, gaz, wkład teflonowy i rolki U, przygotowanie materiału, prąd startowy, krater i tabela prądów.",
        okruszki=[("Blog", "/blog/"), ("Aluminium migomatem", "/blog/spawanie-aluminium-migomatem-drut-gaz-technika/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/puls-podwojny-puls-migomat-ustawienia/", "blog-puls-podwojny-puls-migomat-ustawienia.html",
        "Puls i podwójny puls w migomacie: krzywa i ustawienia",
        "Kurs MIG/MAG cz. 4: jak działa spawanie impulsowe, kształt krzywej prądowej, synergia, korekta łuku i ustawienia podwójnego pulsu.",
        okruszki=[("Blog", "/blog/"), ("Puls i podwójny puls w migomacie", "/blog/puls-podwojny-puls-migomat-ustawienia/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/prowadnice-liniowe-kontra-tuleje/", "blog-prowadnice-liniowe-kontra-tuleje.html",
        "Prowadnice liniowe czy tuleje? Sztywność, cena i analiza",
        "Porównujemy sztywność i koszty prowadnic liniowych oraz tulei ślizgowych. Analiza techniczna dla utrzymania ruchu i mechaników maszyn CNC.",
        okruszki=[("Blog", "/blog/"), ("Prowadnice liniowe kontra tuleje", "/blog/prowadnice-liniowe-kontra-tuleje/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/regeneracja-alternatora-krok-po-kroku/", "blog-regeneracja-alternatora-krok-po-kroku.html",
        "Regeneracja alternatora: co wymieniać, a co zostawić | DRUCIK",
        "Techniczny poradnik regeneracji alternatora. Sprawdź, jakie elementy podlegają wymianie, a jakie weryfikacji. Wiedza dla mechaników od F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("Regeneracja alternatora", "/blog/regeneracja-alternatora-krok-po-kroku/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/pierwsza-warstwa-kalibracja-stolu-i-typowe-problemy/", "blog-pierwsza-warstwa-kalibracja-stolu-i-typowe-problemy.html",
        "Kalibracja pierwszej warstwy w druku 3D | F.W. DRUCIK",
        "Techniczne aspekty kalibracji pierwszej warstwy w druku 3D. Analiza błędów, procedury poziomowania i wpływ na adhezję wydruku. Wiedza dla techników.",
        okruszki=[("Blog", "/blog/"), ("Pierwsza warstwa", "/blog/pierwsza-warstwa-kalibracja-stolu-i-typowe-problemy/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/diagnostyka-ukladu-klimatyzacji-mostkowanie-przekaznika/", "blog-diagnostyka-ukladu-klimatyzacji-mostkowanie-przekaznika.html",
        "Diagnostyka klimatyzacji: mostkowanie przekaźnika AC | DRUCIK",
        "Dowiedz się, jak zdiagnozować brak załączania sprzęgła klimatyzacji poprzez testowe mostkowanie przekaźnika. Poradnik techniczny dla mechaników.",
        okruszki=[("Blog", "/blog/"), ("Diagnostyka układu klimatyzacji", "/blog/diagnostyka-ukladu-klimatyzacji-mostkowanie-przekaznika/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/csmio-ip-s-ip-m-ip-a-porownanie/", "blog-csmio-ip-s-ip-m-ip-a-porownanie.html",
        "CSMIO/IP-S, IP-M, IP-A: Porównanie sterowników CNC | DRUCIK",
        "Analiza techniczna sterowników ruchu CSMIO/IP-S, IP-M oraz IP-A. Dowiedz się, który model wybrać do modernizacji maszyny CNC w F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("CSMIO/IP-S, IP-M i IP-A", "/blog/csmio-ip-s-ip-m-ip-a-porownanie/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/spawarka-inwertorowa-diagnostyka/", "blog-spawarka-inwertorowa-diagnostyka.html",
        "Spawarka inwertorowa: schemat blokowy i diagnoza | F.W. DRUCIK",
        "Techniczny przewodnik diagnostyki spawarek inwertorowych. Analiza blokowa, pomiary napięć i procedura serwisowa dla elektroników i mechaników.",
        okruszki=[("Blog", "/blog/"), ("Spawarka inwertorowa", "/blog/spawarka-inwertorowa-diagnostyka/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/kurs-esp32-czesc-3-can-twai/", "blog-kurs-esp32-czesc-3-can-twai.html",
        "Kurs ESP32 cz. 3: Magistrala CAN i TWAI | F.W. DRUCIK",
        "Analiza magistrali CAN w pojazdach przy użyciu ESP32. Techniczne aspekty protokołu TWAI, podłączenie fizyczne i diagnostyka sygnałów w warsztacie.",
        okruszki=[("Blog", "/blog/"), ("Kurs ESP32 część 3", "/blog/kurs-esp32-czesc-3-can-twai/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/warping-i-odklejanie-wydrukow-3d/", "blog-warping-i-odklejanie-wydrukow-3d.html",
        "Warping i odklejanie wydruków 3D - poradnik techniczny F.W.",
        "Analiza techniczna przyczyn powstawania wypaczeń (warping) i odklejania się wydruków 3D od stołu roboczego. Wskazówki dla techników i operatorów maszyn.",
        okruszki=[("Blog", "/blog/"), ("Warping i odklejanie wydruków 3D", "/blog/warping-i-odklejanie-wydrukow-3d/")],
        priority="0.8", og_type="article",
        robots="noindex,nofollow", noindex=True,  # SZKIC
    ),

    strona(
        "/blog/pt100-z-max31865-pomiar-precyzyjny/", "blog-pt100-z-max31865-pomiar-precyzyjny.html",
        "PT100 z MAX31865: Precyzyjny pomiar temperatury | F.W. DRUCIK",
        "Techniczne aspekty wykorzystania przetwornika MAX31865 z czujnikami PT100 w układach przemysłowych. Wskazówki dla automatyków i techników utrzymania ruchu.",
        okruszki=[("Blog", "/blog/"), ("PT100 z MAX31865", "/blog/pt100-z-max31865-pomiar-precyzyjny/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/uklady-scalone-sg3525-i-ka3525a-w-spawarkach/", "blog-uklady-scalone-sg3525-i-ka3525a-w-spawarkach.html",
        "Układy SG3525 i KA3525A w spawarkach - diagnostyka | F.W.",
        "Poradnik techniczny dla serwisantów spawarek inwertorowych: diagnostyka układów SG3525 i KA3525A. Sprawdź objawy uszkodzeń i procedury pomiarowe.",
        okruszki=[("Blog", "/blog/"), ("Diagnostyka układów scalonych SG3525 i KA3525A", "/blog/uklady-scalone-sg3525-i-ka3525a-w-spawarkach/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/terminatory-magistrali-can-pomiar-60-omow/", "blog-terminatory-magistrali-can-pomiar-60-omow.html",
        "Terminatory magistrali CAN: pomiar 60 omów | F.W. DRUCIK",
        "Diagnostyka sieci CAN zaczyna się od pomiaru rezystancji terminującej. Sprawdź, jak poprawnie wykonać test 60 omów w warsztacie F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("Terminatory magistrali CAN", "/blog/terminatory-magistrali-can-pomiar-60-omow/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/sruby-trapezowe-kontra-kulowe/", "blog-sruby-trapezowe-kontra-kulowe.html",
        "Śruby trapezowe a kulowe: luz, sprawność i zastosowania",
        "Analiza techniczna śrub trapezowych i kulowych. Porównanie sprawności, luzów oraz zastosowań w maszynach CNC. Wskazówki serwisowe dla mechaników.",
        okruszki=[("Blog", "/blog/"), ("Śruby trapezowe kontra kulowe", "/blog/sruby-trapezowe-kontra-kulowe/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/mpu6050-pomiar-drgan-i-przechylu-maszyny/", "blog-mpu6050-pomiar-drgan-i-przechylu-maszyny.html",
        "MPU6050: Pomiar drgań i przechyłu maszyn | F.W. DRUCIK",
        "Analiza techniczna czujnika MPU6050 w diagnostyce drgań i przechyłów maszyn. Wskazówki dla techników utrzymania ruchu i elektroników w F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("MPU6050", "/blog/mpu6050-pomiar-drgan-i-przechylu-maszyny/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/weryfikacja-odpowiedzi-ai-dokumentacja-serwisowa/", "blog-weryfikacja-odpowiedzi-ai-dokumentacja-serwisowa.html",
        "Weryfikacja danych AI z dokumentacją serwisową | F.W. DRUCIK",
        "Dowiedz się, jak weryfikować techniczne odpowiedzi AI z dokumentacją serwisową. Unikaj błędów w diagnostyce maszyn i pojazdów w warsztacie F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("Weryfikacja odpowiedzi AI danymi z dokumentacją", "/blog/weryfikacja-odpowiedzi-ai-dokumentacja-serwisowa/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/dobor-materialow-do-druku-3d-w-warsztacie/", "blog-dobor-materialow-do-druku-3d-w-warsztacie.html",
        "PLA, PETG, ABS, ASA: dobór materiałów 3D w F.W. DRUCIK",
        "Analiza techniczna właściwości materiałów PLA, PETG, ABS i ASA w zastosowaniach warsztatowych. Sprawdź, co wybrać do druku części zamiennych i narzędzi.",
        okruszki=[("Blog", "/blog/"), ("Dobór materiałów do druku 3D w warunkach", "/blog/dobor-materialow-do-druku-3d-w-warsztacie/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/oktokopter-lx1100-budowa-i-konfiguracja/", "blog-oktokopter-lx1100-budowa-i-konfiguracja.html",
        "Oktokopter LX1100: budowa i konfiguracja | F.W. DRUCIK",
        "Instrukcja budowy oktokoptera 12S LX1100: rama, zasilanie 12S, Pixhawk 6X, czujniki co 45°, druk 3D, parametry ArduPilot, film i rysunki techniczne.",
        okruszki=[("Blog", "/blog/"), ("Oktokopter LX1100", "/blog/oktokopter-lx1100-budowa-i-konfiguracja/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/filmy/", "filmy.html",
        "Filmy z warsztatu: rolki i poradniki wideo | F.W. DRUCIK",
        "Rolki i poradniki wideo F.W. DRUCIK ułożone tematycznie: klimatyzacja, spawanie, elektronika i magistrale, CNC, druk 3D i budowa drona. Każdy film z artykułem.",
        okruszki=[("Filmy z warsztatu", "/filmy/")], priority="0.7", changefreq="weekly",
    ),

    strona(
        "/blog/adxl345-akcelerometr-wibracje/", "blog-adxl345-akcelerometr-wibracje.html",
        "ADXL345: Diagnostyka wibracji w warsztacie - F.W. DRUCIK",
        "Analiza techniczna czujnika ADXL345 w diagnostyce maszyn. Jak wykrywać wibracje i interpretować dane w warsztacie F.W. DRUCIK. Sprawdź szczegóły.",
        okruszki=[("Blog", "/blog/"), ("ADXL345", "/blog/adxl345-akcelerometr-wibracje/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/kondensatory-470u-400v-inwerter-diagnostyka/", "blog-kondensatory-470u-400v-inwerter-diagnostyka.html",
        "Diagnostyka kondensatorów 470uF 400V w inwerterach | F.W.",
        "Poradnik techniczny: jak diagnozować kondensatory elektrolityczne 470uF 400V w inwerterach, na co uważać przy wymianie i jak zachować bezpieczeństwo pracy.",
        okruszki=[("Blog", "/blog/"), ("Diagnostyka i wymiana kondensatorów 470uF 400V", "/blog/kondensatory-470u-400v-inwerter-diagnostyka/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/regulator-napiecia-alternator-diagnostyka/", "blog-regulator-napiecia-alternator-diagnostyka.html",
        "Regulator napięcia w alternatorze: diagnostyka i pomiary",
        "Dowiedz się, jak zdiagnozować uszkodzony regulator napięcia w alternatorze. Procedury pomiarowe, wartości referencyjne i zasady bezpieczeństwa.",
        okruszki=[("Blog", "/blog/"), ("Regulator napięcia w alternatorze", "/blog/regulator-napiecia-alternator-diagnostyka/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/silnik-dymi-na-zimnym-rozruchu-diagnoza/", "blog-silnik-dymi-na-zimnym-rozruchu-diagnoza.html",
        "Silnik dymi na zimnym rozruchu: diagnostyka - F.W. DRUCIK",
        "Analiza techniczna dymienia silnika przy zimnym rozruchu. Jak odróżnić spalanie oleju od paliwa na podstawie koloru spalin i zapachu. Porady F.W. DRUCIK.",
        okruszki=[("Blog", "/blog/"), ("Silnik dymi na zimnym rozruchu", "/blog/silnik-dymi-na-zimnym-rozruchu-diagnoza/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/sprzeglo-elektromagnetyczne-sprezarki-pomiar-i-regulacja/", "blog-sprzeglo-elektromagnetyczne-sprezarki-pomiar-i-regulacja.html",
        "Sprzęgło sprężarki klimatyzacji: pomiar i regulacja | DRUCIK",
        "Poradnik techniczny: jak diagnozować cewkę sprzęgła sprężarki klimatyzacji, mierzyć rezystancję i ustawiać szczelinę powietrzną zgodnie z dokumentacją.",
        okruszki=[("Blog", "/blog/"), ("Diagnostyka i regulacja sprzęgła", "/blog/sprzeglo-elektromagnetyczne-sprezarki-pomiar-i-regulacja/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/analiza-logow-magistrali-can-python/", "blog-analiza-logow-magistrali-can-python.html",
        "Analiza logów magistrali CAN w Pythonie | F.W. DRUCIK",
        "Praktyczny przewodnik dla techników: jak analizować ramki CAN w Pythonie. Diagnostyka błędów, struktura ramek i interpretacja danych w warsztacie.",
        okruszki=[("Blog", "/blog/"), ("Analiza logów magistrali CAN w Pythonie", "/blog/analiza-logow-magistrali-can-python/")],
        priority="0.8", og_type="article",
    ),

    strona(
        "/blog/rozpoznawanie-obrazu-w-kontroli-jakosci-detali/", "blog-rozpoznawanie-obrazu-w-kontroli-jakosci-detali.html",
        "Rozpoznawanie obrazu w kontroli jakości detali | F.W. DRUCIK",
        "Techniczne aspekty systemów wizyjnych w kontroli jakości detali. Dowiedz się, jak wdrożyć inspekcję optyczną w procesach produkcyjnych i serwisowych.",
        okruszki=[("Blog", "/blog/"), ("Rozpoznawanie obrazu w kontroli jakości detali", "/blog/rozpoznawanie-obrazu-w-kontroli-jakosci-detali/")],
        priority="0.8", og_type="article",
    ),

# === AGENT BLOGA: nowe wpisy wstawiane powyżej tej linii ===

    strona(
        "/forum/", "forum.html",
        "Forum dyskusyjne i porady techniczne — F.W. DRUCIK",
        "Społeczność i forum techniczne: elektromechanika, diagnostyka, spawanie MIG/TIG, "
        "maszyny CNC i mechanika. Zadaj pytanie naszym specjalistom.",
        okruszki=[("Forum dyskusyjne", "/forum/")], priority="0.8", changefreq="daily",
    ),

    strona(
        "/regulamin/", "regulamin.html",
        "Regulamin sklepu internetowego — F.W. DRUCIK",
        "Zasady sprzedaży, dostawy, zwrotów i reklamacji w sklepie F.W. DRUCIK. "
        "Prawo odstąpienia, wyjątki dla wyrobów na zamówienie, tryb reklamacyjny.",
        okruszki=[("Regulamin sklepu", "/regulamin/")], priority="0.4",
        changefreq="yearly",
    ),

    strona(
        "/odstapienie/", "odstapienie.html",
        "Odstąpienie od umowy — formularz i zasady zwrotu",
        "Jak zwrócić towar kupiony w sklepie F.W. DRUCIK: 14 dni bez podania przyczyny, "
        "gotowy wzór formularza odstąpienia i informacja o kosztach zwrotu.",
        okruszki=[("Regulamin sklepu", "/regulamin/"), ("Odstąpienie od umowy", "/odstapienie/")],
        priority="0.4", changefreq="yearly",
    ),

    # Koszyk i zamówienie to strony transakcyjne — nie mają czego szukać
    # w wynikach wyszukiwania, a ich treść zależy od zawartości przeglądarki.
    strona(
        "/koszyk/", "koszyk.html",
        "Koszyk — F.W. DRUCIK",
        "Zawartość koszyka i przejście do zamówienia w sklepie F.W. DRUCIK.",
        okruszki=[("Sklep", "/sklep/"), ("Koszyk", "/koszyk/")],
        robots="noindex,follow", noindex=True,
    ),

    strona(
        "/zamowienie/", "zamowienie.html",
        "Zamówienie — dostawa i zapłata | F.W. DRUCIK",
        "Wybór sposobu dostawy i zapłaty oraz złożenie zamówienia w sklepie F.W. DRUCIK.",
        okruszki=[("Sklep", "/sklep/"), ("Zamówienie", "/zamowienie/")],
        robots="noindex,nofollow", noindex=True,
    ),

    strona(
        "/narzedzia/", "narzedzia.html",
        "Narzędzia online: przelicznik, kody OBD-II, notatnik",
        "Przelicznik jednostek, kod kolorów rezystora, podręcznik kodów błędów OBD-II, "
        "kalkulator wyceny naprawy oraz notatnik i kalendarz na koncie. Dostęp bezpłatny.",
        okruszki=[("Narzędzia online", "/narzedzia/")], priority="0.7",
        dodatkowe=[
            {
                "@type": "WebApplication",
                "name": "Narzędzia online F.W. DRUCIK",
                "url": SITE + "/narzedzia/",
                "applicationCategory": "UtilitiesApplication",
                "operatingSystem": "Dowolna przeglądarka",
                "inLanguage": "pl-PL",
                "featureList": [
                    "Wyszukiwarka treści serwisu",
                    "Notatnik zapisywany na koncie",
                    "Kalendarz terminów",
                    "Przelicznik jednostek warsztatowych",
                    "Kod kolorów rezystora",
                    "Podręcznik kodów błędów OBD-II",
                    "Kalkulator wyceny naprawy",
                ],
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "PLN"},
                "publisher": {"@id": SITE + "/#organizacja"},
            },
        ],
    ),

    strona(
        "/pracownia/", "pracownia.html",
        "Pracownia Drucika – elektronika, Arduino i druk 3D",
        "Ćwiczenia dla najmłodszych. Zamknij obwód z LED, ułóż rytm Arduino i znajdź pierwszą warstwę druku 3D. "
        "Wypróbuj też studio robota.",
        okruszki=[("Narzędzia online", "/narzedzia/"), ("Pracownia Drucika", "/pracownia/")],
        priority="0.7",
    ),

    strona(
        "/pracownia/kompendium/", "pracownia-kompendium.html",
        "Kompendium Pracowni Drucika dla dzieci",
        "Ilustrowana baza wiedzy dla dzieci. Odkrywaj elektronikę, Arduino i druk 3D, a potem zrób próbę w odpowiedniej lekcji Pracowni Drucika.",
        okruszki=[("Pracownia Drucika", "/pracownia/"), ("Kompendium", "/pracownia/kompendium/")],
        priority="0.6",
    ),

    strona(
        "/konto/", "konto.html",
        "Moje konto i logowanie — F.W. DRUCIK",
        "Logowanie i rejestracja konta użytkownika. Uzyskaj dostęp do pełnych artykułów bloga "
        "oraz zadawania pytań na forum dyskusyjnym.",
        okruszki=[("Moje konto", "/konto/")], priority="0.4",
    ),

    strona(
        "/admin/", "admin.html",
        "Panel Administratora — F.W. DRUCIK",
        "Panel zarządczy: moderacja wątków forum i komentarzy oraz zarządzanie kontami "
        "użytkowników serwisu.",
        okruszki=[("Panel Admina", "/admin/")], priority="0.1", robots="noindex,nofollow", noindex=True,
    ),

    # ------------------------------------------------------------- 404
    strona(
        "/404", "404.html",
        "Nie znaleziono strony (404) — F.W. DRUCIK",
        "Podana strona nie istnieje. Skorzystaj z menu lub przejdź do listy usług F.W. DRUCIK.",
        robots="noindex,follow", noindex=True,
    ),
]

# Kompendium AI: podstrony powstaja z modulu `kompendium`, nie z plikow w src/.
# Import jest tutaj, a nie na gorze, bo kompendium_strony korzysta z build.py,
# ktory sam wczytuje ten plik — kolejnosc musi byc taka.
from kompendium_strony import STRONY as STRONY_KOMPENDIUM  # noqa: E402

STRONY.extend(STRONY_KOMPENDIUM)

# Kursy: cztery strony o identycznej budowie, wiec skladane z danych zamiast
# z czterech kopii HTML w src/. Import z tego samego powodu co wyzej.
from kursy_strony import STRONY as STRONY_KURSY  # noqa: E402

STRONY.extend(STRONY_KURSY)
