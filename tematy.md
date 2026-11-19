# Kolejka tematów bloga

Agent (`agent-bloga.py`) odhacza wykorzystaną pozycję, dopisując datę i adres.

Wybór tematu zależy od trybu:

- **z harmonogramu** (co drugi dzień) i z `--losowo` — agent losuje **dziedzinę**
  (nagłówek `##`), a w niej bierze pierwszą wolną pozycję. Losowanie jest
  **ważone liczbą wolnych tematów**: dziedzina z 70 pozycjami wypada mniej
  więcej 70 razy częściej niż ta z jedną, więc proporcje wpisów na blogu idą
  za tym, ile materiału na dany temat przygotowano. Chcesz, żeby jakaś
  dziedzina pojawiała się częściej — dopisz do niej tematy. Kolejność
  w obrębie dziedziny decyduje, co powstanie z niej najwcześniej, a dziedzina
  bez wolnych pozycji wypada z losowania sama.
- **bez `--losowo`** — agent bierze pierwszą wolną pozycję w całym pliku, więc
  liczy się kolejność sekcji.

Nagłówki nie mogą się powtarzać — dwie sekcje o tej samej nazwie agent
potraktuje jako jedną dziedzinę.

Format jednej pozycji: `- [ ] temat wpisu`. Nic poza tym w linii.
Komentarze i nagłówki agent ignoruje.

## Elektronika pojazdowa, magistrale i protokoły

- [x] Magistrala LIN w pojazdach — po co druga sieć obok CAN i jak ją zdiagnozować  <!-- 2026-08-08, /blog/magistrala-lin-w-pojazdach-diagnostyka/ -->
- [x] FlexRay i Automotive Ethernet — dokąd idzie sieć pokładowa nowych pojazdów  <!-- 2026-08-10, /blog/flexray-i-automotive-ethernet-sieci-pokladowe/ -->
- [x] Diagnostyka J1939 w ciężarówkach — PGN, SPN, FMI i czytanie ramek  <!-- 2026-08-15, /blog/diagnostyka-j1939-ciezarowki/ -->
- [x] UDS (ISO 14229) — usługi diagnostyczne, sesje, kody NRC w praktyce warsztatowej  <!-- 2026-08-15, /blog/uds-iso-14229-diagnostyka-warsztatowa/ -->
- [x] Czujniki w pojeździe: indukcyjne, Halla, PWM, SENT — jak je odróżnić na oscyloskopie  <!-- 2026-08-15, /blog/diagnostyka-czujnikow-oscyloskopem/ -->
- [x] Sterowniki nadwozia BCM i sieć komfortu — typowe usterki i zwarcia w wiązkach  <!-- 2026-08-15, /blog/sterowniki-bcm-i-siec-komfortu/ -->
- [x] Retarder, tempomat, sterowanie skrzynią AMT — kto z kim rozmawia po CAN  <!-- 2026-08-15, /blog/retarder-tempomat-skrzynia-amt-komunikacja-can/ -->
- [x] Zasilanie 24 V w pojazdach ciężarowych — masy, spadki napięć, pomiar pod obciążeniem  <!-- 2026-08-15, /blog/zasilanie-24v-pojazdy-ciezarowe/ -->
- [ ] Akumulatory AGM, EFB i litowe w pojazdach — ładowanie, pomiar, najczęstsze błędy

## Kursy: Arduino, ESP32, Python

- [x] Kurs ESP32 część 2 — Wi-Fi, MQTT i wysyłanie pomiarów z warsztatu  <!-- 2026-08-15, /blog/kurs-esp32-czesc-2-wifi-mqtt/ -->
- [x] Kurs ESP32 część 3 — CAN (TWAI) i podsłuchiwanie magistrali pojazdu  <!-- 2026-10-09, /blog/kurs-esp32-czesc-3-can-twai/ -->
- [ ] Kurs ESP32 część 4 — Modbus RTU przez RS-485 i sterowanie falownikiem
- [ ] Arduino a ESP32 — którą płytkę wybrać do konkretnego zadania w warsztacie
- [ ] Python w warsztacie — raport z pliku CSV z rejestratora w 30 linijkach kodu
- [ ] Zasilanie układów mikrokontrolerowych w pojeździe — przetwornice, zabezpieczenia, filtracja
- [ ] Sterowanie silnikiem krokowym i BLDC — driver, mikrokrok, dobór prądu

## Klimatyzacja i chłodnictwo

- [ ] Odgrzybianie klimatyzacji — ozon, ultradźwięki, preparaty; co naprawdę działa
- [ ] Sprężarki klimatyzacji ze zmiennym skokiem i sterowaniem elektronicznym
- [ ] Olej w układzie klimatyzacji — PAG, POE, dobór lepkości i skutki pomyłki
- [ ] Wykrywanie nieszczelności: azot, barwnik UV, detektor elektroniczny — porównanie metod
- [ ] Klimatyzacja w maszynach rolniczych i budowlanych — czym różni się serwis

## CNC, obróbka i produkcja

- [x] Dobór parametrów skrawania — posuw na ostrze, prędkość skrawania, zagłębienie  <!-- 2026-08-15, /blog/dobor-parametrow-skrawania/ -->
- [x] Retrofit starej frezarki na sterowanie CNC — od czego zacząć  <!-- 2026-08-15, /blog/retrofit-frezarki-cnc-od-czego-zaczac/ -->
- [ ] Serwo kontra krokowiec w maszynie CNC — momenty, sprzężenie, koszty
- [ ] G-code od zera — 20 komend, które wystarczą do pierwszego detalu
- [ ] Sztywność konstrukcji i drgania w maszynach CNC — dlaczego detal wychodzi falowany

## Spawanie i łączenie metali

- [ ] Gazy osłonowe w MIG/MAG i TIG — argon, mieszanki, wpływ na spoinę
- [ ] Odkształcenia spawalnicze — kolejność spawania i sposoby ich ograniczenia
- [ ] Spawanie stali nierdzewnej — przebarwienia, trawienie, pasywacja
- [ ] Luty twarde srebrne — dobór spoiwa i topnika do miedzi, mosiądzu i stali

## Druk 3D i odtwarzanie części

- [x] Materiały do druku 3D w warsztacie — PLA, PETG, ABS, ASA, PA-CF pod obciążenie  <!-- 2026-08-15, /blog/materialy-do-druku-3d-w-warsztacie/ -->
- [x] Skanowanie 3D uszkodzonej części — od chmury punktów do gotowego modelu  <!-- 2026-08-15, /blog/skanowanie-3d-uszkodzonej-czesci/ -->
- [ ] Wydruk 3D jako część zamienna — kiedy wytrzyma, a kiedy trzeba metalu

## AI i nowe technologie w warsztacie

- [x] Modele językowe w serwisie — do czego nadają się przy diagnostyce, a do czego nie  <!-- 2026-08-15, /blog/modele-jezykowe-w-diagnostyce-pojazdow/ -->
- [x] Wizja komputerowa w kontroli jakości detali — co da się zrobić małym kosztem  <!-- 2026-08-15, /blog/wizja-komputerowa-w-kontroli-jakosci/ -->
- [x] Predykcyjne utrzymanie ruchu — pomiar drgań i temperatury zamiast wymiany po awarii  <!-- 2026-08-16, /blog/predykcyjne-utrzymanie-ruchu-pomiary/ -->
- [ ] Lokalne modele AI na własnym sprzęcie — prywatność danych serwisowych

## Diagnostyka usterek pojazdowych — objawy z warsztatu

