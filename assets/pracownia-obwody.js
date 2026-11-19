// Gotowe układy płytki stykowej dla prób, w których temat to obwód (E01, E02, E04, E10).
// Ustawia istniejący symulator z pracownia.js; link z opisu filmu: /pracownia/?obwod=e04#obwody
(() => {
  'use strict';
  const board = document.querySelector('[data-obwody]');
  if (!board) return;
  const $ = (id) => board.querySelector('#' + id);
  const Z = 'zarowka', L = 'led', P = 'puste';

  const PRESETY = {
    e01: { proba: null, uklad: 'pojedynczy', el: [[L, 470]], bateria: false,
      tekst: 'Przełącznik jest otwarty. Zgadnij, co zrobi LED, gdy włączysz baterię.' },
    e02: { proba: 'proba-e02', uklad: 'pojedynczy', el: [[L, 470]], bateria: true,
      tekst: 'Zapisz prąd przy 470 Ω. Potem zmień rezystor na 1000 Ω i porównaj odczyt.' },
    e04: { proba: 'proba-e04', uklad: 'szereg', el: [[Z], [P], [Z]], bateria: true,
      tekst: 'Szereg z przerwą w miejscu 2. Przełącz połączenie na równoległe i sprawdź, co zrobią żarówki 1 i 3.' },
    e04r: { proba: null, uklad: 'rownolegle', el: [[Z], [P], [Z]], bateria: true,
      tekst: 'Równolegle: gałąź 2 jest przerwana. Które żarówki dalej mają swoją drogę do baterii?' },
    e10: { proba: 'proba-e10', zagadka: true,
      tekst: 'Jedna LED zgubiła światło. Znajdź usterkę i napraw ją jednym ruchem.' },
  };

  // Zagadka E10: trzy LED równolegle, jedna usterka losowo: pusta gałąź albo wyłączona bateria.
  function zagadka() {
    const el = [[L, 470], [L, 470], [L, 470]];
    const k = Math.floor(Math.random() * 4);
    if (k < 3) el[k] = [P];
    return { uklad: 'rownolegle', el, bateria: k !== 3 };
  }

  function ustaw(nazwa) {
    const p = PRESETY[nazwa];
    if (!p) return false;
    const u = p.zagadka ? zagadka() : p;
    $('lab-uklad').value = u.uklad;
    [1, 2, 3].forEach((n) => {
      const [typ, opor] = u.el[n - 1] || [Z];
      $('lab-element-' + n).value = typ;
      $('lab-opor-' + n).value = String(opor || 470);
    });
    $('lab-bateria').setAttribute('aria-pressed', String(u.bateria));
    $('lab-uklad').dispatchEvent(new Event('change')); // render() z pracownia.js
    $('lab-wyzwanie').textContent = p.tekst;
    return true;
  }

  function pokaz(nazwa) {
    if (!ustaw(nazwa)) return;
    board.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
    $('lab-uklad').focus({ preventScroll: true });
  }

  Object.entries(PRESETY).forEach(([nazwa, p]) => {
    const panel = p.proba && document.querySelector('#' + p.proba + ' [data-proba]');
    if (!panel) return;
    const akapit = document.createElement('p');
    akapit.className = 'kurs-linki';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-outline';
    btn.textContent = 'Ustaw ten układ na płytce';
    btn.addEventListener('click', () => pokaz(nazwa));
    akapit.append(btn);
    panel.append(akapit);
  });

  const zAdresu = new URLSearchParams(location.search).get('obwod');
  if (zAdresu) requestAnimationFrame(() => pokaz(zAdresu.toLowerCase()));
})();
