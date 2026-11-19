<?php
declare(strict_types=1);

/**
 * Strona sklepu — lista produktów albo informacja o przebudowie.
 *
 * Dopóki w konfiguracji nie ma `sklep_otwarty`, katalog widzi wyłącznie
 * administrator. Pozostali dostają stronę z informacją i możliwością zapisania
 * się po powiadomienie o otwarciu. Strona przebudowy jest oznaczona jako
 * `noindex` — nie chcemy, żeby to ona weszła do wyszukiwarki zamiast sklepu.
 *
 * Katalog renderujemy po stronie serwera, a nie skryptem w przeglądarce.
 * Produkty mają być widoczne dla wyszukiwarek razem z ceną i dostępnością —
 * bez tego dane strukturalne Product nie miałyby żadnego sensu.
 */

require_once __DIR__ . '/../api/_lib.php';
require_once __DIR__ . '/../api/_sklep.php';
require_once __DIR__ . '/../api/_poczta.php';

const FW_SITE = 'https://fwdrucik.pl';

function fw_h(string $tekst): string
{
    return htmlspecialchars($tekst, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

$otwarty = fw_sklep_dostepny_dla_mnie();
$u = fw_uzytkownik();
$podglad = $otwarty && !fw_sklep_otwarty();

$produkty = $otwarty ? fw_produkty_publiczne((string) ($_GET['kategoria'] ?? '')) : [];

$kategorie = [];
foreach ($produkty as $p) {
    $kategorie[$p['kategoria']] = ($kategorie[$p['kategoria']] ?? 0) + 1;
}

$tytul = $otwarty
    ? 'Sklep — wyroby z żywicy, wydruki 3D i konstrukcje | F.W. DRUCIK'
    : 'Sklep w przebudowie — F.W. DRUCIK';
$opis = $otwarty
    ? 'Gotowe wyroby rękodzielnicze i produkty na indywidualne zamówienie: żywica epoksydowa, druk 3D, konstrukcje stalowe i obróbka CNC.'
    : 'Przebudowujemy sklep internetowy F.W. DRUCIK. Zamówienia przyjmujemy telefonicznie pod numerem 601 726 924 i przez formularz kontaktowy.';
$robots = $otwarty
    ? 'index,follow,max-image-preview:large,max-snippet:-1'
    : 'noindex,follow';

// Dane strukturalne listy produktów. Bez otwartego sklepu nie ma czego opisywać.
$ld = null;
if ($otwarty && $produkty) {
    $ld = [
        '@context' => 'https://schema.org',
        '@type' => 'ItemList',
        'name' => 'Produkty F.W. DRUCIK',
        'numberOfItems' => count($produkty),
        'itemListElement' => [],
    ];
    foreach ($produkty as $i => $p) {
        $ld['itemListElement'][] = [
            '@type' => 'ListItem',
            'position' => $i + 1,
            'item' => [
                '@type' => 'Product',
                'name' => $p['nazwa'],
                'description' => $p['opis_krotki'],
                'url' => FW_SITE . $p['url'],
                'image' => $p['obrazy'] ? FW_SITE . $p['obrazy'][0]['src'] : null,
                'brand' => ['@type' => 'Brand', 'name' => 'F.W. DRUCIK'],
                'offers' => [
                    '@type' => 'Offer',
                    'price' => number_format(fw_cena_obowiazujaca($p) / 100, 2, '.', ''),
                    'priceCurrency' => 'PLN',
                    'availability' => ($p['stan'] === null || $p['stan'] > 0)
                        ? 'https://schema.org/InStock'
                        : 'https://schema.org/OutOfStock',
                    'url' => FW_SITE . $p['url'],
                    'seller' => ['@id' => FW_SITE . '/#organizacja'],
                    'priceValidUntil' => date('Y-m-d', strtotime('+1 year')),
                    'shippingDetails' => fw_dostawa_ld($p),
                    'hasMerchantReturnPolicy' => fw_zwroty_ld($p),
                ],
            ],
        ];
    }
}

header('Content-Type: text/html; charset=UTF-8');
header('Cache-Control: private, max-age=0, must-revalidate');

$glowa = <<<'GLOWA'
{{GLOWA}}
GLOWA;

echo strtr($glowa, [
    '{{TYTUL}}'  => fw_h($tytul),
    '{{OPIS}}'   => fw_h($opis),
    '{{URL}}'    => FW_SITE . '/sklep/',
    '{{ROBOTS}}' => $robots,
]);
?>
<nav class="breadcrumbs" aria-label="Okruszki nawigacyjne"><div class="container"><a href="/">Strona główna</a><span class="sep">/</span><span aria-current="page">Sklep</span></div></nav>
<main id="tresc">
<?php if ($ld !== null): ?>
<script type="application/ld+json"><?= fw_json_ld($ld) ?></script>
<?php endif; ?>

<?php if (!$otwarty): ?>
<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Sklep internetowy</div>
    <h1>Sklep jest w przebudowie</h1>
    <p class="lead">Przepraszamy za utrudnienie. Budujemy nowy sklep z płatnościami online,
      koszykiem i śledzeniem zamówienia. Do czasu otwarcia zamówienia przyjmujemy tak jak dotąd —
      telefonicznie i mailem.</p>
  </div>
</section>

<section class="diamond-bg">
  <div class="container">
    <div class="przebudowa">
      <h2>Co się zmienia</h2>
      <ul class="check-list">
        <li><strong>Koszyk i zamówienie online</strong> — bez telefonowania i ustalania szczegółów w kilku wiadomościach.</li>
        <li><strong>Płatności BLIK, Google Pay i kartą</strong> — zapłata od razu przy zamówieniu.</li>
        <li><strong>Konto z historią zamówień</strong> — dane do wysyłki wpisane raz, status zamówienia widoczny na bieżąco.</li>
        <li><strong>Wysyłka kurierem i do paczkomatu</strong> albo odbiór osobisty w warsztacie.</li>
      </ul>

      <h2>Chcesz coś zamówić już teraz?</h2>
      <p>Wszystko, co było w sklepie, robimy dalej: blaty i stoliki z żywicy epoksydowej, wydruki 3D,
        elementy toczone i frezowane oraz konstrukcje spawane na wymiar. Napisz albo zadzwoń —
        wycena jest bezpłatna.</p>
      <div class="hero-cta">
        <a href="tel:+48601726924" class="btn btn-primary">Zadzwoń: 601 726 924</a>
        <a href="/kontakt/" class="btn btn-outline">Formularz kontaktowy</a>
      </div>

      <div class="przebudowa-powiadom">
        <h2>Powiadomimy Cię o otwarciu</h2>
        <p data-gdy="niezalogowany">Załóż darmowe konto — wyślemy wiadomość w dniu uruchomienia sklepu.
          Konto daje też dostęp do <a href="/narzedzia/">narzędzi online</a>.</p>
        <p data-gdy="zalogowany" hidden>Masz konto, więc dostaniesz wiadomość w dniu otwarcia sklepu.
          Nic więcej nie musisz robić.</p>
        <div class="hero-cta" data-gdy="niezalogowany">
          <a href="/konto/" class="btn btn-primary">Załóż konto</a>
        </div>
      </div>
    </div>
  </div>
</section>

<?php else: ?>
<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Produkty</div>
    <h1>Sklep — wyroby z żywicy, wydruki 3D i konstrukcje na zamówienie</h1>
    <p class="lead">Gotowe produkty rękodzielnicze oraz wyroby wykonywane na indywidualne zamówienie.</p>
    <?php if ($podglad): ?>
      <p class="podglad-admina">⚠ Widzisz sklep w trybie podglądu administratora. Dla pozostałych
        odwiedzających wyświetla się strona o przebudowie. Otwarcie sklepu włącza się wpisem
        <code>sklep_otwarty</code> w konfiguracji serwera.</p>
    <?php endif; ?>
  </div>
</section>

<section class="diamond-bg">
  <div class="container">
    <?php if (count($kategorie) > 1): ?>
      <div class="narzedzia-paski">
        <a class="tab-btn<?= ($_GET['kategoria'] ?? '') === '' ? ' active' : '' ?>" href="/sklep/">Wszystko</a>
        <?php foreach ($kategorie as $k => $ile): ?>
          <a class="tab-btn<?= ($_GET['kategoria'] ?? '') === $k ? ' active' : '' ?>"
             href="/sklep/?kategoria=<?= urlencode((string) $k) ?>"><?= fw_h((string) $k) ?> (<?= $ile ?>)</a>
        <?php endforeach; ?>
      </div>
    <?php endif; ?>

    <div class="allegro-info-banner">
      <div class="allegro-info-ikona">🟠</div>
      <div class="allegro-info-tekst">
        <strong>Sprzedaż przez Allegro:</strong> Kliknięcie <em>„Kup na Allegro ↗”</em> lub dodanie do koszyka
        otwiera ofertę w serwisie Allegro. Dostępne płatności, koszty dostawy oraz warunki
        programów Allegro sprawdź w konkretnej ofercie przed zakupem.
      </div>
    </div>

    <?php if (!$produkty): ?>
      <p class="pusto">Katalog jest jeszcze pusty. Produkty dodaje się w
        <a href="/admin/">panelu administratora</a>.</p>
    <?php else: ?>
      <div class="produkty-siatka">
        <?php foreach ($produkty as $p): ?>
          <?php
            $linkDocelowy = !empty($p['allegro_url']) ? fw_h($p['allegro_url']) : fw_h($p['url']);
            $targetAttr = !empty($p['allegro_url']) ? ' target="_blank" rel="noopener noreferrer"' : '';
            $animacja = null;
            if (!empty($p['obrazy'])) {
                foreach ($p['obrazy'] as $ob) {
                    $ext = strtolower(pathinfo($ob['src'], PATHINFO_EXTENSION));
                    if (in_array($ext, ['mp4', 'webm', 'gif'], true)) {
                        $animacja = $ob;
                        break;
                    }
                }
            }
          ?>
          <article class="produkt-karta">
            <a class="produkt-obraz" href="<?= $linkDocelowy ?>"<?= $targetAttr ?>>
              <?php if ($animacja && in_array(strtolower(pathinfo($animacja['src'], PATHINFO_EXTENSION)), ['mp4', 'webm'], true)): ?>
                <video src="<?= fw_h($animacja['src']) ?>" autoplay loop muted playsinline class="produkt-animacja-360" style="width:100%;height:100%;object-fit:cover;border-radius:8px;"></video>
              <?php elseif ($animacja): ?>
                <img src="<?= fw_h($animacja['src']) ?>" class="produkt-animacja-360" loading="lazy" alt="<?= fw_h($animacja['alt'] ?: $p['nazwa']) ?>" style="width:100%;height:100%;object-fit:cover;border-radius:8px;">
              <?php elseif ($p['obrazy']): ?>
                <img src="<?= fw_h($p['obrazy'][0]['src']) ?>"
                     <?= $p['obrazy'][0]['szerokosc'] > 0 ? ('width="' . (int) $p['obrazy'][0]['szerokosc'] . '"') : '' ?>
                     <?= $p['obrazy'][0]['wysokosc'] > 0 ? ('height="' . (int) $p['obrazy'][0]['wysokosc'] . '"') : '' ?>
                     loading="lazy"
                     alt="<?= fw_h($p['obrazy'][0]['alt'] ?: $p['nazwa']) ?>">
              <?php else: ?>
                <svg class="produkt-ilustracja" viewBox="0 0 320 200" role="img"
                     aria-label="Rysunek kategorii <?= fw_h($p['kategoria']) ?> — produkt nie ma jeszcze zdjęcia">
                  <use href="/assets/kategorie.svg#<?= fw_h(fw_ilustracja_kategorii($p['kategoria'])) ?>"/>
                </svg>
              <?php endif; ?>
            </a>
            <div class="produkt-tresc">
              <p class="produkt-kat"><?= fw_h($p['kategoria']) ?></p>
              <h2 class="produkt-nazwa"><a href="<?= $linkDocelowy ?>"<?= $targetAttr ?>><?= fw_h($p['nazwa']) ?></a></h2>
              <p class="produkt-opis"><?= fw_h($p['opis_krotki']) ?></p>
              <p class="produkt-cena">
                <?php if ($p['cena_promo_gr'] !== null): ?>
                  <span class="cena-stara"><?= fw_h(fw_zlote($p['cena_gr'])) ?></span>
                <?php endif; ?>
                <strong><?= fw_h(fw_zlote(fw_cena_obowiazujaca($p))) ?></strong>
                <span class="produkt-jednostka">/ <?= fw_h($p['jednostka']) ?></span>
              </p>
              <?php if (!empty($p['allegro_url'])): ?>
                <a href="<?= fw_h($p['allegro_url']) ?>" target="_blank" rel="noopener noreferrer"
                   class="btn btn-primary kup-allegro"
                   title="Sprawdź ofertę i warunki zakupu na Allegro">
                  Kup na Allegro ↗
                </a>
                <span class="allegro-badge-mini">Warunki płatności i dostawy w ofercie</span>
              <?php elseif ($p['stan'] !== null && $p['stan'] < 1): ?>
                <button type="button" class="btn btn-outline" disabled>Chwilowo niedostępny</button>
              <?php else: ?>
                <a href="<?= fw_h($p['url']) ?>" class="btn btn-primary">
                  Szczegóły / Zamów
                </a>
              <?php endif; ?>
            </div>
          </article>
        <?php endforeach; ?>
      </div>
    <?php endif; ?>
  </div>
</section>
<?php endif; ?>
{{RIVER_TABLE}}
</main>
<?php
echo <<<'STOPKA'
<!-- Obsluga koszyka i galerii produktu. Bez tego przyciski „Dodaj do koszyka"
     nie robily NIC: skrypt byl dolaczony na koszyku, koncie i zamowieniu,
     ale nie na samej liscie sklepu ani na karcie produktu. -->
<script src="/assets/sklep.js" defer></script>

{{STOPKA}}
STOPKA;