- [x] Klimatyzacja przestała działać po wymianie akumulatora — od czego zacząć szukanie  <!-- 2026-08-26, /blog/klimatyzacja-po-wymianie-akumulatora/ -->
- [x] Sprężarka klimatyzacji nie załącza się, choć ciśnienie czynnika jest poprawne  <!-- 2026-09-01, /blog/sprezarka-klimatyzacji-nie-zalacza-sie/ -->
- [x] Przycisk AC świeci, sprzęgło nie łapie — mostkowanie przekaźnika jako test diagnostyczny  <!-- 2026-10-03, /blog/diagnostyka-ukladu-klimatyzacji-mostkowanie-przekaznika/ -->
- [x] Silnik dymi na zimnym rozruchu — jak odróżnić olej od paliwa po kolorze i zapachu  <!-- 2026-11-01, /blog/silnik-dymi-na-zimnym-rozruchu-diagnoza/ -->
- [ ] Wyciek oleju spod pokrywy zaworów — kiedy uszczelka, a kiedy zapchane odpowietrzenie
- [ ] Spadek mocy pod pełnym obciążeniem — sprawdzanie ciśnienia doładowania krok po kroku
- [ ] Auto gaśnie w czasie jazdy — czujnik położenia wału, pompa czy masa
- [ ] Nie ma rozruchu, ale przekaźnik klika — pomiar spadku napięcia zamiast wymiany części
- [ ] Rozrusznik kręci wolno przy dobrym akumulatorze — rezystancja przejścia w obwodzie
- [ ] Lampka ładowania świeci przy pracującym silniku — alternator, regulator czy pasek
- [ ] Akumulator rozładowuje się przez noc — pomiar prądu spoczynkowego metodą odłączania bezpieczników
- [ ] Wycieraczki działają tylko na najszybszym biegu — moduł nadwozia czy przełącznik
- [ ] Kierunkowskaz miga za szybko po wymianie żarówek na LED — rezystory czy przeprogramowanie
- [ ] Światła przygasają przy hamowaniu — masy nadwozia i typowe miejsca korozji
- [ ] Elektryczna szyba rusza i staje — silnik, prowadnice czy moduł komfortu
- [ ] Centralny zamek zamyka, nie otwiera — pilot, siłownik czy przełącznik w klamce
- [ ] Immobilizer nie rozpoznaje kluczyka — cewka, transponder, sterownik
- [ ] Błąd komunikacji ze sterownikiem — kiedy wina jest w wiązce, a nie w module
- [ ] Zwarcie w wiązce — jak szukać metodą podziału bez rozbierania połowy auta
- [ ] Przerwa w przewodzie pod izolacją — pomiar rezystancji pod obciążeniem
- [ ] Korozja styków w złączu — czyszczenie, konserwacja i kiedy wymienić całe złącze
- [ ] Woda w złączu sterownika — osuszanie, mycie płytki i ocena szkód
- [ ] Sterownik po zalaniu — kiedy naprawa ma sens, a kiedy tylko wymiana
- [ ] Zimne luty w sterowniku — jak je znaleźć i poprawnie przelutować
- [ ] Uszkodzone kondensatory elektrolityczne w module — objawy i szybka weryfikacja
- [ ] Czujnik temperatury podaje absurdalne wartości — sprawdzanie charakterystyki NTC
- [ ] Czujnik ABS bez sygnału — pomiar rezystancji, szczelina i pierścień magnetyczny
- [ ] Sonda lambda wolno reaguje — odróżnienie zużycia od problemu z układem paliwowym
- [ ] Przepływomierz zaniża wskazania — test porównawczy zamiast wymiany w ciemno
- [ ] Zawór EGR zapchany czy zablokowany elektrycznie — dwie różne diagnozy
- [ ] Filtr DPF nie wypala się — warunki regeneracji i dlaczego bywają niespełnione
- [ ] Turbosprężarka o zmiennej geometrii — objawy zatarcia mechanizmu sterującego
- [ ] Wtryskiwacze — pomiar przelewów jako pierwsza szybka diagnoza
- [ ] Pompa paliwa traci wydajność — pomiar ciśnienia zamiast wymiany na oślep
- [ ] Sterownik pompy paliwa — gdzie siedzi i jak sprawdzić, czy podaje zasilanie
- [ ] Świece żarowe — pomiar prądu każdej osobno bez wykręcania
- [ ] Cewka zapłonowa pod obciążeniem — dlaczego pomiar rezystancji nie wystarcza
- [ ] Kompresja i szczelność cylindrów — próba ciśnieniowa i odczyt wyniku
- [ ] Rozrząd przeskoczył o ząb — objawy, weryfikacja i konsekwencje
- [ ] Czujnik ciśnienia oleju kłamie — mechaniczny manometr jako punkt odniesienia
- [ ] Wentylator chłodnicy chodzi bez przerwy — czujnik, sterownik czy zapowietrzenie
- [ ] Termostat nie otwiera się — szybki test bez demontażu
- [ ] Nagrzewnica grzeje słabo — powietrze w układzie czy zapchany radiator
- [ ] Hałas z osprzętu silnika — jak zlokalizować źródło stetoskopem
- [ ] Drgania przy prędkości drogowej — wyważenie, przeguby czy piasty
- [ ] Skrzynia automatyczna zmienia biegi szarpnięciami — olej, adaptacje czy elektronika
- [ ] Sprzęgło dwumasowe — objawy zużycia i pomiar luzu obrotowego
- [ ] Retarder nie zwalnia — komunikacja po CAN czy część wykonawcza
- [ ] Tempomat nie włącza się — warunki blokady i sygnały wejściowe
- [ ] Sterownik EBS zgłasza błąd czujnika — sprawdzanie zasilania i masy odniesienia
- [ ] ECAS nie podnosi zawieszenia — zawory, czujniki wysokości, sprężarka
- [ ] Ładowarka w pojeździe elektrycznym nie startuje — protokół komunikacji z punktem ładowania
- [ ] Pojazd hybrydowy — bezpieczne odłączenie wysokiego napięcia przed naprawą
- [ ] Diagnostyka maszyn rolniczych — czym różni się od samochodowej w praktyce
- [ ] Wózek widłowy — układ sterowania jazdy i typowe usterki elektryczne

## Elektronika pojazdowa: moduły, sterowniki i sieci

