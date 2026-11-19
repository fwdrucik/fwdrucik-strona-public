<?php
declare(strict_types=1);

/**
 * Wątek forum renderowany po stronie serwera.
 *
 * Do tej pory wątki wczytywał JavaScript z /api/forum.php. W samym kodzie
 * strony nie było ani jednego wątku, w mapie serwisu ani jednego adresu —
 * każda dyskusja techniczna była dla wyszukiwarek niewidoczna. Ten plik
 * oddaje gotowy HTML pod własnym adresem: /forum/watek/<id>-<tytul>/.
 *
 * Szablon (nagłówek, stopka, wersje CSS i JS) wstawia build.py przy budowaniu
 * serwisu, żeby nie było drugiego miejsca z tym samym układem strony.
 *
 * Świadomie NIE podbijamy licznika odsłon: tę stronę odwiedzają też roboty,
 * a licznik ma pokazywać zainteresowanie ludzi. Robi to nadal /api/forum.php.
 */

require_once __DIR__ . '/../api/_lib.php';

const FW_SITE = 'https://fwdrucik.pl';

const FW_KATEGORIE = [
    'regulamin'        => 'Regulamin & Zasady',
    'witam'            => 'Przywitaj się',
    'faq'              => 'FAQ & Pomoc',
    'instrukcje'       => 'Instrukcje & Poradniki',
    'ksiazkiserwisowe' => 'Książki Serwisowe / DTR',
    'elektro'          => 'Elektromechanika & CAN',
    'spawanie'         => 'Spawanie & CNC & 3D',
    'klimatyzacja'     => 'Klimatyzacja',
    'poczekalnia'      => 'Poczekalnia / Hyde Park',
    'general'          => 'Dyskusje Ogólne',
];

