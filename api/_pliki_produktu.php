<?php
declare(strict_types=1);

/**
 * Pliki produktu inne niż zdjęcia: wideo, modele 3D i szkice.
 *
 * PO CO TO ISTNIEJE: warsztat sprzedaje rzeczy, których zdjęcie nie pokazuje.
 * Wydruk 3D ogląda się z każdej strony, spaw widać dopiero na filmie, a przy
 * zleceniu na zamówienie klient chce zobaczyć model, zanim zapłaci. Dotąd
 * sklep przyjmował wyłącznie JPG, PNG i WEBP.
 *
 * ZASADA BEZPIECZEŃSTWA: nazwa pliku i nagłówek `Content-Type` pochodzą od
 * klienta i obu można skłamać. Rodzaj rozpoznajemy po ZAWARTOŚCI — dla obrazów
 * przez `getimagesize`, dla reszty po sygnaturze pierwszych bajtów. Plik, którego
 * nie umiemy rozpoznać, jest odrzucany, a nie zapisywany „na wszelki wypadek".
 *
 * Nazwę na dysku nadajemy sami (`<id>-<losowe>.<rozszerzenie>`), więc nic
 * z nazwy przysłanej przez klienta nie trafia do systemu plików.
 */

/** Katalog na pliki produktów — ten sam, co zdjęcia. */
const FW_KATALOG_PLIKOW = __DIR__ . '/../assets/sklep';

/**
 * Limity rozmiaru.
 *
 * Wideo jest hojne, bo film ze spawania to kilkadziesiąt megabajtów, ale nie
 * bez końca: hosting współdzielony ma swoje `upload_max_filesize`, a strona
 * ma się otwierać na telefonie w terenie.
 */
const FW_MAX_PLIK_B = 67108864;    // 64 MB — ogólny limit na plik przed rozpoznaniem rodzaju
const FW_MAX_WIDEO_B = 67108864;   // 64 MB
const FW_MAX_MODEL_B = 33554432;   // 32 MB
const FW_MAX_ANIMACJA_B = 16777216; // 16 MB — GIF-y produktowe z Meta AI maja 2-4 MB

/**
 * Co przyjmujemy, jak to rozpoznać i za jaki rodzaj uznać.
 *
 * `sygnatura` to bajty od początku pliku; `przesuniecie` mówi, gdzie ich szukać
 * (kontenery MP4/MOV mają `ftyp` dopiero na czwartym bajcie).
 */
