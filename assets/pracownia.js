(() => {
  'use strict';
  const board = document.querySelector('[data-obwody]');
  if (!board) return;
  const type = board.querySelector('#lab-uklad');
  const power = board.querySelector('#lab-bateria');
  const paths = board.querySelector('#lab-sciezki');
  const result = board.querySelector('#lab-odczyt');
  const challenge = board.querySelector('#lab-wyzwanie');
  const example = board.querySelector('#lab-przyklad-ohma');
  const format = new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 2 });
  const voltage = 9;
  const bulbResistance = 90;
  const ledDrop = 2;
  const defaultResistor = 470;
  const layouts = {
    pojedynczy: {
      leads: [['M304 43V67M304 276V297', 0]],
      places: [[304, 67, 276]],
      hint: 'Przestaw przełącznik baterii i sprawdź, czy obwód jest otwarty, czy zamknięty.'
    },
    szereg: {
      leads: [['M304 43V67', -1], ['M304 276V297', -1]],
      places: [[304, 67, 124], [304, 124, 200], [304, 200, 276]],
      hint: 'W szeregu wszystkie lampki mają jeden wspólny prąd. Wyjmij jedną i zobacz, co się stanie.'
    },
    rownolegle: {
      leads: [['M208 43V67M208 276V297', 0], ['M304 43V67M304 276V297', 1], ['M496 43V67M496 276V297', 2]],
      places: [[208, 67, 276], [304, 67, 276], [496, 67, 276]],
      hint: 'Każda gałąź ma własną drogę do baterii. Wyjmij jedną lampkę i sprawdź pozostałe.'
    },
    mieszane: {
      leads: [['M304 43V67', -1], ['M304 142H240M240 276V297', 1], ['M304 142H432M432 276V297', 2]],
      places: [[304, 67, 142], [240, 142, 276], [432, 142, 276]],
      hint: 'Prąd najpierw płynie przez element 1, a potem może się rozdzielić na dwie gałęzie.'
    }
  };
  const slots = [1, 2, 3].map((n) => {
    const card = document.createElement('div');
    card.innerHTML = '<label for="lab-element-' + n + '">Element ' + n + '</label>'
      + '<select id="lab-element-' + n + '"><option value="zarowka">Żarówka</option>'
      + '<option value="led">LED + rezystor</option><option value="puste">Puste miejsce</option></select>'
      + '<div class="lab-opor" hidden><label for="lab-opor-' + n + '">Rezystor LED ' + n + '</label>'
      + '<select id="lab-opor-' + n + '"><option value="470">470 Ω</option>'
      + '<option value="680">680 Ω</option><option value="1000">1000 Ω</option></select></div>'
      + '<p class="lab-pomiar">Nie świeci</p>';
    board.querySelector('#lab-elementy').append(card);
    return { card, element: card.querySelector('select'), resistor: card.querySelector('.lab-opor select'),
      resistorField: card.querySelector('.lab-opor'), reading: card.querySelector('p') };
  });

  function measure(parts, on) {
    const [first, second, third] = parts;
    const kind = type.value;
    const closed = kind === 'pojedynczy' ? Boolean(first) : kind === 'szereg' ? parts.every(Boolean)
      : kind === 'rownolegle' ? parts.some(Boolean) : Boolean(first && (second || third));
    const zero = [0, 0, 0];
    if (!on || !closed) return { closed, current: 0, flows: zero };

    const flow = (part, u) => part ? Math.max(0, u - part.drop) / part.resistance : 0;
    if (kind === 'pojedynczy') {
      const current = flow(first, voltage);
      return { closed, current, flows: [current, 0, 0] };
    }
    if (kind === 'szereg') {
      const drop = parts.reduce((sum, part) => sum + part.drop, 0);
      const resistance = parts.reduce((sum, part) => sum + part.resistance, 0);
      const current = Math.max(0, voltage - drop) / resistance;
      return { closed, current, flows: [current, current, current] };
    }
    if (kind === 'rownolegle') {
      const flows = parts.map((part) => flow(part, voltage));
      return { closed, current: flows.reduce((sum, value) => sum + value, 0), flows };
    }

    // Napięcie rozgałęzienia jest tam, gdzie prąd z elementu 1 równa się sumie prądów gałęzi.
    let low = 0;
    let high = voltage;
    for (let i = 0; i < 32; i += 1) {
      const mid = (low + high) / 2;
      if (flow(first, voltage - mid) > flow(second, mid) + flow(third, mid)) low = mid;
      else high = mid;
    }
    const node = (low + high) / 2;
    const b = flow(second, node);
    const c = flow(third, node);
    return { closed, current: b + c, flows: [b + c, b, c] };
  }

  function symbol(part, x, y, flow) {
    if (!part) return '<rect class="lab-gniazdo" x="' + (x - 9) + '" y="' + (y - 22) + '" width="18" height="44" rx="5"/>';
    const active = flow > 0.000001;
    const level = active ? Math.min(1, Math.sqrt(flow / (part.led ? .015 : .1))) : 0;
    const glass = active ? .25 + .75 * level : 1;
    const lamp = part.led
      ? '<circle class="lab-poswiata" cx="0" cy="-12" r="16" opacity="' + level + '"/>'
        + '<path class="lab-klosz" fill-opacity="' + glass + '" d="M-8 -5v-9a8 8 0 0 1 16 0v9z"/>'
        + '<path class="lab-drucik" d="M0 -5v11m0 13v3"/>'
        + '<rect class="lab-opornik" x="-8" y="6" width="16" height="13" rx="3"/>'
        + '<path class="lab-paski" d="M-8 10h16m-16 5h16"/>'
        + '<text class="lab-wartosc" x="11" y="17">' + part.resistance + ' Ω</text>'
      : '<circle class="lab-poswiata" r="22" opacity="' + level + '"/>'
        + '<path class="lab-drucik" d="M0 -22v9m0 26v9"/>'
        + '<circle class="lab-klosz" r="13" fill-opacity="' + glass + '"/><path class="lab-drucik" d="M-6 -6l12 12m0-12L-6 6"/>';
    return '<g class="lab-swiatlo ' + (part.led ? 'lab-led' : 'lab-zarowka') + (active ? ' swieci' : '')
      + '" transform="translate(' + x + ' ' + y + ')">' + lamp + '</g>';
  }

  function render() {
    const parts = slots.map((slot) => {
      if (slot.element.value === 'puste') return null;
      const led = slot.element.value === 'led';
      return { led, drop: led ? ledDrop : 0, resistance: led ? Number(slot.resistor.value) : bulbResistance };
    });
    const on = power.getAttribute('aria-pressed') === 'true';
    const { closed, current, flows } = measure(parts, on);
    const { leads, places, hint } = layouts[type.value];
    slots.forEach((slot, index) => { slot.card.hidden = index >= places.length; });
    const wire = (d, active, color) => '<path class="lab-przewod' + (active ? ' przewodzi' : '')
      + '" d="' + d + '"' + (color ? ' stroke="' + color + '"' : '') + '/>';
    const single = type.value === 'pojedynczy';
    const positive = single && !on ? 'M30 123V43H63l22-12M91 43H133' : 'M30 123V43H133';
    let diagram = wire(positive, current, '#b12d35') + wire('M62 123V93H92V297H133', current, '#245893');
    if (single) diagram += '<circle cx="63" cy="43" r="4"/><circle cx="91" cy="43" r="4"/>';
    leads.forEach(([line, branch]) => {
      diagram += wire(line, branch < 0 ? current : flows[branch]);
    });
    places.forEach(([x, y1, y2], i) => {
      const mid = (y1 + y2) / 2;
      const part = parts[i];
      const flow = flows[i];
      diagram += wire('M' + x + ' ' + y1 + 'V' + (mid - 22) + 'M' + x + ' ' + (mid + 22) + 'V' + y2, flow)
        + '<circle cx="' + x + '" cy="' + y1 + '" r="4"/><circle cx="' + x + '" cy="' + y2 + '" r="4"/>'
        + symbol(part, x, mid, flow)
        + '<text x="' + (x + 18) + '" y="' + (mid - 6) + '" fill="#172b44">' + (i + 1) + '</text>';
      slots[i].resistorField.hidden = !part?.led;
      slots[i].reading.textContent = !part ? 'Puste miejsce' : flow > .000001
        ? 'Świeci · ' + format.format(flow * 1000) + ' mA · ' + format.format(flow * part.resistance + part.drop) + ' V'
        : 'Nie świeci · 0 mA';
    });
    paths.innerHTML = diagram;
    power.textContent = on ? 'Wyłącz baterię' : 'Włącz baterię 9 V';
    result.textContent = !on ? 'Bateria wyłączona · 0 mA'
      : 'Prąd z baterii: ' + format.format(current * 1000) + ' mA. ' + (closed ? 'Obwód zamknięty.' : 'Obwód otwarty.');
    challenge.textContent = hint;
    const resistance = parts.slice(0, places.length).find((part) => part?.led)?.resistance ?? defaultResistor;
    example.textContent = 'Jedna czerwona LED z rezystorem podłączona do 9 V: na LED jest około 2 V, '
      + 'więc na rezystorze zostaje 7 V. 7 V ÷ ' + resistance + ' Ω ≈ ' + format.format(7000 / resistance) + ' mA.';
  }

  board.querySelector('#lab-elementy').addEventListener('change', render);
  type.addEventListener('change', render);
  power.addEventListener('click', () => {
    power.setAttribute('aria-pressed', String(power.getAttribute('aria-pressed') !== 'true'));
    render();
  });
  board.querySelector('#lab-jedna-led').addEventListener('click', () => {
    slots[0].element.value = 'led';
    slots[0].resistor.value = String(defaultResistor);
    type.value = 'pojedynczy';
    power.setAttribute('aria-pressed', 'false');
    render();
    challenge.textContent = 'Przełącznik jest otwarty. Zgadnij, co zrobi LED, gdy włączysz baterię.';
    power.focus({ preventScroll: true });
  });
  board.querySelector('#lab-reset').addEventListener('click', () => {
    slots.forEach((slot) => { slot.element.value = 'zarowka'; slot.resistor.value = String(defaultResistor); });
    type.value = 'szereg';
    power.setAttribute('aria-pressed', 'false');
    render();
  });
  const lessons = board.querySelectorAll('[data-lab-temat]');
  lessons.forEach((button) => button.addEventListener('click', () => {
    lessons.forEach((lesson) => {
      const selected = lesson === button;
      lesson.setAttribute('aria-pressed', String(selected));
      document.getElementById(lesson.getAttribute('aria-controls')).hidden = !selected;
    });
  }));
  render();
  board.hidden = false;
})();