function fw_h(string $tekst): string
{
    return htmlspecialchars($tekst, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/** Treść wpisu: uciekamy wszystko, a łamania wierszy zamieniamy na akapity. */
function fw_tresc_html(string $tekst): string
{
    $akapity = preg_split('/\R{2,}/u', trim($tekst)) ?: [];
    $wynik = '';
    foreach ($akapity as $a) {
        $a = trim($a);
        if ($a !== '') {
            $wynik .= '<p>' . nl2br(fw_h($a)) . '</p>';
        }
    }
    return $wynik !== '' ? $wynik : '<p></p>';
}

function fw_data_pl(string $sql): string
{
    $d = date_create($sql);
    return $d ? $d->format('j.m.Y, H:i') : $sql;
}

/**
 * Data w formacie ISO 8601 dla danych strukturalnych i znacznika <time>.
 *
 * date_create() zwraca przy blednym wejsciu `false`, a nie `null` — operator
 * `?->` tego nie wychwytuje i strona konczylaby sie bledem krytycznym zamiast
 * pominac jedno pole.
 */
function fw_iso(?string $sql): string
{
    $d = $sql === null ? false : date_create($sql);
    return $d ? $d->format('c') : '';
}

// ------------------------------------------------------------------ wątek

$id = filter_var($_GET['id'] ?? 0, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
if ($id === false) {
    http_response_code(404);
    header('Location: /forum/', true, 302);
    exit;
}

$pdo = fw_baza();

// Tylko treści opublikowane. Wpisy czekające na moderację widzi ich autor,
// ale wyłącznie w wersji z JavaScriptem — strona serwerowa jest publiczna
// i cache'owalna, więc nie może zależeć od tego, kto ją otworzył.
$st = $pdo->prepare('SELECT w.id, w.kategoria, w.tytul, w.tresc, w.wyswietlenia,'
    . ' w.utworzony, w.ostatnia_aktywnosc, a.nick AS autor, a.id AS autor_id'
    . ' FROM ' . fw_tabela('watki') . ' w'
    . ' JOIN ' . fw_tabela('uzytkownicy') . ' a ON a.id = w.autor_id'
    . ' WHERE w.id = ? AND w.status = "opublikowany"');
$st->execute([$id]);
$watek = $st->fetch();

if (!$watek) {
    http_response_code(404);
    header('Content-Type: text/html; charset=UTF-8');
    readfile(__DIR__ . '/../404.html');
    exit;
}

$st = $pdo->prepare('SELECT o.id, o.tresc, o.utworzona, a.nick AS autor, a.id AS autor_id'
    . ' FROM ' . fw_tabela('odpowiedzi') . ' o'
    . ' JOIN ' . fw_tabela('uzytkownicy') . ' a ON a.id = o.autor_id'
    . ' WHERE o.watek_id = ? AND o.status = "opublikowany"'
    . ' ORDER BY o.utworzona ASC LIMIT 500');
$st->execute([$id]);
$odpowiedzi = $st->fetchAll();

// --------------------------------------------------------------- kanoniczny

$slug = fw_slug_tytulu((string) $watek['tytul']);
$sciezka = '/forum/watek/' . $watek['id'] . ($slug !== '' ? '-' . $slug : '') . '/';
$zadana = strtok((string) ($_SERVER['REQUEST_URI'] ?? ''), '?');

// Jeden adres na jedną treść: wejście z niepełnym albo starym tytułem
// przekierowujemy trwale, zamiast pozwalać na dwie wersje tej samej strony.
if ($zadana !== false && rawurldecode($zadana) !== $sciezka) {
    header('Location: ' . FW_SITE . $sciezka, true, 301);
    exit;
}

$kategoria = FW_KATEGORIE[$watek['kategoria']] ?? 'Forum';
$tytul = (string) $watek['tytul'];
$dopisekSeo = ' — forum F.W. DRUCIK';
$tytulSeo = $tytul;
$limitSeo = 60 - mb_strlen($dopisekSeo, 'UTF-8');
if (mb_strlen($tytulSeo, 'UTF-8') > $limitSeo) {
    $skrot = mb_substr($tytulSeo, 0, $limitSeo - 1, 'UTF-8');
    $pelneSlowa = preg_replace('/\s+\S*$/u', '', $skrot);
    $tytulSeo = (preg_replace('/[\s,;:—–-]+$/u', '', $pelneSlowa ?: $skrot) ?: $skrot) . '…';
}
$tytulSeo .= $dopisekSeo;
$opis = mb_substr(trim(preg_replace('/\s+/u', ' ', (string) $watek['tresc']) ?? ''), 0, 155, 'UTF-8');
if ($opis === '') {
    $opis = 'Dyskusja techniczna na forum warsztatu F.W. DRUCIK.';
}
$kanoniczny = FW_SITE . $sciezka;

// Dane strukturalne dyskusji — to one sprawiają, że wyszukiwarka rozumie,
// że strona jest wątkiem z odpowiedziami, a nie zwykłym artykułem.
$ld = [
    '@context' => 'https://schema.org',
    '@type' => 'DiscussionForumPosting',
    '@id' => $kanoniczny . '#watek',
    'headline' => $tytul,
    'articleSection' => $kategoria,
    'url' => $kanoniczny,
    'datePublished' => fw_iso((string) $watek['utworzony']),
    'dateModified' => fw_iso((string) $watek['ostatnia_aktywnosc']),
    'author' => ['@type' => 'Person', 'name' => (string) $watek['autor']],
    'publisher' => ['@id' => FW_SITE . '/#organizacja'],
    'inLanguage' => 'pl-PL',
    'text' => mb_substr((string) $watek['tresc'], 0, 1200, 'UTF-8'),
    'interactionStatistic' => [
        '@type' => 'InteractionCounter',
        'interactionType' => 'https://schema.org/ReplyAction',
        'userInteractionCount' => count($odpowiedzi),
    ],
];
if ($odpowiedzi) {
    $ld['comment'] = array_map(static fn(array $o): array => [
        '@type' => 'Comment',
        'text' => mb_substr((string) $o['tresc'], 0, 800, 'UTF-8'),
        'datePublished' => fw_iso((string) $o['utworzona']),
        'author' => ['@type' => 'Person', 'name' => (string) $o['autor']],
    ], $odpowiedzi);
}

header('Content-Type: text/html; charset=UTF-8');
// Wątek zmienia się rzadko, ale odpowiedź może dojść w każdej chwili —
// pięć minut w cache pośredniczącym to kompromis między świeżością a obciążeniem.
header('Cache-Control: public, max-age=0, s-maxage=300');

// Nagłówek wstawia build.py jako blok bez interpolacji (nowdoc) — w danych
// strukturalnych firmy jest m.in. "priceRange": "$$", a zwykły heredoc
// próbowałby czytać takie miejsca jako nazwy zmiennych.
$glowa = <<<'GLOWA'
{{GLOWA}}
GLOWA;

echo strtr($glowa, [
    '{{TYTUL}}' => fw_h($tytulSeo),
    '{{OPIS}}'  => fw_h($opis),
    '{{URL}}'   => fw_h($kanoniczny),
]);
?>
<nav class="breadcrumbs" aria-label="Okruszki nawigacyjne"><div class="container"><a href="/">Strona główna</a><span class="sep">/</span><a href="/forum/">Forum dyskusyjne</a><span class="sep">/</span><span aria-current="page"><?= fw_h(mb_substr($tytul, 0, 60, 'UTF-8')) ?></span></div></nav>
<main id="tresc">
<script type="application/ld+json"><?= json_encode($ld, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?></script>

<section class="diamond-bg">
  <div class="container">
    <article class="watek">
      <header class="watek-glowa">
        <div class="blog-card-meta">
          <span class="badge badge-blue"><?= fw_h($kategoria) ?></span>
          <span>💬 <?= count($odpowiedzi) ?> odpowiedzi</span>
          <span>👁️ <?= (int) $watek['wyswietlenia'] ?></span>
          <span>📅 <?= fw_h(fw_data_pl((string) $watek['utworzony'])) ?></span>
        </div>
        <h1><?= fw_h($tytul) ?></h1>
        <p class="watek-autor">Pytanie zadał: <strong><?= fw_h((string) $watek['autor']) ?></strong><span class="community-level" data-author-id="<?= (int)$watek['autor_id'] ?>"></span></p>
      </header>

      <div class="watek-tresc"><?= fw_tresc_html((string) $watek['tresc']) ?></div>

      <h2 id="odpowiedzi"><?= $odpowiedzi ? 'Odpowiedzi' : 'Brak odpowiedzi' ?></h2>
      <?php if ($odpowiedzi): ?>
        <ol class="watek-odpowiedzi">
          <?php foreach ($odpowiedzi as $o): ?>
            <li id="odp-<?= (int) $o['id'] ?>">
              <div class="watek-odp-glowa">
                <strong><?= fw_h((string) $o['autor']) ?></strong><span class="community-level" data-author-id="<?= (int)$o['autor_id'] ?>"></span>
                <time datetime="<?= fw_h(fw_iso((string) $o['utworzona'])) ?>"><?= fw_h(fw_data_pl((string) $o['utworzona'])) ?></time>
              </div>
              <div class="watek-odp-tresc"><?= fw_tresc_html((string) $o['tresc']) ?></div>
            </li>
          <?php endforeach; ?>
        </ol>
      <?php else: ?>
        <p class="watek-pusto">Nikt jeszcze nie odpowiedział. Jeśli znasz rozwiązanie — napisz.</p>
      <?php endif; ?>

      <div class="watek-doloz" id="watek-serwerowy" data-watek-id="<?= (int) $watek['id'] ?>">
        <h2>Dołóż swoją odpowiedź</h2>
        <p data-gdy="niezalogowany">Odpowiadać mogą osoby zalogowane.
          <a href="/konto/">Załóż darmowe konto</a> — jest bezpłatne i zajmuje chwilę.</p>
        <form id="watek-odpowiedz-form" data-gdy="zalogowany" hidden>
          <label class="sr-only" for="watek-odpowiedz">Treść odpowiedzi</label>
          <textarea id="watek-odpowiedz" class="form-control" rows="4"
            placeholder="Napisz, jak rozwiązałeś ten problem…" required></textarea>
          <div class="notatnik-akcje">
            <button type="submit" class="btn btn-primary">Wyślij odpowiedź</button>
            <span class="komunikat" id="watek-odpowiedz-info"></span>
          </div>
        </form>
        <p class="watek-wroc"><a href="/forum/">← Wszystkie wątki na forum</a></p>
      </div>
    </article>
  </div>
</section>
</main>
<?php
echo <<<'STOPKA'
{{STOPKA}}
STOPKA;