function fw_rodzaje_plikow(): array
{
    return [
        // --- wideo ---
        'mp4'  => ['rodzaj' => 'wideo', 'mime' => 'video/mp4',       'sygnatura' => 'ftyp', 'przesuniecie' => 4],
        'mov'  => ['rodzaj' => 'wideo', 'mime' => 'video/quicktime', 'sygnatura' => 'ftyp', 'przesuniecie' => 4],
        'webm' => ['rodzaj' => 'wideo', 'mime' => 'video/webm',      'sygnatura' => "\x1A\x45\xDF\xA3", 'przesuniecie' => 0],
        // RIFF maja tez WAV i WEBP, wiec sprawdzamy dodatkowo znacznik „AVI "
        // na osmym bajcie — patrz fw_rozpoznaj_plik().
        'avi'  => ['rodzaj' => 'wideo', 'mime' => 'video/x-msvideo', 'sygnatura' => 'RIFF', 'przesuniecie' => 0],
        'mkv'  => ['rodzaj' => 'wideo', 'mime' => 'video/x-matroska','sygnatura' => "\x1A\x45\xDF\xA3", 'przesuniecie' => 0],

        // --- animacja ---
        // GIF jest tu osobnym rodzajem, a nie zdjeciem ani wideo. Powod jest
        // praktyczny: pokazuje sie go znacznikiem <img> (sam sie odtwarza,
        // bez kontrolek), ale w galerii ma stac przed nieruchomymi zdjeciami
        // tak samo jak film. Wrzucenie go do `obraz-wgraj` zrobiloby z niego
        // zwykle zdjecie na koncu listy.
        //
        // Bierze sie stad, ze Meta AI oddaje animacje wylacznie jako GIF —
        // filmu w tej chwili nie generuje.
        'gif'  => ['rodzaj' => 'animacja', 'mime' => 'image/gif', 'sygnatura' => 'GIF8', 'przesuniecie' => 0],

        // --- modele 3D ---
        // STL binarny nie ma sygnatury: to 80 bajtów nagłówka i liczba trójkątów.
        // Dlatego sprawdzamy go osobno, w fw_wyglada_na_stl().
        'stl'  => ['rodzaj' => 'model',  'mime' => 'model/stl',        'sygnatura' => null, 'przesuniecie' => 0],
        'obj'  => ['rodzaj' => 'model',  'mime' => 'model/obj',        'sygnatura' => null, 'przesuniecie' => 0],
        '3mf'  => ['rodzaj' => 'model',  'mime' => 'model/3mf',        'sygnatura' => 'PK',   'przesuniecie' => 0],
        'step' => ['rodzaj' => 'model',  'mime' => 'model/step',       'sygnatura' => 'ISO-10303', 'przesuniecie' => 0],
        'stp'  => ['rodzaj' => 'model',  'mime' => 'model/step',       'sygnatura' => 'ISO-10303', 'przesuniecie' => 0],
        'gcode'=> ['rodzaj' => 'szkic',  'mime' => 'text/plain',       'sygnatura' => null, 'przesuniecie' => 0],

        // --- szkice i dokumenty techniczne ---
        'pdf'  => ['rodzaj' => 'szkic',  'mime' => 'application/pdf',  'sygnatura' => '%PDF', 'przesuniecie' => 0],
        'dxf'  => ['rodzaj' => 'szkic',  'mime' => 'image/vnd.dxf',    'sygnatura' => null, 'przesuniecie' => 0],
        // SVG NIE JEST PRZYJMOWANY. To nie jest obrazek, tylko dokument XML,
        // ktory moze zawierac <script> i atrybuty zdarzen — wyswietlony na
        // naszej domenie wykonuje sie jak nasz wlasny kod. Do szkicu wystarczy
        // PDF albo DXF, wiec nie ma powodu brac na siebie tego ryzyka.
    ];
}

/**
 * Czy plik naprawdę jest tym, za co się podaje.
 *
 * Zwraca opis rodzaju albo `null`. Świadomie nie ufamy rozszerzeniu samemu
 * w sobie — służy tylko do wskazania, czego szukać w zawartości.
 */
function fw_rozpoznaj_plik(string $sciezka, string $rozszerzenie): ?array
{
    $rozszerzenie = strtolower($rozszerzenie);
    $rodzaje = fw_rodzaje_plikow();
    if (!isset($rodzaje[$rozszerzenie])) {
        return null;
    }
    $opis = $rodzaje[$rozszerzenie];

    $uchwyt = @fopen($sciezka, 'rb');
    if ($uchwyt === false) {
        return null;
    }
    $poczatek = (string) fread($uchwyt, 1024);
    fclose($uchwyt);

    if ($rozszerzenie === 'stl') {
        return fw_wyglada_na_stl($sciezka, $poczatek) ? $opis : null;
    }
    if (in_array($rozszerzenie, ['obj', 'gcode', 'dxf'], true)) {
        return fw_wyglada_na_tekst($sciezka, $poczatek, $rozszerzenie) ? $opis : null;
    }

    $sygnatura = $opis['sygnatura'];
    if ($sygnatura === null) {
        return null;
    }
    if (substr($poczatek, (int) $opis['przesuniecie'], strlen($sygnatura)) !== $sygnatura) {
        return null;
    }

    // Sygnatura to za malo dla kontenerow, ktore dziela poczatek z innymi
    // formatami. Kazdy z tych przypadkow zostal wskazany w recenzji kodu:
    return match ($rozszerzenie) {
        // RIFF zaczyna tez WAV i WEBP; dopiero „AVI " na osmym bajcie rozstrzyga.
        'avi'  => substr($poczatek, 8, 4) === 'AVI ',
        // „GIF8" maja obie wersje formatu, ale nic wiecej — domykamy do pelnej
        // sygnatury, zeby nie przeszlo cos, co tylko tak sie zaczyna.
        'gif'  => in_array(substr($poczatek, 0, 6), ['GIF87a', 'GIF89a'], true),
        // „ftyp" bez marki to dowolny plik z czterema bajtami na poczatku.
        'mp4', 'mov' => fw_marka_kontenera($poczatek) !== null,
        // 3MF to ZIP z konkretnym wnetrzem — bez tego przeszedlby kazdy DOCX i APK.
        '3mf'  => fw_zip_ma_wpis($sciezka, '3D/3dmodel.model'),
        default => true,
    } ? $opis : null;
}