// Próba Blink. Pasek pokazuje oba odcinki cyklu także przy wyłączonej animacji.
(() => {
  const lesson = document.querySelector('[data-lekcja-arduino]');
  if (!lesson) return;
  const on = lesson.querySelector('#blink-swiatlo');
  const off = lesson.querySelector('#blink-przerwa');
  const play = lesson.querySelector('#blink-podglad');
  const led = lesson.querySelector('.lekcja-dioda');
  const rhythm = lesson.querySelector('.lekcja-rytm');
  const outcome = lesson.querySelector('#blink-wynik');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const seconds = new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 2 });
  let animation;

  function render() {
    const light = Number(on.value);
    const pause = Number(off.value);
    const duration = light + pause;
    const stopped = reduced.matches || document.documentElement.classList.contains('niebo-stop');
    const playing = !stopped && play.getAttribute('aria-pressed') === 'true';
    lesson.querySelector('#blink-kod-swiatlo').textContent = on.value;
    lesson.querySelector('#blink-kod-przerwa').textContent = off.value;
    rhythm.style.gridTemplateColumns = light + 'fr ' + pause + 'fr';
    outcome.textContent = seconds.format(light / 1000) + ' s światła i '
      + seconds.format(pause / 1000) + ' s przerwy. Cały cykl trwa ' + seconds.format(duration / 1000) + ' s.';
    play.disabled = stopped;
    play.setAttribute('aria-pressed', String(playing));
    play.textContent = stopped ? 'Animacja wstrzymana' : playing ? 'Zatrzymaj mruganie' : 'Pokaż mruganie';
    animation?.cancel();
    animation = playing ? led.animate([
      { opacity: 1, offset: 0, easing: 'step-end' },
      { opacity: 0.28, offset: light / duration },
      { opacity: 0.28, offset: 1 }
    ], { duration, iterations: Infinity }) : null;
  }

  on.addEventListener('change', render);
  off.addEventListener('change', render);
  play.addEventListener('click', () => {
    play.setAttribute('aria-pressed', String(play.getAttribute('aria-pressed') !== 'true'));
    render();
  });
  reduced.addEventListener('change', render);
  let stoppedBySite = document.documentElement.classList.contains('niebo-stop');
  new MutationObserver(() => {
    const stopped = document.documentElement.classList.contains('niebo-stop');
    if (stopped === stoppedBySite) return;
    stoppedBySite = stopped;
    render();
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
  render();
})();