- [x] Moduł nadwozia BCM — mapa funkcji i typowe punkty awarii  <!-- 2026-08-27, /blog/modul-nadwozia-bcm-diagnostyka/ -->
- [x] Gdzie w aucie siedzą sterowniki — mapa lokalizacji i dostęp bez demontażu deski  <!-- 2026-09-09, /blog/lokalizacja-sterownikow-w-samochodzie/ -->
- [x] Bramka CAN (gateway) — po co jest i co się dzieje, gdy padnie  <!-- 2026-09-21, /blog/bramka-can-gateway-diagnostyka-i-usterki/ -->
- [x] Terminatory magistrali CAN — pomiar 60 omów jako pierwszy test sieci  <!-- 2026-10-17, /blog/terminatory-magistrali-can-pomiar-60-omow/ -->
- [ ] CAN High i CAN Low na oscyloskopie — jak wygląda zdrowa ramka
- [ ] Zwarcie CAN do masy i do plusa — objawy w komunikacji i sposób lokalizacji
- [ ] Magistrala LIN — jeden przewód, wiele podzespołów, inne pułapki niż CAN
- [ ] Sieć FlexRay — kiedy ją spotkasz i czym różni się diagnostyka
- [ ] Automotive Ethernet w warsztacie — po co, w jakich autach i jakim narzędziem
- [ ] Protokół UDS — sesje diagnostyczne w praktyce warsztatowej
- [ ] Kody NRC w UDS — co naprawdę znaczy odmowa sterownika
- [ ] Seed & Key — dlaczego sterownik nie chce rozmawiać o wszystkim
- [ ] OBD-II a diagnostyka producenta — gdzie kończy się uniwersalny interfejs
- [ ] Tryb 06 w OBD-II — dane, które mówią więcej niż kod błędu
- [ ] Freeze frame — czytanie warunków, w jakich powstał błąd
- [ ] Kody błędów P, B, C, U — co oznacza pierwsza litera
- [ ] Błędy sporadyczne — jak je złapać rejestratorem zamiast zgadywać
- [ ] Rejestracja danych w jeździe — co ustawić, żeby zapis miał sens
- [ ] Interfejsy diagnostyczne — czym różni się tani klon od narzędzia warsztatowego
- [ ] J1939 w pojazdach ciężarowych — PGN, SPN i FMI w praktyce
- [ ] Adresowanie węzłów w J1939 — kto z kim rozmawia w ciężarówce
- [ ] Programowanie i kodowanie sterownika — różnica, której nie wolno mylić
- [ ] Adaptacje po wymianie części — kiedy są konieczne
- [ ] Sterownik z demontażu — dlaczego rzadko działa po prostu po wpięciu
- [ ] Klonowanie sterowników — ryzyka techniczne i prawne
- [ ] Aktualizacja oprogramowania sterownika — co może pójść źle
- [ ] Sterownik po nieudanej aktualizacji — procedura odzyskiwania
- [ ] Zasilanie sterowników — obwody podtrzymania i wybudzania
- [ ] Sygnał PWM w pojeździe — jak go zmierzyć i zinterpretować
- [ ] Czujniki SENT — nowy standard, którego multimetr nie zmierzy
- [ ] Czujniki Halla kontra indukcyjne — jak je rozróżnić w praktyce
- [ ] Rezolwer w napędzie elektrycznym — zasada i diagnostyka
- [ ] Sterowanie wentylatorami przez PWM — typowe usterki
- [ ] Sterownik świateł LED — matryca, sterowanie i awarie
- [ ] Magistrala danych w przyczepie — złącze 15-pinowe i komunikacja
- [ ] Systemy ADAS — kalibracja po naprawie blacharskiej
- [ ] Kamera cofania i czujniki parkowania — diagnostyka bez oprogramowania fabrycznego
- [ ] Sterownik poduszek powietrznych — bezpieczne postępowanie przy naprawie
- [ ] Tachograf cyfrowy — obsługa serwisowa i typowe błędy komunikacji
- [ ] Instalacja dodatkowego wyposażenia w aucie z CAN — jak nie popsuć sieci
- [ ] Alarmy i blokady dorabiane — najczęstsze błędy montażu
- [ ] Instalacja gazowa LPG a elektronika silnika — punkty styku i konflikty

## Elektromechanika: alternatory, rozruszniki, silniki

- [x] Regeneracja alternatora krok po kroku — co się wymienia, a co zostaje  <!-- 2026-09-29, /blog/regeneracja-alternatora-krok-po-kroku/ -->
- [x] Regulator napięcia w alternatorze — objawy uszkodzenia i pomiar  <!-- 2026-10-31, /blog/regulator-napiecia-alternator-diagnostyka/ -->
- [ ] Alternatory sterowane po LIN — dlaczego stary sposób sprawdzania zawodzi
- [ ] Sprzęgło jednokierunkowe alternatora — objawy zużycia i skutki
- [ ] Diody prostownicze w alternatorze — test bez demontażu
- [ ] Szczotki i pierścienie ślizgowe — granica zużycia w praktyce
- [ ] Łożyska alternatora — rozpoznanie po dźwięku i wymiana
- [ ] Rozrusznik — budowa, typowe awarie i kolejność sprawdzania
- [ ] Bendix i sprzęgło jednokierunkowe rozrusznika — objawy uszkodzenia
- [ ] Elektromagnes rozrusznika — pomiar cewek wciągającej i trzymającej
- [ ] Rozruszniki reduktorowe — czym różni się serwis
- [ ] Silniki krokowe w podzespołach pojazdu — diagnostyka i naprawa
- [ ] Silniki szczotkowe DC — regeneracja czy wymiana
- [ ] Silniki bezszczotkowe BLDC — zasada działania i typowe usterki sterownika
- [ ] Silnik indukcyjny trójfazowy — pomiar izolacji i rezystancji uzwojeń
- [ ] Falownik do silnika trójfazowego — dobór i parametryzacja od podstaw
- [ ] Silnik jednofazowy z kondensatorem — dobór pojemności i objawy jej utraty
- [ ] Przezwajanie silnika — kiedy się opłaca, a kiedy nie
- [ ] Wyważanie wirnika — po co i jakie są skutki zaniedbania
- [ ] Łożyska w silnikach elektrycznych — dobór, smarowanie, montaż na gorąco
- [ ] Prądy łożyskowe przy zasilaniu z falownika — skąd biorą się wżery
- [ ] Zabezpieczenia silnika — przekaźnik termiczny, wyłącznik silnikowy, PTC
- [ ] Rozruch gwiazda-trójkąt — kiedy nadal ma sens
- [ ] Softstart kontra falownik — co wybrać do konkretnej maszyny
- [ ] Pomiar poboru prądu jako wskaźnik stanu maszyny
- [ ] Termowizja w elektromechanice — co widać, czego nie
- [ ] Analiza drgań łożysk — proste narzędzia zamiast drogiego systemu
- [ ] Prądnice i agregaty prądotwórcze — regulacja napięcia i typowe usterki
- [ ] Alternator jako prądnica w instalacji wyspowej — czy to ma sens
- [ ] Instalacja 24 V w pojazdach ciężarowych — masy i spadki napięć
- [ ] Przetwornice 24/12 V — dobór mocy i typowe błędy montażu
- [ ] Akumulatory trakcyjne w wózkach — obsługa i pomiary
- [ ] Ładowanie akumulatorów żelowych i AGM — parametry, których nie wolno przekroczyć
- [ ] Prostowniki i ładowarki warsztatowe — czym różni się dobra od taniej
- [ ] Testery akumulatorów — jak czytać wynik pomiaru rezystancji wewnętrznej
- [ ] Instalacja elektryczna w naczepie — typowe usterki i konserwacja
- [ ] Ogrzewanie postojowe — diagnostyka układu sterowania
- [ ] Wciągniki i suwnice — układ sterowania i bezpieczeństwo
- [ ] Szafa sterownicza od podstaw — dobór aparatury i estetyka montażu

## Klimatyzacja, chłodnictwo i ogrzewanie

