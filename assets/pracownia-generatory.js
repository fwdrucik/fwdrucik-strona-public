// Generatory kompendium Pracowni: interaktywny model do każdego hasła (E01–E10, A01–A10, D01–D10).
// Każdy generator rysuje SVG, ma przyciski lub suwaki i opis wyniku w aria-live.
// Przy prefers-reduced-motion i html.niebo-stop nie ma ciągłych animacji — wynik zmienia się skokowo.
(() => {
  'use strict';
  const calm = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
    || document.documentElement.classList.contains('niebo-stop');
  const C = { tlo: '#101b2d', karta: '#172841', linia: '#c8d9ee', przyg: '#304967', tyrk: '#68e8d6', zloto: '#ffc775', czerw: '#ff8883', nieb: '#8fb9ff', miedz: '#efa66e' };

  function ramka(el, tytul) {
    el.innerHTML = `<p class="gen-tytul">Model interaktywny: ${tytul}</p><svg viewBox="0 0 320 170" role="img" aria-label="${tytul}"></svg><div class="gen-ster"></div><p class="gen-wynik" aria-live="polite"></p>`;
    return { svg: el.querySelector('svg'), ster: el.querySelector('.gen-ster'), wynik: el.querySelector('.gen-wynik') };
  }
  function przycisk(ster, tekst, fn) {
    const b = document.createElement('button'); b.type = 'button'; b.className = 'btn btn-outline'; b.textContent = tekst;
    b.addEventListener('click', () => fn(b)); ster.append(b); return b;
  }
  function suwak(ster, etykieta, min, max, krok, wartosc, fn) {
    const l = document.createElement('label'); l.className = 'gen-suwak';
    l.innerHTML = `<span>${etykieta}</span><input type="range" min="${min}" max="${max}" step="${krok}" value="${wartosc}"><output></output>`;
    const i = l.querySelector('input'), o = l.querySelector('output');
    const zmien = () => { o.textContent = fn(Number(i.value)); };
    i.addEventListener('input', zmien); ster.append(l); zmien(); return i;
  }
  // obwód: bateria z lewej, elementy na górze, przewód zamknięty dookoła
  const petla = (kolor, kropki) => `<path d="M40 130 V40 H280 V130 Z" fill="none" stroke="${kolor}" stroke-width="4"/>`
    + (kropki && !calm() ? `<path class="gen-prad" d="M40 130 V40 H280 V130 Z" fill="none" stroke="${C.zloto}" stroke-width="4" stroke-dasharray="2 14"/>` : '');
  const bateria = (x = 40, y = 85) => `<rect x="${x - 14}" y="${y - 24}" width="28" height="48" rx="4" fill="${C.karta}" stroke="${C.zloto}" stroke-width="2"/><text x="${x}" y="${y - 6}" class="gen-t" fill="${C.zloto}">+</text><text x="${x}" y="${y + 16}" class="gen-t">−</text>`;
  const rezystor = (x, y, txt) => `<rect x="${x - 22}" y="${y - 8}" width="44" height="16" rx="4" fill="${C.zloto}"/>` + (txt ? `<text x="${x}" y="${y - 14}" class="gen-t gen-m">${txt}</text>` : '');
  const led = (x, y, jasnosc, kolor = C.tyrk) => `<circle cx="${x}" cy="${y}" r="${10 + 10 * jasnosc}" fill="${kolor}" opacity="${0.25 * jasnosc}"/><circle cx="${x}" cy="${y}" r="10" fill="${jasnosc > 0.02 ? kolor : C.przyg}" stroke="${C.linia}" stroke-width="2" opacity="${0.35 + 0.65 * Math.min(1, jasnosc + 0.0001)}"/>`;
  const lacznik = (x, y, zamk) => `<circle cx="${x - 16}" cy="${y}" r="4" fill="${C.linia}"/><circle cx="${x + 16}" cy="${y}" r="4" fill="${C.linia}"/><line x1="${x - 16}" y1="${y}" x2="${x + 16}" y2="${zamk ? y : y - 16}" stroke="${C.linia}" stroke-width="4" stroke-linecap="round"/>`;

  const G = {
    E01(el) {
      const r = ramka(el, 'zamknięty obwód'); let z = false;
      const rys = () => {
        r.svg.innerHTML = petla(z ? C.tyrk : C.linia, z) + `<rect x="120" y="32" width="80" height="16" fill="${C.tlo}"/>` + bateria() + rezystor(110, 40) + lacznik(170, 40, z) + `<rect x="226" y="30" width="28" height="20" fill="${C.tlo}"/>` + led(240, 40, z ? 1 : 0);
        r.wynik.textContent = z ? 'Przełącznik zamknięty: prąd ma pełną drogę, dioda świeci.' : 'Przełącznik otwarty: przerwa w obwodzie, dioda nie świeci.';
      };
      przycisk(r.ster, 'Przełącz', () => { z = !z; rys(); }); rys();
    },
    E02(el) {
      const r = ramka(el, 'rezystor i prąd');
      suwak(r.ster, 'Rezystor', 220, 2200, 10, 470, (R) => {
        const mA = (7 / R) * 1000;
        r.svg.innerHTML = petla(C.tyrk) + bateria() + rezystor(130, 40, `${R} Ω`) + led(230, 40, Math.min(1, mA / 20))
          + `<text x="52" y="159" class="gen-t gen-m">prąd</text><rect x="72" y="150" width="${Math.min(210, mA * 6.5)}" height="10" rx="3" fill="${C.zloto}"/>`;
        r.wynik.textContent = `9 V, LED ok. 2 V, rezystor ${R} Ω: prąd ≈ ${mA.toFixed(1)} mA. Większy opór — mniejszy prąd.`;
        return `${R} Ω`;
      });
    },
    E03(el) {
      const r = ramka(el, 'płytka stykowa'); let wyb = null;
      const rys = () => {
        let s = `<rect x="10" y="10" width="300" height="150" rx="8" fill="#e9eef5"/><line x1="10" y1="85" x2="310" y2="85" stroke="#b7c3d3" stroke-width="6"/>`;
        for (let k = 0; k < 12; k++) for (let w = 0; w < 10; w++) {
          const x = 30 + k * 24, y = 22 + w * 13 + (w >= 5 ? 12 : 0), pol = wyb && wyb.k === k && (wyb.w < 5) === (w < 5);
          s += `<rect data-k="${k}" data-w="${w}" x="${x - 5}" y="${y - 5}" width="10" height="10" rx="2" fill="${pol ? C.tyrk : '#3b4a5f'}" style="cursor:pointer"/>`;
        }
        r.svg.innerHTML = s;
        r.wynik.textContent = wyb ? `Otwór w kolumnie ${wyb.k + 1}: połączone jest 5 otworów tej kolumny po tej stronie rowka. Druga połowa jest osobno.` : 'Kliknij dowolny otwór, żeby zobaczyć, z którymi jest połączony pod spodem.';
      };
      r.svg.addEventListener('click', (e) => { const t = e.target.closest('[data-k]'); if (t) { wyb = { k: +t.dataset.k, w: +t.dataset.w }; rys(); } });
      rys();
    },
    E04(el) {
      const r = ramka(el, 'szereg i równolegle'); let row = false, przerwa = false;
      const rys = () => {
        const l1 = przerwa ? 0 : 1, l2 = row ? 1 : (przerwa ? 0 : 1);
        let s = bateria();
        if (!row) s += `<path d="M40 61 V40 H280 V130 H40 V109" fill="none" stroke="${l2 ? C.tyrk : C.linia}" stroke-width="4"/>` + led(130, 40, l1, C.zloto) + led(220, 40, l2, C.zloto);
        else s += `<path d="M40 61 V30 H280 V140 H40 V109 M160 30 V140" fill="none" stroke="${C.tyrk}" stroke-width="4"/><path d="M40 85 H280" stroke="${C.tyrk}" stroke-width="4" fill="none"/>` + led(100, 30, l1, C.zloto) + led(100, 85, l2, C.zloto);
        if (przerwa) s += `<text x="${row ? 70 : 105}" y="${row ? 22 : 30}" class="gen-t" fill="${C.czerw}">✕</text>`;
        r.svg.innerHTML = s;
        r.wynik.textContent = row ? (przerwa ? 'Równolegle: gałąź z przerwą gaśnie, druga żarówka dalej świeci.' : 'Równolegle: każda żarówka ma własną drogę.')
          : (przerwa ? 'Szeregowo: jedna przerwa gasi obie żarówki — jest tylko jedna droga.' : 'Szeregowo: prąd płynie po kolei przez obie żarówki.');
      };
      przycisk(r.ster, 'Szereg / równolegle', () => { row = !row; rys(); });
      przycisk(r.ster, 'Przerwa przy pierwszej', () => { przerwa = !przerwa; rys(); }); rys();
    },
    E05(el) {
      const r = ramka(el, 'kierunek diody'); let prz = true;
      const rys = () => {
        const tri = prz ? 'M145 70 L175 85 L145 100 Z' : 'M175 70 L145 85 L175 100 Z', bar = prz ? 177 : 143;
        r.svg.innerHTML = `<line x1="40" y1="85" x2="280" y2="85" stroke="${C.linia}" stroke-width="4"/>` + bateria(40, 85) + `<path d="${tri}" fill="${prz ? C.tyrk : C.czerw}"/><line x1="${bar}" y1="68" x2="${bar}" y2="102" stroke="${prz ? C.tyrk : C.czerw}" stroke-width="4"/>`
          + led(250, 85, prz ? 1 : 0) + `<text x="${prz ? 140 : 180}" y="125" class="gen-t gen-m">anoda</text><text x="${prz ? 182 : 138}" y="125" class="gen-t gen-m">katoda</text>`;
        r.wynik.textContent = prz ? 'Anoda od strony plusa: kierunek przewodzenia, dioda świeci.' : 'Dioda odwrócona: kierunek zaporowy, dioda nie świeci.';
      };
      przycisk(r.ster, 'Obróć diodę', () => { prz = !prz; rys(); }); rys();
    },
    E06(el) {
      const r = ramka(el, 'przycisk i przełącznik'); let wcis = false, prz = false;
      const rys = () => {
        r.svg.innerHTML = `<text x="80" y="30" class="gen-t">przycisk</text><text x="240" y="30" class="gen-t">przełącznik</text>` + lacznik(80, 90, wcis) + led(80, 140, wcis ? 1 : 0) + lacznik(240, 90, prz) + led(240, 140, prz ? 1 : 0);
        r.wynik.textContent = `Przycisk: ${wcis ? 'wciśnięty — styki zwarte' : 'puszczony — styki rozwarte'}. Przełącznik: ${prz ? 'włączony i zostaje' : 'wyłączony'}.`;
      };
      const b = przycisk(r.ster, 'Trzymaj przycisk', () => {});
      const ustaw = (v) => { wcis = v; rys(); };
      b.addEventListener('pointerdown', () => ustaw(true)); ['pointerup', 'pointerleave', 'pointercancel'].forEach((t) => b.addEventListener(t, () => ustaw(false)));
      b.addEventListener('keydown', (e) => { if (e.key === ' ' || e.key === 'Enter') ustaw(true); }); b.addEventListener('keyup', () => ustaw(false));
      przycisk(r.ster, 'Przestaw przełącznik', () => { prz = !prz; rys(); }); rys();
    },
    E07(el) {
      const r = ramka(el, 'pomiar między dwoma punktami'); let zam = false;
      const rys = () => {
        const v = zam ? -9 : 9, kat = v > 0 ? 40 : -40;
        r.svg.innerHTML = bateria(60, 85) + `<rect x="170" y="30" width="120" height="110" rx="12" fill="${C.karta}" stroke="${C.linia}" stroke-width="2"/><text x="230" y="70" class="gen-t gen-duzy" fill="${C.tyrk}">${v > 0 ? '+' : '−'}9,0 V</text>`
          + `<line x1="230" y1="125" x2="${230 + 30 * Math.sin(kat * Math.PI / 180)}" y2="${125 - 30 * Math.cos(kat * Math.PI / 180)}" stroke="${C.zloto}" stroke-width="3"/>`
          + `<path d="M60 61 C110 20 150 40 195 140" fill="none" stroke="${zam ? '#222' : C.czerw}" stroke-width="3"/><path d="M60 109 C110 150 150 150 265 140" fill="none" stroke="${zam ? C.czerw : '#222'}" stroke-width="3"/>`;
        r.wynik.textContent = `Czerwona sonda na ${zam ? 'minusie' : 'plusie'}: miernik pokazuje ${v > 0 ? '+9,0' : '−9,0'} V. Zamiana sond zmienia znak, nie wartość.`;
      };
      przycisk(r.ster, 'Zamień sondy', () => { zam = !zam; rys(); }); rys();
    },
    E08(el) {
      const r = ramka(el, 'ciągłość przewodu'); let przerwa = Math.random() < 0.5, wnetrze = false, wynik = '';
      const rys = () => {
        r.svg.innerHTML = `<rect x="40" y="70" width="240" height="30" rx="15" fill="${wnetrze ? 'rgba(143,185,255,.25)' : C.nieb}"/>`
          + (wnetrze ? `<line x1="40" y1="85" x2="${przerwa ? 150 : 280}" y2="85" stroke="${C.miedz}" stroke-width="6"/>` + (przerwa ? `<line x1="168" y1="85" x2="280" y2="85" stroke="${C.miedz}" stroke-width="6"/>` : '') : '')
          + `<text x="160" y="140" class="gen-t">${wynik}</text>`;
        r.wynik.textContent = wynik || 'Z zewnątrz przewód wygląda tak samo. Sprawdź ciągłość albo zajrzyj do środka.';
      };
      przycisk(r.ster, 'Sprawdź ciągłość', () => { wynik = przerwa ? 'Brak ciągłości — miernik milczy' : 'Ciągłość jest — miernik piszczy'; rys(); });
      przycisk(r.ster, 'Pokaż wnętrze', () => { wnetrze = !wnetrze; rys(); });
      przycisk(r.ster, 'Nowy przewód', () => { przerwa = Math.random() < 0.5; wynik = ''; wnetrze = false; rys(); }); rys();
    },
    E09(el) {
      const r = ramka(el, 'żyła i izolacja');
      suwak(r.ster, 'Zdjęta izolacja', 0, 40, 1, 12, (mm) => {
        const x = 280 - mm * 4;
        r.svg.innerHTML = `<rect x="30" y="70" width="${x - 30}" height="30" rx="8" fill="${C.nieb}"/><rect x="${x}" y="78" width="${280 - x}" height="14" rx="3" fill="${C.miedz}"/><text x="${(x + 280) / 2}" y="65" class="gen-t gen-m">${mm ? 'żyła' : ''}</text><text x="${(30 + x) / 2}" y="125" class="gen-t gen-m">izolacja</text>`;
        r.wynik.textContent = mm < 5 ? 'Za mało gołej żyły — styk może nie złapać.' : mm > 12 ? 'Za dużo gołej żyły — może dotknąć sąsiedniego styku.' : 'Tyle gołej żyły, ile wchodzi w złącze; reszta zostaje w izolacji.';
        return `${mm} mm`;
      });
    },
    E10(el) {
      const r = ramka(el, 'szukanie usterki'); const BLEDY = ['dioda', 'łącznik', 'przewód']; let blad, stan;
      const nowa = () => { blad = BLEDY[Math.floor(Math.random() * 3)]; stan = { dioda: blad !== 'dioda', 'łącznik': blad !== 'łącznik', 'przewód': blad !== 'przewód' }; };
      const rys = () => {
        const ok = stan.dioda && stan['łącznik'] && stan['przewód'];
        r.svg.innerHTML = petla(ok ? C.tyrk : C.linia, ok) + `<rect x="120" y="32" width="150" height="16" fill="${C.tlo}"/>` + bateria() + lacznik(140, 40, stan['łącznik']) + led(230, 40, ok ? 1 : 0)
          + (stan['przewód'] ? '' : `<rect x="272" y="95" width="16" height="16" fill="${C.tlo}"/><text x="300" y="108" class="gen-t" fill="${C.czerw}">?</text>`)
          + (stan.dioda ? '' : `<text x="230" y="75" class="gen-t gen-m" fill="${C.czerw}">odwrotnie?</text>`);
        r.wynik.textContent = ok ? `Działa! Usterka: ${blad}. Zmieniałeś po jednej rzeczy — tak się szuka.` : 'LED nie świeci. Popraw jedną rzecz i sprawdź.';
      };
      BLEDY.forEach((b) => przycisk(r.ster, `Popraw: ${b}`, () => { stan[b] = true; rys(); }));
      przycisk(r.ster, 'Nowa usterka', () => { nowa(); rys(); }); nowa(); rys();
    },

    A01(el) {
      const r = ramka(el, 'pętla i rytm'); let on = 1000, off = 1000, t0 = performance.now(), raf = 0;
      const rys = (teraz) => {
        const okres = on + off, faza = ((teraz - t0) % okres), swieci = faza < on;
        let p = 'M20 140'; let x = 20; const skala = 280 / (2 * okres);
        for (let i = 0; i < 2; i++) { p += ` V60 H${x + on * skala} V140 H${x + okres * skala}`; x += okres * skala; }
        r.svg.innerHTML = led(160, 30, swieci || calm() ? 1 : 0) + `<path d="${p}" fill="none" stroke="${C.tyrk}" stroke-width="3"/>` + (calm() ? '' : `<line x1="${20 + faza * skala}" y1="50" x2="${20 + faza * skala}" y2="150" stroke="${C.zloto}" stroke-width="2"/>`);
        if (!calm() && el.isConnected) raf = requestAnimationFrame(rys);
      };
      const opis = () => { r.wynik.textContent = `delay(${on}) świecenia i delay(${off}) przerwy: jeden obieg pętli trwa ${(on + off) / 1000} s.`; };
      suwak(r.ster, 'Świeci (ms)', 100, 2000, 100, on, (v) => { on = v; opis(); return v; });
      suwak(r.ster, 'Przerwa (ms)', 100, 2000, 100, off, (v) => { off = v; opis(); return v; });
      cancelAnimationFrame(raf); rys(performance.now());
    },
    A02(el) {
      const r = ramka(el, 'wejście i wyjście'); let w = false;
      const rys = () => {
        r.svg.innerHTML = `<rect x="20" y="40" width="110" height="90" rx="10" fill="${C.karta}" stroke="${C.linia}"/><text x="75" y="70" class="gen-t">D2</text><text x="75" y="105" class="gen-t gen-duzy" fill="${w ? C.czerw : C.tyrk}">${w ? 'LOW' : 'HIGH'}</text>` + lacznik(190, 85, w) + led(270, 85, w ? 1 : 0);
        r.wynik.textContent = w ? 'Wciśnięty: wejście połączone z GND, digitalRead daje LOW, program zapala LED.' : 'Puszczony: INPUT_PULLUP trzyma wejście na HIGH, LED zgaszona.';
      };
      const b = przycisk(r.ster, 'Trzymaj przycisk', () => {});
      b.addEventListener('pointerdown', () => { w = true; rys(); }); ['pointerup', 'pointerleave'].forEach((t) => b.addEventListener(t, () => { w = false; rys(); })); rys();
    },
    A03(el) {
      const r = ramka(el, 'serwo pozycyjne');
      suwak(r.ster, 'Kąt', 0, 180, 5, 90, (k) => {
        const a = (180 - k) * Math.PI / 180;
        r.svg.innerHTML = `<rect x="120" y="100" width="80" height="50" rx="8" fill="${C.nieb}"/><circle cx="160" cy="100" r="10" fill="${C.linia}"/><line x1="160" y1="100" x2="${160 + 80 * Math.cos(a)}" y2="${100 - 80 * Math.sin(a)}" stroke="${C.zloto}" stroke-width="10" stroke-linecap="round"/><text x="160" y="165" class="gen-t gen-m">ramie.write(${k});</text>`;
        r.wynik.textContent = `Polecenie ramie.write(${k}) ustawia oś serwa na ${k}°.`;
        return `${k}°`;
      });
    },
    A04(el) {
      const r = ramka(el, 'polecenie STOP'); let stop = false, kat = 0, raf = 0;
      const rys = () => {
        if (!stop && !calm()) kat = (kat + 6) % 360;
        r.svg.innerHTML = `<g transform="rotate(${kat} 110 95)"><circle cx="110" cy="95" r="45" fill="none" stroke="${C.linia}" stroke-width="8"/><line x1="65" y1="95" x2="155" y2="95" stroke="${C.linia}" stroke-width="5"/><line x1="110" y1="50" x2="110" y2="140" stroke="${C.linia}" stroke-width="5"/></g><rect x="200" y="65" width="90" height="60" rx="10" fill="${stop ? C.czerw : C.tyrk}"/><text x="245" y="101" class="gen-t gen-duzy" fill="${C.tlo}">${stop ? 'STOP' : 'JAZDA'}</text>`;
        r.wynik.textContent = stop ? 'STOP zapamiętany: silnik stoi, nawet gdy puścisz przycisk. Ruszy dopiero po restarcie.' : 'Silnik pracuje. Naciśnij STOP.';
        if (!stop && !calm() && el.isConnected) raf = requestAnimationFrame(rys);
      };
      przycisk(r.ster, 'STOP', () => { stop = true; rys(); });
      przycisk(r.ster, 'Restart', () => { stop = false; cancelAnimationFrame(raf); rys(); }); rys();
    },
    A05(el) {
      const r = ramka(el, 'czas bez zatrzymywania programu'); let tryb = 'delay', zaliczone = 0, pominiete = 0, t0 = performance.now();
      const rys = () => {
        r.svg.innerHTML = `<text x="160" y="30" class="gen-t">${tryb === 'delay' ? 'delay(): program czeka i nie patrzy na przycisk' : 'millis(): program co chwilę sprawdza zegar i przycisk'}</text>`
          + `<rect x="20" y="60" width="280" height="24" rx="4" fill="${C.karta}"/>` + (tryb === 'delay' ? `<rect x="20" y="60" width="210" height="24" rx="4" fill="${C.czerw}" opacity=".7"/><text x="125" y="77" class="gen-t gen-m">czekanie — przycisk ślepy</text>` : `<text x="160" y="77" class="gen-t gen-m">pętla działa cały czas</text>`)
          + `<text x="90" y="130" class="gen-t gen-duzy" fill="${C.tyrk}">${zaliczone}</text><text x="90" y="150" class="gen-t gen-m">zauważone</text><text x="230" y="130" class="gen-t gen-duzy" fill="${C.czerw}">${pominiete}</text><text x="230" y="150" class="gen-t gen-m">przeoczone</text>`;
        r.wynik.textContent = `Tryb ${tryb}: zauważone ${zaliczone}, przeoczone ${pominiete} wciśnięć.`;
      };
      przycisk(r.ster, 'Wciśnij przycisk', () => {
        const w = ((performance.now() - t0) % 1000) < 750; // przy delay(750) program przez 3/4 czasu czeka
        if (tryb === 'delay' && w) pominiete++; else zaliczone++; rys();
      });
      przycisk(r.ster, 'Zmień: delay / millis', () => { tryb = tryb === 'delay' ? 'millis' : 'delay'; zaliczone = pominiete = 0; rys(); }); rys();
    },
    A06(el) {
      const r = ramka(el, 'kolory światła RGB'); const k = { r: 255, g: 255, b: 0 };
      const rys = () => {
        const kol = `rgb(${k.r},${k.g},${k.b})`;
        r.svg.innerHTML = `<circle cx="160" cy="80" r="60" fill="${kol}" opacity=".3"/><circle cx="160" cy="80" r="30" fill="${kol}" stroke="${C.linia}" stroke-width="2"/><text x="160" y="160" class="gen-t gen-m">analogWrite: R=${k.r} G=${k.g} B=${k.b}</text>`;
        r.wynik.textContent = `Czerwony ${k.r}, zielony ${k.g}, niebieski ${k.b}. ${k.r > 200 && k.g > 200 && k.b < 60 ? 'Czerwony z zielonym daje żółty.' : ''}`;
      };
      [['r', 'Czerwony'], ['g', 'Zielony'], ['b', 'Niebieski']].forEach(([x, n]) => suwak(r.ster, n, 0, 255, 5, k[x], (v) => { k[x] = v; rys(); return v; }));
    },
    A07(el) {
      const r = ramka(el, 'pokrętło i odczyt');
      suwak(r.ster, 'Pokrętło', 0, 1023, 1, 512, (v) => {
        const kat = -135 + 270 * v / 1023;
        r.svg.innerHTML = `<circle cx="90" cy="85" r="50" fill="${C.karta}" stroke="${C.linia}" stroke-width="3"/><line x1="90" y1="85" x2="${90 + 42 * Math.sin(kat * Math.PI / 180)}" y2="${85 - 42 * Math.cos(kat * Math.PI / 180)}" stroke="${C.zloto}" stroke-width="6" stroke-linecap="round"/>`
          + `<text x="230" y="75" class="gen-t gen-duzy" fill="${C.tyrk}">${v}</text><text x="230" y="105" class="gen-t gen-m">analogRead(A0)</text><text x="230" y="130" class="gen-t gen-m">${(v * 5 / 1023).toFixed(2)} V</text>`;
        r.wynik.textContent = `analogRead(A0) = ${v}, czyli około ${(v * 5 / 1023).toFixed(2)} V na wejściu.`;
        return v;
      });
    },
    A08(el) {
      const r = ramka(el, 'dźwięk jako sygnał'); let ile = 2, hz = 880, ctx;
      const rys = (aktywny = -1) => {
        let s = '';
        for (let i = 0; i < ile; i++) s += `<circle cx="${100 + i * 60}" cy="85" r="${aktywny === i ? 26 : 18}" fill="${aktywny === i ? C.zloto : C.przyg}"/>`;
        r.svg.innerHTML = s + `<text x="160" y="150" class="gen-t gen-m">tone(8, ${hz}, 150) × ${ile}</text>`;
        r.wynik.textContent = `${ile} ${ile === 1 ? 'pisk' : 'piski'} o tonie ${hz} Hz — umówiony sygnał.`;
      };
      suwak(r.ster, 'Liczba pisków', 1, 3, 1, ile, (v) => { ile = v; rys(); return v; });
      suwak(r.ster, 'Ton (Hz)', 220, 1760, 20, hz, (v) => { hz = v; rys(); return v; });
      przycisk(r.ster, 'Odtwórz', () => {
        ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
        for (let i = 0; i < ile; i++) {
          const o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.value = hz; g.gain.value = 0.08;
          o.connect(g).connect(ctx.destination); o.start(ctx.currentTime + i * 0.3); o.stop(ctx.currentTime + i * 0.3 + 0.15);
          setTimeout(() => rys(i), i * 300); setTimeout(() => rys(), i * 300 + 150);
        }
      }); rys();
    },
    A09(el) {
      const r = ramka(el, 'zapis obserwacji'); const log = ['czas_ms;stan']; const t0 = performance.now();
      const rys = () => {
        r.svg.innerHTML = `<rect x="10" y="10" width="300" height="150" rx="8" fill="#141a21"/>` + log.slice(-8).map((l, i) => `<text x="22" y="${32 + i * 17}" class="gen-kod">${l}</text>`).join('');
        r.wynik.textContent = log.length > 1 ? `Ostatni wpis: ${log[log.length - 1]}` : 'Wciśnij i puść przycisk — monitor zapisze każdą zmianę.';
      };
      const b = przycisk(r.ster, 'Trzymaj przycisk', () => {});
      const zapisz = (s) => { log.push(`${Math.round(performance.now() - t0)};${s}`); rys(); };
      b.addEventListener('pointerdown', () => zapisz('wcisniety')); b.addEventListener('pointerup', () => zapisz('puszczony')); rys();
    },
    A10(el) {
      const r = ramka(el, 'warunek w programie'); let w = false, licznik = 0;
      const rys = () => {
        r.svg.innerHTML = led(90, 70, w ? 1 : 0) + `<text x="90" y="125" class="gen-t gen-m">LED: „jest wciśnięty”</text><text x="230" y="80" class="gen-t gen-duzy" fill="${C.zloto}">${licznik}</text><text x="230" y="125" class="gen-t gen-m">piski: „właśnie wciśnięty”</text>`;
        r.wynik.textContent = `LED świeci, dopóki trzymasz. Pisk liczy tylko chwile wciśnięcia: ${licznik}.`;
      };
      const b = przycisk(r.ster, 'Trzymaj przycisk', () => {});
      b.addEventListener('pointerdown', () => { if (!w) licznik++; w = true; rys(); }); ['pointerup', 'pointerleave'].forEach((t) => b.addEventListener(t, () => { w = false; rys(); })); rys();
    },

    D01(el) {
      const r = ramka(el, 'pierwsza warstwa'); let ile = 1, raf = 0;
      const rys = () => {
        let s = `<rect x="30" y="145" width="260" height="10" fill="${C.linia}"/>`;
        for (let i = 0; i < ile; i++) s += `<rect x="110" y="${137 - i * 8}" width="100" height="7" rx="2" fill="${i === 0 ? C.zloto : C.tyrk}"/>`;
        r.svg.innerHTML = s + `<rect x="${150}" y="${120 - ile * 8}" width="20" height="14" fill="${C.nieb}"/>`;
        r.wynik.textContent = ile === 1 ? 'Pierwsza warstwa leży bezpośrednio na stole.' : `Warstw: ${ile}. Każda nowa leży na poprzedniej — wydruk rośnie od dołu.`;
      };
      const s = suwak(r.ster, 'Warstwy', 1, 14, 1, 1, (v) => { ile = v; rys(); return v; });
      przycisk(r.ster, 'Drukuj', () => {
        if (calm()) { ile = 14; s.value = 14; rys(); return; }
        ile = 1; cancelAnimationFrame(raf); let t = 0;
        const krok = () => { t++; if (t % 12 === 0 && ile < 14) { ile++; s.value = ile; rys(); } if (ile < 14 && el.isConnected) raf = requestAnimationFrame(krok); };
        krok();
      });
    },
    D02(el) {
      const r = ramka(el, 'ułożenie części do druku'); let stoi = false;
      const rys = () => {
        r.svg.innerHTML = `<rect x="30" y="145" width="260" height="10" fill="${C.linia}"/>` + (stoi
          ? `<path d="M140 145 V45 H170 V115 H220 V145 Z" fill="${C.tyrk}"/><rect x="140" y="145" width="80" height="6" fill="${C.zloto}"/>`
          : `<path d="M100 145 V115 H220 V145 Z M100 115 V85 H130 V115" fill="${C.tyrk}"/><rect x="100" y="145" width="120" height="6" fill="${C.zloto}"/>`);
        r.wynik.textContent = stoi ? 'Na stojąco: mały ślad na stole, część może się chwiać.' : 'Na płasko: duży ślad na stole (złota linia) — lepsze trzymanie.';
      };
      przycisk(r.ster, 'Obróć część', () => { stoi = !stoi; rys(); }); rys();
    },
    D03(el) {
      const r = ramka(el, 'miejsce na wtyczkę');
      suwak(r.ster, 'Odstęp ścianki', 4, 30, 1, 10, (mm) => {
        const kol = mm < 18;
        r.svg.innerHTML = `<rect x="30" y="60" width="110" height="50" rx="4" fill="${C.nieb}"/><text x="85" y="90" class="gen-t gen-m">płytka</text><rect x="140" y="75" width="${18 * 4}" height="20" rx="3" fill="${kol ? C.czerw : C.zloto}"/><rect x="${140 + mm * 4}" y="30" width="10" height="110" fill="${C.linia}"/>`;
        r.wynik.textContent = kol ? `Ścianka ${mm} mm od złącza — wtyczka (18 mm) w nią uderza.` : `Ścianka ${mm} mm od złącza — wtyczka się mieści.`;
        return `${mm} mm`;
      });
    },
    D04(el) {
      const r = ramka(el, 'droga przewodu'); let d = 0; const DROGI = ['przez krawędź pokrywki', 'przez wycięcie', 'pod płytką'];
      const rys = () => {
        const ok = d === 1;
        const p = ['M40 120 H150 V40 H290', 'M40 120 H200 V60 H290', 'M40 130 H290'][d];
        r.svg.innerHTML = `<rect x="140" y="30" width="120" height="110" rx="6" fill="none" stroke="${C.linia}" stroke-width="3"/><rect x="190" y="25" width="20" height="10" fill="${C.tlo}"/><path d="${p}" fill="none" stroke="${ok ? C.tyrk : C.czerw}" stroke-width="5"/>`;
        r.wynik.textContent = `Przewód ${DROGI[d]}: ${ok ? 'pokrywka domyka się bez nacisku.' : 'pokrywka przyciśnie przewód.'}`;
      };
      przycisk(r.ster, 'Inna droga', () => { d = (d + 1) % 3; rys(); }); rys();
    },
    D05(el) {
      const r = ramka(el, 'widok i rozmiar modelu'); let zoom = 1, skala = 100;
      const rys = () => {
        const w = 60 * zoom * skala / 100, otw = 5 * skala / 100;
        r.svg.innerHTML = `<rect x="${160 - w / 2}" y="${85 - w / 4}" width="${w}" height="${w / 2}" rx="6" fill="${C.tyrk}"/><circle cx="160" cy="85" r="${otw * zoom}" fill="${C.tlo}"/>`;
        r.wynik.textContent = `Widok ×${zoom}: tylko obraz większy. Skala ${skala}%: otwór ma naprawdę ${otw.toFixed(1)} mm.`;
      };
      suwak(r.ster, 'Przybliżenie widoku', 1, 3, 0.5, 1, (v) => { zoom = v; rys(); return `×${v}`; });
      suwak(r.ster, 'Skala modelu', 50, 200, 10, 100, (v) => { skala = v; rys(); return `${v}%`; });
    },
    D06(el) {
      const r = ramka(el, 'obrys i wypełnienie'); let wz = 'kratka';
      const s = suwak(r.ster, 'Wypełnienie', 0, 60, 5, 20, (p) => { rys(p); return `${p}%`; });
      function rys(p = Number(s ? s.value : 20)) {
        const krok = p ? Math.max(8, 120 / (p / 5)) : 0; let lin = '';
        for (let x = 90 + krok; krok && x < 230; x += krok) lin += `<line x1="${x}" y1="40" x2="${x}" y2="130" stroke="${C.tyrk}" stroke-width="2"/>`;
        if (wz === 'kratka') for (let y = 40 + krok; krok && y < 130; y += krok) lin += `<line x1="90" y1="${y}" x2="230" y2="${y}" stroke="${C.tyrk}" stroke-width="2"/>`;
        r.svg.innerHTML = `<rect x="80" y="30" width="160" height="110" rx="6" fill="none" stroke="${C.zloto}" stroke-width="5"/><rect x="88" y="38" width="144" height="94" rx="4" fill="none" stroke="${C.zloto}" stroke-width="3"/>${lin}`;
        r.wynik.textContent = `Złote ścieżki to obrys przy krawędzi. W środku ${p}% wypełnienia (${wz}).`;
      }
      przycisk(r.ster, 'Kratka / linie', () => { wz = wz === 'kratka' ? 'linie' : 'kratka'; rys(); }); rys();
    },
    D07(el) {
      const r = ramka(el, 'oparcie pod górną warstwą');
      suwak(r.ster, 'Wypełnienie', 0, 40, 5, 15, (p) => {
        const krok = p ? 240 / (p / 2.5) : 240, ugiecie = Math.min(30, krok / 6);
        let s = `<rect x="40" y="40" width="8" height="110" fill="${C.zloto}"/><rect x="272" y="40" width="8" height="110" fill="${C.zloto}"/>`, top = 'M40 40';
        for (let x = 40; x < 280; x += krok) { const nx = Math.min(280, x + krok); if (nx < 280) s += `<rect x="${nx - 2}" y="44" width="4" height="106" fill="${C.tyrk}"/>`; top += ` Q${(x + nx) / 2} ${40 + ugiecie} ${nx} 40`; }
        r.svg.innerHTML = s + `<path d="${top}" fill="none" stroke="${C.nieb}" stroke-width="5"/>`;
        r.wynik.textContent = ugiecie > 12 ? `${p}% wypełnienia: górna warstwa nie ma oparcia i opada między podporami.` : `${p}% wypełnienia: górna warstwa opiera się na ścianach i wypełnieniu.`;
        return `${p}%`;
      });
    },
    D08(el) {
      const r = ramka(el, 'tymczasowa podpora'); let podpora = true, usunieta = false;
      const rys = () => {
        let s = `<rect x="30" y="145" width="260" height="10" fill="${C.linia}"/><rect x="60" y="45" width="40" height="100" fill="${C.tyrk}"/>`;
        s += podpora && !usunieta ? `<rect x="100" y="45" width="140" height="18" fill="${C.tyrk}"/><rect x="190" y="63" width="40" height="82" fill="${C.przyg}" stroke="${C.linia}" stroke-dasharray="4 4"/>`
          : podpora ? `<rect x="100" y="45" width="140" height="18" fill="${C.tyrk}"/>` : `<path d="M100 45 Q170 100 240 130" fill="none" stroke="${C.czerw}" stroke-width="10"/>`;
        r.svg.innerHTML = s;
        r.wynik.textContent = !podpora ? 'Bez podpory nawis nie ma oparcia i opada.' : usunieta ? 'Po druku dorosły usuwa podporę — zostaje równy nawis.' : 'Podpora (kreskowana) trzyma nawis w czasie druku.';
      };
      przycisk(r.ster, 'Podpora tak / nie', () => { podpora = !podpora; usunieta = false; rys(); });
      przycisk(r.ster, 'Usuń podporę po druku', () => { if (podpora) usunieta = true; rys(); }); rys();
    },
    D09(el) {
      const r = ramka(el, 'most w wydruku');
      suwak(r.ster, 'Długość mostu', 10, 80, 5, 30, (mm) => {
        const w = mm * 2.6, x0 = 160 - w / 2, ugiecie = Math.max(0, (mm - 40) * 0.8);
        r.svg.innerHTML = `<rect x="${x0 - 40}" y="60" width="40" height="90" fill="${C.tyrk}"/><rect x="${x0 + w}" y="60" width="40" height="90" fill="${C.tyrk}"/><path d="M${x0} 62 Q160 ${62 + ugiecie * 2} ${x0 + w} 62" fill="none" stroke="${ugiecie > 10 ? C.czerw : C.zloto}" stroke-width="6"/>`;
        r.wynik.textContent = ugiecie > 10 ? `Most ${mm} mm: ścieżka mocno opada w środku.` : `Most ${mm} mm: ścieżka łączy oba brzegi i ma po drugiej stronie oparcie.`;
        return `${mm} mm`;
      });
    },
    D10(el) {
      const r = ramka(el, 'obrzeże przy pierwszej warstwie'); const T = ['brak', 'brim', 'skirt']; let t = 0;
      const rys = () => {
        let s = `<rect x="20" y="20" width="280" height="130" rx="8" fill="${C.karta}"/>`;
        if (T[t] === 'brim') s += `<rect x="100" y="50" width="120" height="70" rx="16" fill="${C.zloto}" opacity=".7"/>`;
        if (T[t] === 'skirt') s += `<rect x="80" y="35" width="160" height="100" rx="18" fill="none" stroke="${C.zloto}" stroke-width="3"/>`;
        r.svg.innerHTML = s + `<rect x="120" y="65" width="80" height="40" rx="4" fill="${C.tyrk}"/>`;
        r.wynik.textContent = { brak: 'Bez obrzeża: tylko ślad samej części.', brim: 'Brim przylega do części i powiększa jej ślad na stole; po druku się go odłamuje.', skirt: 'Skirt to osobna ścieżka dookoła, nie dotyka części.' }[T[t]];
      };
      przycisk(r.ster, 'Brak / brim / skirt', () => { t = (t + 1) % 3; rys(); }); rys();
    },
  };

  document.querySelectorAll('[data-gen]').forEach((el) => {
    const f = G[el.dataset.gen.toUpperCase()];
    if (f) { el.hidden = false; f(el); }
  });
})();