// Przekrój podstawki. Górne pasy znikają, a stół i pierwszy pas zostają na miejscu.
(() => {
  const lesson = document.querySelector('[data-lekcja-warstwy]');
  if (!lesson) return;
  const range = lesson.querySelector('#druk-warstwy');
  const outcome = lesson.querySelector('#druk-wynik');
  const layers = Array.from(lesson.querySelectorAll('[data-warstwa]'));
  range.addEventListener('input', () => {
    lesson.querySelector('#druk-liczba').value = range.value;
    for (const layer of layers) {
      layer.hidden = Number(layer.dataset.warstwa) > Number(range.value);
      layer.setAttribute('aria-pressed', 'false');
    }
    outcome.textContent = 'Wskaż warstwę przy stole.';
  });
  for (const layer of layers) {
    layer.addEventListener('click', () => {
      for (const item of layers) item.setAttribute('aria-pressed', String(item === layer));
      outcome.textContent = layer.dataset.warstwa === '1'
        ? 'Tak! Ten pas dotyka stołu. Drukarka od niego zaczyna.'
        : 'Ten pas leży wyżej. Spróbuj wskazać pas tuż przy stole.';
    });
  }
})();

document.addEventListener('DOMContentLoaded', () => {
  'use strict';
  const studio = document.querySelector('[data-drucik-studio]');
  if (!studio) return;
  const drucik = window.FWDrucik;
  const form = studio.querySelector('#drucik-profil');
  const model = studio.querySelector('[data-drucik-model]');
  const status = studio.querySelector('[data-drucik-stan]');
  const saveStatus = studio.querySelector('#drucik-zapis');
  const play = studio.querySelector('#drucik-start');
  const save = form.querySelector('[type=submit]');
  function cloneRobot(prefix) {
    const svg = document.querySelector('#assistant-launch .robot-svg').cloneNode(true);
    svg.querySelectorAll('[id]').forEach((node) => { node.id = prefix + node.id; });
    svg.querySelectorAll('*').forEach((node) => {
      Array.from(node.attributes).forEach((attribute) => {
        if (attribute.value.includes('url(#rb-')) {
          node.setAttribute(attribute.name, attribute.value.replaceAll('url(#rb-', 'url(#' + prefix + 'rb-'));
        }
      });
    });
    return svg;
  }
  model.append(cloneRobot('studio-'));
  document.querySelector('.lab-robot').append(cloneRobot('lab-'));

  const steps = Array.from({ length: 5 }, (_, i) => {
    const label = document.createElement('label');
    label.textContent = 'Krok ' + (i + 1);
    const select = document.createElement('select');
    select.append(new Option('Pomiń', ''));
    Object.entries(drucik.scenes).forEach(([value, scene]) => select.append(new Option(scene[0], value)));
    label.append(select);
    form.querySelector('#drucik-kroki').append(label);
    return select;
  });
  const snacks = { bit: 12, srubka: 8, paliwo: 25 };
  const fuels = { diesel: 'Olej napędowy', benzyna: 'Benzyna', lpg: 'LPG' };
  let energy = 0;
  let version = 0;
  let owner = 0;
  let accountReady = false;
  let saving = false;
  let playing = false;

  function values() {
    return {
      imie: form.elements.imie.value.trim(),
      kolor: form.elements.kolor.value,
      paliwo: form.elements.paliwo.value,
      kroki: steps.map((select) => select.value).filter(Boolean),
      energia: energy,
      wersja: version
    };
  }

  function render(message = '') {
    const profile = values();
    drucik.apply(model, profile);
    status.textContent = (profile.imie || 'Drucik') + ' · Energia ' + energy + '/100'
      + (message ? ' · ' + message : energy < 24 ? ' · Czas na przekąskę' : ' · Gotowy do pracy');
    studio.querySelector('[data-przekaska="paliwo"]').textContent = fuels[profile.paliwo] + ' +25';
    play.disabled = playing;
    save.disabled = !accountReady || saving || playing;
  }

  function fill(record) {
    const profile = record.profil || drucik.defaults();
    version = record.wersja;
    energy = profile.energia;
    form.elements.imie.value = profile.imie;
    form.elements.kolor.value = profile.kolor;
    form.elements.paliwo.value = profile.paliwo;
    steps.forEach((select, i) => { select.value = profile.kroki[i] || ''; });
    render();
  }

  function dirty() {
    saveStatus.textContent = owner ? 'Zmiany oczekują na zapis.' : '';
  }

  async function syncAuth() {
    const next = window.FWAuth?.getUser()?.id || 0;
    if (next === owner) return;
    owner = next;
    accountReady = false;
    fill({ wersja: 0, profil: null });
    saveStatus.textContent = next ? 'Wczytuję Drucika…' : '';
    if (!next) return;
    try {
      const record = await drucik.load();
      if (owner !== next) return;
      accountReady = true;
      fill(record);
      saveStatus.textContent = record.profil ? 'Profil wczytany z konta.' : 'Możesz zapisać swojego pierwszego Drucika.';
    } catch (error) {
      if (owner === next) saveStatus.textContent = error.message;
    }
  }

  form.addEventListener('input', () => { render(); dirty(); });
  studio.querySelector('#drucik-jedzenie').addEventListener('click', (event) => {
    const snack = event.target.closest('[data-przekaska]')?.dataset.przekaska;
    if (!snack || playing) return;
    const full = energy === 100;
    energy = Math.min(100, energy + snacks[snack]);
    render(full ? 'Już pełny' : 'Dzięki za przekąskę!');
    if (!full) dirty();
  });

  play.addEventListener('click', async () => {
    const { kroki } = values();
    if (!kroki.length) { render('Najpierw wybierz polecenie'); return; }
    if (energy < kroki.length * 6) { render('Za mało energii. Nakarm Drucika'); return; }
    const playingOwner = owner;
    playing = true;
    for (const action of kroki) {
      if (owner !== playingOwner || energy < 6) break;
      energy -= 6;
      render(drucik.scenes[action][0]);
      await drucik.show(model, action);
    }
    playing = false;
    render(owner === playingOwner ? 'Program zakończony' : '');
    if (owner === playingOwner) dirty();
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!accountReady || saving || playing) return;
    const data = values();
    if (!/^[\p{L}\p{N} _-]+$/u.test(data.imie)) {
      saveStatus.textContent = 'W imieniu użyj liter, cyfr, spacji, łącznika lub podkreślenia.';
      return;
    }
    const savedOwner = owner;
    saving = true;
    render();
    saveStatus.textContent = 'Zapisuję…';
    try {
      const record = await drucik.save(data);
      if (owner !== savedOwner) return;
      version = record.wersja;
      saveStatus.textContent = 'Profil zapisany na koncie.';
      const current = values();
      if (Object.keys(data).some((key) => key !== 'wersja' && JSON.stringify(data[key]) !== JSON.stringify(current[key]))) dirty();
    } catch (error) {
      if (owner === savedOwner) saveStatus.textContent = error.message;
    } finally {
      saving = false;
      render();
    }
  });

  fill({ wersja: 0, profil: null });
  document.addEventListener('fw-auth-change', syncAuth);
  studio.hidden = false;
});