- [x] Regeneracja sprężarki klimatyzacji — wyciek na wale i uszczelnienie  <!-- 2026-09-25, /blog/regeneracja-sprezarki-klimatyzacji-wyciek-na-wale/ -->
- [x] Sprzęgło elektromagnetyczne sprężarki — pomiar cewki i regulacja szczeliny  <!-- 2026-11-03, /blog/sprzeglo-elektromagnetyczne-sprezarki-pomiar-i-regulacja/ -->
- [ ] Sprężarka zatarta — jak wypłukać układ, żeby nowa nie padła
- [ ] Wymiana osuszacza — dlaczego to nie jest opcja dodatkowa
- [ ] Zawór rozprężny kontra dysza — różnice w diagnostyce
- [ ] Ciśnienia w układzie klimatyzacji — tabela odczytów i co z nich wynika
- [ ] Za mało czynnika czy za dużo — objawy na manometrach
- [ ] Skraplacz zapchany od zewnątrz — objaw, który udaje poważną usterkę
- [ ] Parownik — mycie, dezynfekcja i kiedy trzeba go wymienić
- [ ] Czujnik ciśnienia w klimatyzacji — pomiar i typowe błędy odczytu
- [ ] Sterownik klimatyzacji automatycznej — kalibracja klap i siłowników
- [ ] Klimatyzacja nie chłodzi na postoju — wentylator, ciśnienie czy sterowanie
- [ ] R134a a R1234yf — czym różni się serwis w praktyce
- [ ] R744 (CO2) w klimatyzacji pojazdów — wysokie ciśnienia i nowe wymagania
- [ ] Stacje do obsługi klimatyzacji — kalibracja i konserwacja
- [ ] Odzysk czynnika — procedura i wymogi formalne
- [ ] Próżnia w układzie — jak długo i dlaczego to najważniejszy etap
- [ ] Wilgoć w układzie — skutki, których nie widać od razu
- [ ] Nieszczelność mikroskopijna — metoda azotowa krok po kroku
- [ ] Barwnik UV — kiedy pomaga, a kiedy zaciemnia obraz
- [ ] Klimatyzacja w pojeździe elektrycznym — pompa ciepła i chłodzenie baterii
- [ ] Klimatyzacja postojowa w ciężarówce — budowa i serwis
- [ ] Chłodnie samochodowe — agregat, sterowanie i rejestracja temperatury
- [ ] Klimatyzacja w kabinie ciągnika — filtry i szczelność kabiny
- [ ] Pompa ciepła powietrze-woda — zasada i najczęstsze błędy montażu
- [ ] Czynniki chłodnicze nowej generacji — co wypiera stare mieszaniny
- [ ] Sprężarki spiralne i tłokowe — różnice w eksploatacji
- [ ] Presostaty w układach chłodniczych — nastawy i kontrola
- [ ] Lutowanie rur miedzianych w chłodnictwie — technika i osłona azotem
- [ ] Rury aluminiowe w klimatyzacji samochodowej — naprawa czy wymiana
- [ ] Szybkozłącza w układach klimatyzacji — typowe przyczyny nieszczelności
- [ ] Olej w sprężarce — kontrola ilości po naprawie układu
- [ ] Zapach z nawiewu — źródła i skuteczne metody usunięcia
- [ ] Filtr kabinowy — węglowy, antyalergiczny, jak często wymieniać
- [ ] Nagrzewnica postojowa Webasto i Eberspächer — diagnostyka usterek
- [ ] Ogrzewanie elektryczne PTC — kiedy się załącza i jak sprawdzić
- [ ] Termostaty elektroniczne w układzie chłodzenia silnika
- [ ] Układ chłodzenia pod ciśnieniem — próba szczelności krok po kroku

## Spawanie, lutowanie i łączenie metali

- [x] Spawanie aluminium MIG — podajnik, uchwyt spool gun i drut miękki  <!-- 2026-08-17, /blog/spawanie-aluminium-mig-podajnik-spool-gun-drut/ -->
- [x] TIG AC — dobór balansu i częstotliwości przy aluminium  <!-- 2026-08-19, /blog/tig-ac-balans-i-czestotliwosc-aluminium/ -->
- [x] Elektrody wolframowe — dobór, szlifowanie i wpływ na jarzenie łuku  <!-- 2026-08-21, /blog/elektrody-wolframowe-dobor-szlifowanie/ -->
- [x] Zajarzanie HF kontra lift arc — różnice i zastosowania  <!-- 2026-08-31, /blog/zajarzanie-hf-kontra-lift-arc/ -->
- [x] Spawanie cienkiej blachy — sposoby na uniknięcie przepaleń  <!-- 2026-09-19, /blog/spawanie-cienkie-blachy-metody-techniczne/ -->
- [ ] Spawanie punktowe blach karoseryjnych — parametry i przygotowanie
- [ ] Spawanie żeliwa — elektrody niklowe i reżim temperaturowy
- [ ] Napawanie zużytych powierzchni — dobór materiału dodatkowego
- [ ] Spawanie stali ocynkowanej — zagrożenia i wentylacja stanowiska
- [ ] Spawanie rur — kolejność, podkładki i grań od środka
- [ ] Spoiny pachwinowe — grubość, wymiary i najczęstsze błędy
- [ ] Przygotowanie krawędzi — ukosowanie i odstęp w praktyce
- [ ] Podgrzewanie wstępne — kiedy jest konieczne i jak je kontrolować
- [ ] Obróbka cieplna po spawaniu — odprężanie konstrukcji
- [ ] Wady spoin — podtopienia, przyklejenia, pory i ich przyczyny
- [ ] Badanie spoin bez niszczenia — wizualne, penetracyjne, magnetyczne
- [ ] Kwalifikowanie spawaczy i technologii — co to znaczy w małym warsztacie
- [ ] Drut proszkowy — kiedy wygrywa z drutem litym
- [ ] MMA na budowie — dobór elektrod otulonych do warunków
- [ ] Elektrody zasadowe — suszenie i przechowywanie
- [ ] Spawanie w pozycjach wymuszonych — technika i parametry
- [ ] Spawanie stali wysokowytrzymałych — ograniczenia energii liniowej
- [ ] Spawanie różnoimienne — stal nierdzewna do czarnej
- [ ] Zgrzewanie kołków i nakrętek — technologia w naprawach nadwozi
- [ ] Lutospawanie MIG brazing — gdzie zastępuje spawanie
- [ ] Lutowanie twarde w chłodnictwie — spoiwa fosforowe i srebrne
- [ ] Lutowanie aluminium — spoiwa niskotemperaturowe i topniki
- [ ] Palnik acetylenowo-tlenowy — bezpieczna obsługa i regulacja płomienia
- [ ] Cięcie plazmowe — dobór dyszy i parametry do grubości
- [ ] Cięcie tlenowe — kiedy nadal jest najlepszym wyborem
- [ ] Klejenie konstrukcyjne metali — alternatywa dla spawania
- [ ] Nitonakrętki i nity zrywalne — dobór i narzędzia
- [ ] Regeneracja gwintów — helicoil, wkładki, wiercenie osi
- [ ] Prostowanie po spawaniu — metody termiczne i mechaniczne
- [ ] Stanowisko spawalnicze — odciąg, oświetlenie, ochrona wzroku
- [ ] Przyłbice samościemniające — parametry, na które warto patrzeć
- [ ] Uziemienie masy spawalniczej — jak uniknąć przepływu prądu przez łożyska
- [ ] Spawanie przy pojeździe z elektroniką — jak nie uszkodzić sterowników
- [ ] Konserwacja spoin — malowanie, cynkowanie, zabezpieczenie antykorozyjne
- [ ] Dobór gazu do stali nierdzewnej — mieszanki z helem i wodorem
- [ ] Ekonomia gazu osłonowego — reduktory, przepływ i straty
- [ ] Naprawa pękniętych ram i podwozi — ocena i technologia

## Naprawa sprzętu spawalniczego i warsztatowego

- [x] Spawarka inwertorowa — schemat blokowy i kolejność diagnozy  <!-- 2026-10-07, /blog/spawarka-inwertorowa-diagnostyka/ -->
- [x] Układy scalone SG3525 i KA3525A w spawarkach — objawy uszkodzenia  <!-- 2026-10-15, /blog/uklady-scalone-sg3525-i-ka3525a-w-spawarkach/ -->
- [x] Kondensatory 470u/400V w inwerterze — jak sprawdzić i czym zastąpić  <!-- 2026-10-29, /blog/kondensatory-470u-400v-inwerter-diagnostyka/ -->
- [ ] Tranzystory kluczujące w spawarce — dlaczego padają seriami
- [ ] Zabezpieczenie termiczne świeci od razu po włączeniu — przyczyny
- [ ] Zasilacz pomocniczy w spawarce — najczęstsze miejsce awarii
- [ ] Mostek prostowniczy i miękki start — kolejność sprawdzania
- [ ] Buczenie transformatora w spawarce — co oznacza
- [ ] Spawarka nie jarzy łuku, wentylator działa — od czego zacząć
- [ ] Pomiar w układzie pod napięciem — bezpieczna metodyka i separacja
- [ ] Naprawa uchwytu TIG i przewodu masy — drobiazgi, które psują spoinę
- [ ] Podajnik drutu — regulacja docisku i rolki do różnych drutów
- [ ] Chłodnica uchwytu TIG — przepływ, płyn i objawy zapowietrzenia
- [ ] Prostownik warsztatowy — modernizacja starego sprzętu
- [ ] Szlifierka kątowa — regeneracja wirnika i wymiana łożysk
- [ ] Elektronarzędzia akumulatorowe — regeneracja pakietów ogniw
- [ ] Ładowarki do elektronarzędzi — typowe usterki i naprawa
- [ ] Kompresor warsztatowy — zawór zwrotny, presostat i typowe awarie
- [ ] Osuszacz sprężonego powietrza — po co i kiedy się zwraca
- [ ] Podnośnik warsztatowy — przegląd, hydraulika i bezpieczeństwo
- [ ] Wyważarka do kół — kalibracja i błędy pomiaru
- [ ] Prostownik do wyciągania wgnieceń — zasada i praktyka
- [ ] Nagrzewnica indukcyjna — zastosowania w warsztacie
- [ ] Myjka ultradźwiękowa — dobór kąpieli i czas mycia części
- [ ] Stacja lutownicza — kalibracja grota i typowe usterki
- [ ] Zasilacz laboratoryjny w warsztacie samochodowym — po co i jaki
- [ ] Oscyloskop warsztatowy — jaki wybrać do diagnostyki pojazdów
- [ ] Multimetr — parametry, które naprawdę mają znaczenie w warsztacie
- [ ] Kamera termowizyjna — dobór rozdzielczości do zastosowań warsztatowych

