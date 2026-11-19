/* ============================================================================
   Sklep fwdrucik.pl — koszyk, kasa i galeria produktu
   ----------------------------------------------------------------------------
   Koszyk żyje w localStorage przeglądarki: trzyma wyłącznie identyfikatory
   i ilości. Ceny i dostępność liczy serwer przy składaniu zamówienia — koszyk
   po stronie klienta jest wygodą, nie źródłem prawdy o kwocie do zapłaty.
   ========================================================================== */
(function () {
  'use strict';

  const KLUCZ_KOSZYKA = 'fw-koszyk-v1';

  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));

  function esc(t) {
    return String(t == null ? '' : t).replace(/[&<>"']/g, c => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  }

  const zl = gr => (gr / 100).toLocaleString('pl-PL', {
    minimumFractionDigits: 2, maximumFractionDigits: 2
  }) + ' zł';

  function ciasteczko(nazwa) {
    const m = document.cookie.match(new RegExp('(?:^|; )' + nazwa + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }

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
  }

  // ================================================================ koszyk
  function wczytajKoszyk() {
    try {
      const dane = JSON.parse(localStorage.getItem(KLUCZ_KOSZYKA) || '[]');
      return Array.isArray(dane) ? dane.filter(p => p && p.id) : [];
    } catch (e) {
      // Uszkodzony wpis w localStorage nie ma prawa wywalic calej strony.
      return [];
    }
  }

  function zapiszKoszyk(koszyk) {
    try {
      localStorage.setItem(KLUCZ_KOSZYKA, JSON.stringify(koszyk));
    } catch (e) { /* tryb prywatny albo brak miejsca — koszyk zyje do przeladowania */ }
    odswiezLicznik();
    document.dispatchEvent(new CustomEvent('fw-koszyk-zmiana'));
  }

  function dodajDoKoszyka(id, nazwa, cenaGr, ilosc) {
    const koszyk = wczytajKoszyk();
    const istnieje = koszyk.find(p => p.id === id);
    if (istnieje) {
      istnieje.ilosc = Math.min(99, istnieje.ilosc + ilosc);
    } else {
      koszyk.push({ id, nazwa, cena_gr: cenaGr, ilosc });
    }
    zapiszKoszyk(koszyk);
  }

  function odswiezLicznik() {
    const sztuk = wczytajKoszyk().reduce((s, p) => s + p.ilosc, 0);
    $$('[data-koszyk-licznik]').forEach(el => {
      el.textContent = sztuk;
      el.hidden = sztuk === 0;
    });
  }

  function pokazPotwierdzenie(nazwa) {
    let toast = $('#koszyk-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'koszyk-toast';
      toast.className = 'koszyk-toast';
      toast.setAttribute('role', 'status');
      document.body.appendChild(toast);
    }
    toast.innerHTML = `<strong>Dodano do koszyka</strong><span>${esc(nazwa)}</span>`
      + '<a class="btn btn-primary" href="/koszyk/">Przejdź do koszyka</a>';
    toast.classList.add('widoczny');
    clearTimeout(toast._licznik);
    toast._licznik = setTimeout(() => toast.classList.remove('widoczny'), 6000);
  }

  // przyciski „dodaj do koszyka" na liście i na karcie produktu
  document.addEventListener('click', e => {
    const btn = e.target.closest('.do-koszyka');
    if (!btn || btn.disabled) return;

    if (btn.dataset.allegroUrl) {
      window.open(btn.dataset.allegroUrl, '_blank', 'noopener,noreferrer');
      return;
    }

    const poleIlosci = btn.dataset.iloscZ ? $('#' + btn.dataset.iloscZ) : null;
    const ilosc = Math.max(1, Math.min(99, parseInt(poleIlosci ? poleIlosci.value : '1', 10) || 1));
    dodajDoKoszyka(Number(btn.dataset.id), btn.dataset.nazwa, Number(btn.dataset.cena), ilosc);
    pokazPotwierdzenie(btn.dataset.nazwa);
  });

  // ====================================================== galeria produktu
  function ustawGalerie() {
    const miniatury = $$('.miniatura');
    if (!miniatury.length) return;
    const glowny = $('#produkt-glowny');
    if (!glowny) return;
    miniatury.forEach(m => m.addEventListener('click', () => {
      glowny.src = m.dataset.src;
      miniatury.forEach(x => x.classList.toggle('aktywna', x === m));
    }));
  }

  // ========================================================= strona koszyka
  function ustawStroneKoszyka() {
    const lista = $('#koszyk-lista');
    if (!lista) return;
    const podsumowanie = $('#koszyk-podsumowanie');

    function rysuj() {
      const koszyk = wczytajKoszyk();
      if (!koszyk.length) {
        lista.innerHTML = '<li class="pusto">Koszyk jest pusty. '
          + '<a href="/sklep/">Wróć do sklepu</a>.</li>';
        podsumowanie.hidden = true;
        return;
      }
      podsumowanie.hidden = false;
      lista.innerHTML = koszyk.map(p => `
        <li class="koszyk-pozycja">
          <div class="koszyk-opis">
            <strong>${esc(p.nazwa)}</strong>
            <span>${zl(p.cena_gr)} / szt.</span>
          </div>
          <div class="koszyk-ilosc">
            <button type="button" class="btn btn-outline" data-mniej="${p.id}" aria-label="Zmniejsz ilość">−</button>
            <span>${p.ilosc}</span>
            <button type="button" class="btn btn-outline" data-wiecej="${p.id}" aria-label="Zwiększ ilość">+</button>
          </div>
          <div class="koszyk-kwota">${zl(p.cena_gr * p.ilosc)}</div>
          <button type="button" class="koszyk-usun" data-usun="${p.id}" aria-label="Usuń z koszyka">✕</button>
        </li>`).join('');

      const suma = koszyk.reduce((s, p) => s + p.cena_gr * p.ilosc, 0);
      $('#koszyk-suma').textContent = zl(suma);
    }

    lista.addEventListener('click', e => {
      const koszyk = wczytajKoszyk();
      const btn = e.target.closest('button');
      if (!btn) return;
      const id = Number(btn.dataset.mniej || btn.dataset.wiecej || btn.dataset.usun);
      const poz = koszyk.find(p => p.id === id);
      if (!poz) return;

      if (btn.dataset.usun !== undefined) {
        zapiszKoszyk(koszyk.filter(p => p.id !== id));
      } else {
        poz.ilosc += btn.dataset.wiecej !== undefined ? 1 : -1;
        zapiszKoszyk(poz.ilosc < 1 ? koszyk.filter(p => p.id !== id) : koszyk);
      }
      rysuj();
    });

    document.addEventListener('fw-koszyk-zmiana', rysuj);
    rysuj();
  }

  // ======================================================= strona zamówienia
  function ustawStroneZamowienia() {
    const form = $('#zamowienie-form');
    if (!form) return;
    const info = $('#zamowienie-komunikat');
    const spis = $('#zamowienie-spis');
    let ustawienia = { dostawa: {}, platnosci: {} };

    async function wczytajUstawienia() {
      try {
        const r = await api('/sklep.php?akcja=ustawienia');
        ustawienia = r;
      } catch (e) { /* zostaja wartosci domyslne z HTML */ }

      const wyborDostawy = $('#zam-dostawa');
      wyborDostawy.innerHTML = Object.entries(ustawienia.dostawa).map(([k, v]) =>
        `<option value="${esc(k)}" data-cena="${v.cena_gr}">${esc(v.nazwa)}`
        + (v.cena_gr ? ' — ' + zl(v.cena_gr) : ' — bezpłatnie') + '</option>').join('');

      const wyborPlatnosci = $('#zam-platnosc');
      wyborPlatnosci.innerHTML = Object.entries(ustawienia.platnosci).map(([k, v]) =>
        `<option value="${esc(k)}">${esc(v)}</option>`).join('');

      przelicz();
    }

    function przelicz() {
      const koszyk = wczytajKoszyk();
      if (!koszyk.length) {
        spis.innerHTML = '<li class="pusto">Koszyk jest pusty. <a href="/sklep/">Wróć do sklepu</a>.</li>';
        form.querySelector('button[type="submit"]').disabled = true;
        return;
      }
      form.querySelector('button[type="submit"]').disabled = false;

      const towar = koszyk.reduce((s, p) => s + p.cena_gr * p.ilosc, 0);
      const wybrana = $('#zam-dostawa').selectedOptions[0];
      const dostawa = wybrana ? Number(wybrana.dataset.cena || 0) : 0;

      spis.innerHTML = koszyk.map(p =>
        `<li><span>${esc(p.nazwa)} × ${p.ilosc}</span><span>${zl(p.cena_gr * p.ilosc)}</span></li>`
      ).join('')
        + `<li class="suma-czesciowa"><span>Dostawa</span><span>${zl(dostawa)}</span></li>`
        + `<li class="suma-calkowita"><span>Razem</span><span>${zl(towar + dostawa)}</span></li>`;
    }

    $('#zam-dostawa').addEventListener('change', przelicz);
    document.addEventListener('fw-koszyk-zmiana', przelicz);

    form.addEventListener('submit', async e => {
      e.preventDefault();
      const przycisk = form.querySelector('button[type="submit"]');
      przycisk.disabled = true;
      komunikat(info, 'Wysyłanie zamówienia...', 'info');
      try {
        // Zgoda leci na serwer jawnie. Sam atrybut `required` na haczyku
        // pilnuje tylko tej przegladarki — sklep musi ja u siebie sprawdzic
        // i zapisac przy zamowieniu, bo to on odpowiada za dowod.
        const dane = {
          koszyk: wczytajKoszyk().map(p => ({ id: p.id, ilosc: p.ilosc })),
          dostawa: $('#zam-dostawa').value,
          platnosc: $('#zam-platnosc').value,
          uwagi: $('#zam-uwagi').value,
          zgoda: $('#zam-regulamin') ? $('#zam-regulamin').checked : false
        };

        // Gosc dopisuje dane kontaktowe z formularza. Zalogowany ich nie ma
        // w tym miejscu i nie powinien — jego adres siedzi w koncie.
        ['email', 'imie', 'nazwisko', 'telefon', 'ulica', 'kod', 'miasto', 'firma', 'nip']
          .forEach(pole => {
            const el = $('#zam-' + pole);
            if (el) dane[pole] = el.value.trim();
          });

        const r = await api('/sklep.php?akcja=zamow', { metoda: 'POST', dane });
        zapiszKoszyk([]);
        $('#zamowienie-wynik').hidden = false;
        $('#zamowienie-wynik').innerHTML =
          `<h2>Zamówienie ${esc(r.numer)} przyjęte</h2><p>${esc(r.komunikat)}</p>`
          + `<p class="zamowienie-kwota">Do zapłaty: <strong>${zl(r.suma_gr)}</strong></p>`
          + '<p><a class="btn btn-outline" href="/konto/#zamowienia">Moje zamówienia</a></p>';
        form.hidden = true;
      } catch (err) {
        komunikat(info, err.message, 'blad');
        przycisk.disabled = false;
      }
    });

    wczytajUstawienia();
  }

  // ============================================================ dane do wysyłki
  function ustawProfil() {
    const form = $('#profil-form');
    if (!form) return;
    const info = $('#profil-komunikat');
    const pola = ['imie', 'nazwisko', 'telefon', 'ulica', 'nr_domu', 'nr_lokalu',
      'kod', 'miasto', 'firma', 'nip'];

    (async () => {
      try {
        const r = await api('/sklep.php?akcja=profil');
        pola.forEach(p => {
          const el = $('#profil-' + p);
          if (el && r.adres && r.adres[p] !== undefined) el.value = r.adres[p];
        });
      } catch (e) { /* niezalogowany — blok i tak jest ukryty */ }
    })();

    form.addEventListener('submit', async e => {
      e.preventDefault();
      const dane = {};
      pola.forEach(p => { dane[p] = ($('#profil-' + p) || {}).value || ''; });
      try {
        await api('/sklep.php?akcja=profil-zapisz', { metoda: 'POST', dane });
        komunikat(info, 'Dane zapisane.', 'ok');
      } catch (err) {
        komunikat(info, err.message, 'blad');
      }
    });
  }

  // ============================================================ moje zamówienia
  function ustawMojeZamowienia() {
    const lista = $('#moje-zamowienia');
    if (!lista) return;
    const OPISY = {
      nowe: 'Przyjęte', oplacone: 'Opłacone', w_realizacji: 'W realizacji',
      wyslane: 'Wysłane', zakonczone: 'Zakończone', anulowane: 'Anulowane'
    };
    (async () => {
      try {
        const r = await api('/sklep.php?akcja=moje-zamowienia');
        lista.innerHTML = r.zamowienia.length
          ? r.zamowienia.map(z => `
            <li class="zamowienie-karta">
              <div class="zamowienie-glowa">
                <strong>${esc(z.numer)}</strong>
                <span class="badge badge-blue">${esc(OPISY[z.status] || z.status)}</span>
                <span>${esc(String(z.utworzone).slice(0, 16).replace('T', ' '))}</span>
              </div>
              <ul class="zamowienie-pozycje">${z.pozycje.map(p =>
                `<li>${esc(p.nazwa)} × ${p.ilosc} — ${zl(p.cena_gr * p.ilosc)}</li>`).join('')}</ul>
              <p class="zamowienie-kwota">Razem: <strong>${zl(z.suma_gr)}</strong></p>
            </li>`).join('')
          : '<li class="pusto">Nie masz jeszcze żadnych zamówień.</li>';
      } catch (e) {
        if (e.kod !== 401) lista.innerHTML = '<li class="pusto">' + esc(e.message) + '</li>';
      }
    })();
  }

  // ==================================================================== start
  function uruchom() {
    odswiezLicznik();
    ustawGalerie();
    ustawStroneKoszyka();
    ustawStroneZamowienia();
    ustawProfil();
    ustawMojeZamowienia();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', uruchom);
  } else {
    uruchom();
  }

  // Udostepniamy panelowi administratora — tam przydaje sie ta sama warstwa
  // wywolan i to samo formatowanie kwot.
  window.FWSklep = { api, zl, esc, komunikat };
})();