// ---------- Pytania do prób i wyszukiwarka kompendium ----------
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-proba]').forEach((proba) => {
    const opcje = proba.querySelector('[data-opcje]');
    const wynik = proba.querySelector('[data-wynik]');
    const odpowiedz = proba.querySelector('[data-odpowiedz]').textContent;
    const wskazowka = proba.querySelector('[data-wskazowka]').content.textContent;
    opcje.addEventListener('click', (event) => {
      const wybor = event.target.closest('button[data-opcja]');
      if (!wybor) return;
      opcje.querySelectorAll('button').forEach((przycisk) => {
        przycisk.setAttribute('aria-pressed', String(przycisk === wybor));
      });
      const trafiony = wybor.dataset.opcja === proba.dataset.poprawna;
      wynik.textContent = trafiony ? odpowiedz : 'Spróbuj jeszcze raz. ' + wskazowka;
    });
    opcje.hidden = false;
  });

  const rgb = document.querySelector('[data-rgb]');
  if (rgb) {
    const nazwy = ['Zgaszona', 'Czerwone światło', 'Zielone światło', 'Żółte światło',
      'Niebieskie światło', 'Purpurowe światło', 'Turkusowe światło', 'Białe światło'];
    const kolory = ['#182034', '#ff3030', '#4ef247', '#fff052', '#526dff', '#ef49ef', '#4ff6fb', '#fff'];
    rgb.addEventListener('change', () => {
      const stan = [...rgb.querySelectorAll('input:checked')].reduce((suma, pole) => suma + Number(pole.value), 0);
      rgb.querySelector('[data-rgb-wynik]').textContent = nazwy[stan];
      rgb.style.setProperty('--swiatlo-rgb', kolory[stan]);
    });
    rgb.hidden = false;
  }

  const szukaj = document.querySelector('[data-szukaj-wiedzy]');
  if (!szukaj) return;
  const pole = szukaj.querySelector('input');
  const licznik = szukaj.querySelector('[data-licznik-wiedzy]');
  const dzialy = [...document.querySelectorAll('[data-dzial-wiedzy]')];
  const uprosc = (tekst) => tekst.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '').replace(/ł/g, 'l');
  const hasla = [...document.querySelectorAll('[data-haslo]')].map((karta) => ({
    karta,
    // kod w oknie Arduino IDE nie wchodzi do wyszukiwania haseł
    tekst: uprosc([...karta.childNodes].filter((n) => !(n.classList && (n.classList.contains('ide') || n.classList.contains('gen')))).map((n) => n.textContent).join(' ') + ' ' + karta.dataset.slowa + ' ' + karta.closest('section').querySelector('h2').textContent),
  }));
  function filtruj() {
    const frazy = uprosc(pole.value.trim()).split(/\s+/);
    let ile = 0;
    hasla.forEach(({ karta, tekst }) => {
      karta.hidden = !frazy.every((fraza) => tekst.includes(fraza));
      if (!karta.hidden) ile++;
    });
    dzialy.forEach((dzial) => {
      dzial.hidden = !dzial.querySelector('[data-haslo]:not([hidden])');
    });
    licznik.textContent = ile ? 'Znalezione hasła: ' + ile : 'Nie ma takiego hasła. Spróbuj wpisać jedno słowo.';
  }
  pole.addEventListener('input', filtruj);
  document.querySelectorAll('a[href^="#wiedza-"]').forEach((link) => {
    link.addEventListener('click', () => {
      pole.value = '';
      filtruj();
    });
  });
  szukaj.hidden = false;
  filtruj();
});
