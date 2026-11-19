/* ============================================================================
   Narzędzia online fwdrucik.pl — /narzedzia/
   ----------------------------------------------------------------------------
   Wczytywane wyłącznie na tej podstronie, żeby nie obciążać reszty serwisu.

   Notatnik i kalendarz chodzą po /api/narzedzia.php i wymagają zalogowania.
   Widocznością bloków steruje `data-gdy` w script.js — tutaj tylko próbujemy
   pobrać dane i po cichu odpuszczamy, gdy serwer odpowie „zaloguj się”.
   Reszta narzędzi liczy wszystko w przeglądarce, bez wysyłania czegokolwiek.
   ========================================================================== */
(function () {
  'use strict';

  // -------------------------------------------------------------- narzędzia
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  function esc(t) {
    return String(t == null ? '' : t).replace(/[&<>"']/g, c => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  }

  function ciasteczko(nazwa) {
    const m = document.cookie.match(new RegExp('(?:^|; )' + nazwa + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }

  /* Własna warstwa wywołań API. script.js trzyma swoją w domknięciu, a ten plik
     wykonuje się przed nim (jest wcześniej w dokumencie), więc nie ma na czym
     się oprzeć — dwadzieścia linii powtórzenia jest tańsze niż zależność
     od kolejności ładowania. */
  async function api(sciezka, opcje) {
    opcje = opcje || {};
    const naglowki = {};
    if (opcje.dane) naglowki['Content-Type'] = 'application/json';
    const csrf = ciasteczko('fw_csrf');
    if (csrf) naglowki['X-FW-CSRF'] = csrf;

    let odp;
    try {
      odp = await fetch('/api' + sciezka, {
        method: opcje.metoda || 'GET',
        headers: naglowki,
        credentials: 'same-origin',
        body: opcje.dane ? JSON.stringify(opcje.dane) : undefined
      });
    } catch (e) {
      throw new Error('Brak połączenia z serwerem.');
    }
    let wynik;
    try {
      wynik = await odp.json();
    } catch (e) {
      throw new Error('Serwer zwrócił nieczytelną odpowiedź (kod ' + odp.status + ').');
    }
    if (!odp.ok || wynik.ok === false) {
      const b = new Error(wynik.blad || 'Operacja nie powiodła się.');
      b.kod = odp.status;
      throw b;
    }
    return wynik;
  }

  function komunikat(el, tekst, rodzaj) {
    if (!el) return;
    el.textContent = tekst;
    el.style.color = rodzaj === 'blad' ? 'var(--red)'
      : rodzaj === 'ok' ? 'var(--green)' : 'var(--muted)';
    if (tekst) setTimeout(() => { if (el.textContent === tekst) el.textContent = ''; }, 4000);
  }

  const dataPl = d => new Date(d + 'T00:00:00').toLocaleDateString('pl-PL',
    { day: 'numeric', month: 'long', year: 'numeric' });

  // =========================================================== przełącznik
  const paski = $$('.narzedzia-paski .tab-btn');
  const panele = $$('.narzedzie');
  const wczytane = {};

  function pokaz(nazwa) {
    paski.forEach(b => b.classList.toggle('active', b.dataset.narzedzie === nazwa));
    panele.forEach(p => { p.hidden = p.dataset.panel !== nazwa; });
    if (!wczytane[nazwa] && startery[nazwa]) {
      wczytane[nazwa] = true;
      startery[nazwa]();
    }
    if (location.hash.slice(1) !== nazwa) {
      history.replaceState(null, '', '#' + nazwa);
    }
  }

  paski.forEach(b => b.addEventListener('click', () => pokaz(b.dataset.narzedzie)));

  // ============================================================ wyszukiwarka
  let indeks = null;

  async function pobierzIndeks() {
    if (indeks) return indeks;
    const odp = await fetch('/szukaj.json', { credentials: 'same-origin' });
    indeks = await odp.json();
    return indeks;
  }

  function punktacja(wpis, slowa) {
    let punkty = 0;
    const tytul = wpis.t.toLowerCase();
    const opis = (wpis.o || '').toLowerCase();
    const tresc = (wpis.s || '').toLowerCase();
    for (const s of slowa) {
      if (tytul.includes(s)) punkty += 10;
      if (opis.includes(s)) punkty += 4;
      if (tresc.includes(s)) punkty += 1;
    }
    // Wszystkie słowa muszą gdzieś wystąpić — inaczej „can spawanie" zwraca
    // wszystko, w czym jest samo „can".
    const komplet = slowa.every(s =>
      tytul.includes(s) || opis.includes(s) || tresc.includes(s));
    return komplet ? punkty : 0;
  }

  function fragment(wpis, slowa) {
    const tresc = wpis.s || wpis.o || '';
    const dolne = tresc.toLowerCase();
    let poz = -1;
    for (const s of slowa) {
      poz = dolne.indexOf(s);
      if (poz !== -1) break;
    }
    if (poz === -1) return esc(tresc.slice(0, 160)) + '…';
    const start = Math.max(0, poz - 70);
    let kawalek = tresc.slice(start, start + 200);
    if (start > 0) kawalek = '…' + kawalek;
    let html = esc(kawalek);
    for (const s of slowa) {
      html = html.replace(new RegExp('(' + s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi'),
        '<mark>$1</mark>');
    }
    return html + '…';
  }

  function ustawSzukanie() {
    const pole = $('#szukaj-fraza');
    const status = $('#szukaj-status');
    const lista = $('#szukaj-wyniki');
    if (!pole) return;

    let czekaj = null;
    pole.addEventListener('input', () => {
      clearTimeout(czekaj);
      czekaj = setTimeout(szukaj, 180);
    });

    async function szukaj() {
      const fraza = pole.value.trim().toLowerCase();
      if (fraza.length < 2) {
        lista.innerHTML = '';
        status.textContent = 'Wpisz co najmniej dwa znaki.';
        return;
      }
      let dane;
      try {
        dane = await pobierzIndeks();
      } catch (e) {
        status.textContent = 'Nie udało się wczytać indeksu wyszukiwania.';
        return;
      }
      const slowa = fraza.split(/\s+/).filter(Boolean);
      const trafienia = dane
        .map(w => ({ w, p: punktacja(w, slowa) }))
        .filter(x => x.p > 0)
        .sort((a, b) => b.p - a.p)
        .slice(0, 25);

      if (!trafienia.length) {
        lista.innerHTML = '';
        status.textContent = 'Nic nie znaleziono. Spróbuj innego słowa.';
        return;
      }
      status.textContent = trafienia.length === 25
        ? 'Pokazuję 25 najlepiej pasujących wyników.'
        : 'Znaleziono: ' + trafienia.length;
      lista.innerHTML = trafienia.map(({ w }) => `
        <li>
          <a href="${esc(w.u)}">${esc(w.t)}</a>
          ${w.k ? `<span class="badge badge-blue">${esc(w.k)}</span>` : ''}
          <p>${fragment(w, slowa)}</p>
        </li>`).join('');
    }

    // Fraza z adresu: /narzedzia/#szukaj?q=... nie jest potrzebna, ale gdy ktoś
    // trafi tu z linku z parametrem, od razu pokazujemy wyniki.
    const q = new URLSearchParams(location.search).get('q');
    if (q) {
      pole.value = q;
      szukaj();
    }
  }

  // ================================================================ notatnik
  function ustawNotatnik() {
    const form = $('#notatka-form');
    if (!form) return;
    const spis = $('#notatki-spis');
    const polaTytul = $('#notatka-tytul');
    const polaTresc = $('#notatka-tresc');
    const przyciskUsun = $('#notatka-usun');
    const info = $('#notatka-komunikat');
    let notatki = [];
    let biezaca = 0;

    function rysujSpis() {
      if (!notatki.length) {
        spis.innerHTML = '<li class="pusto">Brak notatek. Zacznij od „Nowa notatka”.</li>';
        return;
      }
      spis.innerHTML = notatki.map(n => `
        <li>
          <button type="button" class="notatka-poz${n.id === biezaca ? ' aktywna' : ''}" data-id="${n.id}">
            <span class="notatka-tyt">${esc(n.tytul)}</span>
            <span class="notatka-data">${esc((n.zmieniona || '').slice(0, 16).replace('T', ' '))}</span>
          </button>
        </li>`).join('');
    }

    function otworz(id) {
      const n = notatki.find(x => x.id === id);
      biezaca = n ? n.id : 0;
      polaTytul.value = n ? n.tytul : '';
      polaTresc.value = n ? n.tresc : '';
      przyciskUsun.hidden = !n;
      rysujSpis();
    }

    spis.addEventListener('click', e => {
      const b = e.target.closest('.notatka-poz');
      if (b) otworz(Number(b.dataset.id));
    });

    $('#notatka-nowa').addEventListener('click', () => {
      otworz(0);
      polaTytul.focus();
    });

    form.addEventListener('submit', async e => {
      e.preventDefault();
      try {
        const r = await api('/narzedzia.php?akcja=notatka-zapisz', {
          metoda: 'POST',
          dane: { id: biezaca, tytul: polaTytul.value, tresc: polaTresc.value }
        });
        biezaca = r.id;
        await wczytaj();
        otworz(biezaca);
        komunikat(info, 'Zapisano.', 'ok');
      } catch (err) {
        komunikat(info, err.message, 'blad');
      }
    });

    przyciskUsun.addEventListener('click', async () => {
      if (!biezaca || !confirm('Usunąć tę notatkę? Tego nie da się cofnąć.')) return;
      try {
        await api('/narzedzia.php?akcja=notatka-usun', { metoda: 'POST', dane: { id: biezaca } });
        await wczytaj();
        otworz(0);
        komunikat(info, 'Notatka usunięta.', 'ok');
      } catch (err) {
        komunikat(info, err.message, 'blad');
      }
    });

    async function wczytaj() {
      try {
        const r = await api('/narzedzia.php?akcja=notatki');
        notatki = r.notatki;
        rysujSpis();
      } catch (e) {
        // 401 to niezalogowany — blok i tak jest ukryty przez data-gdy.
        if (e.kod !== 401) komunikat(info, e.message, 'blad');
      }
    }

    wczytaj();
  }

  // =============================================================== kalendarz
  function ustawKalendarz() {
    const siatka = $('#kal-siatka');
    if (!siatka) return;
    const etykieta = $('#kal-etykieta');
    const lista = $('#kal-lista');
    const form = $('#kal-form');
    const info = $('#kal-komunikat');
    const usun = $('#kal-usun');
    let widok = new Date();
    let wydarzenia = [];
    let edytowane = 0;

    const iso = d => d.getFullYear() + '-' +
      String(d.getMonth() + 1).padStart(2, '0') + '-' +
      String(d.getDate()).padStart(2, '0');

    function zakres() {
      const od = new Date(widok.getFullYear(), widok.getMonth(), 1);
      const doo = new Date(widok.getFullYear(), widok.getMonth() + 1, 0);
      return [iso(od), iso(doo)];
    }

    function rysuj() {
      etykieta.textContent = widok.toLocaleDateString('pl-PL', { month: 'long', year: 'numeric' });

      const pierwszy = new Date(widok.getFullYear(), widok.getMonth(), 1);
      // Poniedziałek jako pierwszy dzień tygodnia — polski układ kalendarza.
      const przesuniecie = (pierwszy.getDay() + 6) % 7;
      const dni = new Date(widok.getFullYear(), widok.getMonth() + 1, 0).getDate();
      const dzisIso = iso(new Date());

      let html = ['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'So', 'Nd']
        .map(d => `<div class="kal-naglowek">${d}</div>`).join('');
      for (let i = 0; i < przesuniecie; i++) html += '<div class="kal-pusta"></div>';
      for (let d = 1; d <= dni; d++) {
        const data = iso(new Date(widok.getFullYear(), widok.getMonth(), d));
        const ile = wydarzenia.filter(w => w.dzien === data).length;
        html += `<button type="button" class="kal-dzien${data === dzisIso ? ' dzis' : ''}${ile ? ' ma-wpisy' : ''}"
                   data-dzien="${data}" aria-label="${d} ${etykieta.textContent}${ile ? ', wydarzeń: ' + ile : ''}">
                   <span class="kal-numer">${d}</span>
                   ${ile ? `<span class="kal-kropki">${'•'.repeat(Math.min(ile, 3))}</span>` : ''}
                 </button>`;
      }
      siatka.innerHTML = html;

      lista.innerHTML = wydarzenia.length
        ? wydarzenia.map(w => `
            <li>
              <button type="button" class="kal-wpis" data-id="${w.id}">
                <span class="kal-wpis-data">${esc(dataPl(w.dzien))}${w.godzina ? ', ' + esc(w.godzina) : ''}</span>
                <span class="kal-wpis-tytul">${esc(w.tytul)}</span>
                ${w.opis ? `<span class="kal-wpis-opis">${esc(w.opis)}</span>` : ''}
              </button>
            </li>`).join('')
        : '<li class="pusto">W tym miesiącu nic nie zaplanowano.</li>';
    }

    function otworzForm(dzien, w) {
      edytowane = w ? w.id : 0;
      $('#kal-form-tytul').textContent = w ? 'Edytuj wydarzenie' : 'Nowe wydarzenie';
      $('#kal-dzien').value = w ? w.dzien : dzien;
      $('#kal-godzina').value = w ? w.godzina : '';
      $('#kal-tytul').value = w ? w.tytul : '';
      $('#kal-opis').value = w ? w.opis : '';
      usun.hidden = !w;
      form.hidden = false;
      $('#kal-tytul').focus();
    }

    siatka.addEventListener('click', e => {
      const b = e.target.closest('.kal-dzien');
      if (b) otworzForm(b.dataset.dzien, null);
    });

    lista.addEventListener('click', e => {
      const b = e.target.closest('.kal-wpis');
      if (!b) return;
      const w = wydarzenia.find(x => x.id === Number(b.dataset.id));
      if (w) otworzForm(w.dzien, w);
    });

    $('#kal-anuluj').addEventListener('click', () => { form.hidden = true; });

    $('#kal-poprzedni').addEventListener('click', () => {
      widok = new Date(widok.getFullYear(), widok.getMonth() - 1, 1);
      wczytaj();
    });
    $('#kal-nastepny').addEventListener('click', () => {
      widok = new Date(widok.getFullYear(), widok.getMonth() + 1, 1);
      wczytaj();
    });
    $('#kal-dzis').addEventListener('click', () => {
      widok = new Date();
      wczytaj();
    });

    form.addEventListener('submit', async e => {
      e.preventDefault();
      try {
        await api('/narzedzia.php?akcja=wydarzenie-zapisz', {
          metoda: 'POST',
          dane: {
            id: edytowane,
            dzien: $('#kal-dzien').value,
            godzina: $('#kal-godzina').value,
            tytul: $('#kal-tytul').value,
            opis: $('#kal-opis').value
          }
        });
        form.hidden = true;
        await wczytaj();
        komunikat(info, 'Zapisano.', 'ok');
      } catch (err) {
        komunikat(info, err.message, 'blad');
      }
    });

    usun.addEventListener('click', async () => {
      if (!edytowane || !confirm('Usunąć to wydarzenie?')) return;
      try {
        await api('/narzedzia.php?akcja=wydarzenie-usun', { metoda: 'POST', dane: { id: edytowane } });
        form.hidden = true;
        await wczytaj();
        komunikat(info, 'Wydarzenie usunięte.', 'ok');
      } catch (err) {
        komunikat(info, err.message, 'blad');
      }
    });

    async function wczytaj() {
      const [od, doo] = zakres();
      try {
        const r = await api(`/narzedzia.php?akcja=kalendarz&od=${od}&do=${doo}`);
        wydarzenia = r.wydarzenia;
      } catch (e) {
        wydarzenia = [];
        if (e.kod !== 401) komunikat(info, e.message, 'blad');
      }
      rysuj();
    }

    wczytaj();
  }

  // ============================================================= przelicznik
  // Każda jednostka umie przeliczyć siebie na wartość bazową i z powrotem.
  // Skala załatwia większość przypadków, ale temperatura ma przesunięcie,
  // a spalanie jest odwrotnie proporcjonalne — stąd pary funkcji, nie mnożniki.
  const skala = m => ({ do: v => v * m, z: v => v / m });

  const GRUPY = {
    'Ciśnienie': {
      baza: 'Pa',
      j: {
        'bar': skala(1e5),
        'mbar': skala(100),
        'Pa': skala(1),
        'kPa': skala(1e3),
        'MPa': skala(1e6),
        'psi (lbf/in²)': skala(6894.757293),
        'atm': skala(101325),
        'at (kgf/cm²)': skala(98066.5),
        'mmHg (Tr)': skala(133.322387)
      }
    },
    'Moment obrotowy': {
      baza: 'N·m',
      j: {
        'N·m': skala(1),
        'kgf·m': skala(9.80665),
        'lbf·ft': skala(1.355817948),
        'lbf·in': skala(0.112984829)
      }
    },
    'Długość': {
      baza: 'm',
      j: {
        'mm': skala(1e-3),
        'cm': skala(1e-2),
        'm': skala(1),
        'km': skala(1e3),
        'cal (in)': skala(0.0254),
        'stopa (ft)': skala(0.3048),
        'mila': skala(1609.344)
      }
    },
    'Moc': {
      baza: 'W',
      j: {
        'W': skala(1),
        'kW': skala(1e3),
        'KM (metryczne)': skala(735.49875),
        'hp (mechaniczne)': skala(745.699872)
      }
    },
    'Przepływ': {
      baza: 'l/min',
      j: {
        'l/min': skala(1),
        'l/h': skala(1 / 60),
        'm³/h': skala(1000 / 60),
        'gal US/min': skala(3.785411784)
      }
    },
    'Temperatura': {
      baza: '°C',
      j: {
        '°C': { do: v => v, z: v => v },
        '°F': { do: v => (v - 32) * 5 / 9, z: v => v * 9 / 5 + 32 },
        'K': { do: v => v - 273.15, z: v => v + 273.15 }
      }
    },
    'Objętość': {
      baza: 'l',
      j: {
        'ml': skala(1e-3),
        'l': skala(1),
        'm³': skala(1000),
        'gal US': skala(3.785411784),
        'gal UK': skala(4.54609)
      }
    },
    'Masa': {
      baza: 'kg',
      j: {
        'g': skala(1e-3),
        'kg': skala(1),
        't': skala(1000),
        'funt (lb)': skala(0.45359237),
        'uncja (oz)': skala(0.028349523)
      }
    },
    'Spalanie': {
      baza: 'l/100 km',
      j: {
        'l/100 km': { do: v => v, z: v => v },
        'km/l': { do: v => 100 / v, z: v => 100 / v },
        'mpg (US)': { do: v => 235.214583 / v, z: v => 235.214583 / v }
      }
    }
  };

  function ustawPrzelicznik() {
    const grupa = $('#przel-grupa');
    if (!grupa) return;
    const wartosc = $('#przel-wartosc');
    const zJ = $('#przel-z');
    const naJ = $('#przel-na');
    const wynik = $('#przel-wynik');
    const tabela = $('#przel-wszystkie');

    grupa.innerHTML = Object.keys(GRUPY).map(g => `<option>${esc(g)}</option>`).join('');

    function odswiezJednostki() {
      const nazwy = Object.keys(GRUPY[grupa.value].j);
      const opcje = nazwy.map(n => `<option>${esc(n)}</option>`).join('');
      zJ.innerHTML = opcje;
      naJ.innerHTML = opcje;
      zJ.selectedIndex = 0;
      naJ.selectedIndex = Math.min(1, nazwy.length - 1);
      przelicz();
    }

    function formatuj(x) {
      if (!isFinite(x)) return '—';
      const a = Math.abs(x);
      if (a !== 0 && (a < 1e-4 || a >= 1e7)) return x.toExponential(4).replace('.', ',');
      return x.toLocaleString('pl-PL', { maximumFractionDigits: 6 });
    }

    function przelicz() {
      const g = GRUPY[grupa.value];
      const v = parseFloat(wartosc.value);
      if (isNaN(v) || !g.j[zJ.value] || !g.j[naJ.value]) {
        wynik.textContent = '—';
        tabela.innerHTML = '';
        return;
      }
      const bazowa = g.j[zJ.value].do(v);
      wynik.textContent = `${formatuj(v)} ${zJ.value} = ${formatuj(g.j[naJ.value].z(bazowa))} ${naJ.value}`;
      tabela.innerHTML = Object.keys(g.j).map(n =>
        `<tr><td>${esc(n)}</td><td class="liczba">${formatuj(g.j[n].z(bazowa))}</td></tr>`).join('');
    }

    grupa.addEventListener('change', odswiezJednostki);
    [wartosc, zJ, naJ].forEach(el => el.addEventListener('input', przelicz));
    odswiezJednostki();
  }

  // ================================================================ rezystor
  const KOLORY = [
    { n: 'czarny', hex: '#111418', cyfra: 0, mn: 1e0 },
    { n: 'brązowy', hex: '#7a4a20', cyfra: 1, mn: 1e1, tol: 1, tk: 100 },
    { n: 'czerwony', hex: '#c62828', cyfra: 2, mn: 1e2, tol: 2, tk: 50 },
    { n: 'pomarańczowy', hex: '#ef6c00', cyfra: 3, mn: 1e3, tk: 15 },
    { n: 'żółty', hex: '#f9d423', cyfra: 4, mn: 1e4, tk: 25 },
    { n: 'zielony', hex: '#2e7d32', cyfra: 5, mn: 1e5, tol: 0.5 },
    { n: 'niebieski', hex: '#1565c0', cyfra: 6, mn: 1e6, tol: 0.25, tk: 10 },
    { n: 'fioletowy', hex: '#6a1b9a', cyfra: 7, mn: 1e7, tol: 0.1, tk: 5 },
    { n: 'szary', hex: '#757575', cyfra: 8, mn: 1e8, tol: 0.05 },
    { n: 'biały', hex: '#eceff1', cyfra: 9, mn: 1e9 },
    { n: 'złoty', hex: '#c9a227', mn: 1e-1, tol: 5 },
    { n: 'srebrny', hex: '#b0bec5', mn: 1e-2, tol: 10 }
  ];

  function ustawRezystor() {
    const wybor = $('#rez-paski');
    if (!wybor) return;
    const kontener = $('#rez-selecty');
    const podglad = $('#rez-podglad');
    const wynik = $('#rez-wynik');

    function opcje(filtr, wybrany) {
      return KOLORY.filter(filtr)
        .map(k => `<option value="${k.n}"${k.n === wybrany ? ' selected' : ''}>${k.n}</option>`)
        .join('');
    }

    function zbuduj() {
      const ile = Number(wybor.value);
      const cyfr = ile === 4 ? 2 : 3;
      let html = '';
      for (let i = 0; i < cyfr; i++) {
        html += `<div><label for="rez-c${i}">${i + 1}. cyfra</label>
          <select id="rez-c${i}" class="form-control" data-rola="cyfra">
            ${opcje(k => k.cyfra !== undefined, i === 0 ? 'brązowy' : 'czarny')}</select></div>`;
      }
      html += `<div><label for="rez-mn">Mnożnik</label>
        <select id="rez-mn" class="form-control" data-rola="mn">
          ${opcje(k => k.mn !== undefined, 'czerwony')}</select></div>`;
      html += `<div><label for="rez-tol">Tolerancja</label>
        <select id="rez-tol" class="form-control" data-rola="tol">
          ${opcje(k => k.tol !== undefined, 'złoty')}</select></div>`;
      if (ile === 6) {
        html += `<div><label for="rez-tk">Wsp. temperaturowy</label>
          <select id="rez-tk" class="form-control" data-rola="tk">
            ${opcje(k => k.tk !== undefined, 'brązowy')}</select></div>`;
      }
      kontener.innerHTML = html;
      $$('select', kontener).forEach(s => s.addEventListener('change', licz));
      licz();
    }

    function kolor(id) {
      const el = $('#' + id);
      return el ? KOLORY.find(k => k.n === el.value) : null;
    }

    function formatOhm(r) {
      if (r >= 1e6) return (r / 1e6).toLocaleString('pl-PL', { maximumFractionDigits: 3 }) + ' MΩ';
      if (r >= 1e3) return (r / 1e3).toLocaleString('pl-PL', { maximumFractionDigits: 3 }) + ' kΩ';
      return r.toLocaleString('pl-PL', { maximumFractionDigits: 3 }) + ' Ω';
    }

    function licz() {
      const ile = Number(wybor.value);
      const cyfr = ile === 4 ? 2 : 3;
      let cyfry = '';
      const uzyte = [];
      for (let i = 0; i < cyfr; i++) {
        const k = kolor('rez-c' + i);
        if (!k) return;
        cyfry += k.cyfra;
        uzyte.push(k);
      }
      const mn = kolor('rez-mn');
      const tol = kolor('rez-tol');
      const tk = ile === 6 ? kolor('rez-tk') : null;
      if (!mn || !tol) return;
      uzyte.push(mn, tol);
      if (tk) uzyte.push(tk);

      const r = parseInt(cyfry, 10) * mn.mn;
      const odchylka = r * tol.tol / 100;
      wynik.innerHTML = `${formatOhm(r)} <span class="wynik-dodatek">±${tol.tol}%`
        + ` (${formatOhm(r - odchylka)} – ${formatOhm(r + odchylka)})`
        + (tk ? `, ${tk.tk} ppm/K` : '') + '</span>';

      podglad.innerHTML = '<span class="rez-korpus">'
        + uzyte.map(k => `<span class="rez-pasek" style="background:${k.hex}"></span>`).join('')
        + '</span>';
    }

    wybor.addEventListener('change', zbuduj);
    zbuduj();
  }

  // ===================================================================== OBD
  // Kody uniwersalne grupy P0 — definicje są znormalizowane i identyczne
  // w każdej marce. Kodów producenta (P1/P2/P3) świadomie nie ma: te same
  // cztery znaki znaczą co innego u każdego wytwórcy i zgadywanie ich
  // wprowadzałoby w błąd.
  const OBD = [
    ['P0011', 'Ustawienie wałka rozrządu A (bank 1) — nadmierne opóźnienie fazy'],
    ['P0014', 'Ustawienie wałka rozrządu B (bank 1) — nadmierne wyprzedzenie fazy'],
    ['P0016', 'Brak korelacji położenia wału korbowego i wałka rozrządu (bank 1, czujnik A)'],
    ['P0017', 'Brak korelacji położenia wału korbowego i wałka rozrządu (bank 1, czujnik B)'],
    ['P0030', 'Obwód grzałki sondy lambda — bank 1, czujnik 1'],
    ['P0031', 'Obwód grzałki sondy lambda zwarcie do masy — bank 1, czujnik 1'],
    ['P0032', 'Obwód grzałki sondy lambda zwarcie do plusa — bank 1, czujnik 1'],
    ['P0068', 'Niezgodność sygnału przepływomierza z położeniem przepustnicy (możliwy nieszczelny układ dolotowy)'],
    ['P0071', 'Czujnik temperatury powietrza zewnętrznego — sygnał poza zakresem'],
    ['P0087', 'Zbyt niskie ciśnienie w szynie paliwowej'],
    ['P0088', 'Zbyt wysokie ciśnienie w szynie paliwowej'],
    ['P0093', 'Wykryty duży wyciek w układzie paliwowym'],
    ['P0100', 'Obwód przepływomierza powietrza (MAF) — usterka ogólna'],
    ['P0101', 'Przepływomierz powietrza (MAF) — sygnał poza zakresem lub niespójny'],
    ['P0102', 'Przepływomierz powietrza (MAF) — sygnał zbyt niski'],
    ['P0103', 'Przepływomierz powietrza (MAF) — sygnał zbyt wysoki'],
    ['P0105', 'Obwód czujnika ciśnienia bezwzględnego w kolektorze (MAP)'],
    ['P0106', 'Czujnik MAP — sygnał poza zakresem'],
    ['P0107', 'Czujnik MAP — sygnał zbyt niski'],
    ['P0108', 'Czujnik MAP — sygnał zbyt wysoki'],
    ['P0110', 'Obwód czujnika temperatury powietrza dolotowego (IAT)'],
    ['P0112', 'Czujnik temperatury powietrza dolotowego — sygnał zbyt niski'],
    ['P0113', 'Czujnik temperatury powietrza dolotowego — sygnał zbyt wysoki'],
    ['P0115', 'Obwód czujnika temperatury cieczy chłodzącej (ECT)'],
    ['P0117', 'Czujnik temperatury cieczy chłodzącej — sygnał zbyt niski'],
    ['P0118', 'Czujnik temperatury cieczy chłodzącej — sygnał zbyt wysoki'],
    ['P0120', 'Obwód czujnika położenia przepustnicy / pedału A'],
    ['P0122', 'Czujnik położenia przepustnicy A — sygnał zbyt niski'],
    ['P0123', 'Czujnik położenia przepustnicy A — sygnał zbyt wysoki'],
    ['P0125', 'Zbyt niska temperatura cieczy do wejścia w regulację zamkniętą (często termostat)'],
    ['P0128', 'Termostat — silnik nie osiąga temperatury roboczej'],
    ['P0130', 'Obwód sondy lambda — bank 1, czujnik 1'],
    ['P0131', 'Sonda lambda — napięcie zbyt niskie (bank 1, czujnik 1)'],
    ['P0132', 'Sonda lambda — napięcie zbyt wysokie (bank 1, czujnik 1)'],
    ['P0133', 'Sonda lambda — zbyt wolna reakcja (bank 1, czujnik 1)'],
    ['P0134', 'Sonda lambda — brak aktywności sygnału (bank 1, czujnik 1)'],
    ['P0135', 'Grzałka sondy lambda — usterka obwodu (bank 1, czujnik 1)'],
    ['P0136', 'Obwód sondy lambda za katalizatorem — bank 1, czujnik 2'],
    ['P0137', 'Sonda lambda za katalizatorem — napięcie zbyt niskie (bank 1, czujnik 2)'],
    ['P0138', 'Sonda lambda za katalizatorem — napięcie zbyt wysokie (bank 1, czujnik 2)'],
    ['P0140', 'Sonda lambda za katalizatorem — brak aktywności (bank 1, czujnik 2)'],
    ['P0141', 'Grzałka sondy lambda za katalizatorem — usterka (bank 1, czujnik 2)'],
    ['P0150', 'Obwód sondy lambda — bank 2, czujnik 1'],
    ['P0155', 'Grzałka sondy lambda — usterka obwodu (bank 2, czujnik 1)'],
    ['P0160', 'Sonda lambda — brak aktywności (bank 2, czujnik 2)'],
    ['P0170', 'Nieprawidłowa korekta składu mieszanki — bank 1'],
    ['P0171', 'Mieszanka zbyt uboga — bank 1'],
    ['P0172', 'Mieszanka zbyt bogata — bank 1'],
    ['P0173', 'Nieprawidłowa korekta składu mieszanki — bank 2'],
    ['P0174', 'Mieszanka zbyt uboga — bank 2'],
    ['P0175', 'Mieszanka zbyt bogata — bank 2'],
    ['P0190', 'Obwód czujnika ciśnienia w szynie paliwowej'],
    ['P0191', 'Czujnik ciśnienia paliwa — sygnał poza zakresem'],
    ['P0200', 'Obwód wtryskiwaczy — usterka ogólna'],
    ['P0201', 'Obwód wtryskiwacza — cylinder 1'],
    ['P0202', 'Obwód wtryskiwacza — cylinder 2'],
    ['P0203', 'Obwód wtryskiwacza — cylinder 3'],
    ['P0204', 'Obwód wtryskiwacza — cylinder 4'],
    ['P0205', 'Obwód wtryskiwacza — cylinder 5'],
    ['P0206', 'Obwód wtryskiwacza — cylinder 6'],
    ['P0217', 'Przegrzanie silnika'],
    ['P0219', 'Przekroczenie dopuszczalnych obrotów silnika'],
    ['P0230', 'Obwód sterowania pompą paliwa'],
    ['P0234', 'Zbyt wysokie ciśnienie doładowania'],
    ['P0243', 'Zawór sterujący doładowaniem (wastegate) — obwód sterowania'],
    ['P0299', 'Zbyt niskie ciśnienie doładowania (przecieki, zawór, geometria turbiny)'],
    ['P0300', 'Wypadanie zapłonu w przypadkowych cylindrach'],
    ['P0301', 'Wypadanie zapłonu — cylinder 1'],
    ['P0302', 'Wypadanie zapłonu — cylinder 2'],
    ['P0303', 'Wypadanie zapłonu — cylinder 3'],
    ['P0304', 'Wypadanie zapłonu — cylinder 4'],
    ['P0305', 'Wypadanie zapłonu — cylinder 5'],
    ['P0306', 'Wypadanie zapłonu — cylinder 6'],
    ['P0325', 'Obwód czujnika spalania stukowego — bank 1'],
    ['P0327', 'Czujnik spalania stukowego — sygnał zbyt niski (bank 1)'],
    ['P0328', 'Czujnik spalania stukowego — sygnał zbyt wysoki (bank 1)'],
    ['P0335', 'Obwód czujnika położenia wału korbowego (CKP)'],
    ['P0336', 'Czujnik położenia wału korbowego — sygnał poza zakresem'],
    ['P0339', 'Czujnik położenia wału korbowego — sygnał przerywany'],
    ['P0340', 'Obwód czujnika położenia wałka rozrządu (CMP)'],
    ['P0341', 'Czujnik położenia wałka rozrządu — sygnał poza zakresem'],
    ['P0344', 'Czujnik położenia wałka rozrządu — sygnał przerywany'],
    ['P0351', 'Obwód pierwotny/wtórny cewki zapłonowej A'],
    ['P0352', 'Obwód pierwotny/wtórny cewki zapłonowej B'],
    ['P0353', 'Obwód pierwotny/wtórny cewki zapłonowej C'],
    ['P0354', 'Obwód pierwotny/wtórny cewki zapłonowej D'],
    ['P0380', 'Obwód świec żarowych / grzałki wstępnej'],
    ['P0401', 'Recyrkulacja spalin (EGR) — zbyt mały przepływ'],
    ['P0402', 'Recyrkulacja spalin (EGR) — zbyt duży przepływ'],
    ['P0403', 'Obwód sterowania zaworem EGR'],
    ['P0404', 'Zawór EGR — sygnał poza zakresem'],
    ['P0420', 'Sprawność katalizatora poniżej progu — bank 1'],
    ['P0430', 'Sprawność katalizatora poniżej progu — bank 2'],
    ['P0440', 'Układ odprowadzania par paliwa (EVAP) — usterka ogólna'],
    ['P0441', 'EVAP — nieprawidłowy przepływ przedmuchu'],
    ['P0442', 'EVAP — mała nieszczelność'],
    ['P0455', 'EVAP — duża nieszczelność (często niedokręcony korek wlewu)'],
    ['P0456', 'EVAP — bardzo mała nieszczelność'],
    ['P0460', 'Obwód czujnika poziomu paliwa'],
    ['P0480', 'Obwód sterowania wentylatorem chłodnicy 1'],
    ['P0500', 'Obwód czujnika prędkości pojazdu'],
    ['P0505', 'Układ regulacji biegu jałowego — usterka'],
    ['P0520', 'Obwód czujnika ciśnienia oleju'],
    ['P0521', 'Czujnik ciśnienia oleju — sygnał poza zakresem'],
    ['P0532', 'Czujnik ciśnienia czynnika klimatyzacji — sygnał zbyt niski'],
    ['P0533', 'Czujnik ciśnienia czynnika klimatyzacji — sygnał zbyt wysoki'],
    ['P0560', 'Nieprawidłowe napięcie zasilania systemu'],
    ['P0562', 'Napięcie zasilania systemu zbyt niskie'],
    ['P0563', 'Napięcie zasilania systemu zbyt wysokie'],
    ['P0571', 'Obwód wyłącznika świateł stop'],
    ['P0600', 'Błąd komunikacji szeregowej między sterownikami'],
    ['P0601', 'Błąd sumy kontrolnej pamięci sterownika'],
    ['P0602', 'Błąd programowania sterownika'],
    ['P0606', 'Usterka procesora sterownika silnika'],
    ['P0620', 'Obwód sterowania alternatorem'],
    ['P0622', 'Obwód sterowania polem alternatora — usterka'],
    ['P0645', 'Obwód przekaźnika sprzęgła sprężarki klimatyzacji'],
    ['P0700', 'Układ sterowania skrzynią biegów — zgłoszona usterka (kod szczegółowy w sterowniku skrzyni)'],
    ['P0715', 'Obwód czujnika prędkości wejściowej skrzyni'],
    ['P0720', 'Obwód czujnika prędkości wyjściowej skrzyni'],
    ['P0730', 'Nieprawidłowe przełożenie skrzyni biegów'],
    ['P0741', 'Sprzęgło blokady konwertera — brak zazębienia lub poślizg'],
    ['P0750', 'Elektrozawór zmiany biegów A — usterka obwodu'],
    ['P2002', 'Filtr cząstek stałych (DPF) — sprawność poniżej progu, bank 1'],
    ['P2015', 'Czujnik położenia klap kolektora dolotowego — sygnał poza zakresem'],
    ['P2096', 'Korekta po katalizatorze zbyt uboga — bank 1'],
    ['P2097', 'Korekta po katalizatorze zbyt bogata — bank 1'],
    ['P2452', 'Czujnik ciśnienia różnicowego filtra DPF — usterka obwodu'],
    ['P2453', 'Czujnik ciśnienia różnicowego filtra DPF — sygnał poza zakresem'],
    ['P2463', 'Filtr DPF — nadmierne nagromadzenie sadzy'],
    ['P20EE', 'Katalizator SCR — sprawność redukcji NOx poniżej progu (bank 1)'],
    ['U0100', 'Utrata komunikacji ze sterownikiem silnika'],
    ['U0101', 'Utrata komunikacji ze sterownikiem skrzyni biegów'],
    ['U0121', 'Utrata komunikacji ze sterownikiem ABS'],
    ['U0140', 'Utrata komunikacji ze sterownikiem nadwozia (BCM)'],
    ['U0155', 'Utrata komunikacji z zestawem wskaźników']
  ];

  function ustawObd() {
    const pole = $('#obd-fraza');
    if (!pole) return;
    const status = $('#obd-status');
    const lista = $('#obd-wyniki');

    function rysuj(trafienia, fraza) {
      if (!fraza) {
        status.textContent = `Baza zawiera ${OBD.length} kodów uniwersalnych. Wpisz kod albo objaw.`;
        lista.innerHTML = '';
        return;
      }
      if (!trafienia.length) {
        status.textContent = 'Nie znaleziono. Jeśli kod zaczyna się od P1, P2 albo P3, jest to kod producenta — sprawdź dokumentację marki.';
        lista.innerHTML = '';
        return;
      }
      status.textContent = 'Znaleziono: ' + trafienia.length;
      lista.innerHTML = trafienia.slice(0, 40).map(([kod, opis]) =>
        `<li><span class="obd-kod">${esc(kod)}</span><span class="obd-opis">${esc(opis)}</span></li>`).join('');
    }

    pole.addEventListener('input', () => {
      const fraza = pole.value.trim().toLowerCase();
      if (!fraza) return rysuj([], '');
      rysuj(OBD.filter(([k, o]) =>
        k.toLowerCase().includes(fraza) || o.toLowerCase().includes(fraza)), fraza);
    });

    rysuj([], '');
  }

  // ================================================================== wycena
  function ustawWycene() {
    const pola = ['wyc-godziny', 'wyc-stawka', 'wyc-czesci', 'wyc-marza',
      'wyc-km', 'wyc-kmstawka', 'wyc-vat'].map(id => $('#' + id));
    if (pola.some(p => !p)) return;
    const rozbicie = $('#wyc-rozbicie');
    const suma = $('#wyc-suma');
    const zl = x => x.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' zł';

    function licz() {
      const [g, stawka, czesci, marza, km, kmStawka, vat] =
        pola.map(p => parseFloat(p.value) || 0);
      const robocizna = g * stawka;
      const czesciBrutto = czesci * (1 + marza / 100);
      const dojazd = km * kmStawka;
      const netto = robocizna + czesciBrutto + dojazd;
      const podatek = netto * vat / 100;

      rozbicie.innerHTML = [
        ['Robocizna', `${g} h × ${zl(stawka)}`, robocizna],
        ['Części z marżą', `${zl(czesci)} + ${marza}%`, czesciBrutto],
        ['Dojazd', `${km} km × ${zl(kmStawka)}`, dojazd],
        ['Razem netto', '', netto],
        [`VAT ${vat}%`, '', podatek]
      ].map(([nazwa, opis, kwota]) =>
        `<tr><th scope="row">${esc(nazwa)}</th><td class="wyc-opis">${esc(opis)}</td><td class="liczba">${zl(kwota)}</td></tr>`
      ).join('');

      suma.textContent = 'Do zapłaty brutto: ' + zl(netto + podatek);
    }

    pola.forEach(p => p.addEventListener('input', licz));
    licz();
  }

  // ================================================================== start
  const startery = {
    szukaj: ustawSzukanie,
    notatnik: ustawNotatnik,
    kalendarz: ustawKalendarz,
    przelicznik: ustawPrzelicznik,
    rezystor: ustawRezystor,
    obd: ustawObd,
    wycena: ustawWycene
  };

  function uruchom() {
    const zHasha = location.hash.slice(1);
    const start = startery[zHasha] ? zHasha : 'szukaj';
    pokaz(start);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', uruchom);
  } else {
    uruchom();
  }
})();