/** Zdjęcie przygotowane dla Allegro (tło AI). Niewidoczne w galerii strony. */
function fw_rozpoznaj_zdjecie_allegro(string $sciezka): ?array
{
    $info = @getimagesize($sciezka);
    if ($info === false || !in_array($info[2], [IMAGETYPE_JPEG, IMAGETYPE_PNG], true)) {
        return null;
    }
    $roz = $info[2] === IMAGETYPE_PNG ? 'png' : 'jpg';
    return ['rodzaj' => 'allegro', 'mime' => $info['mime'], 'rozszerzenie' => $roz];
}

/** Marka kontenera MP4/MOV z bajtów 8–12, o ile jest z listy, którą znamy. */
function fw_marka_kontenera(string $poczatek): ?string
{
    $marka = substr($poczatek, 8, 4);
    $znane = ['isom', 'iso2', 'mp41', 'mp42', 'avc1', 'qt  ', 'M4V ', 'dash'];
    return in_array($marka, $znane, true) ? $marka : null;
}

/** Czy archiwum ZIP zawiera wskazany wpis — do rozpoznania 3MF. */
function fw_zip_ma_wpis(string $sciezka, string $wpis): bool
{
    if (!class_exists('ZipArchive')) {
        // Bez rozszerzenia ZIP nie mamy jak tego sprawdzic, a „na wszelki
        // wypadek" znaczyloby przyjmowanie kazdego archiwum.
        return false;
    }
    $zip = new ZipArchive();
    if ($zip->open($sciezka) !== true) {
        return false;
    }
    $ma = $zip->locateName($wpis, ZipArchive::FL_NOCASE) !== false;
    $zip->close();
    return $ma;
}

/**
 * STL w obu odmianach.
 *
 * Tekstowy zaczyna się od „solid". Binarny nie ma sygnatury w ogóle, więc
 * liczymy: 80 bajtów nagłówka + 4 bajty licznika + 50 bajtów na trójkąt.
 * Zgodność rozmiaru z tym równaniem jest mocniejszym dowodem niż jakikolwiek
 * nagłówek — plik podrobiony musiałby trafić w rozmiar co do bajta.
 */
function fw_wyglada_na_stl(string $sciezka, string $poczatek): bool
{
    if (stripos(ltrim($poczatek), 'solid') === 0) {
        return true;
    }
    $rozmiar = (int) @filesize($sciezka);
    if ($rozmiar < 84) {
        return false;
    }
    $licznik = unpack('V', substr($poczatek, 80, 4));
    if ($licznik === false) {
        return false;
    }
    return $rozmiar === 84 + 50 * (int) $licznik[1];
}

/**
 * Czy to plik tekstowy z sensowną treścią dla danego formatu.
 *
 * Sprawdzamy CAŁY plik, nie pierwszy kilobajt. Inaczej wystarczyłoby dopisać
 * na początku linijkę wyglądającą na G-code i schować za nią cokolwiek —
 * a przy plikach warsztatowych „cokolwiek" bywa cudzym plikiem wykonywalnym.
 */
