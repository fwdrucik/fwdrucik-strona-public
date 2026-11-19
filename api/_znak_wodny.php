<?php
/**
 * Znak wodny na zdjęciach produktów — logo F.W. DRUCIK w prawym dolnym rogu.
 *
 * PO CO NA SERWERZE, A NIE W CSS: nakładka CSS znika w chwili, w której ktoś
 * zapisze obrazek prawym przyciskiem albo weźmie go wprost z adresu pliku.
 * Zdjęcia wyrobów rzemieślniczych wędrują po serwisach ogłoszeniowych i po
 * cudzych sklepach — znak wypalony w pikselach jedzie razem z nimi.
 *
 * Znak nakładamy RAZ, przy wgraniu. Wersja z nakładaniem przy każdym
 * wyświetleniu wymagałaby liczenia obrazka na każde żądanie albo pamięci
 * podręcznej, a to koszt bez zysku: oryginał i tak zostaje w aplikacji na
 * telefonie i w archiwum.
 *
 * GIF-y pomijamy świadomie — GD spłaszczyłby animację do jednej klatki.
 */

/** Plik logo z przezroczystym tłem. Leży obok reszty grafiki strony. */
const FW_PLIK_ZNAKU = __DIR__ . '/../assets/logo-znak.png';

/** Jaką część szerokości zdjęcia zajmuje znak. */
const FW_SZEROKOSC_ZNAKU = 0.18;

/** Odstęp od krawędzi, też liczony od szerokości zdjęcia. */
const FW_MARGINES_ZNAKU = 0.025;

/**
 * Przezroczystość znaku: 0 = niewidoczny, 100 = pełny.
 *
 * 70 to kompromis sprawdzony na zdjęciach żywicy: znak jest czytelny również
 * na jasnym tle, a nie zabiera uwagi wyrobowi, po który klient przyszedł.
 */
const FW_KRYCIE_ZNAKU = 70;

/**
 * Czy da się wczytać to zdjęcie do pamięci bez wywrócenia PHP.
 *
 * PO CO: 6 MB to rozmiar PLIKU, nie obrazu w pamięci. GD rozpakowuje zdjęcie
 * do `szerokość * wysokość * 4` bajtów — zdjęcie 6000x4000 z telefonu to około
 * 96 MB, a razem z kopią pod znak i narzutem PHP przekracza typowe
 * `memory_limit` hostingu. Przekroczenie to fatal error, czyli wgrywanie
 * kończy się błędem 500 i zdjęcie nie trafia do sklepu wcale.
 *
 * Wolimy zdjęcie bez znaku niż brak zdjęcia, więc przy ciasnym limicie po
 * prostu odpuszczamy.
 */
function fw_znak_zmiesci_sie(string $sciezka): bool
{
    $info = @getimagesize($sciezka);
    if ($info === false) {
        return false;
    }

    $limit = ini_get('memory_limit');
    if ($limit === false || $limit === '' || (int) $limit < 0) {
        return true;   // brak limitu — nie ma czego pilnować
    }

    $mnozniki = ['k' => 1024, 'm' => 1048576, 'g' => 1073741824];
    $ostatni = strtolower(substr((string) $limit, -1));
    $bajty = (int) $limit * ($mnozniki[$ostatni] ?? 1);

    // Zapas 1,8x: obraz źródłowy plus bufor zapisu. Do tego 8 MB na to,
    // co PHP zajmuje niezależnie od nas.
    $potrzeba = (int) ($info[0] * $info[1] * 4 * 1.8) + 8 * 1048576;

    return ($bajty - memory_get_usage(true)) > $potrzeba;
}

/**
 * Wypala logo w prawym dolnym rogu zdjęcia. Nadpisuje plik w miejscu.
 *
 * Zwraca true, gdy znak został nałożony. Każde niepowodzenie kończy się
 * zwróceniem false i NIETKNIĘTYM plikiem — zdjęcie bez znaku jest lepsze niż
 * zepsute zdjęcie albo odrzucone wgranie.
 */