## CNC: budowa maszyn, obróbka i pomiary

- [x] Frezarka CNC od zera — co kupić na start i w jakiej kolejności  <!-- 2026-08-29, /blog/frezarka-cnc-od-zera-poradnik/ -->
- [x] Retrofit tokarki na CNC — silniki, enkodery, sterowanie  <!-- 2026-09-13, /blog/retrofit-tokarki-na-cnc-silniki-enkodery-sterowanie/ -->
- [x] Prowadnice liniowe kontra tuleje — sztywność i cena  <!-- 2026-09-27, /blog/prowadnice-liniowe-kontra-tuleje/ -->
- [x] Śruby trapezowe kontra kulowe — luz, sprawność, zastosowania  <!-- 2026-10-19, /blog/sruby-trapezowe-kontra-kulowe/ -->
- [ ] Kompensacja luzu w osi — kiedy pomaga, a kiedy maskuje problem
- [ ] Krańcówki i bazowanie maszyny — czujniki mechaniczne, indukcyjne, optyczne
- [ ] Sterowniki GRBL, LinuxCNC, Mach — co wybrać do jakiej maszyny
- [ ] Zasilanie i ekranowanie w szafie CNC — walka z zakłóceniami
- [ ] Falownik wrzeciona — parametryzacja i sterowanie z programu
- [ ] Chłodzenie narzędzia — mgła olejowa, powietrze, emulsja
- [ ] Odciąg wiórów i pyłu — projekt instalacji do małej hali
- [ ] Frezy do aluminium — geometria, powłoki i posuwy
- [ ] Frezowanie stali na małej maszynie — realne parametry
- [ ] Frezowanie tworzyw — topienie materiału i jak go uniknąć
- [ ] Grawerowanie — dobór frezu V i głębokości
- [ ] Toczenie CNC — cykle obróbcze bez pisania G-code ręcznie
- [ ] Gwintowanie na CNC — sztywne i z kompensacją
- [ ] Wiercenie głębokich otworów — cykle przerywane i odprowadzanie wióra
- [ ] Mocowanie detalu — imadła, uchwyty, przyssawki, mocowanie na wosk
- [ ] Bazowanie detalu i sonda pomiarowa — jak trafić w zerowy punkt
- [ ] CAM od podstaw — od modelu do ścieżki narzędzia
- [ ] Strategie obróbkowe — adaptacyjna, konturowa, resztkowa
- [ ] Symulacja obróbki — jak wyłapać kolizję przed maszyną
- [ ] Postprocesor — dlaczego ten sam program nie działa na innej maszynie
- [ ] Korektory narzędzi — długość, promień i typowe pomyłki
- [ ] Zużycie narzędzia — jak je rozpoznać po powierzchni detalu
- [ ] Drgania i chatter — diagnoza po dźwięku i śladzie
- [ ] Dokładność wymiarowa — pomiar, kompensacja i realne tolerancje
- [ ] Tolerancje i pasowania — dobór do funkcji części
- [ ] Chropowatość powierzchni — od czego naprawdę zależy
- [ ] Obróbka po hartowaniu — kiedy szlifowanie, kiedy frez
- [ ] Cięcie laserem, plazmą i wodą — porównanie dla warsztatu
- [ ] Gięcie blachy — rozwinięcia, promienie i odsprężynowanie
- [ ] Projektowanie części pod obróbkę — jak nie utrudnić sobie życia
- [ ] Rysunek techniczny — co musi się na nim znaleźć dla wykonawcy
- [ ] Kontrola jakości detalu — suwmiarka, mikrometr, czujnik zegarowy
- [ ] Płyta pomiarowa i przymiary — organizacja pomiarów w warsztacie
- [ ] Kalkulacja kosztu detalu — czas maszynowy, narzędzia, materiał
- [ ] Wycena zlecenia obróbkowego — na co uważać przy jednostkówce
- [ ] Materiały konstrukcyjne — dobór stali do zastosowania
- [ ] Obróbka cieplna stali — hartowanie, odpuszczanie, wyżarzanie
- [ ] Anodowanie i powłoki ochronne — kiedy warto

## Druk 3D, skanowanie i odtwarzanie części

- [x] Drukarka FDM w warsztacie — co realnie da się na niej zrobić  <!-- 2026-09-17, /blog/drukarka-fdm-w-warsztacie/ -->
- [x] Pierwsza warstwa — kalibracja stołu i typowe problemy  <!-- 2026-10-01, /blog/pierwsza-warstwa-kalibracja-stolu-i-typowe-problemy/ -->
- [x] Warping i odklejanie — temperatura, komora, adhezja  <!-- 2026-10-11, /blog/warping-i-odklejanie-wydrukow-3d/ -->
- [x] PLA, PETG, ABS, ASA — do czego który materiał w warsztacie  <!-- 2026-10-25, /blog/dobor-materialow-do-druku-3d-w-warsztacie/ -->
- [ ] Nylon i włókna węglowe — wytrzymałość kontra trudność druku
- [ ] Suszenie filamentu — dlaczego zmienia wszystko
- [ ] Wypełnienie i ścianki — co naprawdę decyduje o wytrzymałości
- [ ] Orientacja wydruku a kierunek obciążenia
- [ ] Podpory — kiedy potrzebne i jak ich uniknąć projektowaniem
- [ ] Tolerancje w druku 3D — luzy pasowań w praktyce
- [ ] Gwinty w wydrukach — nacinane, wtapiane, nakrętki zatapiane
- [ ] Wtapianie mosiężnych insertów — technika i dobór otworu
- [ ] Łączenie wydruków — kleje, zgrzewanie, wzmocnienia
- [ ] Obróbka po druku — szlifowanie, wygładzanie oparami, malowanie
- [ ] Druk z materiałów odpornych na temperaturę — pod maską auta
- [ ] Odporność chemiczna wydruków — paliwo, oleje, płyny eksploatacyjne
- [ ] Druk SLA żywicą — kiedy wygrywa nad FDM
- [ ] Bezpieczeństwo pracy z żywicami — wentylacja i ochrona skóry
- [ ] Druk z metalu — dostępne technologie i realne koszty
- [ ] Odlewanie w formach drukowanych — żywice i silikony
- [ ] Skanowanie 3D — technologie i realna dokładność
- [ ] Skanowanie części o błyszczącej powierzchni — matowanie i markery
- [ ] Od chmury punktów do modelu — proces w praktyce
- [ ] Inżynieria odwrotna części zamiennej — od pomiaru do wydruku
- [ ] Pomiar części bez skanera — suwmiarka, promieniomierz, odrys
- [ ] Modelowanie parametryczne dla warsztatu — od czego zacząć
- [ ] Darmowe programy CAD — co wystarczy do części zamiennych
- [ ] Gdzie szukać gotowych modeli i jak sprawdzić ich jakość
- [ ] Prawa autorskie do modeli 3D — czego nie wolno kopiować
- [ ] Wydruk prototypu przed obróbką CNC — oszczędność czy strata czasu
- [ ] Oprzyrządowanie warsztatowe z druku 3D — szablony i uchwyty
- [ ] Obudowy elektroniki z drukarki — szczelność i odprowadzanie ciepła
- [ ] Koła zębate z druku 3D — kiedy wytrzymają
- [ ] Uszczelki i elementy elastyczne z TPU
- [ ] Naprawa plastików w aucie — zgrzewanie kontra wydruk nowej części
- [ ] Konserwacja drukarki 3D — dysze, pasy, prowadnice
- [ ] Kalibracja przepływu i kroków ekstrudera
- [ ] Koszt wydruku — jak policzyć realną cenę części