function fw_wyglada_na_tekst(string $sciezka, string $poczatek, string $rozszerzenie): bool
{
    $tresc = (string) @file_get_contents($sciezka, false, null, 0, FW_MAX_MODEL_B);
    if ($tresc === '') {
        return false;
    }
    // Bajt zerowy w tekscie znaczy, ze to nie jest tekst.
    if (strpos($tresc, "\0") !== false) {
        return false;
    }
    // Znacznik PHP ani <script> nie maja prawa znalezc sie w modelu czy szkicu.
    // Serwer i tak nie wykona pliku z katalogu assets, ale nie zapisujemy czegos
    // takiego u siebie — to jest ta jedna linijka, ktora dzieli „nieszkodliwe"
    // od „czeka na okazje".
    $male = strtolower($tresc);
    if (str_contains($male, '<?php') || str_contains($male, '<script')) {
        return false;
    }

    return match ($rozszerzenie) {
        'obj'   => str_contains($male, 'v ') || str_contains($male, '# '),
        'gcode' => str_contains($male, 'g0') || str_contains($male, 'g1') || str_contains($male, ';'),
        'dxf'   => str_contains($male, 'section') || str_contains($male, '  0'),
        default => false,
    };
}


/** Górna granica rozmiaru dla rodzaju. */
function fw_limit_dla_rodzaju(string $rodzaj): int
{
    return match ($rodzaj) {
        'wideo' => FW_MAX_WIDEO_B,
        // GIF wazy swoje przy dluzszej animacji (klatki sa nieskompresowane
        // miedzy soba), ale nie ma prawa siegac filmowych 64 MB — przy takim
        // rozmiarze i tak lepiej wgrac MP4.
        'animacja' => FW_MAX_ANIMACJA_B,
        'allegro' => 12 * 1048576,
        default => FW_MAX_MODEL_B,
    };
}

/**
 * Zakłada tabelę na pliki produktu.
 *
 * Osobna od `produkty_obrazy`, bo zdjęcia mają szerokość i wysokość, a film
 * i model nie — wpychanie ich do jednej tabeli skończyłoby się kolumnami,
 * które przy połowie wierszy nic nie znaczą.
 */
function fw_zapewnij_tabele_plikow(PDO $pdo): void
{
    $pdo->exec(
        'CREATE TABLE IF NOT EXISTS ' . fw_tabela('produkty_pliki') . ' ('
        . ' id         INT UNSIGNED NOT NULL AUTO_INCREMENT,'
        . ' produkt_id INT UNSIGNED NOT NULL,'
        . ' plik       VARCHAR(190) NOT NULL,'
        . ' rodzaj     VARCHAR(20)  NOT NULL,'
        . ' mime       VARCHAR(60)  NOT NULL,'
        . ' opis       VARCHAR(190) NOT NULL DEFAULT "",'
        . ' rozmiar_b  INT UNSIGNED NOT NULL DEFAULT 0,'
        . ' pozycja    INT          NOT NULL DEFAULT 100,'
        . ' PRIMARY KEY (id),'
        . ' KEY idx_produkt (produkt_id, pozycja),'
        . ' CONSTRAINT fk_plik_produkt FOREIGN KEY (produkt_id)'
        . '   REFERENCES ' . fw_tabela('produkty') . ' (id) ON DELETE CASCADE'
        . ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
    );
}

/** Pliki przypięte do wskazanych produktów, pogrupowane po produkcie. */
function fw_pliki_dla(array $idki): array
{
    if (!$idki) {
        return [];
    }
    $znaki = implode(',', array_fill(0, count($idki), '?'));
    $st = fw_baza()->prepare('SELECT id, produkt_id, plik, rodzaj, mime, opis, rozmiar_b'
        . ' FROM ' . fw_tabela('produkty_pliki')
        . ' WHERE produkt_id IN (' . $znaki . ') ORDER BY pozycja ASC, id ASC');
    $st->execute($idki);

    $wynik = [];
    foreach ($st->fetchAll() as $w) {
        $wynik[(int) $w['produkt_id']][] = [
            'id'      => (int) $w['id'],
            'src'     => '/assets/sklep/' . $w['plik'],
            'rodzaj'  => $w['rodzaj'],
            'mime'    => $w['mime'],
            'opis'    => $w['opis'],
            'rozmiar' => (int) $w['rozmiar_b'],
        ];
    }
    return $wynik;
}