function fw_nanies_znak_wodny(string $sciezka, int $typ): bool
{
    if (!extension_loaded('gd') || !is_file(FW_PLIK_ZNAKU)) {
        return false;
    }

    if (!fw_znak_zmiesci_sie($sciezka)) {
        return false;
    }

    // GIF pomijamy: imagecreatefromgif czyta tylko pierwszą klatkę i zapis
    // skasowałby animację.
    $obraz = match ($typ) {
        IMAGETYPE_JPEG => @imagecreatefromjpeg($sciezka),
        IMAGETYPE_PNG  => @imagecreatefrompng($sciezka),
        IMAGETYPE_WEBP => @imagecreatefromwebp($sciezka),
        default        => null,
    };
    if (!$obraz) {
        return false;
    }

    $znak = @imagecreatefrompng(FW_PLIK_ZNAKU);
    if (!$znak) {
        imagedestroy($obraz);
        return false;
    }

    $szerZdj = imagesx($obraz);
    $wysZdj  = imagesy($obraz);
    $szerZnak = (int) round($szerZdj * FW_SZEROKOSC_ZNAKU);

    // Na miniaturze znak zajmowałby całą szerokość i zasłonił wyrób; poniżej
    // 120 px szerokości zdjęcia odpuszczamy.
    if ($szerZdj < 120) {
        imagedestroy($obraz);
        imagedestroy($znak);
        return false;
    }
    $wysZnak = max(1, (int) round($szerZnak * imagesy($znak) / imagesx($znak)));

    $margines = (int) round($szerZdj * FW_MARGINES_ZNAKU);
    $x = $szerZdj - $szerZnak - $margines;
    $y = $wysZdj - $wysZnak - $margines;

    // Zmniejszamy logo osobno, zachowując kanał alfa. Bez `imagealphablending`
    // na false i `imagesavealpha` przezroczyste tło logo wyszłoby czarne.
    $maly = imagecreatetruecolor($szerZnak, $wysZnak);
    imagealphablending($maly, false);
    imagesavealpha($maly, true);
    imagefill($maly, 0, 0, imagecolorallocatealpha($maly, 0, 0, 0, 127));
    imagecopyresampled($maly, $znak, 0, 0, 0, 0, $szerZnak, $wysZnak,
        imagesx($znak), imagesy($znak));

    // imagecopymerge nie umie kanału alfa źródła, a imagecopy nie umie krycia.
    // Stąd ta droga: krycie wnosimy przez przeskalowanie alfy w samym logo,
    // a nakładamy zwykłym imagecopy, które alfę respektuje.
    if (FW_KRYCIE_ZNAKU < 100) {
        for ($px = 0; $px < $szerZnak; $px++) {
            for ($py = 0; $py < $wysZnak; $py++) {
                $kolor = imagecolorat($maly, $px, $py);
                $alfa = ($kolor >> 24) & 0x7F;
                // 127 = całkiem przezroczysty. Im mniejsze krycie, tym bliżej 127.
                $nowaAlfa = (int) min(127, $alfa + (127 - $alfa) * (100 - FW_KRYCIE_ZNAKU) / 100);
                $nowy = imagecolorallocatealpha(
                    $maly, ($kolor >> 16) & 0xFF, ($kolor >> 8) & 0xFF, $kolor & 0xFF, $nowaAlfa
                );
                imagesetpixel($maly, $px, $py, $nowy);
            }
        }
    }

    imagealphablending($obraz, true);
    imagecopy($obraz, $maly, $x, $y, 0, 0, $szerZnak, $wysZnak);

    // Zapis idzie do pliku tymczasowego, a gotowy wynik podmienia oryginał
    // dopiero przez `rename`.
    //
    // PO CO: `imagejpeg($obraz, $ta_sama_sciezka)` obcina oryginał do zera
    // ZANIM zacznie pisać. Gdy zapis padnie w połowie — brak pamięci, pełny
    // dysk, uszkodzony obrazek — zostaje pusty plik i zdjęcie produktu
    // przepada bezpowrotnie. `rename` w obrębie jednego katalogu jest
    // niepodzielne, więc albo jest stary plik, albo nowy. Nigdy nic pomiędzy.
    $tymczasowy = $sciezka . '.tmp' . bin2hex(random_bytes(4));
    $udane = match ($typ) {
        // Jakość 90: znak ma zostać czytelny po ponownym zapisie, a przy 75
        // cienkie linie logo rozłażą się w artefakty.
        IMAGETYPE_JPEG => imagejpeg($obraz, $tymczasowy, 90),
        IMAGETYPE_PNG  => (imagesavealpha($obraz, true) && imagepng($obraz, $tymczasowy, 6)),
        IMAGETYPE_WEBP => imagewebp($obraz, $tymczasowy, 90),
        default        => false,
    };

    imagedestroy($maly);
    imagedestroy($znak);
    imagedestroy($obraz);

    if (!$udane || !is_file($tymczasowy) || filesize($tymczasowy) === 0) {
        @unlink($tymczasowy);
        return false;
    }
    if (!@rename($tymczasowy, $sciezka)) {
        @unlink($tymczasowy);
        return false;
    }
    @chmod($sciezka, 0644);

    return true;
}