## Kursy ESP32 i Arduino — podstawy i warsztat

- [x] Kurs ESP32 część 5 — BLE i komunikacja z telefonem  <!-- 2026-08-26, /blog/kurs-esp32-czesc-5-ble-i-komunikacja-z-telefonem/ -->
- [x] Kurs ESP32 część 6 — karta SD i rejestrator pomiarów  <!-- 2026-09-07, /blog/kurs-esp32-karta-sd-rejestrator-pomiarow/ -->
- [x] Kurs ESP32 część 7 — wyświetlacz OLED i menu obsługiwane enkoderem  <!-- 2026-09-15, /blog/kurs-esp32-oled-enkoder/ -->
- [ ] Kurs ESP32 część 8 — deep sleep i praca na baterii przez miesiące
- [ ] Kurs ESP32 część 9 — aktualizacja oprogramowania przez Wi-Fi (OTA)
- [ ] Kurs ESP32 część 10 — własny panel WWW do sterowania urządzeniem
- [ ] ESP32 dwa rdzenie — zadania FreeRTOS zamiast jednej pętli loop
- [ ] Przerwania w ESP32 — kiedy są konieczne i jak ich nie zepsuć
- [ ] Timery sprzętowe — pomiar czasu bez blokowania programu
- [ ] Program bez delay — jak pisać kod obsługujący wiele rzeczy naraz
- [ ] ADC w ESP32 — nieliniowość, kalibracja i realna dokładność
- [ ] DAC i generowanie sygnału analogowego
- [ ] PWM w ESP32 — sterowanie mocą, jasnością i serwomechanizmem
- [ ] I2C od podstaw — adresy, skaner magistrali, typowe problemy
- [ ] SPI od podstaw — kiedy szybszy od I2C i jak podłączyć kilka układów
- [ ] UART i konwertery poziomów — łączenie 3,3 V z 5 V
- [ ] Pamięć NVS i EEPROM — zapisywanie ustawień na stałe
- [ ] SPIFFS i LittleFS — pliki w pamięci mikrokontrolera
- [ ] MicroPython na ESP32 — czym różni się od Arduino w praktyce
- [ ] ESP-IDF kontra Arduino — kiedy warto przesiąść się na środowisko natywne
- [ ] PlatformIO — wygodniejsza praca niż w Arduino IDE
- [ ] Debugowanie ESP32 — monitor szeregowy, logi, core dump
- [ ] Reset i brownout — dlaczego układ restartuje się losowo
- [ ] Zasilanie ESP32 — dlaczego USB z komputera często nie wystarcza
- [ ] Anteny i zasięg Wi-Fi — układ płytki i typowe błędy montażu
- [ ] ESP-NOW — komunikacja między płytkami bez routera
- [ ] LoRa z ESP32 — zasięg na terenie zakładu
- [ ] MQTT i broker lokalny — szkielet systemu pomiarowego
- [ ] Home Assistant i ESPHome — automatyka bez pisania kodu
- [ ] Bezpieczeństwo urządzeń IoT — hasła, szyfrowanie, aktualizacje
- [ ] Zegar czasu rzeczywistego i synchronizacja NTP
- [ ] Watchdog — jak zabezpieczyć urządzenie przed zawieszeniem
- [ ] Projektowanie płytki pod ESP32 — od modułu do własnego PCB
- [ ] Lutowanie modułów SMD w warsztacie — stacja gorącego powietrza
- [ ] Zasilanie bateryjne — ogniwa 18650, ładowarka TP4056 i pomiar napięcia
- [ ] Panel słoneczny do czujnika zewnętrznego — dobór mocy
- [ ] Obudowa i szczelność IP — jak zamknąć elektronikę w warsztacie
- [ ] Zabezpieczenie wejść mikrokontrolera w środowisku przemysłowym
- [ ] Optoizolacja i separacja galwaniczna — po co i jak
- [ ] Sterowanie przekaźnikiem i stycznikiem z ESP32 — bezpiecznie
- [ ] Raspberry Pi Pico kontra ESP32 — porównanie do zastosowań warsztatowych
- [ ] Arduino Nano, UNO, Mega — co jeszcze ma sens w 2026

## ESP32 z gotowymi zestawami czujników — projekty warsztatowe

