<?php
declare(strict_types=1);

/**
 * Karta jednego produktu: /sklep/<slug>/.
 *
 * Renderowana po stronie serwera razem z danymi strukturalnymi Product
 * i Offer — to one decydują, czy produkt pokaże się w wynikach z ceną
 * i dostępnością. Dopóki sklep jest w przebudowie, karta produktu jest
 * dostępna wyłącznie dla administratora.
 */

require_once __DIR__ . '/../api/_lib.php';
require_once __DIR__ . '/../api/_sklep.php';
require_once __DIR__ . '/../api/_pliki_produktu.php';
require_once __DIR__ . '/../api/_poczta.php';

const FW_SITE = 'https://fwdrucik.pl';

function fw_h(string $tekst): string
{
    return htmlspecialchars($tekst, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/** Opis produktu: akapity z podwójnych złamań wiersza, wszystko uciekane. */
function fw_opis_html(string $tekst): string
{
    $trim = trim($tekst);
    if (str_contains($trim, 'opis-allegro-kontener')) {
        return fw_sklep_opis_html($trim);
    }
    $wynik = '';
    foreach (preg_split('/\R{2,}/u', $trim) ?: [] as $akapit) {
        $akapit = trim($akapit);
        if ($akapit !== '') {
            $wynik .= '<p>' . nl2br(fw_h($akapit)) . '</p>';
        }
    }
    return $wynik;
}

if (!fw_sklep_dostepny_dla_mnie()) {
    // Bez otwartego sklepu karta produktu nie istnieje dla świata —
    // kierujemy na stronę z informacją o przebudowie, zamiast pokazywać 404.
    header('Location: /sklep/', true, 302);
    exit;
}

fw_zapewnij_tabele_sklepu();

$slug = trim((string) ($_GET['slug'] ?? ''));
$u = fw_uzytkownik();
$adminowe = $u !== null && $u['rola'] === 'admin';

$st = fw_baza()->prepare('SELECT * FROM ' . fw_tabela('produkty')
    . ' WHERE slug = ?' . ($adminowe ? '' : ' AND status = "opublikowany"'));
$st->execute([$slug]);
$wiersz = $st->fetch();

if (!$wiersz) {
    http_response_code(404);
    header('Content-Type: text/html; charset=UTF-8');
    readfile(__DIR__ . '/../404.html');
    exit;
}

$obrazy = fw_obrazy_dla([(int) $wiersz['id']]);
// Wideo, modele 3D i szkice — osobno od zdjec, bo maja inne wlasciwosci
// i inaczej sie je pokazuje. Brak tabeli (starsza instalacja) nie moze
// wywrocic strony produktu, wiec bierzemy to w runCatching PHP-owy.
$pliki = [];
try {
    $pliki = fw_pliki_dla([(int) $wiersz['id']])[(int) $wiersz['id']] ?? [];
} catch (Throwable $e) {
    $pliki = [];
}
$wideo = array_values(array_filter($pliki, static fn($f) => $f['rodzaj'] === 'wideo'));
$animacje = array_values(array_filter($pliki, static fn($f) => $f['rodzaj'] === 'animacja'));
$modele = array_values(array_filter($pliki, static fn($f) => $f['rodzaj'] === 'model'));
$szkice = array_values(array_filter($pliki, static fn($f) => $f['rodzaj'] === 'szkic'));
$p = fw_produkt_publiczny($wiersz, $obrazy[(int) $wiersz['id']] ?? []);
$cena = fw_cena_obowiazujaca($p);
$dostepny = $p['stan'] === null || $p['stan'] > 0;
$kanoniczny = FW_SITE . $p['url'];

$opisSeo = $p['opis_krotki'] !== ''
    ? $p['opis_krotki']
    : mb_substr(trim(preg_replace('/\s+/u', ' ', $p['opis']) ?? ''), 0, 155, 'UTF-8');

$ld = [
    '@context' => 'https://schema.org',
    '@type' => 'Product',
    '@id' => $kanoniczny . '#produkt',
    'name' => $p['nazwa'],
    'description' => $opisSeo,
    'sku' => 'FWD-' . $p['id'],
    'category' => $p['kategoria'],
    'brand' => ['@type' => 'Brand', 'name' => 'F.W. DRUCIK'],
    'url' => $kanoniczny,
    'offers' => [
        '@type' => 'Offer',
        'price' => number_format($cena / 100, 2, '.', ''),
        'priceCurrency' => 'PLN',
        'availability' => $dostepny
            ? 'https://schema.org/InStock'
            : 'https://schema.org/OutOfStock',
        'itemCondition' => 'https://schema.org/NewCondition',
        'url' => $kanoniczny,
        'seller' => ['@id' => FW_SITE . '/#organizacja'],
        // Bez daty waznosci ceny Search Console zglasza ostrzezenie przy ofercie.
        // Liczona od dnia wizyty, wiec nie trzeba jej pamietac przy zmianie ceny.
        'priceValidUntil' => date('Y-m-d', strtotime('+1 year')),
        // Koszt i czas dostawy w wynikach wyszukiwania. Google pokazuje je obok
        // ceny — brak tych pol to utrata miejsca w karcie produktu.
        'shippingDetails' => fw_dostawa_ld($p),
        'hasMerchantReturnPolicy' => fw_zwroty_ld($p),
    ],
];
if ($p['obrazy']) {
    $ld['image'] = array_map(static fn($o) => FW_SITE . $o['src'], $p['obrazy']);
}
if ($p['waga_g'] > 0) {
    $ld['weight'] = ['@type' => 'QuantitativeValue', 'value' => $p['waga_g'], 'unitCode' => 'GRM'];
}
if (!empty($p['allegro_url'])) {
    $ld['sameAs'] = [$p['allegro_url']];
    $ld['offers']['url'] = $p['allegro_url'];
}
if (!empty($p['allegro_id'])) {
    $ld['mpn'] = (string) $p['allegro_id'];
}

$okruszki = [
    '@context' => 'https://schema.org',
    '@type' => 'BreadcrumbList',
    'itemListElement' => [
        ['@type' => 'ListItem', 'position' => 1, 'name' => 'Strona główna', 'item' => FW_SITE . '/'],
        ['@type' => 'ListItem', 'position' => 2, 'name' => 'Sklep', 'item' => FW_SITE . '/sklep/'],
        ['@type' => 'ListItem', 'position' => 3, 'name' => $p['nazwa'], 'item' => $kanoniczny],
    ],
];

header('Content-Type: text/html; charset=UTF-8');
header('Cache-Control: private, max-age=0, must-revalidate');

/**
 * Tytuł z ceną. Cena w wyniku wyszukiwania podnosi klikalność i odsiewa
 * osoby, dla których produkt jest poza budżetem — trafniejszy ruch.
 * Nazwę tniemy na granicy słowa, a nie w połowie wyrazu jak wcześniej.
 */
$marka = ' | F.W. DRUCIK';
$dopisek = ' — ' . fw_zlote($cena) . $marka;
$nazwaTytul = $p['nazwa'];
if (mb_strlen($nazwaTytul . $dopisek, 'UTF-8') > 62) {
    $nazwaTytul = mb_substr($nazwaTytul, 0, 62 - mb_strlen($dopisek, 'UTF-8'), 'UTF-8');
    $spacja = mb_strrpos($nazwaTytul, ' ', 0, 'UTF-8');
    if ($spacja !== false) {
        $nazwaTytul = mb_substr($nazwaTytul, 0, $spacja, 'UTF-8');
    }
    $nazwaTytul = rtrim($nazwaTytul, " ,;:—–-");
}

$glowa = <<<'GLOWA'
{{GLOWA}}
GLOWA;

$podmianyGlowy = [
    '{{TYTUL}}'  => fw_h($nazwaTytul . $dopisek),
    '{{OPIS}}'   => fw_h($opisSeo),
    '{{URL}}'    => fw_h($kanoniczny),
    // Szkic i produkt ukryty widzi tylko administrator — nie mogą trafić
    // do wyszukiwarki nawet przypadkiem.
    '{{ROBOTS}}' => ($p['status'] === 'opublikowany' && fw_sklep_otwarty())
        ? 'index,follow,max-image-preview:large'
        : 'noindex,nofollow',
];

if (!empty($p['obrazy'])) {
    $glownyObrazUrl = FW_SITE . $p['obrazy'][0]['src'];
    $podmianyGlowy['https://fwdrucik.pl/assets/hero-bg-1600.jpg'] = fw_h($glownyObrazUrl);
}

$metaDodatkowe = '';
if (!empty($p['allegro_url'])) {
    $metaDodatkowe .= "\n" . '<meta property="product:brand" content="F.W. DRUCIK">';
    $metaDodatkowe .= "\n" . '<meta property="product:availability" content="' . ($dostepny ? 'in stock' : 'out of stock') . '">';
    $metaDodatkowe .= "\n" . '<meta property="product:condition" content="new">';
    $metaDodatkowe .= "\n" . '<meta property="product:price:amount" content="' . number_format($cena / 100, 2, '.', '') . '">';
    $metaDodatkowe .= "\n" . '<meta property="product:price:currency" content="PLN">';
    $metaDodatkowe .= "\n" . '<meta property="og:see_also" content="' . fw_h($p['allegro_url']) . '">';
}

$glowaHtml = strtr($glowa, $podmianyGlowy);
if ($metaDodatkowe !== '') {
    $glowaHtml = str_replace('</head>', $metaDodatkowe . "\n</head>", $glowaHtml);
}
echo $glowaHtml;
?>
<nav class="breadcrumbs" aria-label="Okruszki nawigacyjne"><div class="container"><a href="/">Strona główna</a><span class="sep">/</span><a href="/sklep/">Sklep</a><span class="sep">/</span><span aria-current="page"><?= fw_h(mb_substr($p['nazwa'], 0, 60, 'UTF-8')) ?></span></div></nav>
<main id="tresc">
<script type="application/ld+json"><?= fw_json_ld($ld) ?></script>
<?php foreach ($wideo as $w): ?>
<?php
// VideoObject osobno dla kazdego filmu. Google pokazuje z tego miniature
// z ikona odtwarzania w wynikach — przy wyrobie robionym na zamowienie to
// jest roznica miedzy „jakis warsztat" a „widac, jak to robia".
$ldWideo = [
    '@context'     => 'https://schema.org',
    '@type'        => 'VideoObject',
    'name'         => $p['nazwa'],
    'description'  => $w['opis'] !== '' ? $w['opis'] : ($p['opis_krotki'] ?? $p['nazwa']),
    'contentUrl'   => FW_SITE . $w['src'],
    'uploadDate'   => date('c', strtotime((string) ($wiersz['utworzony'] ?? 'now'))),
    'thumbnailUrl' => $p['obrazy'] ? [FW_SITE . $p['obrazy'][0]['src']] : [FW_SITE . '/assets/hero-bg-1600.jpg'],
];
?>
<script type="application/ld+json"><?= fw_json_ld($ldWideo) ?></script>
<?php endforeach; ?>
<script type="application/ld+json"><?= fw_json_ld($okruszki) ?></script>

<section class="diamond-bg">
  <div class="container">
    <?php if ($p['status'] !== 'opublikowany'): ?>
      <p class="podglad-admina">⚠ Ten produkt ma status <strong><?= fw_h($p['status']) ?></strong>
        i nie jest widoczny dla klientów.</p>
    <?php endif; ?>
    <?php if ($adminowe): ?>
      <div class="admin-pasek" id="admin-pasek-produkt" data-id="<?= (int) $p['id'] ?>"
           data-nazwa="<?= fw_h($p['nazwa']) ?>" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:0 0 16px;">
        <span class="badge badge-orange">ADMIN</span>
        <a class="btn btn-outline" href="/admin/?edytuj=<?= (int) $p['id'] ?>#panel-sklep">✏️ Edytuj</a>
        <select class="form-control" style="max-width:260px;" aria-label="Status produktu">
          <?php foreach (['opublikowany' => 'Opublikowany', 'ukryty' => 'Ukryty (prywatny)', 'szkic' => 'Szkic'] as $s => $etykieta): ?>
            <option value="<?= $s ?>"<?= $p['status'] === $s ? ' selected' : '' ?>><?= $etykieta ?></option>
          <?php endforeach; ?>
        </select>
        <button type="button" class="btn btn-outline" data-usun>🗑️ Usuń</button>
      </div>
    <?php endif; ?>

    <article class="produkt-karta-pelna">
      <div class="produkt-galeria">
        <?php
        // RUCH IDZIE PIERWSZY.
        //
        // Wczesniej galeria zaczynala sie od nieruchomego zdjecia, a film lezal
        // pod nim — czyli poza pierwszym ekranem telefonu. Materialu, ktory
        // pokazuje wyrob ze wszystkich stron, nikt wtedy nie ogladal. Zdjecia
        // zostaja tam, gdzie byly, tylko za ruchem.
        ?>
        <?php foreach ($wideo as $w): ?>
          <video class="produkt-wideo produkt-wideo-glowne" controls preload="metadata" playsinline
                 <?php if ($p['obrazy']): ?>poster="<?= fw_h($p['obrazy'][0]['src']) ?>"<?php endif; ?>>
            <source src="<?= fw_h($w['src']) ?>" type="<?= fw_h($w['mime']) ?>">
            Twoja przeglądarka nie odtworzy tego filmu —
            <a href="<?= fw_h($w['src']) ?>">pobierz go</a>.
          </video>
          <?php if ($w['opis'] !== ''): ?>
            <p class="produkt-podpis"><?= fw_h($w['opis']) ?></p>
          <?php endif; ?>
        <?php endforeach; ?>

        <?php foreach ($animacje as $a): ?>
          <!-- GIF odtwarza sie sam, wiec idzie znacznikiem <img>. `loading=lazy`
               swiadomie NIE, bo to pierwszy materiał na stronie produktu. -->
          <img class="produkt-animacja" src="<?= fw_h($a['src']) ?>"
               alt="<?= fw_h($a['opis'] !== '' ? $a['opis'] : ('Animacja: ' . $p['nazwa'])) ?>">
          <?php if ($a['opis'] !== ''): ?>
            <p class="produkt-podpis"><?= fw_h($a['opis']) ?></p>
          <?php endif; ?>
        <?php endforeach; ?>

        <?php if ($p['obrazy']): ?>
          <img id="produkt-glowny" src="<?= fw_h($p['obrazy'][0]['src']) ?>"
               width="<?= (int) $p['obrazy'][0]['szerokosc'] ?>"
               height="<?= (int) $p['obrazy'][0]['wysokosc'] ?>"
               alt="<?= fw_h($p['obrazy'][0]['alt'] ?: $p['nazwa']) ?>">
          <?php if ($modele || $szkice): ?>
            <?php foreach ($modele as $i => $m): ?>
              <?php if (str_ends_with(strtolower($m['src']), '.stl')): ?>
                <!-- Model do obejrzenia z kazdej strony. Rysuje go wlasny podglad
                     w WebGL, bez zadnej biblioteki — 30 kB zamiast pol megabajta. -->
                <canvas class="produkt-model" data-model="<?= fw_h($m['src']) ?>"
                        aria-label="Podgląd modelu 3D: <?= fw_h($m['opis'] ?: $p['nazwa']) ?>"></canvas>
              <?php endif; ?>
              <p class="produkt-podpis">
                <a href="<?= fw_h($m['src']) ?>" download>Pobierz model
                  (<?= strtoupper(pathinfo($m['src'], PATHINFO_EXTENSION)) ?>,
                  <?= (int) round($m['rozmiar'] / 1048576) ?: 1 ?> MB)</a>
              </p>
            <?php endforeach; ?>

            <?php foreach ($szkice as $sz): ?>
              <p class="produkt-podpis">
                <a href="<?= fw_h($sz['src']) ?>" download>
                  Pobierz <?= strtoupper(pathinfo($sz['src'], PATHINFO_EXTENSION)) ?><?php
                  ?><?= $sz['opis'] !== '' ? ' — ' . fw_h($sz['opis']) : '' ?></a>
              </p>
            <?php endforeach; ?>
          <?php endif; ?>

          <?php if (count($p['obrazy']) > 1): ?>
            <div class="produkt-miniatury">
              <?php foreach ($p['obrazy'] as $i => $o): ?>
                <button type="button" class="miniatura<?= $i === 0 ? ' aktywna' : '' ?>"
                        data-src="<?= fw_h($o['src']) ?>"
                        aria-label="Pokaż zdjęcie <?= $i + 1 ?>">
                  <img src="<?= fw_h($o['src']) ?>" width="<?= (int) $o['szerokosc'] ?>"
                       height="<?= (int) $o['wysokosc'] ?>" loading="lazy"
                       alt="<?= fw_h($o['alt'] ?: $p['nazwa']) ?>">
                </button>
              <?php endforeach; ?>
            </div>
          <?php endif; ?>
        <?php else: ?>
          <svg class="produkt-ilustracja duza" viewBox="0 0 320 200" role="img"
               aria-label="Rysunek kategorii <?= fw_h($p['kategoria']) ?> — ten produkt nie ma jeszcze zdjęcia">
            <use href="/assets/kategorie.svg#<?= fw_h(fw_ilustracja_kategorii($p['kategoria'])) ?>"/>
          </svg>
        <?php endif; ?>
      </div>

      <div class="produkt-panel">
        <p class="produkt-kat"><?= fw_h($p['kategoria']) ?></p>
        <h1><?= fw_h($p['nazwa']) ?></h1>
        <?php if ($p['opis_krotki'] !== ''): ?>
          <p class="lead"><?= fw_h($p['opis_krotki']) ?></p>
        <?php endif; ?>

        <p class="produkt-cena duza">
          <?php if ($p['cena_promo_gr'] !== null): ?>
            <span class="cena-stara"><?= fw_h(fw_zlote($p['cena_gr'])) ?></span>
          <?php endif; ?>
          <strong><?= fw_h(fw_zlote($cena)) ?></strong>
          <span class="produkt-jednostka">/ <?= fw_h($p['jednostka']) ?></span>
        </p>

        <dl class="produkt-dane">
          <dt>Dostępność</dt>
          <dd><?= $p['stan'] === null
                ? 'Wykonywane na zamówienie'
                : ($p['stan'] > 0
                    ? ($p['stan'] <= 3
                        ? '<strong class="stan-niski">Zostały ' . (int) $p['stan'] . ' ' . fw_h($p['jednostka']) . '</strong>'
                        : 'Na stanie: ' . (int) $p['stan'] . ' ' . fw_h($p['jednostka']))
                    : 'Chwilowo niedostępny') ?></dd>
          <?php if ($p['czas_realizacji'] !== ''): ?>
            <dt>Czas realizacji</dt><dd><?= fw_h($p['czas_realizacji']) ?></dd>
          <?php endif; ?>
          <?php if ($p['waga_g'] > 0): ?>
            <dt>Waga</dt><dd><?= number_format($p['waga_g'] / 1000, 2, ',', ' ') ?> kg</dd>
          <?php endif; ?>
        </dl>

        <div class="produkt-akcje">
          <?php if (!empty($p['allegro_url'])): ?>
            <div class="allegro-zakup-blok">
              <a href="<?= fw_h($p['allegro_url']) ?>" target="_blank" rel="noopener noreferrer"
                 class="btn btn-primary btn-lg kup-allegro-duzy"
                 title="Otwórz oficjalne ogłoszenie na Allegro">
                Kup na Allegro ↗
              </a>
              <p class="allegro-wskazowka">
                <span class="allegro-ikona" aria-hidden="true">ℹ️</span>
                <span>Kliknięcie otwiera ofertę tego wyrobu na <strong>Allegro</strong>. Płatności, koszty dostawy i warunki programów Allegro sprawdź w konkretnej ofercie przed zakupem.</span>
              </p>
            </div>
          <?php else: ?>
            <label class="sr-only" for="produkt-ilosc">Ilość</label>
            <input type="number" id="produkt-ilosc" class="form-control" value="1" min="1" max="99">
            <a href="/kontakt/?temat=<?= urlencode('Zapytanie o produkt: ' . $p['nazwa']) ?>" class="btn btn-primary">
              Zapytaj o produkt / Zamów na wymiar
            </a>
          <?php endif; ?>
        </div>
        <?php
        // Rzeczy, o ktore klient i tak zapyta przed zakupem. Trzymamy je przy
        // przycisku, a nie w regulaminie — kazde przejscie na inna strone
        // to porzucony koszyk.
        $paczkomat = fw_zlote(FW_DOSTAWA['paczkomat']['cena_gr']);
        $kurier = fw_zlote(FW_DOSTAWA['kurier']['cena_gr']);
        ?>
        <ul class="produkt-zaufanie">
          <?php if (!empty($p['allegro_url'])): ?>
            <li><strong>Zakup przez Allegro</strong> — sprawdź warunki oferty i sprzedawcy.</li>
            <li>Dostępne metody dostawy i zwrotów są podane w ofercie.</li>
          <?php else: ?>
            <li><strong>Odbiór osobisty za 0 zł</strong> — Domosław 13A pod Winnicą</li>
            <li>Paczkomat <?= fw_h($paczkomat) ?> · kurier <?= fw_h($kurier) ?> · wysyłka w całej Polsce</li>
          <?php endif; ?>
          <li>Faktura VAT do każdego zamówienia (NIP 888-292-19-00)</li>
          <?php if ($p['stan'] === null): ?>
            <li>Wyrób na wymiar — przed rozpoczęciem potwierdzamy wygląd i cenę.
              <a href="/odstapienie/">Rzeczy robione na indywidualne zamówienie nie podlegają zwrotowi</a>.</li>
          <?php else: ?>
            <li><a href="/odstapienie/">14 dni na zwrot</a> bez podawania przyczyny</li>
          <?php endif; ?>
        </ul>
        <p class="produkt-kontakt">Chcesz zmodyfikować ten wyrób lub zamówić bezpośrednio w warsztacie? Zadzwoń:
          <a href="tel:+48601726924">601 726 924</a> — doradzę osobiście, wycena jest bezpłatna.
          Można też napisać przez <a href="/kontakt/">formularz</a>.</p>
      </div>
    </article>

    <?php if (trim($p['opis']) !== ''): ?>
      <div class="produkt-opis-pelny">
        <h2>Opis produktu</h2>
        <?= fw_opis_html($p['opis']) ?>
      </div>
    <?php endif; ?>

    <?php $powiazane = fw_produkty_powiazane((int) $p['id'], $p['kategoria']); ?>
    <?php if ($powiazane): ?>
      <section class="produkty-powiazane">
        <h2>Z tego samego warsztatu</h2>
        <div class="produkty-siatka">
          <?php foreach ($powiazane as $x): ?>
            <article class="produkt-karta">
              <a class="produkt-obraz" href="<?= fw_h($x['url']) ?>">
                <?php if ($x['obrazy']): ?>
                  <img src="<?= fw_h($x['obrazy'][0]['src']) ?>"
                       width="<?= (int) $x['obrazy'][0]['szerokosc'] ?>"
                       height="<?= (int) $x['obrazy'][0]['wysokosc'] ?>" loading="lazy"
                       alt="<?= fw_h($x['obrazy'][0]['alt'] ?: $x['nazwa']) ?>">
                <?php else: ?>
                  <svg class="produkt-ilustracja" viewBox="0 0 320 200" role="img"
                       aria-label="Rysunek kategorii <?= fw_h($x['kategoria']) ?>">
                    <use href="/assets/kategorie.svg#<?= fw_h(fw_ilustracja_kategorii($x['kategoria'])) ?>"/>
                  </svg>
                <?php endif; ?>
              </a>
              <div class="produkt-tresc">
                <h3 class="produkt-nazwa"><a href="<?= fw_h($x['url']) ?>"><?= fw_h($x['nazwa']) ?></a></h3>
                <p class="produkt-cena"><strong><?= fw_h(fw_zlote(fw_cena_obowiazujaca($x))) ?></strong></p>
              </div>
            </article>
          <?php endforeach; ?>
        </div>
      </section>
    <?php endif; ?>

    <p class="watek-wroc"><a href="/sklep/">← Wszystkie produkty</a></p>
  </div>
</section>
</main>
<?php
echo <<<'STOPKA'
<!-- Obsluga koszyka i galerii produktu. Bez tego przyciski „Dodaj do koszyka"
     nie robily NIC: skrypt byl dolaczony na koszyku, koncie i zamowieniu,
     ale nie na samej liscie sklepu ani na karcie produktu. -->
<script src="/assets/sklep.js" defer></script>
<?php if ($adminowe): ?>
<script>
// Pasek admina: status i usuwanie wprost z karty produktu. Uprawnienia sprawdza sklep.php.
document.addEventListener('DOMContentLoaded', () => {
  const pasek = document.getElementById('admin-pasek-produkt');
  const { api } = window.FWSklep || {};
  if (!pasek || !api) return;
  const id = Number(pasek.dataset.id);
  pasek.querySelector('select').addEventListener('change', async (e) => {
    try {
      await api('/sklep.php?akcja=produkt-status', { metoda: 'POST', dane: { id, status: e.target.value } });
      location.reload();
    } catch (err) { alert(err.message); }
  });
  pasek.querySelector('[data-usun]').addEventListener('click', async () => {
    if (prompt('Usunięcie produktu i jego zdjęć jest nieodwracalne.\nWpisz nazwę produktu, żeby potwierdzić:') !== pasek.dataset.nazwa) return;
    try {
      await api('/sklep.php?akcja=produkt-usun', { metoda: 'POST', dane: { id } });
      location.href = '/sklep/';
    } catch (err) { alert(err.message); }
  });
});
</script>
<?php endif; ?>

{{STOPKA}}
STOPKA;
