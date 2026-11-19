/* ============================================================================
   Panel administratora — produkty i zamówienia
   ----------------------------------------------------------------------------
   Dodawanie produktu prowadzone krok po kroku: podstawowe dane, cena
   i dostępność, zdjęcia, publikacja. Zdjęcia można wgrać dopiero po zapisaniu
   produktu — plik musi mieć do czego przypisać nazwę, a wgrywanie „na zapas"
   zostawiałoby na dysku pliki bez właściciela.
   ========================================================================== */
(function () {
  'use strict';

  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));

  const korzen = $('#panel-sklep');
  if (!korzen) return;

  const { api, zl, esc, komunikat } = window.FWSklep || {};
  if (!api) return;

  const STATUSY = {
    szkic: 'Szkic — widoczny tylko dla Ciebie',
    opublikowany: 'Opublikowany — widoczny w sklepie',
    ukryty: 'Ukryty — schowany, ale nie skasowany'
  };

  let produkty = [];
  let edytowany = null;   // pełny produkt albo null przy dodawaniu
  let zaladowanyAllegroUrl = '';
  let zaladowanyAllegroId = '';
  let krok = 1;

  // ------------------------------------------------------------- lista
  async function wczytajProdukty() {
    const spis = $('#produkty-spis');
    try {
      const r = await api('/sklep.php?akcja=admin-produkty');
      produkty = r.produkty;
    } catch (e) {
      spis.innerHTML = '<li class="pusto">' + esc(e.message) + '</li>';
      return;
    }
    spis.innerHTML = produkty.length ? produkty.map(p => `
      <li class="produkt-wiersz" data-id="${p.id}">
        <div class="produkt-wiersz-obraz">
          ${p.obrazy.length
            ? `<img src="${esc(p.obrazy[0].src)}" width="${p.obrazy[0].szerokosc}"
                 height="${p.obrazy[0].wysokosc}" loading="lazy" alt="">`
            : '<span aria-hidden="true">📦</span>'}
        </div>
        <div class="produkt-wiersz-dane">
          <strong>${esc(p.nazwa)}</strong>
          <span class="produkt-wiersz-meta">
            ${esc(p.kategoria)} · ${zl(p.cena_promo_gr != null ? p.cena_promo_gr : p.cena_gr)}
            · ${p.stan === null ? 'na zamówienie' : p.stan + ' szt.'}
          </span>
        </div>
        <span class="plakietka-status stan-${esc(p.status)}">${esc(p.status)}</span>
        ${p.allegro_url ? `<a href="${esc(p.allegro_url)}" target="_blank" rel="noopener" class="plakietka-status" style="background:#ff5a00; color:#fff; text-decoration:none; padding:3px 8px; border-radius:4px; font-weight:600;" title="Otwórz ofertę na Allegro">🟠 Allegro ↗</a>` : ''}
        <div class="produkt-wiersz-akcje">
          <button type="button" class="btn btn-outline" data-edytuj="${p.id}">Edytuj</button>
          <select data-status="${p.id}" aria-label="Zmień status produktu ${esc(p.nazwa)}">
            ${Object.keys(STATUSY).map(s =>
              `<option value="${s}"${s === p.status ? ' selected' : ''}>${s}</option>`).join('')}
          </select>
          <button type="button" class="btn btn-outline usun" data-usun="${p.id}">Usuń</button>
        </div>
      </li>`).join('')
      : '<li class="pusto">Nie ma jeszcze żadnych produktów. Zacznij od „Dodaj produkt".</li>';
  }

  $('#produkty-spis').addEventListener('click', async e => {
    const btn = e.target.closest('button');
    if (!btn) return;

    if (btn.dataset.edytuj) {
      const p = produkty.find(x => x.id === Number(btn.dataset.edytuj));
      if (p) otworzKreator(p);
      return;
    }
    if (btn.dataset.usun) {
      const p = produkty.find(x => x.id === Number(btn.dataset.usun));
      if (!p) return;
      // Kasowanie usuwa takze pliki zdjec — nie ma cofniecia, wiec pytamy
      // o nazwe, a nie o zwykle „czy na pewno".
      if (prompt('Usunięcie produktu i jego zdjęć jest nieodwracalne.\n'
        + 'Wpisz nazwę produktu, żeby potwierdzić:') !== p.nazwa) {
        return;
      }
      try {
        await api('/sklep.php?akcja=produkt-usun', { metoda: 'POST', dane: { id: p.id } });
        await wczytajProdukty();
      } catch (err) {
        alert(err.message);
      }
    }
  });

  $('#produkty-spis').addEventListener('change', async e => {
    const sel = e.target.closest('select[data-status]');
    if (!sel) return;
    try {
      await api('/sklep.php?akcja=produkt-status', {
        metoda: 'POST', dane: { id: Number(sel.dataset.status), status: sel.value }
      });
      await wczytajProdukty();
    } catch (err) {
      alert(err.message);
    }
  });

  // ----------------------------------------------------------- formularz
  const kreator = $('#produkt-kreator');
  const info = $('#kreator-komunikat');

  function pokazKrok(n) {
    krok = n;
    $$('.kreator-krok', kreator).forEach(el => {
      el.hidden = Number(el.dataset.krok) !== n;
    });
    $$('.kreator-kroki li', kreator).forEach(li => {
      const numer = Number(li.dataset.krok);
      li.classList.toggle('aktywny', numer === n);
      li.classList.toggle('zrobiony', numer < n);
    });
    // Zdjecia dopiero po zapisaniu — bez identyfikatora nie ma do czego
    // przypisac pliku.
    $('#kreator-zdjecia-brama').hidden = edytowany !== null;
    $('#kreator-zdjecia-panel').hidden = edytowany === null;
  }

  function otworzKreator(produkt) {
    edytowany = produkt || null;
    kreator.hidden = false;
    $('#kreator-tytul').textContent = produkt ? 'Edytujesz: ' + produkt.nazwa : 'Nowy produkt';

    const p = produkt || {};
    $('#pr-nazwa').value = p.nazwa || '';
    $('#pr-slug').value = p.slug || '';
    $('#pr-kategoria').value = p.kategoria || 'inne';
    $('#pr-opis-krotki').value = p.opis_krotki || '';
    $('#pr-opis').value = p.opis || '';
    $('#pr-cena').value = p.cena_gr ? (p.cena_gr / 100).toFixed(2).replace('.', ',') : '';
    $('#pr-cena-promo').value = p.cena_promo_gr ? (p.cena_promo_gr / 100).toFixed(2).replace('.', ',') : '';
    $('#pr-stan').value = p.stan === null || p.stan === undefined ? '' : p.stan;
    $('#pr-waga').value = p.waga_g || '';
    $('#pr-jednostka').value = p.jednostka || 'szt.';
    $('#pr-czas').value = p.czas_realizacji || '';
    $('#pr-pozycja').value = p.pozycja || 100;
    $('#pr-status').value = p.status || 'szkic';

    // Allegro
    $('#pr-allegro-url').value = p.allegro_url || '';
    $('#pr-allegro-cena').value = p.allegro_cena_gr ? (p.allegro_cena_gr / 100).toFixed(2).replace('.', ',') : '';
    $('#pr-allegro-id').value = p.allegro_id || '';
    $('#pr-allegro-status').value = p.allegro_status || 'brak';
    // Zapamietujemy wczytane url/id, zeby przy zapisie odroznic "admin recznie
    // podlaczyl/zmienil aukcje" od "pola po prostu wroty z serwera niezmienione"
    // — allegro_id/url sa wlasnoscia serwera (kontrakt 1), z wyjatkiem tej
    // swiadomej reki admina.
    zaladowanyAllegroUrl = p.allegro_url || '';
    zaladowanyAllegroId = p.allegro_id || '';

    rysujZdjecia();
    pokazKrok(1);
    kreator.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  $('#produkt-dodaj').addEventListener('click', () => otworzKreator(null));
  $('#kreator-zamknij').addEventListener('click', () => { kreator.hidden = true; });

  const importPanel = $('#allegro-import-panel');
  const btnOtworzImport = $('#allegro-import-otworz');
  const btnWykonajImport = $('#allegro-import-wykonaj');
  const btnAnulujImport = $('#allegro-import-anuluj');
  const inputImportUrl = $('#allegro-import-url');
  const infoImport = $('#allegro-import-komunikat');

  if (btnOtworzImport && importPanel) {
    btnOtworzImport.addEventListener('click', () => {
      importPanel.style.display = importPanel.style.display === 'none' ? 'block' : 'none';
      if (importPanel.style.display === 'block') inputImportUrl.focus();
    });
    if (btnAnulujImport) {
      btnAnulujImport.addEventListener('click', () => {
        importPanel.style.display = 'none';
        infoImport.textContent = '';
      });
    }
    if (btnWykonajImport) {
      btnWykonajImport.addEventListener('click', async () => {
        const url = inputImportUrl.value.trim();
        if (!url || !url.startsWith('http')) {
          komunikat(infoImport, 'Podaj prawidłowy link do aukcji Allegro (https://allegro.pl/oferta/...)', 'blad');
          return;
        }
        btnWykonajImport.disabled = true;
        btnWykonajImport.textContent = 'Pobieranie danych...';
        komunikat(infoImport, 'Pobieranie i standaryzacja danych z aukcji Allegro...', 'info');

        try {
          const r = await api('/sklep.php?akcja=allegro-import-z-linku', {
            metoda: 'POST',
            dane: { url }
          });
          komunikat(infoImport, '✅ Zaimportowano! Produkt: ' + (r.url || r.id), 'ok');
          inputImportUrl.value = '';
          await wczytajProdukty();
          setTimeout(() => {
            importPanel.style.display = 'none';
            infoImport.textContent = '';
          }, 2500);
        } catch (err) {
          komunikat(infoImport, 'Błąd: ' + err.message, 'blad');
        } finally {
          btnWykonajImport.disabled = false;
          btnWykonajImport.textContent = 'Pobierz i opublikuj';
        }
      });
    }
  }

  $$('.kreator-dalej', kreator).forEach(b =>
    b.addEventListener('click', () => pokazKrok(Math.min(4, krok + 1))));
  $$('.kreator-wstecz', kreator).forEach(b =>
    b.addEventListener('click', () => pokazKrok(Math.max(1, krok - 1))));

  $('#produkt-form').addEventListener('submit', async e => {
    e.preventDefault();
    const dane = {
      id: edytowany ? edytowany.id : 0,
      nazwa: $('#pr-nazwa').value,
      slug: $('#pr-slug').value,
      kategoria: $('#pr-kategoria').value,
      opis_krotki: $('#pr-opis-krotki').value,
      opis: $('#pr-opis').value,
      cena: $('#pr-cena').value,
      cena_promo: $('#pr-cena-promo').value,
      stan: $('#pr-stan').value,
      waga_g: $('#pr-waga').value,
      jednostka: $('#pr-jednostka').value,
      czas_realizacji: $('#pr-czas').value,
      pozycja: $('#pr-pozycja').value,
      status: $('#pr-status').value,
      allegro_url: $('#pr-allegro-url').value,
      allegro_cena: $('#pr-allegro-cena').value,
      allegro_id: $('#pr-allegro-id').value,
      allegro_status: $('#pr-allegro-status').value
    };
    // Admin recznie zmienil url/id aukcji wzgledem tego, co bylo wczytane —
    // to jedyny sygnal dla serwera, ze wolno nadpisac pola nalezace do serwera
    // (kontrakt 1); apka telefonu tych pol nie edytuje, wiec flagi nigdy nie wysyla.
    if (dane.allegro_url.trim() !== zaladowanyAllegroUrl || dane.allegro_id.trim() !== zaladowanyAllegroId) {
      dane.allegro_reczne_polaczenie = 1;
    }
    try {
      const r = await api('/sklep.php?akcja=produkt-zapisz', { metoda: 'POST', dane });
      komunikat(info, 'Zapisano. Adres produktu: ' + r.url, 'ok');
      await wczytajProdukty();
      // Po pierwszym zapisie produkt ma juz identyfikator — od tej chwili
      // mozna wgrywac zdjecia bez zamykania kreatora.
      edytowany = produkty.find(x => x.id === r.id) || null;
      rysujZdjecia();
      pokazKrok(krok);
    } catch (err) {
      komunikat(info, err.message, 'blad');
    }
  });

  // ------------------------------------------------------------ zdjęcia
  function rysujZdjecia() {
    const kontener = $('#kreator-zdjecia');
    if (!edytowany) {
      kontener.innerHTML = '';
      return;
    }
    kontener.innerHTML = edytowany.obrazy.length
      ? edytowany.obrazy.map(o => `
        <figure class="zdjecie-kafel">
          <img src="${esc(o.src)}" width="${o.szerokosc}" height="${o.wysokosc}" alt="${esc(o.alt)}">
          <button type="button" class="btn btn-outline" data-usun-obraz="${o.id}">Usuń</button>
        </figure>`).join('')
      : '<p class="pusto">Brak zdjęć. Dodaj przynajmniej jedno — produkt bez zdjęcia sprzedaje się źle.</p>';
  }

  $('#kreator-zdjecia').addEventListener('click', async e => {
    const btn = e.target.closest('[data-usun-obraz]');
    if (!btn || !confirm('Usunąć to zdjęcie?')) return;
    try {
      await api('/sklep.php?akcja=obraz-usun', {
        metoda: 'POST', dane: { id: Number(btn.dataset.usunObraz) }
      });
      await wczytajProdukty();
      edytowany = produkty.find(x => x.id === edytowany.id) || null;
      rysujZdjecia();
    } catch (err) {
      alert(err.message);
    }
  });

  $('#zdjecie-plik').addEventListener('change', async e => {
    const plik = e.target.files && e.target.files[0];
    if (!plik || !edytowany) return;

    const dane = new FormData();
    dane.append('plik', plik);
    dane.append('produkt_id', String(edytowany.id));
    dane.append('alt', $('#zdjecie-alt').value || edytowany.nazwa);

    komunikat($('#zdjecie-komunikat'), 'Wysyłanie zdjęcia...', 'info');
    try {
      // FormData wysylamy bez naglowka Content-Type — przegladarka sama
      // dopisze granice bloku multipart.
      const naglowki = {};
      const m = document.cookie.match(/(?:^|; )fw_csrf=([^;]*)/);
      if (m) naglowki['X-FW-CSRF'] = decodeURIComponent(m[1]);

      const odp = await fetch('/api/sklep.php?akcja=obraz-wgraj', {
        method: 'POST', headers: naglowki, credentials: 'same-origin', body: dane
      });
      const wynik = await odp.json();
      if (!odp.ok || wynik.ok === false) throw new Error(wynik.blad || 'Nie udało się wgrać zdjęcia.');

      komunikat($('#zdjecie-komunikat'), 'Zdjęcie dodane.', 'ok');
      $('#zdjecie-plik').value = '';
      $('#zdjecie-alt').value = '';
      await wczytajProdukty();
      edytowany = produkty.find(x => x.id === edytowany.id) || null;
      rysujZdjecia();
      rysujPliki();
    } catch (err) {
      komunikat($('#zdjecie-komunikat'), err.message, 'blad');
    }
  });

  // ---------------------------------------------- wideo, modele 3D, szkice
  //
  // Osobna sciezka niz zdjecia: te pliki nie maja szerokosci ani wysokosci,
  // za to maja rodzaj, ktory decyduje o tym, jak pokaze je strona produktu.

  function rysujPliki() {
    const kafle = $('#kreator-pliki');
    if (!kafle) return;
    const pliki = (edytowany && edytowany.pliki) || [];
    kafle.innerHTML = pliki.length ? pliki.map(f => `
      <div class="zdjecie-kafel">
        <span>${f.rodzaj === 'wideo' ? '🎬' : f.rodzaj === 'model' ? '🧩' : '📄'}
          ${f.src.split('/').pop()}</span>
        <button type="button" class="btn btn-mini" data-plik="${f.id}">Usuń</button>
      </div>`).join('') : '<p class="pusto">Brak plików dodatkowych.</p>';

    kafle.querySelectorAll('[data-plik]').forEach(b => {
      b.addEventListener('click', async () => {
        try {
          await api('/sklep.php?akcja=plik-usun', { metoda: 'POST', dane: { id: b.dataset.plik } });
          await wczytajProdukty();
          edytowany = produkty.find(x => x.id === edytowany.id) || null;
          rysujPliki();
        } catch (err) {
          komunikat($('#plik-komunikat'), err.message, 'blad');
        }
      });
    });
  }

  const polePliku = $('#produkt-plik');
  if (polePliku) polePliku.addEventListener('change', async e => {
    const plik = e.target.files && e.target.files[0];
    if (!plik || !edytowany) return;

    const dane = new FormData();
    dane.append('plik', plik);
    dane.append('produkt_id', String(edytowany.id));
    dane.append('opis', $('#plik-opis').value || '');

    // Film potrafi wazyc 60 MB — bez tej informacji wyglada to na zawieszenie.
    komunikat($('#plik-komunikat'),
      `Wysyłanie (${Math.max(1, Math.round(plik.size / 1048576))} MB)...`, 'info');
    try {
      const naglowki = {};
      const m = document.cookie.match(/(?:^|; )fw_csrf=([^;]*)/);
      if (m) naglowki['X-FW-CSRF'] = decodeURIComponent(m[1]);

      const odp = await fetch('/api/sklep.php?akcja=plik-wgraj', {
        method: 'POST', headers: naglowki, credentials: 'same-origin', body: dane
      });
      const wynik = await odp.json();
      if (!odp.ok || wynik.ok === false) throw new Error(wynik.blad || 'Nie udało się wgrać pliku.');

      komunikat($('#plik-komunikat'), 'Plik dodany.', 'ok');
      polePliku.value = '';
      $('#plik-opis').value = '';
      await wczytajProdukty();
      edytowany = produkty.find(x => x.id === edytowany.id) || null;
      rysujPliki();
    } catch (err) {
      komunikat($('#plik-komunikat'), err.message, 'blad');
    }
  });

  // --------------------------------------------------------- zamówienia
  async function wczytajZamowienia() {
    const spis = $('#zamowienia-spis');
    if (!spis) return;
    try {
      const r = await api('/sklep.php?akcja=admin-zamowienia');
      spis.innerHTML = r.zamowienia.length ? r.zamowienia.map(z => `
        <li class="zamowienie-karta">
          <div class="zamowienie-glowa">
            <strong>${esc(z.numer)}</strong>
            <span>${esc(z.nick)} · ${esc(z.email)}</span>
            <span>${esc(String(z.utworzone).slice(0, 16).replace('T', ' '))}</span>
          </div>
          <ul class="zamowienie-pozycje">${z.pozycje.map(p =>
            `<li>${esc(p.nazwa)} × ${p.ilosc} — ${zl(p.cena_gr * p.ilosc)}</li>`).join('')}</ul>
          <p class="zamowienie-adres">${esc([z.adres.imie, z.adres.nazwisko, z.adres.ulica,
            z.adres.nr_domu, z.adres.kod, z.adres.miasto, z.adres.telefon]
            .filter(Boolean).join(', ')) || 'Odbiór osobisty'}</p>
          <p class="zamowienie-kwota">Razem: <strong>${zl(z.suma_gr)}</strong>
            · ${esc(z.sposob_platnosci)} · ${esc(z.sposob_dostawy)}</p>
          <label>Status:
            <select data-zamowienie="${z.id}">
              ${['nowe', 'oplacone', 'w_realizacji', 'wyslane', 'zakonczone', 'anulowane'].map(s =>
                `<option value="${s}"${s === z.status ? ' selected' : ''}>${s}</option>`).join('')}
            </select>
          </label>
        </li>`).join('')
        : '<li class="pusto">Brak zamówień.</li>';
    } catch (e) {
      spis.innerHTML = '<li class="pusto">' + esc(e.message) + '</li>';
    }
  }

  const spisZamowien = $('#zamowienia-spis');
  if (spisZamowien) {
    spisZamowien.addEventListener('change', async e => {
      const sel = e.target.closest('select[data-zamowienie]');
      if (!sel) return;
      try {
        await api('/sklep.php?akcja=zamowienie-status', {
          metoda: 'POST', dane: { id: Number(sel.dataset.zamowienie), status: sel.value }
        });
      } catch (err) {
        alert(err.message);
      }
    });
  }

  // /admin/?edytuj=12 — link „Edytuj" z paska admina na karcie produktu.
  const doEdycji = Number(new URLSearchParams(location.search).get('edytuj'));
  wczytajProdukty().then(() => {
    const p = doEdycji && produkty.find(x => x.id === doEdycji);
    if (p) {
      otworzKreator(p);
      kreator.scrollIntoView({ behavior: 'smooth' });
    }
  });
  wczytajZamowienia();
})();