- [x] DHT22 i AHT20 — pomiar temperatury i wilgotności w hali  <!-- 2026-08-16, /blog/dht22-aht20-pomiar-temperatury-wilgotnosci/ -->
- [x] DS18B20 — wiele czujników temperatury na jednym przewodzie  <!-- 2026-08-16, /blog/ds18b20-wiele-czujnikow-na-jednym-przewodzie/ -->
- [x] BME280 — temperatura, wilgotność i ciśnienie w jednym module  <!-- 2026-08-26, /blog/bme280-czujnik-temperatury-wilgotnosci-cisnienia/ -->
- [x] MLX90614 — bezdotykowy pomiar temperatury łożyska  <!-- 2026-09-11, /blog/mlx90614-bezdotykowy-pomiar-temperatury-lozyska/ -->
- [x] Termopara typu K z MAX6675 — pomiar wysokich temperatur  <!-- 2026-09-23, /blog/termopara-typu-k-z-max6675/ -->
- [x] PT100 z MAX31865 — pomiar precyzyjny w układach przemysłowych  <!-- 2026-10-13, /blog/pt100-z-max31865-pomiar-precyzyjny/ -->
- [x] MPU6050 — pomiar drgań i przechyłu maszyny  <!-- 2026-10-21, /blog/mpu6050-pomiar-drgan-i-przechylu-maszyny/ -->
- [x] ADXL345 — akcelerometr do wykrywania nadmiernych wibracji  <!-- 2026-10-27, /blog/adxl345-akcelerometr-wibracje/ -->
- [ ] HC-SR04 — pomiar odległości ultradźwiękami i jego ograniczenia
- [ ] VL53L0X — laserowy pomiar odległości z dokładnością do milimetrów
- [ ] Czujnik indukcyjny zbliżeniowy — zliczanie obrotów wału
- [ ] Czujnik Halla A3144 — obrotomierz i wykrywanie położenia
- [ ] Enkoder obrotowy — pomiar położenia i prędkości
- [ ] Czujnik prądu ACS712 — pomiar poboru maszyny
- [ ] Czujnik prądu SCT-013 — pomiar bez ingerencji w instalację
- [ ] INA219 i INA226 — pomiar prądu i mocy po I2C
- [ ] PZEM-004T — pomiar zużycia energii w warsztacie
- [ ] Przekładnik prądowy — bezpieczne podłączenie do mikrokontrolera
- [ ] MQ-2 i MQ-135 — czujniki gazów i ich realna wiarygodność
- [ ] MH-Z19 — pomiar CO2 w warsztacie i sterowanie wentylacją
- [ ] SDS011 — pomiar pyłu zawieszonego przy stanowisku szlifierskim
- [ ] Czujnik tlenku węgla — bezpieczeństwo w hali z silnikami
- [ ] Czujnik dymu — czy nadaje się do warsztatu spawalniczego
- [ ] BH1750 — pomiar natężenia oświetlenia stanowiska
- [ ] Czujnik ruchu PIR — automatyka oświetlenia w hali
- [ ] Bariera świetlna — zabezpieczenie strefy niebezpiecznej maszyny
- [ ] Czujnik wilgotności gleby — projekt spoza warsztatu na rozgrzewkę
- [ ] Czujnik poziomu cieczy — kontrola zbiornika emulsji
- [ ] Czujnik przepływu wody YF-S201 — kontrola chłodzenia maszyny
- [ ] Czujnik ciśnienia BMP280 — pomiar w układzie pneumatycznym
- [ ] Przetwornik ciśnienia 4-20 mA — podłączenie do ESP32
- [ ] Sygnał 0-10 V — jak go poprawnie odczytać mikrokontrolerem
- [ ] Tensometr i HX711 — waga warsztatowa własnej konstrukcji
- [ ] Czujnik siły nacisku — pomiar w prasie hydraulicznej
- [ ] RFID RC522 — kontrola dostępu do narzędziowni
- [ ] Czytnik kodów kreskowych — ewidencja części
- [ ] Moduł RTC DS3231 — dokładny czas w rejestratorze
- [ ] Karta microSD — zapis pomiarów w formacie CSV
- [ ] Wyświetlacz LCD 1602 z I2C — prosty pulpit maszyny
- [ ] Wyświetlacz TFT — czytelny panel do warsztatu
- [ ] Wyświetlacz e-ink — tablica informacyjna bez zasilania
- [ ] Matryca LED WS2812 — sygnalizacja stanu maszyny kolorem
- [ ] Buzzer i alarm dźwiękowy — sygnalizacja przekroczeń
- [ ] Moduł przekaźnikowy — sterowanie odbiornikami 230 V
- [ ] Sterowanie serwomechanizmem — klapy, zawory, mechanizmy
- [ ] Sterownik silnika krokowego A4988 i TMC2209
- [ ] Sterownik silnika DC L298N i lepsze zamienniki
- [ ] Moduł CAN SN65HVD230 — podsłuch magistrali pojazdu
- [ ] Konwerter RS-485 MAX485 — komunikacja na duże odległości
- [ ] Modbus RTU z ESP32 — odczyt z falownika i licznika energii
- [ ] Moduł GSM SIM800 — alarm SMS z maszyny
- [ ] Moduł GPS NEO-6M — lokalizacja sprzętu na budowie
- [ ] Kamera ESP32-CAM — podgląd stanowiska i zdjęcia na żądanie
- [ ] ESP32-CAM z detekcją ruchu — prosty monitoring warsztatu
- [ ] Mikrofon MAX9814 — pomiar hałasu na stanowisku
- [ ] Czujnik zbliżeniowy pojemnościowy — wykrywanie poziomu w zbiorniku
- [ ] Kontaktron — kontrola otwarcia bramy i drzwi hali
- [ ] Czujnik wibracji SW-420 — najprostszy wykrywacz pracy maszyny
- [ ] Czujnik temperatury i wilgotności do suszarki filamentu
- [ ] Stacja pogodowa dla warsztatu — komplet czujników i zasilanie
- [ ] Rejestrator temperatury w chłodni — wymogi i realizacja
- [ ] Licznik motogodzin maszyny — pomiar bez ingerencji w instalację
- [ ] System kontroli emulsji i chłodziwa w maszynie CNC
- [ ] Monitorowanie sprężarki — ciśnienie, temperatura, czas pracy
- [ ] Nadzór nad agregatem prądotwórczym — pomiary i alarmy
- [ ] Sterownik ogrzewania hali z harmonogramem
- [ ] Automatyka wentylacji stanowiska spawalniczego
- [ ] System powiadomień o awarii — od czujnika do telefonu
- [ ] Panel andon — sygnalizacja stanu produkcji
- [ ] Zliczanie sztuk na stanowisku — czujnik i licznik
- [ ] Pomiar czasu cyklu maszyny — dane zamiast wrażeń
- [ ] Zdalne wyłączanie maszyny — bezpieczeństwo i wymagania

## Python, automatyzacja i dane w warsztacie

- [x] Python od zera dla mechanika — pierwszy skrypt, który coś liczy  <!-- 2026-08-16, /blog/python-dla-mechanika-pierwszy-skrypt/ -->
- [x] Odczyt danych z rejestratora i wykres w kilkunastu linijkach  <!-- 2026-09-05, /blog/odczyt-danych-z-rejestratora-i-wykres/ -->
- [x] Analiza logów z magistrali CAN w Pythonie  <!-- 2026-11-05, /blog/analiza-logow-magistrali-can-python/ -->
- [ ] Dekodowanie ramek CAN z pliku — od bajtów do wartości fizycznych
- [ ] Automatyczne raporty miesięczne z pliku Excel
- [ ] Faktury i zestawienia — automatyzacja powtarzalnej roboty biurowej
- [ ] Baza narzędzi i części w arkuszu kontra prosta baza danych
- [ ] Skrypt do wyceny detalu na podstawie czasu i materiału
- [ ] Odczyt z Modbus w Pythonie — komunikacja z falownikiem
- [ ] Zapis pomiarów do bazy i wykresy historyczne
- [ ] Prosty serwer w sieci lokalnej do zbierania danych z czujników
- [ ] Kopie zapasowe danych warsztatu — jak to zautomatyzować
- [ ] Harmonogram przeglądów maszyn — przypomnienia automatyczne
- [ ] Etykiety i kody QR do oznaczania części
- [ ] Generowanie dokumentacji zdjęciowej naprawy
- [ ] Rozpoznawanie tekstu ze zdjęć tabliczek znamionowych
- [ ] Obróbka zdjęć z warsztatu do publikacji w sieci
- [ ] Prosta strona z ofertą warsztatu — statyczna, szybka, tania
- [ ] Automatyczne pobieranie kursów walut do wyceny części z importu
- [ ] Powiadomienia na telefon ze skryptu — najprostsze sposoby
- [ ] Wersjonowanie własnych skryptów i programów maszyn
- [ ] Git dla nieprogramisty — po co i jak zacząć

## AI, automatyzacja i cyfryzacja zakładu

- [x] Pierwsza automatyzacja n8n w firmie — od zapytania do szkicu odpowiedzi  <!-- 2026-11-19, /blog/n8n-pierwsza-automatyzacja-w-firmie/ -->
- [ ] n8n od podstaw — wyzwalacze, dane między krokami i test pierwszego workflow
- [ ] Bezpieczny import workflow n8n — węzły, poświadczenia, dane testowe i wyłączone wyzwalacze
- [ ] Obsługa błędów w n8n — kiedy ponawiać wykonanie i jak unikać duplikatów
- [ ] Zatwierdzanie wyniku agenta w n8n — szkic, akceptacja przez pracownika i historia decyzji
- [ ] n8n, CRM i poczta — kwalifikacja zapytań w małej firmie usługowej
- [ ] n8n, e-commerce i magazyn — jak obsłużyć rozbieżne stany i korekty
- [ ] Z dokumentu PDF do kolejki wyjątków — OCR, walidacja i decyzja pracownika
- [ ] Firmowy asystent z dokumentacją — RAG, źródła odpowiedzi i podział dostępu
- [ ] Jak przeprowadzić pilotaż agenta AI w dużej firmie — jeden dział, dane testowe i pomiar wyniku
- [ ] Automatyczne szkice treści z n8n — planowanie, akceptacja i obsługa błędu publikacji
- [ ] ChatGPT, Claude i Gemini w biurze — ćwiczenia z dokumentem i weryfikacją źródeł
- [ ] Claude Code od podstaw — pierwsze zadanie w repozytorium i przegląd zmian
- [ ] Codex dla pracownika technicznego — jak zlecić poprawkę, sprawdzić diff i uruchomić test
- [ ] Hermes Agent w firmie — dobór narzędzi, podział dostępu i zasady pracy z pamięcią
- [ ] Google Antigravity w pracy zespołu — plan zadania, próba lokalna i odbiór wyniku
- [ ] Visual Studio Code z asystentem AI — jak czytać poprawki i sprawdzać je testami
- [ ] Agent AI na zamówienie — jak opisać zadania, dane, narzędzia i czynności do akceptacji
- [ ] Szkolenie po wdrożeniu n8n — ćwiczenia dla operatora, instrukcja awaryjna i odbiór obsługi

- [x] Modele językowe przy diagnostyce — gdzie pomagają, gdzie zmyślają  <!-- 2026-09-03, /blog/modele-jezykowe-w-diagnostyce/ -->
- [x] Weryfikacja odpowiedzi AI danymi z dokumentacji serwisowej  <!-- 2026-10-23, /blog/weryfikacja-odpowiedzi-ai-dokumentacja-serwisowa/ -->
- [x] Rozpoznawanie obrazu w kontroli jakości detali — realne możliwości  <!-- 2026-11-07, /blog/rozpoznawanie-obrazu-w-kontroli-jakosci-detali/ -->
- [ ] Wykrywanie wad spoin na zdjęciach — co da się zautomatyzować
- [ ] Predykcja awarii z danych drganiowych — od pomiaru do decyzji
- [ ] Analiza dźwięku maszyny jako sygnał wczesnego ostrzegania
- [ ] Lokalne modele AI na komputerze warsztatowym — sprzęt i koszty
- [ ] Prywatność danych klientów przy korzystaniu z narzędzi AI
- [ ] Automatyczne opisy usług i ofert — gdzie to ma sens
- [ ] Asystent głosowy w hali — czy warto przy hałasie
- [ ] Cyfrowy bliźniak maszyny — czy to ma sens w małym zakładzie
- [ ] Systemy MES dla małego warsztatu — czy warto
- [ ] Zbieranie danych produkcyjnych bez drogiego systemu
- [ ] Wizualizacja stanu produkcji na ekranie w hali
- [ ] Skanowanie i archiwizacja dokumentacji technicznej
- [ ] Rzeczywistość rozszerzona w serwisie — stan faktyczny technologii
- [ ] Roboty współpracujące — kiedy opłacają się w małej produkcji
- [ ] Automatyzacja stanowiska spawalniczego — pozycjoner i robot
- [ ] Bezpieczeństwo maszyn zautomatyzowanych — wymagania formalne
- [ ] Dotacje na automatyzację i cyfryzację — na co zwrócić uwagę

## CNC: sterowanie, CSMIO, enkodery i modernizacja

- [x] CSMIO/IP-S, IP-M i IP-A — czym się różnią i który wybrać do swojej maszyny  <!-- 2026-10-05, /blog/csmio-ip-s-ip-m-ip-a-porownanie/ -->
- [ ] Migracja ze sterowania SSK-MB2 na CSMIO/IP-S — plan przebudowy krok po kroku
- [ ] SSK-MB2 kontra CSMIO — co realnie zyskujesz po zamianie
- [ ] Przygotowanie szafy pod CSMIO — zasilanie, masy, rozmieszczenie aparatury
- [ ] CSMIO/IP-S — pierwsze uruchomienie i konfiguracja sieci Ethernet
- [ ] Plugin CSMIO do Mach3 — instalacja, biblioteki .NET i typowe błędy startu
- [ ] Konfiguracja osi w Mach3 z CSMIO — kroki na milimetr, przyspieszenia, zjazdy
- [ ] Sygnały step/dir — różnicowe kontra pojedyncze i dlaczego to ważne
- [ ] Okablowanie step/dir do sterowników krokowych — przekroje, ekrany, długości
- [ ] Wejścia i wyjścia CSMIO — podłączenie krańcówek, bazowania i awaryjnego stopu
- [ ] Bazowanie maszyny z CSMIO — czujniki, kolejność osi, offsety
- [ ] Moduł CSMIO-ENC — do czego służy i kiedy jest naprawdę potrzebny
- [ ] Montaż enkodera na wrzecionie — sprzęgło, mocowanie, dobór rozdzielczości
- [ ] Sygnał indeksu enkodera — po co jest i jak sprawdzić, czy działa
- [ ] Podłączenie CSMIO-ENC po szynie CAN — zasilanie i adresacja modułów
- [ ] Gwintowanie na tokarce z CSMIO-ENC — konfiguracja i pierwszy gwint
- [ ] Makro M20 i pozycjonowanie wrzeciona — konfiguracja i ograniczenia
- [ ] Konflikt makra M20 z funkcją „Align at stop" — czego nie wolno łączyć
- [ ] Przekładnia między silnikiem a wrzecionem — przełożenie w zakładce Spindle Pulleys
- [ ] Enkoder wrzeciona przeciążony sygnałem — dlaczego nie wolno go rozgałęziać
- [ ] Sterowanie falownikiem wrzeciona z CSMIO — 0-10 V i sygnały kierunku
- [ ] Pomiar rzeczywistych obrotów wrzeciona — kontrola zamiast wiary w nastawę
- [ ] Sonda pomiarowa i czujnik długości narzędzia w CSMIO
- [ ] Mach3 kontra Mach4 — czy migracja się opłaca
- [ ] LinuxCNC z kartami Mesa jako alternatywa dla CSMIO — porównanie kosztów
- [ ] Zamknięta pętla na krokowcach — co to realnie daje, a czego nie naprawi
- [ ] Silnik krokowy z wbudowanym enkoderem kontra doklejony enkoder DIY
- [ ] Sterowniki hybrydowe HBS86H i iHSS57 — zasada działania i dobór
- [ ] Krokowiec z dwustronnym wałkiem — podstawa taniej przebudowy na zamkniętą pętlę
- [ ] Dobór enkodera do silnika krokowego — impulsy na obrót i rozdzielczość napędu
- [ ] Mocowanie enkodera do krokowca — uchwyt drukowany 3D i osiowość
- [ ] Sprzęgło do enkodera — dlaczego sztywne mocowanie kończy się błędami
- [ ] Enkoder z wyjściem line driver kontra open collector — co wybrać
- [ ] Zasilanie enkoderów 5 V w szafie CNC — spadki napięć i separacja
- [ ] Ekranowanie przewodów enkoderowych — najczęstsze źródło gubionych impulsów
- [ ] Zakłócenia od falownika w torze enkodera — objawy i skuteczne środki zaradcze
- [ ] Sygnał alarmu ze sterownika hybrydowego — podłączenie do CSMIO i reakcja programu
- [ ] Wykrywanie zgubionych kroków — jak potwierdzić problem pomiarem
- [ ] Kompensacja błędu pozycji — czego zamknięta pętla nie załatwi za mechanikę
- [ ] Strojenie sterownika hybrydowego — prąd, mikrokrok, filtry
- [ ] Rezonans silnika krokowego — objawy i sposoby tłumienia
- [ ] Moment trzymający a moment przy prędkości — dlaczego krokowiec gubi kroki na szybkich zjazdach
- [ ] Zasilanie silników krokowych — napięcie, prąd i realny wpływ na dynamikę
- [ ] Krokowiec, hybryda, serwo AC — porównanie kosztu i efektu na jednej maszynie
- [ ] Przebudowa maszyny na zamkniętą pętlę najtaniej — kompletny kosztorys DIY
- [ ] Enkodery liniowe na osiach — kiedy mają sens w maszynie domowej
- [ ] Pomiar dokładności pozycjonowania — czujnik zegarowy i test powtarzalności
- [ ] Luz w mechanice kontra błąd sterowania — jak je rozróżnić pomiarem
- [ ] Dokumentowanie przebudowy maszyny — schematy, opisy, zdjęcia

