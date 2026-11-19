document.addEventListener('DOMContentLoaded', () => {
  // Escapowanie treści od użytkownika — komentarze i tytuły wątków trafiają
  // do innerHTML, więc bez tego dowolny <script>/<img onerror> by się wykonał.
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));

  // ---------- menu mobilne i dropdowny ----------
  const burger = document.querySelector('.burger');
  const navMenu = document.querySelector('.nav-menu') || document.querySelector('.nav ul');
  if (burger && navMenu) {
    const mobile = window.matchMedia('(max-width: 960px)');
    const header = burger.closest('header');
    const updateHeaderHeight = () => {
      if (header) document.documentElement.style.setProperty('--header-h', `${header.getBoundingClientRect().height}px`);
    };
    updateHeaderHeight();
    if (header && 'ResizeObserver' in window) new ResizeObserver(updateHeaderHeight).observe(header);
    const ustaw = (otwarte, restoreFocus = true) => {
      otwarte = otwarte && mobile.matches;
      const wasOpen = navMenu.classList.contains('open');
      navMenu.classList.toggle('open', otwarte);
      document.body.classList.toggle('menu-open', otwarte);
      burger.setAttribute('aria-expanded', String(otwarte));
      burger.setAttribute('aria-label', otwarte ? 'Zamknij menu' : 'Rozwiń menu');
      navMenu.inert = mobile.matches && !otwarte;
      if (mobile.matches) navMenu.setAttribute('aria-hidden', String(!otwarte));
      else navMenu.removeAttribute('aria-hidden');
      if (otwarte) {
        updateHeaderHeight();
        navMenu.querySelector('a[href], button:not([disabled])')?.focus({preventScroll: true});
      } else if (wasOpen && restoreFocus && mobile.matches) {
        burger.focus({preventScroll: true});
      }
    };
    ustaw(false, false);
    burger.addEventListener('click', () => ustaw(!navMenu.classList.contains('open')));

    // Na mobile: kliknięcie w linki z rozwijaniem (.has-dropdown > .dropdown-toggle)
    // na ekranie <= 960px najpierw rozwija akordeon, chyba że jest już rozwinięty.
    const dropdownItems = navMenu.querySelectorAll('.nav-item.has-dropdown');
    dropdownItems.forEach(item => {
      const toggle = item.querySelector('.dropdown-toggle');
      if (toggle) {
        toggle.addEventListener('click', (e) => {
          if (window.innerWidth <= 960) {
            e.preventDefault();
            const isExpanded = item.classList.contains('drawer-expanded');
            dropdownItems.forEach(d => {
              d.classList.remove('drawer-expanded');
              const t = d.querySelector('.dropdown-toggle');
              if (t) t.setAttribute('aria-expanded', 'false');
            });
            if (!isExpanded) {
              item.classList.add('drawer-expanded');
              toggle.setAttribute('aria-expanded', 'true');
            }
          }
        });
      }
    });

    // Płynna obsługa podmenu na desktopie z buforem czasowym (hover intent)
    // Zapobiega przedwczesnemu znikaniu submenu podczas przesuwania kursora z nagłówka
    let aktywneMenu = null;
    let zamknijTimer = null;

    const anulujZamkniecie = () => {
      if (zamknijTimer) {
        clearTimeout(zamknijTimer);
        zamknijTimer = null;
      }
    };

    const zamknijWszystkieDropdowny = () => {
      anulujZamkniecie();
      dropdownItems.forEach(d => {
        d.classList.remove('is-open');
        const t = d.querySelector('.dropdown-toggle');
        if (t) t.setAttribute('aria-expanded', 'false');
      });
      aktywneMenu = null;
    };

    dropdownItems.forEach(item => {
      const toggle = item.querySelector('.dropdown-toggle');
      const panel = item.querySelector('.dropdown-panel');

      const otworzDropdown = () => {
        if (window.innerWidth <= 960) return;
        anulujZamkniecie();

        if (aktywneMenu && aktywneMenu !== item) {
          aktywneMenu.classList.remove('is-open');
          const prevToggle = aktywneMenu.querySelector('.dropdown-toggle');
          if (prevToggle) prevToggle.setAttribute('aria-expanded', 'false');
        }

        item.classList.add('is-open');
        if (toggle) toggle.setAttribute('aria-expanded', 'true');
        aktywneMenu = item;
      };

      const zaplanujZamkniecie = () => {
        if (window.innerWidth <= 960) return;
        anulujZamkniecie();
        zamknijTimer = setTimeout(() => {
          item.classList.remove('is-open');
          if (toggle) toggle.setAttribute('aria-expanded', 'false');
          if (aktywneMenu === item) aktywneMenu = null;
        }, 220);
      };

      item.addEventListener('mouseenter', otworzDropdown);
      item.addEventListener('mouseleave', zaplanujZamkniecie);

      if (panel) {
        panel.addEventListener('mouseenter', otworzDropdown);
        panel.addEventListener('mouseleave', zaplanujZamkniecie);
      }

      // Dostępność: klawiatura (focusin / focusout)
      item.addEventListener('focusin', otworzDropdown);
      item.addEventListener('focusout', (e) => {
        if (window.innerWidth <= 960) return;
        if (!item.contains(e.relatedTarget)) {
          zaplanujZamkniecie();
        }
      });
    });

    // Zwykłe linki (bezpośrednie lub wewnątrz panelu) zamykają menu mobilne lub otwarty dropdown
    navMenu.querySelectorAll('.dropdown-panel a, .nav-item:not(.has-dropdown) a, .mobile-quick-btn').forEach(a => {
      a.addEventListener('click', () => {
        if (window.innerWidth <= 960) {
          ustaw(false);
        } else {
          zamknijWszystkieDropdowny();
        }
      });
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (navMenu.classList.contains('open')) {
          e.preventDefault();
          ustaw(false);
        }
        zamknijWszystkieDropdowny();
      }
      if (e.key === 'Tab' && mobile.matches && navMenu.classList.contains('open')) {
        const items = [burger, ...navMenu.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]')]
          .filter(el => el.tabIndex >= 0 && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
        const index = items.indexOf(document.activeElement);
        if (e.shiftKey && index <= 0) {
          e.preventDefault();
          items[items.length - 1].focus();
        } else if (!e.shiftKey && (index === -1 || index === items.length - 1)) {
          e.preventDefault();
          items[0].focus();
        } else if (!e.shiftKey && index === 0) {
          e.preventDefault();
          items[1]?.focus();
        } else if (e.shiftKey && index === 1) {
          e.preventDefault();
          burger.focus();
        }
      }
    });

    // Dotknięcie poza panelem zamyka menu mobilne lub dropdowny desktop
    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 960) {
        if (!navMenu.classList.contains('open')) return;
        if (navMenu.contains(e.target) || burger.contains(e.target)) return;
        ustaw(false);
      } else {
        if (!navMenu.contains(e.target)) {
          zamknijWszystkieDropdowny();
        }
      }
    });

    mobile.addEventListener('change', () => {
      const focusWasInside = navMenu.contains(document.activeElement);
      ustaw(false, false);
      zamknijWszystkieDropdowny();
      dropdownItems.forEach(item => item.classList.remove('drawer-expanded'));
      if (mobile.matches && focusWasInside) burger.focus({preventScroll: true});
    });
    window.addEventListener('resize', updateHeaderHeight);

  }

  // ---------- live status warsztatu (godziny pracy) ----------
  const statusEl = document.getElementById('workshop-status');
  if (statusEl) {
    const teraz = new Date();
    const dzien = teraz.getDay(); // 0 = nd, 1 = pn, ..., 6 = sob
    const godz = teraz.getHours() + teraz.getMinutes() / 60;
    let otwarte = false;

    if (dzien >= 1 && dzien <= 5) {
      otwarte = (godz >= 8 && godz < 17);
    } else if (dzien === 6) {
      otwarte = (godz >= 9 && godz < 13);
    }

    if (!otwarte) {
      statusEl.classList.add('closed');
      const label = statusEl.querySelector('.status-label');
      if (label) {
        label.innerHTML = 'Warsztat poza godzinami (zapraszamy: <b>pn–pt 8:00–17:00, sob 9:00–13:00</b>)';
      }
    }
  }

  // ---------- licznik koszyka w nagłówku ----------
  try {
    const rawKoszyk = localStorage.getItem('fw_koszyk');
    if (rawKoszyk) {
      const kosz = JSON.parse(rawKoszyk);
      const ile = Array.isArray(kosz) ? kosz.reduce((acc, p) => acc + (Number(p.ilosc) || 1), 0) : 0;
      document.querySelectorAll('[data-koszyk-licznik]').forEach(el => {
        if (ile > 0) {
          el.textContent = String(ile);
          el.hidden = false;
        } else {
          el.hidden = true;
        }
      });
    }
  } catch (_) {}

  // ---------- animacja wejścia sekcji ----------
  const revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(el => io.observe(el));
    // zabezpieczenie: gdyby obserwator nie zadziałał, po 1,5 s pokaż wszystko
    setTimeout(() => revealEls.forEach(el => el.classList.add('visible')), 1500);
  } else {
    revealEls.forEach(el => el.classList.add('visible'));
  }

  // ---------- spis treści bloga ----------
  // Spis jest w HTML otwarty, żeby bez JavaScriptu nic się nie chowało.
  // Na wąskim ekranie zwijamy go przy wczytaniu: rozwinięty zajmuje tam
  // prawie trzy tysiące pikseli i odsuwa karty wpisów poza zasięg kciuka.
  const spis = document.querySelector('details.spis-bloga');
  if (spis && window.matchMedia('(max-width: 760px)').matches) {
    spis.open = false;
  }

  // ---------- filtrowanie produktów w sklepie ----------
  // Zawezone do stron z kartami produktow: /narzedzia/ uzywa tych samych
  // przyciskow do przelaczania paneli i nie chce cudzej obslugi kliniecia.
  const cards = document.querySelectorAll('.product-card');
  const tabs = cards.length ? document.querySelectorAll('.tab-btn') : [];
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const cat = tab.dataset.cat;
      cards.forEach(card => {
        card.style.display = (cat === 'all' || card.dataset.cat === cat) ? '' : 'none';
      });
    });
  });


  // ---------- wspólny przełącznik animacji ----------
  (() => {
    const calm = matchMedia('(prefers-reduced-motion: reduce)');
    let stopped = false;
    try { stopped = localStorage.getItem('niebo') === 'stop'; } catch (e) { /* tryb prywatny */ }
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'niebo-przycisk';
    const ICON_STOP = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>';
    const ICON_PLAY = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2.5l2.6 6.2 6.7.6-5.1 4.4 1.6 6.5L12 16.7 6.2 20.2l1.6-6.5L2.7 9.3l6.7-.6z"/></svg>';
    const label = () => {
      button.innerHTML = stopped ? ICON_PLAY : ICON_STOP;
      button.setAttribute('aria-label', stopped ? 'Wznów animacje' : 'Zatrzymaj animacje');
      button.title = button.getAttribute('aria-label');
      document.documentElement.classList.toggle('niebo-stop', stopped);
      button.hidden = calm.matches;
    };
    button.addEventListener('click', () => {
      stopped = !stopped;
      try { localStorage.setItem('niebo', stopped ? 'stop' : 'ruch'); } catch (e) { /* prywatny tryb */ }
      label();
    });
    document.body.append(button);
    calm.addEventListener('change', label);
    label();
  })();

  // ---------- robot DRUCIK: przycisk asystenta AI, czasem siada przy komputerze w wolnym miejscu ----------
  // Spaceruje tylko na szerokim ekranie, bez ograniczonego ruchu i gdy animacje nie są zatrzymane.
  // Miejsce musi być puste: pod robotem nie może być tekstu ani elementu interaktywnego.
  (() => {
    const button = document.getElementById('assistant-launch');
    if (!button || !button.classList.contains('robot')) return;
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)');
    const wide = window.matchMedia('(min-width: 1024px)');
    const scena = document.createElement('div');
    scena.className = 'robot-scena';
    scena.dataset.stan = 'kat';
    const biurko = document.createElement('div');
    biurko.className = 'robot-biurko';
    biurko.setAttribute('aria-hidden', 'true');
    biurko.innerHTML = '<svg viewBox="0 0 104 86" width="104" height="86"><defs><clipPath id="rb-ekran"><rect x="12" y="10" width="54" height="36" rx="3"/></clipPath></defs>'
      + '<rect x="6" y="4" width="66" height="48" rx="7" fill="#2a1d0e" stroke="#e7b75f" stroke-width="2"/>'
      + '<rect x="12" y="10" width="54" height="36" rx="3" fill="#04121a"/>'
      + '<g clip-path="url(#rb-ekran)"><g class="robot-kod" fill="#5ff3e6" opacity=".85">'
      + [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => `<rect x="${16 + (i % 3) * 4}" y="${14 + i * 6}" width="${14 + ((i * 7) % 26)}" height="2" rx="1"/>`).join('')
      + '</g></g><circle cx="64" cy="49" r="1.6" fill="#ff5a4e"/>'
      + '<rect x="30" y="52" width="18" height="8" fill="#2a1d0e"/><rect x="0" y="60" width="104" height="7" rx="2" fill="#7a5320" stroke="#3b2a12"/>'
      + '<rect x="18" y="55" width="38" height="5" rx="1.5" fill="#1b2338" stroke="#5ff3e6" stroke-opacity=".4"/>'
      + '<rect x="8" y="67" width="6" height="19" fill="#5a3d17"/><rect x="90" y="67" width="6" height="19" fill="#5a3d17"/></svg>';
    button.replaceWith(scena);
    scena.insertAdjacentHTML('beforeend', '<div class="chmurka" aria-hidden="true"><svg viewBox="0 0 80 70"><g class="ch-slonce"><circle cx="40" cy="26" r="9"/><path d="M40 8v5M40 39v5M22 26h5M53 26h5M27 13l3.5 3.5M49.5 35.5L53 39M27 39l3.5-3.5M49.5 16.5L53 13"/></g><path class="ch-ksiezyc" d="M50 34A14 14 0 0 1 34 12a14 14 0 1 0 16 22z"/><path class="ch-chmura" d="M20 36h40a10 10 0 0 0 1-20 14 14 0 0 0-27 3 9 9 0 0 0-14 17z"/><g class="ch-krople"><path d="M26 42l-2 6"/><path d="M34 42l-2 6"/><path d="M42 42l-2 6"/><path d="M50 42l-2 6"/><path d="M30 50l-2 6"/><path d="M46 50l-2 6"/></g><g class="ch-platki"><circle cx="26" cy="44" r="2"/><circle cx="36" cy="46" r="1.6"/><circle cx="46" cy="44" r="2"/><circle cx="54" cy="47" r="1.5"/><circle cx="31" cy="53" r="1.7"/><circle cx="49" cy="54" r="1.8"/></g><path class="ch-piorun" d="M44 36l-7 12h7l-5 13 13-17h-7l5-8z"/><g class="ch-wiatr"><path d="M8 46h30a5 5 0 1 0-5-5"/><path d="M14 54h40a5 5 0 1 1-5 5"/><path d="M4 62h26"/></g><g class="ch-mgla"><path d="M12 44h48"/><path d="M6 52h56"/><path d="M16 60h40"/></g><g class="ch-wir"><path d="M40 30m-3 0a3 3 0 1 0 6 0a6 6 0 1 0-12 0a9 9 0 1 0 18 0a12 12 0 1 0-24 0"/></g></svg></div>');
    scena.append(biurko, button);

    const WOLNE = 'a,button,input,select,textarea,label,img,picture,video,iframe,svg,table,pre,code,form,header,nav,'
      + 'h1,h2,h3,h4,h5,h6,p,li,dt,dd,blockquote,figcaption,.ring-stage,[data-scene],#assistant-panel';
    const zajete = (x, y) => {
      const el = document.elementFromPoint(x, y);
      if (!el || el === document.documentElement || el === document.body) return !el;
      if (el.closest(WOLNE) || scena.contains(el)) return true;
      return Array.from(el.childNodes).some((n) => n.nodeType === 3 && n.textContent.trim());
    };
    const wolneMiejsce = (left, top, w, h) => {
      for (let i = 0; i <= 4; i += 1) {
        for (let j = 0; j <= 4; j += 1) {
          if (zajete(left + (w * i) / 4, top + (h * j) / 4)) return false;
        }
      }
      return true;
    };
    const naglowek = () => {
      const h = document.querySelector('header');
      return h ? Math.max(0, h.getBoundingClientRect().bottom) : 0;
    };

    let timer = 0;
    let watch = 0;
    const aktywny = () => !calm.matches && !document.hidden
      && !document.documentElement.classList.contains('niebo-stop')
      && !(document.getElementById('assistant-panel') && !document.getElementById('assistant-panel').hidden);
    const wolno = () => wide.matches && aktywny();
    const zaplanuj = (sekundy) => {
      clearTimeout(timer);
      timer = setTimeout(wycieczka, sekundy * 1000);
    };
    const doKata = () => {
      clearTimeout(watch);
      window.removeEventListener('scroll', pilnuj);
      scena.classList.toggle('w-lewo', false);
      scena.dataset.stan = 'idzie';
      scena.style.setProperty('--rx', '0px');
      scena.style.setProperty('--ry', '0px');
      setTimeout(() => { scena.dataset.stan = 'kat'; }, 2700);
      zaplanuj(30 + Math.random() * 40);
    };
    let pole = null;
    function pilnuj() {
      // po przewinięciu pod robotem mógł pojawić się tekst — wtedy wraca do rogu
      if (!pole || scena.dataset.stan === 'kat') return; // sprawdza też miejsce, do którego dopiero idzie
      scena.classList.add('sprawdza');
      const zle = !wolneMiejsce(pole.left, pole.top, pole.w, pole.h);
      scena.classList.remove('sprawdza');
      if (zle) doKata();
    }
    function wycieczka() {
      if (!aktywny()) { zaplanuj(20); return; }
      const polecenie = window.FWDrucik?.nextAction();
      if (window.FWDrucik && (!wide.matches || (polecenie ? polecenie !== 'spacer' : Math.random() < .55))) {
        const sceny = Object.keys(window.FWDrucik.scenes).filter((nazwa) => nazwa !== 'spacer');
        window.FWDrucik.show(scena, polecenie || sceny[Math.floor(Math.random() * sceny.length)]);
        zaplanuj(22 + Math.random() * 28);
        return;
      }
      if (!wolno()) { zaplanuj(20); return; }
      const box = scena.getBoundingClientRect();
      const w = 104 + 4 + button.querySelector('.robot-svg').getBoundingClientRect().width; // biurko + robot, bez etykiety
      const h = Math.max(112, box.height);
      const gora = naglowek() + 16;
      scena.classList.add('sprawdza'); // robot nie może zasłaniać własnego sprawdzenia
      let cel = null;
      for (let proba = 0; proba < 70 && !cel; proba += 1) {
        const left = 12 + Math.random() * (window.innerWidth - w - 24);
        const top = gora + Math.random() * Math.max(0, window.innerHeight - h - gora - 130);
        const blisko = Math.hypot(left - box.left, top - box.top) < 260;
        if (!blisko && wolneMiejsce(left, top, w, h)) cel = { left, top };
      }
      scena.classList.remove('sprawdza');
      if (!cel) { zaplanuj(15 + Math.random() * 20); return; }
      const dx = cel.left + w - box.right;
      const dy = cel.top + h - box.bottom;
      pole = { left: cel.left, top: cel.top, w, h };
      scena.classList.toggle('w-lewo', dx < 0);
      scena.dataset.stan = 'idzie';
      window.addEventListener('scroll', pilnuj, { passive: true });
      scena.style.setProperty('--rx', `${Math.round(dx)}px`);
      scena.style.setProperty('--ry', `${Math.round(dy)}px`);
      setTimeout(() => {
        if (scena.dataset.stan !== 'idzie') return;
        scena.classList.toggle('w-lewo', false);
        scena.dataset.stan = 'biurko';
        pilnuj();
        watch = setTimeout(doKata, 9000 + Math.random() * 7000);
      }, 2700);
    }
    button.addEventListener('click', () => { if (scena.dataset.stan !== 'kat') doKata(); });
    [calm, wide].forEach((mq) => mq.addEventListener('change', () => { if (!wolno()) doKata(); }));
    zaplanuj(10 + Math.random() * 8);
  })();

  // ---------- pogoda: pasek górny, kolory strony, chmurka nad robotem ----------
  // Okolica bez pytania: ze strefy czasowej przeglądarki (stolica regionu). Dokładniej: przycisk
  // „moja okolica” (zgoda przeglądarki), współrzędne zaokrąglone do ok. 25 km i trzymane tylko lokalnie.
  // Dane idą przez /api/pogoda.php, więc IP odwiedzającego nie trafia do dostawcy prognozy.
  (() => {
    const STREFY = {
      'Europe/Warsaw': [52.23, 21.01, 'Warszawa'], 'Europe/Berlin': [52.52, 13.4, 'Berlin'],
      'Europe/London': [51.51, -0.13, 'Londyn'], 'Europe/Dublin': [53.35, -6.26, 'Dublin'],
      'Europe/Paris': [48.86, 2.35, 'Paryż'], 'Europe/Amsterdam': [52.37, 4.9, 'Amsterdam'],
      'Europe/Brussels': [50.85, 4.35, 'Bruksela'], 'Europe/Oslo': [59.91, 10.75, 'Oslo'],
      'Europe/Stockholm': [59.33, 18.07, 'Sztokholm'], 'Europe/Copenhagen': [55.68, 12.57, 'Kopenhaga'],
      'Europe/Prague': [50.08, 14.44, 'Praga'], 'Europe/Vienna': [48.21, 16.37, 'Wiedeń'],
      'Europe/Rome': [41.9, 12.5, 'Rzym'], 'Europe/Madrid': [40.42, -3.7, 'Madryt'],
      'Europe/Kyiv': [50.45, 30.52, 'Kijów'], 'Europe/Kiev': [50.45, 30.52, 'Kijów'],
      'Europe/Vilnius': [54.69, 25.28, 'Wilno'], 'Europe/Bratislava': [48.15, 17.11, 'Bratysława'],
      'Europe/Budapest': [47.5, 19.04, 'Budapeszt'], 'America/New_York': [40.71, -74.01, 'Nowy Jork'],
      'America/Chicago': [41.88, -87.63, 'Chicago'], 'America/Los_Angeles': [34.05, -118.24, 'Los Angeles'],
    };
    const OPIS = {
      pogodnie: 'pogodnie', noc: 'pogodna noc', chmury: 'pochmurno', mgla: 'mgła', deszcz: 'deszcz',
      snieg: 'śnieg', burza: 'burza', wiatr: 'silny wiatr', huragan: 'wichura',
    };
    const IKONA = {
      pogodnie: '<circle cx="12" cy="12" r="4.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
      noc: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
      chmury: '<path d="M7 18h10a4 4 0 0 0 .4-8 6 6 0 0 0-11.5 1.6A3.3 3.3 0 0 0 7 18z"/>',
      mgla: '<path d="M4 9h16M2 13h20M5 17h14"/>',
      deszcz: '<path d="M7 14h10a4 4 0 0 0 .4-8 6 6 0 0 0-11.5 1.6A3.3 3.3 0 0 0 7 14z"/><path d="M8 17l-1 3M12 17l-1 3M16 17l-1 3"/>',
      snieg: '<path d="M7 14h10a4 4 0 0 0 .4-8 6 6 0 0 0-11.5 1.6A3.3 3.3 0 0 0 7 14z"/><path d="M8 18h.01M12 20h.01M16 18h.01"/>',
      burza: '<path d="M7 14h10a4 4 0 0 0 .4-8 6 6 0 0 0-11.5 1.6A3.3 3.3 0 0 0 7 14z"/><path d="M12 14l-2 4h4l-2 4"/>',
      wiatr: '<path d="M3 9h11a3 3 0 1 0-3-3M3 15h15a3 3 0 1 1-3 3"/>',
      huragan: '<path d="M12 12m-2 0a2 2 0 1 0 4 0a2 2 0 1 0-4 0M12 4a8 8 0 0 0-7 5M12 20a8 8 0 0 0 7-5M20 12a8 8 0 0 0-5-7M4 12a8 8 0 0 0 5 7"/>',
    };
    const stanZ = (d) => {
      const k = d.kod;
      if (d.porywy >= 100) return 'huragan';
      if (k >= 95) return 'burza';
      if ((k >= 71 && k <= 77) || k === 85 || k === 86) return 'snieg';
      if ((k >= 51 && k <= 67) || (k >= 80 && k <= 82)) return 'deszcz';
      if (k === 45 || k === 48) return 'mgla';
      if (d.porywy >= 55) return 'wiatr';
      if (k >= 2) return 'chmury';
      return d.dzien ? 'pogodnie' : 'noc';
    };
    const czytaj = (klucz) => { try { return JSON.parse(localStorage.getItem(klucz) || 'null'); } catch (e) { return null; } };
    const zapisz = (klucz, v) => { try { localStorage.setItem(klucz, JSON.stringify(v)); } catch (e) { /* prywatny tryb */ } };

    const pasek = document.querySelector('.header-top-inner');
    const chip = document.createElement('div');
    chip.className = 'pogoda-pasek';
    chip.hidden = true;
    chip.innerHTML = '<svg class="pogoda-ikona" viewBox="0 0 24 24" aria-hidden="true"></svg>'
      + '<span class="pogoda-tekst" aria-live="polite"></span>'
      + '<button type="button" class="pogoda-gps" aria-label="Pogoda dla mojej okolicy" title="Pogoda dla mojej okolicy">'
      + '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6-5.6-6-10.5a6 6 0 1 1 12 0C18 15.4 12 21 12 21z"/><circle cx="12" cy="10.5" r="2.2"/></svg></button>';
    if (pasek) pasek.insertBefore(chip, pasek.children[1] || null);

    const pokaz = (d, miejsce) => {
      const stan = new URLSearchParams(location.search).get('pogoda') || stanZ(d);
      document.documentElement.dataset.pogoda = stan;
      chip.querySelector('.pogoda-ikona').innerHTML = IKONA[stan] || IKONA.chmury;
      chip.querySelector('.pogoda-tekst').textContent = `${d.temp}°C · ${OPIS[stan] || ''} · ${miejsce}`;
      chip.title = `Wiatr ${d.wiatr} km/h, porywy ${d.porywy} km/h · dane: Open-Meteo`;
      chip.hidden = false;
      const robot = document.querySelector('.robot-scena');
      if (robot) robot.dataset.pogoda = stan;
    };

    const pobierz = async (lat, lon, miejsce) => {
      const klucz = `pogoda:${lat.toFixed(2)},${lon.toFixed(2)}`;
      const pamiec = czytaj(klucz);
      if (pamiec && Date.now() - pamiec.t < 15 * 60 * 1000) { pokaz(pamiec.d, miejsce); return; }
      let d = null;
      try {
        const r = await fetch(`/api/pogoda.php?lat=${lat}&lon=${lon}`, { headers: { Accept: 'application/json' } });
        if (r.ok) d = await r.json();
      } catch (e) { /* brak sieci albo PHP */ }
      if ((!d || !d.ok) && /^(localhost|127\.0\.0\.1)$/.test(location.hostname)) {
        // tylko podgląd lokalny bez PHP: bezpośrednio do Open-Meteo
        try {
          const r = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code,wind_speed_10m,wind_gusts_10m,is_day&wind_speed_unit=kmh`);
          if (!r.ok) return;
          const c = (await r.json()).current;
          if (!c) return;
          d = { ok: true, temp: Math.round(c.temperature_2m), kod: c.weather_code, wiatr: Math.round(c.wind_speed_10m), porywy: Math.round(c.wind_gusts_10m), dzien: c.is_day };
        } catch (e) { return; }
      }
      if (!d || !d.ok) return;
      zapisz(klucz, { t: Date.now(), d });
      pokaz(d, miejsce);
    };

    const okolica = () => {
      const moja = czytaj('pogoda:okolica');
      if (moja) return moja;
      let strefa = '';
      try { strefa = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (e) { /* stara przeglądarka */ }
      const s = STREFY[strefa] || STREFY['Europe/Warsaw'];
      return { lat: s[0], lon: s[1], miejsce: s[2] };
    };
    const start = () => { const o = okolica(); pobierz(o.lat, o.lon, o.miejsce); };

    chip.querySelector('.pogoda-gps').addEventListener('click', () => {
      if (!navigator.geolocation) return;
      navigator.geolocation.getCurrentPosition((pos) => {
        const o = { lat: Math.round(pos.coords.latitude * 4) / 4, lon: Math.round(pos.coords.longitude * 4) / 4, miejsce: 'Twoja okolica' };
        zapisz('pogoda:okolica', o);
        pobierz(o.lat, o.lon, o.miejsce);
      }, () => {}, { maximumAge: 3600000, timeout: 10000 });
    });
    // pogoda nie blokuje pierwszego wyświetlenia strony
    if ('requestIdleCallback' in window) requestIdleCallback(start, { timeout: 2500 }); else setTimeout(start, 1200);
  })();

  // ---------- pierścień usług 3D na stronie głównej ----------
  // Płyty krążą po szerokiej elipsie; położenie każdej liczy skrypt, głębię daje perspektywa.
  // Bez JS i przy ograniczonym ruchu lista zostaje zwykłą siatką odnośników.
  let sparkAt = null; // podpina blok hero niżej: iskry, gdy płyta siada w stacji
  const ring = document.querySelector('[data-ring]');
  if (ring) {
    const stage = ring.querySelector('.ring-stage');
    const list = ring.querySelector('.ring-list');
    const items = Array.from(list.children);
    const controls = ring.querySelector('.ring-controls');
    const status = ring.querySelector('[data-ring-status]');
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)');
    const count = items.length;
    const step = 360 / count;
    const RAD = Math.PI / 180;
    const TILT = 16;         // pochylenie płaszczyzny orbity [deg]; to samo co w style.css
    const TURN = 58;         // największy obrót płyty wokół osi pionowej [deg]
    const STIFFNESS = 120;   // sprężyna dociągająca do zapadki
    const DAMPING = 17;      // poniżej 2*sqrt(120): lekki przestrzał przed zatrzymaniem
    let on = false;
    let rx = 0;              // półoś orbity w poziomie [px]
    let rz = 0;              // półoś orbity w głąb [px]
    let turn = TURN;         // obrót płyt po uwzględnieniu ciasnoty [deg]
    let angle = 0;           // bieżący obrót orbity [deg]
    let target = 0;          // zapadka, do której zmierza [deg]
    let velocity = 0;        // [deg/s]
    let frame = 0;
    let last = 0;
    let front = -1;
    let drag = null;
    let dragged = false;
    let frontAtPress = 0;
    let speak = false;
    let viewportWidth = window.innerWidth;
    let hoverFrame = 0;
    let hoverX = 0;
    let hoverY = 0;

    const mod = (value, m) => ((value % m) + m) % m;
    const indexAt = (deg) => mod(Math.round(-deg / step), count);
    const spinning = (state) => ring.classList.toggle('is-spinning', state);

    const paint = () => {
      items.forEach((item, i) => {
        const theta = (i * step + angle) * RAD;
        const sin = Math.sin(theta);
        // płyta stoi pionowo (kontra do pochylenia orbity) i odwraca się lekko na zewnątrz
        item.style.transform = `translate3d(${(rx * sin).toFixed(1)}px,0,${(rz * (Math.cos(theta) - 1)).toFixed(1)}px)`
          + ` rotateX(${TILT}deg) rotateY(${(turn * sin).toFixed(2)}deg)`;
      });
      list.style.setProperty('--ring-spin', `${angle.toFixed(2)}deg`); // impuls prądu na drucie orbity
      const now = indexAt(angle);
      if (now === front) return;
      front = now;
      items.forEach((item, i) => {
        item.dataset.d = String(Math.min(mod(i - now, count), mod(now - i, count)));
      });
    };

    const settle = () => {
      angle = target;
      velocity = 0;
      frame = 0;
      paint();
      spinning(false);
      if (!speak) return;
      speak = false;
      status.textContent = (front + 1) + ' z ' + count + ': ' + items[front].querySelector('h3').textContent;
      if (sparkAt) {
        const box = stage.getBoundingClientRect();
        sparkAt(box.left + box.width / 2, box.bottom - 12, 18, 440);
      }
    };
    const paused = () => document.documentElement.classList.contains('niebo-stop');
    const tick = (time) => {
      const dt = Math.min((time - last) / 1000, 0.032);
      last = time;
      if (drag?.captured) {
        paint();
        frame = 0;
        return;
      }
      velocity += ((target - angle) * STIFFNESS - velocity * DAMPING) * dt;
      angle += velocity * dt;
      if (paused() || (Math.abs(target - angle) < 0.03 && Math.abs(velocity) < 1)) {
        settle();
        return;
      }
      paint();
      frame = requestAnimationFrame(tick);
    };
    const run = () => {
      if (frame) return;
      if (paused()) {
        settle();
        return;
      }
      spinning(true);
      last = performance.now();
      frame = requestAnimationFrame(tick);
    };
    const halt = () => {
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
    };

    const goTo = (index) => {
      const wanted = -index * step;
      target = wanted + 360 * Math.round((angle - wanted) / 360);
      run();
    };
    const stepBy = (direction) => {
      speak = true;
      target = Math.round(target / step) * step - direction * step;
      run();
    };

    const layout = () => {
      on = !calm.matches;
      ring.classList.toggle('is-ring', on);
      controls.hidden = !on;
      if (!on) {
        halt();
        spinning(false);
        ['--ring-spin', '--px', '--py'].forEach((name) => list.style.removeProperty(name));
        items.forEach((item) => {
          item.style.transform = '';
          delete item.dataset.d;
        });
        return;
      }
      // orbita na prawie całą szerokość okna; na telefonie tak, by sąsiednie płyty wystawały zza przedniej
      const plate = list.offsetWidth;
      rx = Math.round(Math.min(Math.max(stage.clientWidth * 0.46, plate * 1.05), 760));
      rz = Math.round(Math.min(rx * 0.5, 360));
      // gdy sąsiednie płyty zachodzą za przednią, stoją płasko — obrócona krawędź przebiłaby przednią płytę
      turn = TURN * Math.max(0, Math.min(1, (rx * Math.sin(step * RAD) - plate * 0.85) / (plate * 0.25)));
      ring.style.setProperty('--ring-rx', `${rx}px`);
      ring.style.setProperty('--ring-rz', `${rz}px`);
      ring.style.setProperty('--ring-ratio', rz / rx);
      front = -1;
      paint();
    };

    controls.querySelectorAll('button').forEach((button) => {
      button.addEventListener('click', () => stepBy(Number(button.dataset.ringStep)));
    });

    ring.addEventListener('keydown', (event) => {
      if (!on || (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight')) return;
      event.preventDefault();
      const within = stage.contains(document.activeElement);
      stepBy(event.key === 'ArrowRight' ? 1 : -1);
      if (within) items[indexAt(target)].firstElementChild.focus({ preventScroll: true });
    });

    // fokus z klawiatury obraca orbitę do wskazanej płyty
    stage.addEventListener('focusin', (event) => {
      const link = event.target.closest('a');
      if (on && link) goTo(items.indexOf(link.parentElement));
    });

    stage.addEventListener('pointerdown', (event) => {
      if (!on || !event.isPrimary || event.button !== 0) return;
      frontAtPress = indexAt(target);
      dragged = false;
      drag = { id: event.pointerId, x: event.clientX, angle, lastX: event.clientX, lastT: event.timeStamp, v: 0, captured: false };
    });

    stage.addEventListener('pointermove', (event) => {
      if (!on) return;
      if (!drag || drag.id !== event.pointerId) {
        if (event.pointerType !== 'mouse' || frame || paused()) return;
        hoverX = event.clientX;
        hoverY = event.clientY;
        if (!hoverFrame) hoverFrame = requestAnimationFrame(() => {
          hoverFrame = 0;
          if (!on || frame || paused()) return;
          const area = stage.getBoundingClientRect();
          const plate = items[front].firstElementChild;
          const box = plate.getBoundingClientRect();
          list.style.setProperty('--px', ((hoverX - area.left) / area.width - 0.5).toFixed(3));
          list.style.setProperty('--py', ((hoverY - area.top) / area.height - 0.5).toFixed(3));
          plate.style.setProperty('--mx', Math.round(hoverX - box.left) + 'px');
          plate.style.setProperty('--my', Math.round(hoverY - box.top) + 'px');
        });
        return;
      }
      const dx = event.clientX - drag.x;
      if (!drag.captured) {
        if (Math.abs(dx) < 6) return;
        drag.captured = true;
        dragged = true;
        stage.setPointerCapture(event.pointerId);
        stage.classList.add('is-dragging');
        halt();
        spinning(true);
      }
      // przednia płyta idzie dokładnie za palcem
      const perPx = 180 / (Math.PI * rx);
      const dt = event.timeStamp - drag.lastT;
      if (dt > 0) drag.v = 0.7 * ((event.clientX - drag.lastX) * perPx / dt * 1000) + 0.3 * drag.v;
      drag.lastX = event.clientX;
      drag.lastT = event.timeStamp;
      angle = drag.angle + dx * perPx;
      if (!frame) frame = requestAnimationFrame(tick);
    });
    stage.addEventListener('pointerleave', () => {
      cancelAnimationFrame(hoverFrame);
      hoverFrame = 0;
      if (drag && !drag.captured) drag = null;
      list.style.removeProperty('--px');
      list.style.removeProperty('--py');
    });

    const release = (event) => {
      if (!drag || drag.id !== event.pointerId) return;
      const ended = drag;
      drag = null;
      stage.classList.remove('is-dragging');
      if (ended.captured) {
        // bezwładność: orbita dojeżdża do zapadki zgodnie z prędkością puszczenia
        velocity = event.timeStamp - ended.lastT > 80 ? 0 : Math.max(-900, Math.min(900, ended.v));
        target = Math.round((angle + velocity * 0.25) / step) * step;
        speak = true;
      }
      run();
    };
    stage.addEventListener('pointerup', release);
    stage.addEventListener('pointercancel', release);
    stage.addEventListener('lostpointercapture', release);
    stage.addEventListener('dragstart', (event) => event.preventDefault());

    stage.addEventListener('click', (event) => {
      const link = event.target.closest('a');
      if (!on || !link) return;
      const byPointer = event.detail !== 0;
      if (byPointer && dragged) {
        event.preventDefault();
        dragged = false;
        return;
      }
      const index = items.indexOf(link.parentElement);
      if (index !== (byPointer ? frontAtPress : indexAt(target))) {
        // dalsza płyta: najpierw obrót do niej, przejście dopiero po drugim kliknięciu
        event.preventDefault();
        speak = true;
        goTo(index);
        return;
      }
      // tytuł płyty przechodzi w tytuł podstrony (cross-document view transition)
      items.forEach((item) => { item.querySelector('h3').style.viewTransitionName = ''; });
      link.querySelector('h3').style.viewTransitionName = 'tytul-strony';
    });

    calm.addEventListener('change', layout);
    window.addEventListener('resize', () => {
      if (window.innerWidth === viewportWidth) return;
      viewportWidth = window.innerWidth;
      layout();
    });

    // jeden obrót wejściowy, gdy orbita pojawia się w oknie; bez autoodtwarzania
    if (!calm.matches && !paused() && 'IntersectionObserver' in window) {
      angle = 84;
      const seen = new IntersectionObserver((entries) => {
        if (!entries[0].isIntersecting) return;
        seen.disconnect();
        if (on) run();
      }, { threshold: 0.35 });
      seen.observe(stage);
    }
    layout();
  }

  // ---------- podglądy warsztatu: jedna biblioteka ładowana po wejściu w kadr ----------
  const scenes = [...document.querySelectorAll('[data-scene]')];
  if (scenes.length && 'IntersectionObserver' in window && 'ResizeObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      if (!entries.some(entry => entry.isIntersecting)) return;
      observer.disconnect();
      import(document.body.dataset.scenesModule)
        .then(({ mountStages }) => mountStages(scenes))
        .catch(() => scenes.forEach(scene => scene.classList.add('scene-unavailable')));
    }, { rootMargin: '160px' });
    scenes.forEach(scene => observer.observe(scene));
  }

  // ---------- gra: rozbrój instalację ----------
  (function () {
    const btn = document.getElementById('detonator-btn');
    const modal = document.getElementById('detonator-modal');
    if (!btn || !modal) return;
    const close = document.getElementById('detonator-close');
    const replay = document.getElementById('detonator-reset');
    const offer = document.getElementById('detonator-offer');
    const result = document.getElementById('detonator-result');
    const scene = modal.querySelector('[data-scene]');
    const wires = [...modal.querySelectorAll('[data-wire]')];
    let safeWire;

    function showRound(wire = '', success = false) {
      scene.dataset.cut = wire;
      scene.dataset.success = String(success);
      scene.dispatchEvent(new CustomEvent('warsztat:wire', { detail: { wire, success } }));
    }

    function reset() {
      safeWire = wires[Math.floor(Math.random() * wires.length)].dataset.wire;
      result.textContent = '';
      result.className = '';
      replay.hidden = true;
      offer.hidden = true;
      wires.forEach(wire => { wire.disabled = false; });
      showRound();
    }

    let previousFocus;
    function closeModal() {
      modal.classList.remove('open');
      previousFocus.focus();
    }

    [btn, ...document.querySelectorAll('[data-open-cabinet]')].forEach(opener => {
      opener.hidden = false;
      opener.addEventListener('click', () => {
        previousFocus = opener;
        reset();
        modal.classList.add('open');
        close.focus();
      });
    });
    close.addEventListener('click', closeModal);
    replay.addEventListener('click', () => {
      reset();
      wires[0].focus();
    });
    modal.addEventListener('click', (event) => { if (event.target === modal) closeModal(); });
    document.addEventListener('keydown', (event) => {
      if (!modal.classList.contains('open')) return;
      if (event.key === 'Escape') closeModal();
      if (event.key !== 'Tab') return;
      const focusable = [...modal.querySelectorAll('button:not([disabled]), a[href]')]
        .filter(el => !el.hidden);
      const first = focusable[0];
      const last = focusable.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });

    wires.forEach(button => {
      button.addEventListener('click', () => {
        const wire = button.dataset.wire;
        const success = wire === safeWire;
        wires.forEach(item => { item.disabled = true; });
        result.className = success ? 'ok' : 'fail';
        result.textContent = success
          ? 'Instalacja zabezpieczona! Odbierz 5% rabatu na diagnostykę.'
          : 'Zwarcie! Zresetuj bezpiecznik, żeby spróbować ponownie.';
        offer.hidden = !success;
        replay.hidden = false;
        showRound(wire, success);
        (success ? offer : replay).focus();
      });
    });
  })();

  // ==========================================================================
  // KONTA, KOMENTARZE, FORUM I MODERACJA — całość na backendzie /api/
  // ==========================================================================

  // ---------- 0. Warstwa wywołań API ----------
  // Sesja siedzi w ciasteczku HttpOnly (przeglądarka dokłada je sama),
  // a token CSRF w zwykłym ciasteczku — przepisujemy go do nagłówka.
  function ciasteczko(nazwa) {
    const m = document.cookie.match(new RegExp('(?:^|; )' + nazwa + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }

  async function api(sciezka, opcje = {}) {
    const { metoda = 'GET', dane = null } = opcje;
    const naglowki = {};
    if (dane) naglowki['Content-Type'] = 'application/json';
    const csrf = ciasteczko('fw_csrf');
    if (csrf) naglowki['X-FW-CSRF'] = csrf;

    let odp;
    try {
      odp = await fetch('/api' + sciezka, {
        method: metoda,
        headers: naglowki,
        credentials: 'same-origin',
        body: dane ? JSON.stringify(dane) : undefined
      });
    } catch (e) {
      throw new Error('Brak połączenia z serwerem. Sprawdź internet i spróbuj ponownie.');
    }

    let wynik;
    try {
      wynik = await odp.json();
    } catch (e) {
      throw new Error('Serwer zwrócił nieczytelną odpowiedź (kod ' + odp.status + ').');
    }
    if (!odp.ok || wynik.ok === false) {
      throw new Error(wynik.blad || 'Operacja nie powiodła się.');
    }
    return wynik;
  }

  function dataPl(tekst) {
    if (!tekst) return '';
    const d = new Date(String(tekst).replace(' ', 'T'));
    if (isNaN(d)) return String(tekst);
    return d.toLocaleDateString('pl-PL') + ' ' +
      d.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });
  }

  function komunikat(el, tekst, rodzaj) {
    if (!el) return;
    el.textContent = tekst;
    el.style.color = rodzaj === 'blad' ? 'var(--red)'
      : rodzaj === 'ok' ? 'var(--green)' : 'var(--muted)';
  }

  // Adres wątku forum. Musi dawać ten sam wynik co fw_slug_tytulu() w PHP,
  // inaczej strona wątku odesłałaby przekierowaniem na własną wersję adresu.
  const ZAMIANA_LITER = { 'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z' };

  function slugTytulu(tytul) {
    return String(tytul).toLowerCase()
      .replace(/[ąćęłńóśźż]/g, z => ZAMIANA_LITER[z])
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  function adresWatku(id, tytul) {
    const s = slugTytulu(tytul);
    return '/forum/watek/' + id + (s ? '-' + s : '') + '/';
  }

  // Znacznik "czeka na zatwierdzenie" widzi wyłącznie autor własnego wpisu.
  function plakietkaStatusu(status) {
    return status === 'oczekuje'
      ? ' <span class="badge badge-orange">czeka na zatwierdzenie</span>'
      : '';
  }

  const IKONY_KATEGORII = {
    regulamin: '📜 Regulamin',
    witam: '🤝 Witam',
    faq: '❓ FAQ',
    instrukcje: '🛠️ Instrukcje',
    ksiazkiserwisowe: '📚 Książki / DTR',
    elektro: '⚡ Elektromechanika',
    spawanie: '🔥 Spawanie & CNC',
    klimatyzacja: '❄️ Klimatyzacja',
    poczekalnia: '☕ Poczekalnia',
    general: '📢 Dyskusje Ogólne'
  };

  function plakietkaKategorii(kat) {
    const etykieta = IKONY_KATEGORII[kat] || kat;
    return `<span class="badge badge-metal">${esc(etykieta)}</span>`;
  }

  function plakietkaAutora(autor) {
    if (autor && (autor.includes('Admin') || autor.includes('F.W. DRUCIK') || autor.includes('fwdrucik'))) {
      return ' <span class="badge badge-orange" style="background:#ff5a00;color:#000;font-weight:700;font-size:0.75rem;padding:2px 6px;border-radius:4px;vertical-align:middle;">🛡️ Admin AI</span>';
    }
    return '';
  }

  // ---------- 1. Konta i sesja ----------
  window.FWAuth = {
    uzytkownik: null,

    getUser() { return this.uzytkownik; },
    czyAdmin() { return !!this.uzytkownik && this.uzytkownik.rola === 'admin'; },

    async odswiez() {
      try {
        const r = await api('/auth.php?akcja=ja');
        this.uzytkownik = r.uzytkownik;
      } catch (e) {
        this.uzytkownik = null;
      }
      this.updateUI();
      return this.uzytkownik;
    },

    async login(login, haslo) {
      const r = await api('/auth.php?akcja=logowanie', {
        metoda: 'POST', dane: { login, haslo }
      });
      this.uzytkownik = r.uzytkownik;
      this.updateUI();
      return r;
    },

    async register(nick, email, haslo, pulapka, captcha) {
      const r = await api('/auth.php?akcja=rejestracja', {
        metoda: 'POST',
        dane: {
          nick, email, haslo, firma: pulapka || '',
          captcha_id: (captcha && captcha.id) || '',
          captcha: (captcha && captcha.odpowiedz) || ''
        }
      });
      this.uzytkownik = r.uzytkownik;
      this.updateUI();
      return r;
    },

    async logout() {
      try { await api('/auth.php?akcja=wylogowanie', { metoda: 'POST' }); } catch (e) { /* i tak czyścimy stan */ }
      this.uzytkownik = null;
      window.location.href = '/';
    },

    updateUI() {
      queueMicrotask(() => document.dispatchEvent(new CustomEvent("fw-auth-change")));
      const u = this.uzytkownik;
      document.querySelectorAll('.auth-nav-link').forEach(link => {
        if (u) {
          link.href = u.rola === 'admin' ? '/admin/' : '/konto/';
          link.innerHTML = `👤 ${esc(u.nick)}${u.rola === 'admin' ? ' <span class="badge badge-orange">ADMIN</span>' : ''}`;
        } else {
          link.href = '/konto/';
          link.innerHTML = '🔑 Zaloguj / Konto';
        }
      });
      document.querySelectorAll('[data-gdy="zalogowany"]').forEach(el => {
        el.hidden = !u;
      });
      document.querySelectorAll('[data-gdy="niezalogowany"]').forEach(el => {
        el.hidden = !!u;
      });
      document.querySelectorAll('[data-pole="nick"]').forEach(el => {
        el.textContent = u ? u.nick : '';
      });
    }
  };

  // Jedno wspólne sprawdzenie sesji na start — reszta modułów na nie czeka.
  window.FWDrucik?.connect(api);
  const sesjaGotowa = FWAuth.odswiez();

  // ---------- 1b. Captcha przy rejestracji ----------
  // Kod pobieramy dopiero po przełączeniu formularza na rejestrację — przy
  // samym logowaniu nie jest potrzebny i nie ma po co obciążać serwera.
  const captchaObraz = document.getElementById('captcha-obraz');
  const captchaId = document.getElementById('auth-captcha-id');

  async function odswiezCaptche() {
    if (!captchaObraz) return;
    try {
      const r = await api('/captcha.php?akcja=nowa');
      captchaId.value = r.id;
      // Znacznik czasu wymusza pobranie nowego obrazka zamiast wersji z cache.
      captchaObraz.src = r.obraz + '&t=' + Date.now();
    } catch (e) {
      captchaObraz.alt = 'Nie udało się wczytać kodu. Odśwież stronę.';
    }
  }

  const captchaOdswiez = document.getElementById('captcha-odswiez');
  if (captchaOdswiez) captchaOdswiez.addEventListener('click', odswiezCaptche);
  window.FWCaptcha = { odswiez: odswiezCaptche };

  // ---------- 1c. Potwierdzenie adresu e-mail ----------
  // Link z wiadomości prowadzi na /konto/?potwierdz=<token>; obsługujemy go
  // tutaj, żeby użytkownik od razu zobaczył wynik na stronie konta.
  (async () => {
    const token = new URLSearchParams(location.search).get('potwierdz');
    if (!token) return;
    try {
      const r = await api('/auth.php?akcja=potwierdz-email&token=' + encodeURIComponent(token));
      alert(r.komunikat);
      await FWAuth.odswiez();
    } catch (e) {
      alert(e.message);
    }
    history.replaceState(null, '', '/konto/');
  })();

  const prosbaPotwierdz = document.getElementById('potwierdz-email-prosba');
  if (prosbaPotwierdz) {
    sesjaGotowa.then(u => {
      prosbaPotwierdz.hidden = !u || u.email_potwierdzony !== false;
    });
    const przyciskPonow = document.getElementById('wyslij-potwierdzenie');
    if (przyciskPonow) {
      przyciskPonow.addEventListener('click', async () => {
        const info = document.getElementById('potwierdzenie-komunikat');
        try {
          const r = await api('/auth.php?akcja=wyslij-potwierdzenie', { metoda: 'POST' });
          komunikat(info, r.komunikat, 'ok');
        } catch (e) {
          komunikat(info, e.message, 'blad');
        }
      });
    }
  }

  // ---------- 2. Formularz logowania i rejestracji (/konto/) ----------
  const authForm = document.getElementById('fw-auth-form');
  if (authForm) {
    let tryb = 'login';
    const tabLogin = document.getElementById('tab-login');
    const tabReg = document.getElementById('tab-register');
    const grupaNick = document.getElementById('group-name');
    const tytul = document.getElementById('auth-title');
    const notka = document.getElementById('auth-note');
    const przycisk = authForm.querySelector('button[type="submit"]');
    const polePass = document.getElementById('auth-password');

    function ustawTryb(nowy) {
      tryb = nowy;
      const rejestracja = tryb === 'register';
      if (tabLogin) tabLogin.classList.toggle('active', !rejestracja);
      if (tabReg) tabReg.classList.toggle('active', rejestracja);
      if (grupaNick) grupaNick.style.display = rejestracja ? 'block' : 'none';
      const grupaCaptcha = document.getElementById('group-captcha');
      if (grupaCaptcha) {
        grupaCaptcha.style.display = rejestracja ? 'block' : 'none';
        // Kod pobieramy dopiero przy wejsciu w rejestracje — jedno wyzwanie
        // na jedno podejscie, bo serwer zuzywa je przy pierwszym sprawdzeniu.
        if (rejestracja && window.FWCaptcha) FWCaptcha.odswiez();
      }
      if (tytul) tytul.textContent = rejestracja ? 'Zarejestruj nowe konto' : 'Zaloguj się do konta';
      if (przycisk) przycisk.textContent = rejestracja ? 'Załóż konto →' : 'Zaloguj się →';
      if (polePass) polePass.setAttribute('autocomplete', rejestracja ? 'new-password' : 'current-password');
      komunikat(notka, rejestracja ? 'Hasło musi mieć co najmniej 10 znaków.' : '', 'info');
    }

    if (tabLogin) tabLogin.addEventListener('click', () => ustawTryb('login'));
    if (tabReg) tabReg.addEventListener('click', () => ustawTryb('register'));

    authForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = (document.getElementById('auth-email') || {}).value || '';
      const haslo = (document.getElementById('auth-password') || {}).value || '';
      const nick = (document.getElementById('auth-name') || {}).value || '';
      const pulapka = (document.getElementById('auth-firma') || {}).value || '';

      if (przycisk) przycisk.disabled = true;
      komunikat(notka, 'Łączenie z serwerem...', 'info');
      try {
        const r = tryb === 'login'
          ? await FWAuth.login(email, haslo)
          : await FWAuth.register(nick, email, haslo, pulapka, {
              id: (document.getElementById('auth-captcha-id') || {}).value || '',
              odpowiedz: (document.getElementById('auth-captcha') || {}).value || ''
            });
        komunikat(notka, r.komunikat || 'Zalogowano.', 'ok');
        setTimeout(() => {
          window.location.href = FWAuth.czyAdmin() ? '/admin/' : '/forum/';
        }, 700);
      } catch (err) {
        komunikat(notka, err.message, 'blad');
        if (przycisk) przycisk.disabled = false;
        // Serwer zuzywa wyzwanie przy kazdym sprawdzeniu, takze nieudanym —
        // bez nowego obrazka kolejna proba nie mialaby szans.
        if (tryb === 'register' && window.FWCaptcha) {
          FWCaptcha.odswiez();
          const pole = document.getElementById('auth-captcha');
          if (pole) pole.value = '';
        }
      }
    });

    // Zalogowanemu nie pokazujemy formularza, tylko skrót do jego sekcji.
    sesjaGotowa.then(u => {
      if (u) {
        authForm.hidden = true;
        const tabs = document.querySelector('.auth-tabs');
        if (tabs) tabs.hidden = true;
        if (tytul) tytul.textContent = 'Jesteś zalogowany jako ' + u.nick;
        komunikat(notka, u.zaufany
          ? 'Twoje wpisy publikują się od razu.'
          : 'Twój pierwszy wpis czeka na zatwierdzenie przez moderatora.', 'info');
      }
    });
  }

  // Wylogowanie — dowolny przycisk z klasą .btn-logout
  document.querySelectorAll('.btn-logout').forEach(b => {
    b.addEventListener('click', (e) => { e.preventDefault(); FWAuth.logout(); });
  });

  // ---------- 3. Komentarze pod wpisami blogowymi ----------
  const listaKom = document.getElementById('comments-list');
  const formKom = document.getElementById('comment-form');
  if (listaKom) {
    const slug = document.body.dataset.slug || '';

    async function wczytajKomentarze() {
      listaKom.innerHTML = '<p style="color:var(--muted);font-size:0.9rem;">Wczytywanie komentarzy...</p>';
      try {
        const r = await api('/komentarze.php?akcja=lista&slug=' + encodeURIComponent(slug));
        if (!r.komentarze.length) {
          listaKom.innerHTML = '<p style="color:var(--muted);font-size:0.9rem;">Brak komentarzy. Bądź pierwszy!</p>';
          return;
        }
        listaKom.innerHTML = r.komentarze.map(k => `
          <div class="comment-card">
            <div class="comment-header">
              <span class="comment-author">👤 ${esc(k.autor)}${k.poziom ? `<span class="community-level">${esc(k.poziom.nazwa)} · ${k.poziom.gwiazdki}/5</span>` : ""}${plakietkaStatusu(k.status)}</span>
              <span class="comment-date">${esc(dataPl(k.data))}</span>
            </div>
            <p class="comment-text">${esc(k.tresc)}</p>
            ${k.odpowiedz ? `<blockquote><strong>Odpowiedź F.W. DRUCIK</strong><p class="community-pre">${esc(k.odpowiedz)}</p></blockquote>` : ""}
          </div>
        `).join('');
      } catch (err) {
        listaKom.innerHTML = '<p style="color:var(--red);font-size:0.9rem;">Nie udało się wczytać komentarzy: '
          + esc(err.message) + '</p>';
      }
    }
    wczytajKomentarze();

    if (formKom) {
      const notkaKom = document.getElementById('comment-note');
      const przyciskKom = formKom.querySelector('button[type="submit"]');

      sesjaGotowa.then(u => {
        if (!u) {
          komunikat(notkaKom, 'Aby dodać komentarz, zaloguj się na konto.', 'info');
          if (przyciskKom) przyciskKom.disabled = true;
        }
      });

      formKom.addEventListener('submit', async (e) => {
        e.preventDefault();
        const pole = document.getElementById('comment-text');
        const tresc = (pole.value || '').trim();
        if (!tresc) return;
        if (przyciskKom) przyciskKom.disabled = true;
        komunikat(notkaKom, 'Wysyłanie...', 'info');
        try {
          const r = await api('/komentarze.php?akcja=dodaj', {
            metoda: 'POST', dane: { slug, tresc }
          });
          pole.value = '';
          komunikat(notkaKom, r.komunikat, 'ok');
          await wczytajKomentarze();
        } catch (err) {
          komunikat(notkaKom, err.message, 'blad');
        }
        if (przyciskKom) przyciskKom.disabled = false;
      });
    }
  }

  // ---------- 4. Forum (/forum/) ----------
  const forumApp = document.getElementById('forum-app');
  if (forumApp) {
    const widokLista = document.getElementById('forum-lista');
    const widokWatek = document.getElementById('forum-watek');
    const listaWatkow = document.getElementById('threads-list');
    const notkaForum = document.getElementById('forum-note');
    let kategoria = 'all';

    function idZAdresu() {
      const v = new URLSearchParams(window.location.search).get('watek');
      return /^\d+$/.test(v || '') ? v : null;
    }

    // --- lista wątków ---
    async function wczytajWatki() {
      if (!listaWatkow) return;
      listaWatkow.innerHTML = '<p style="color:var(--muted);">Wczytywanie wątków...</p>';
      try {
        const r = await api('/forum.php?akcja=watki&kategoria=' + encodeURIComponent(kategoria));
        if (!r.watki.length) {
          listaWatkow.innerHTML = '<p style="color:var(--muted);">W tym dziale nie ma jeszcze wątków. Załóż pierwszy.</p>';
          return;
        }
        listaWatkow.innerHTML = r.watki.map(t => `
          <div class="forum-thread-item">
            <div class="forum-thread-main">
              <h3 class="forum-thread-title"><a href="${adresWatku(t.id, t.tytul)}">${esc(t.tytul)}</a>${plakietkaStatusu(t.status)}</h3>
              <div class="forum-thread-meta">
                <span>👤 ${esc(t.autor)}<span class="community-level" data-author-id="${Number(t.autor_id)||0}"></span>${plakietkaAutora(t.autor)}</span>
                <span>📅 ${esc(dataPl(t.data))}</span>
                ${plakietkaKategorii(t.kategoria)}
              </div>
            </div>
            <div class="forum-thread-stats">
              <div><b>${t.odpowiedzi}</b> odp.</div>
              <div><b>${t.wyswietlenia}</b> wyśw.</div>
            </div>
          </div>
        `).join('');
      } catch (err) {
        listaWatkow.innerHTML = '<p style="color:var(--red);">Nie udało się wczytać forum: ' + esc(err.message) + '</p>';
      }
    }

    // --- pojedynczy wątek ---
    async function wczytajWatek(id) {
      if (!widokWatek) return;
      if (widokLista) widokLista.hidden = true;
      widokWatek.hidden = false;
      widokWatek.innerHTML = '<p style="color:var(--muted);">Wczytywanie wątku...</p>';
      try {
        const r = await api('/forum.php?akcja=watek&id=' + encodeURIComponent(id));
        const w = r.watek;
        const odpowiedzi = r.odpowiedzi.map(o => `
          <div class="comment-card">
            <div class="comment-header">
              <span class="comment-author">👤 ${esc(o.autor)}<span class="community-level" data-author-id="${Number(o.autor_id)||0}"></span>${plakietkaAutora(o.autor)}${plakietkaStatusu(o.status)}</span>
              <span class="comment-date">${esc(dataPl(o.data))}</span>
            </div>
            <p class="comment-text">${esc(o.tresc)}</p>
          </div>
        `).join('') || '<p style="color:var(--muted);font-size:0.9rem;">Brak odpowiedzi. Odpowiedz jako pierwszy.</p>';

        widokWatek.innerHTML = `
          <p><a href="/forum/" class="btn btn-outline">← Wróć do listy wątków</a></p>
          <article class="forum-thread-view">
            <h2 style="color:#fff;margin:16px 0 8px;">${esc(w.tytul)}${plakietkaStatusu(w.status)}</h2>
            <div class="forum-thread-meta" style="margin-bottom:16px;">
              <span>👤 ${esc(w.autor)}<span class="community-level" data-author-id="${Number(w.autor_id)||0}"></span>${plakietkaAutora(w.autor)}</span>
              <span>📅 ${esc(dataPl(w.data))}</span>
              ${plakietkaKategorii(w.kategoria)}
              <span>${w.wyswietlenia} wyśw.</span>
            </div>
            <p class="comment-text" style="white-space:pre-wrap;">${esc(w.tresc)}</p>
          </article>
          <h3 style="color:#fff;margin:28px 0 12px;">Odpowiedzi</h3>
          <div id="watek-odpowiedzi">${odpowiedzi}</div>
          <form id="reply-form" style="margin-top:24px;">
            <div style="margin-bottom:12px;">
              <textarea id="reply-text" class="form-control" rows="4"
                placeholder="Napisz odpowiedź..." required></textarea>
            </div>
            <div id="reply-note" style="font-size:0.9rem;margin-bottom:10px;"></div>
            <button type="submit" class="btn btn-primary">Wyślij odpowiedź</button>
          </form>
        `;

        const formOdp = document.getElementById('reply-form');
        const notkaOdp = document.getElementById('reply-note');
        const przyciskOdp = formOdp.querySelector('button[type="submit"]');
        if (!FWAuth.getUser()) {
          komunikat(notkaOdp, 'Aby odpowiedzieć, zaloguj się na konto.', 'info');
          przyciskOdp.disabled = true;
        }
        formOdp.addEventListener('submit', async (e) => {
          e.preventDefault();
          const tresc = (document.getElementById('reply-text').value || '').trim();
          if (!tresc) return;
          przyciskOdp.disabled = true;
          komunikat(notkaOdp, 'Wysyłanie...', 'info');
          try {
            await api('/forum.php?akcja=odpowiedz', {
              metoda: 'POST', dane: { watek_id: Number(id), tresc }
            });
            await wczytajWatek(id);
          } catch (err) {
            komunikat(notkaOdp, err.message, 'blad');
            przyciskOdp.disabled = false;
          }
        });
      } catch (err) {
        widokWatek.innerHTML = '<p><a href="/forum/" class="btn btn-outline">← Wróć do listy wątków</a></p>'
          + '<p style="color:var(--red);margin-top:16px;">' + esc(err.message) + '</p>';
      }
    }

    // --- odpowiedź na stronie wątku renderowanej po stronie serwera ---
    // Ta strona jest zwykłym HTML-em z PHP, więc formularz trzeba podpiąć tutaj.
    // Po dodaniu odpowiedzi przeładowujemy stronę: nowa treść ma przyjść
    // z serwera, żeby to samo widzieli wyszukiwarka i czytelnik.
    const watekSerwerowy = document.getElementById('watek-serwerowy');
    if (watekSerwerowy) {
      const formSerwer = document.getElementById('watek-odpowiedz-form');
      const infoSerwer = document.getElementById('watek-odpowiedz-info');
      const polaSerwer = document.getElementById('watek-odpowiedz');
      if (formSerwer) {
        formSerwer.addEventListener('submit', async (e) => {
          e.preventDefault();
          const tresc = (polaSerwer.value || '').trim();
          if (!tresc) return;
          const przycisk = formSerwer.querySelector('button[type="submit"]');
          przycisk.disabled = true;
          komunikat(infoSerwer, 'Wysyłanie...', 'info');
          try {
            const r = await api('/forum.php?akcja=odpowiedz', {
              metoda: 'POST',
              dane: { watek_id: Number(watekSerwerowy.dataset.watekId), tresc }
            });
            if (r.status === 'opublikowany') {
              window.location.reload();
              return;
            }
            polaSerwer.value = '';
            komunikat(infoSerwer, r.komunikat || 'Odpowiedź czeka na zatwierdzenie.', 'ok');
            przycisk.disabled = false;
          } catch (err) {
            komunikat(infoSerwer, err.message, 'blad');
            przycisk.disabled = false;
          }
        });
      }
    }

    // --- filtrowanie kategorii ---
    document.querySelectorAll('.forum-cat-card').forEach(card => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.forum-cat-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        kategoria = card.dataset.cat || 'all';
        wczytajWatki();
      });
    });

    // --- nowy wątek ---
    const formWatek = document.getElementById('new-thread-form');
    if (formWatek) {
      const przyciskWatek = formWatek.querySelector('button[type="submit"]');
      sesjaGotowa.then(u => {
        if (!u) {
          komunikat(notkaForum, 'Aby założyć wątek, zaloguj się na konto.', 'info');
          if (przyciskWatek) przyciskWatek.disabled = true;
        }
      });

      formWatek.addEventListener('submit', async (e) => {
        e.preventDefault();
        const tytul = (document.getElementById('thread-title').value || '').trim();
        const tresc = (document.getElementById('thread-text').value || '').trim();
        const kat = document.getElementById('thread-cat').value;
        if (przyciskWatek) przyciskWatek.disabled = true;
        komunikat(notkaForum, 'Wysyłanie...', 'info');
        try {
          const r = await api('/forum.php?akcja=nowy-watek', {
            metoda: 'POST', dane: { tytul, tresc, kategoria: kat }
          });
          document.getElementById('thread-title').value = '';
          document.getElementById('thread-text').value = '';
          komunikat(notkaForum, r.komunikat, 'ok');
          await wczytajWatki();
        } catch (err) {
          komunikat(notkaForum, err.message, 'blad');
        }
        if (przyciskWatek) przyciskWatek.disabled = false;
      });
    }

    // Adres /forum/?kat=elektro otwiera od razu wybrany dział. Linki z artykułów
    // prowadzą w konkretne miejsce forum zamiast wysypywać czytelnika na listę
    // wszystkich wątków, w której musi szukać swojego tematu od nowa.
    const zadanaKat = new URLSearchParams(window.location.search).get('kat');
    if (zadanaKat) {
      const karta = document.querySelector(`.forum-cat-card[data-cat="${zadanaKat}"]`);
      if (karta) {
        document.querySelectorAll('.forum-cat-card').forEach(c => c.classList.remove('active'));
        karta.classList.add('active');
        kategoria = zadanaKat;
      }
    }

    // Widok zależy od adresu: /forum/ = lista, /forum/?watek=12 = jeden wątek.
    sesjaGotowa.then(() => {
      const id = idZAdresu();
      if (id) wczytajWatek(id); else wczytajWatki();
    });
  }

  // ---------- 5. Panel administratora (/admin/) ----------
  const adminApp = document.getElementById('admin-app');
  if (adminApp) {
    const bramka = document.getElementById('admin-gate-login');
    const pulpit = document.getElementById('admin-dashboard-content');
    const listaKolejki = document.getElementById('mod-kolejka');
    const listaKont = document.getElementById('mod-uzytkownicy');
    const licznik = document.getElementById('mod-licznik');

    function pokazPulpit(czy) {
      if (bramka) bramka.style.display = czy ? 'none' : 'block';
      if (pulpit) pulpit.style.display = czy ? 'grid' : 'none';
    }

    async function wczytajKolejke() {
      if (!listaKolejki) return;
      listaKolejki.innerHTML = '<p style="color:var(--muted);">Wczytywanie kolejki...</p>';
      try {
        const r = await api('/moderacja.php?akcja=kolejka');
        if (licznik) licznik.textContent = String(r.ile);
        if (!r.kolejka.length) {
          listaKolejki.innerHTML = '<p style="color:var(--green);">Kolejka pusta — nic nie czeka na decyzję.</p>';
          return;
        }
        listaKolejki.innerHTML = r.kolejka.map(p => {
          // Wpis blogowy leży już na serwerze jako szkic, więc zamiast
          // suchego kontekstu dostaje link do podglądu całego artykułu.
          const wpis = p.typ === 'wpis';
          const kontekst = wpis
            ? `<a href="${esc(p.podglad)}" target="_blank" rel="noopener">🔍 Podgląd szkicu: ${esc(p.podglad)}</a>`
              + (p.run_url ? ` · <a href="${esc(p.run_url)}" target="_blank" rel="noopener nofollow">przebieg agenta</a>` : '')
            : esc(p.kontekst);
          return `
          <div class="comment-card" data-typ="${esc(p.typ)}" data-id="${p.id}">
            <div class="comment-header">
              <span class="comment-author">${wpis ? '🤖' : '👤'} ${esc(p.autor)} <span class="badge ${wpis ? 'badge-orange' : 'badge-metal'}">${esc(p.typ)}</span></span>
              <span class="comment-date">${esc(dataPl(p.data))}</span>
            </div>
            <p style="color:var(--metal-light);font-weight:600;margin:6px 0;">${esc(p.naglowek)}</p>
            <p class="comment-text" style="white-space:pre-wrap;">${esc(p.tresc)}</p>
            <p style="font-size:0.8rem;color:var(--muted);">${kontekst}</p>
            ${p.notatka ? `<p style="font-size:0.82rem;color:var(--metal-light);background:rgba(255,255,255,0.05);border-left:3px solid var(--orange);padding:8px 10px;margin:8px 0 0;">🧪 <strong>Agent kontroli:</strong> ${esc(p.notatka)}</p>` : ''}
            <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;">
              <button class="btn btn-primary mod-akcja" data-akcja="zatwierdz">${wpis ? '✅ Publikuj' : '✅ Zatwierdź'}</button>
              <button class="btn btn-outline mod-akcja" data-akcja="odrzuc">${wpis ? '🚫 Odrzuć i skasuj' : '🚫 Odrzuć'}</button>
              ${wpis ? '' : '<button class="btn btn-outline mod-akcja" data-akcja="usun">🗑️ Usuń</button>'}
            </div>
          </div>
        `;
        }).join('');
      } catch (err) {
        listaKolejki.innerHTML = '<p style="color:var(--red);">' + esc(err.message) + '</p>';
      }
    }

    async function wczytajKonta() {
      if (!listaKont) return;
      listaKont.innerHTML = '<p style="color:var(--muted);">Wczytywanie kont...</p>';
      try {
        const r = await api('/moderacja.php?akcja=uzytkownicy');
        listaKont.innerHTML = r.uzytkownicy.map(u => `
          <div class="comment-card" data-konto="${u.id}">
            <div class="comment-header">
              <span class="comment-author">👤 ${esc(u.nick)}
                ${u.rola === 'admin' ? '<span class="badge badge-orange">ADMIN</span>' : ''}
                ${u.zaufany ? '<span class="badge badge-green">zaufany</span>' : ''}
                ${u.zablokowany ? '<span class="badge badge-red">zablokowany</span>' : ''}
              </span>
              <span class="comment-date">${esc(dataPl(u.utworzony))}</span>
            </div>
            <p style="font-size:0.85rem;color:var(--muted);margin:4px 0 10px;">${esc(u.email)}</p>
            ${u.rola === 'admin' ? '' : `
              <button class="btn btn-outline konto-blokada" data-zablokuj="${u.zablokowany ? '0' : '1'}">
                ${u.zablokowany ? '🔓 Odblokuj konto' : '🔒 Zablokuj konto'}
              </button>`}
          </div>
        `).join('');
      } catch (err) {
        listaKont.innerHTML = '<p style="color:var(--red);">' + esc(err.message) + '</p>';
      }
    }

    // Obsługa klików w obu listach — jedna delegacja zamiast setek nasłuchów.
    adminApp.addEventListener('click', async (e) => {
      const przyciskMod = e.target.closest('.mod-akcja');
      if (przyciskMod) {
        const karta = przyciskMod.closest('[data-typ]');
        const akcja = przyciskMod.dataset.akcja;
        if (akcja === 'usun' && !window.confirm('Usunąć tę treść bezpowrotnie?')) return;
        if (karta.dataset.typ === 'wpis' && akcja === 'odrzuc'
            && !window.confirm('Odrzucić wpis? Zniknie z repozytorium i z serwera.')) return;
        przyciskMod.disabled = true;
        try {
          const odp = await api('/moderacja.php?akcja=' + akcja, {
            metoda: 'POST',
            dane: { typ: karta.dataset.typ, id: Number(karta.dataset.id) }
          });
          // Decyzja o wpisie nie kończy się od razu — publikację robi
          // workflow w tle, więc admin musi wiedzieć, czy w ogóle ruszył.
          if (karta.dataset.typ === 'wpis') {
            window.alert(odp.ostrzezenie ? odp.komunikat + '\n\n' + odp.ostrzezenie : odp.komunikat);
          }
          await wczytajKolejke();
        } catch (err) {
          window.alert(err.message);
          przyciskMod.disabled = false;
        }
        return;
      }

      const przyciskKonto = e.target.closest('.konto-blokada');
      if (przyciskKonto) {
        const karta = przyciskKonto.closest('[data-konto]');
        przyciskKonto.disabled = true;
        try {
          await api('/moderacja.php?akcja=blokuj', {
            metoda: 'POST',
            dane: { id: Number(karta.dataset.konto), zablokowany: przyciskKonto.dataset.zablokuj }
          });
          await wczytajKonta();
        } catch (err) {
          window.alert(err.message);
          przyciskKonto.disabled = false;
        }
      }
    });

    // Bramka logowania admina — autoryzacja zapada po stronie serwera.
    const formAdmin = document.getElementById('admin-login-form');
    if (formAdmin) {
      const notkaAdmin = document.getElementById('admin-login-note');
      formAdmin.addEventListener('submit', async (e) => {
        e.preventDefault();
        const login = document.getElementById('admin-login').value;
        const haslo = document.getElementById('admin-password').value;
        komunikat(notkaAdmin, 'Sprawdzanie...', 'info');
        try {
          await FWAuth.login(login, haslo);
          if (!FWAuth.czyAdmin()) {
            komunikat(notkaAdmin, 'To konto nie ma uprawnień administratora.', 'blad');
            return;
          }
          komunikat(notkaAdmin, 'Zalogowano.', 'ok');
          pokazPulpit(true);
          wczytajKolejke();
          wczytajKonta();
        } catch (err) {
          komunikat(notkaAdmin, err.message, 'blad');
        }
      });
    }

    // --- Treści na stronie: edycja, ukrywanie, usuwanie ---
    const listaTresci = document.getElementById('tresci-lista');
    const typTresci = document.getElementById('tresci-typ');
    const szukajTresci = document.getElementById('tresci-szukaj');
    let tresci = [];

    async function wczytajTresci() {
      if (!listaTresci) return;
      listaTresci.innerHTML = '<p style="color:var(--muted);">Wczytywanie...</p>';
      try {
        const r = await api('/moderacja.php?akcja=tresci&typ=' + encodeURIComponent(typ())
          + '&szukaj=' + encodeURIComponent(szukajTresci.value.trim()));
        tresci = r.pozycje;
      } catch (err) {
        listaTresci.innerHTML = '<p style="color:var(--red);">' + esc(err.message) + '</p>';
        return;
      }
      if (!tresci.length) {
        listaTresci.innerHTML = '<p style="color:var(--muted);">Nic nie znaleziono.</p>';
        return;
      }
      listaTresci.innerHTML = tresci.map((t, i) => {
        const link = t.watek_id ? adresWatku(t.watek_id, t.watek_tytul) : t.link;
        const ukryty = t.status !== 'opublikowany';
        return `
        <div class="comment-card" data-tresc="${i}">
          <div class="comment-header">
            <span class="comment-author">${t.autor ? '👤 ' + esc(t.autor) : '📰'}
              <span class="badge ${ukryty ? 'badge-red' : 'badge-green'}">${esc(t.status)}</span></span>
            <span class="comment-date">${esc(dataPl(t.data))}</span>
          </div>
          <p style="color:var(--metal-light);font-weight:600;margin:6px 0;">${esc(t.naglowek)}</p>
          ${t.tresc ? `<p class="comment-text" style="white-space:pre-wrap;max-height:9em;overflow:hidden;">${esc(t.tresc)}</p>` : ''}
          <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;">
            ${link && !(ukryty && typ() !== 'wpis') ? `<a class="btn btn-outline" href="${esc(link)}" target="_blank" rel="noopener">↗ Otwórz</a>` : ''}
            ${typ() === 'wpis'
              ? (t.edycja ? `<a class="btn btn-outline" href="${esc(t.edycja)}" target="_blank" rel="noopener">✏️ Edytuj (GitHub)</a>` : '')
              : '<button class="btn btn-outline tresc-akcja" data-akcja="edytuj">✏️ Edytuj</button>'}
            <button class="btn btn-outline tresc-akcja" data-akcja="${ukryty ? 'przywroc' : 'ukryj'}">${ukryty ? '👁️ Przywróć' : '🙈 Ukryj (prywatne)'}</button>
            <button class="btn btn-outline tresc-akcja" data-akcja="usun">🗑️ Usuń</button>
          </div>
        </div>`;
      }).join('');
    }

    const typ = () => typTresci.value;

    if (listaTresci) {
      typTresci.addEventListener('change', wczytajTresci);
      let zwloka;
      szukajTresci.addEventListener('input', () => {
        clearTimeout(zwloka);
        zwloka = setTimeout(wczytajTresci, 350);
      });

      listaTresci.addEventListener('click', async (e) => {
        const btn = e.target.closest('.tresc-akcja');
        if (!btn) return;
        const karta = btn.closest('[data-tresc]');
        const t = tresci[Number(karta.dataset.tresc)];
        const akcja = btn.dataset.akcja;
        const wpis = typ() === 'wpis';
        const cel = wpis ? { typ: 'wpis', slug: t.id } : { typ: typ(), id: t.id };

        if (akcja === 'edytuj') {
          // Edycja w miejscu karty — tytuł tylko dla wątku, reszta to sama treść.
          karta.innerHTML = `
            ${typ() === 'watek' ? `<input class="form-control" data-pole="tytul" maxlength="160" value="${esc(t.naglowek)}" style="margin-bottom:8px;">` : ''}
            <textarea class="form-control" data-pole="tresc" rows="8">${esc(t.tresc)}</textarea>
            <div style="display:flex;gap:8px;margin-top:10px;align-items:center;flex-wrap:wrap;">
              <button class="btn btn-primary tresc-zapisz">Zapisz</button>
              <button class="btn btn-outline tresc-anuluj">Anuluj</button>
              <span class="komunikat"></span>
            </div>`;
          karta.querySelector('.tresc-anuluj').addEventListener('click', wczytajTresci);
          karta.querySelector('.tresc-zapisz').addEventListener('click', async () => {
            const pole = karta.querySelector('[data-pole="tytul"]');
            try {
              await api('/moderacja.php?akcja=edytuj', {
                metoda: 'POST',
                dane: { ...cel, tresc: karta.querySelector('[data-pole="tresc"]').value,
                        tytul: pole ? pole.value : '' }
              });
              await wczytajTresci();
            } catch (err) {
              komunikat(karta.querySelector('.komunikat'), err.message, 'blad');
            }
          });
          return;
        }

        if (akcja === 'usun' && !window.confirm(wpis
          ? 'Usunąć wpis bloga bezpowrotnie? Zniknie z repozytorium i z serwera.\nJeśli chcesz tylko schować — użyj „Ukryj".'
          : 'Usunąć tę treść bezpowrotnie?\nJeśli chcesz tylko schować — użyj „Ukryj".')) return;

        btn.disabled = true;
        try {
          const odp = await api('/moderacja.php?akcja=' + akcja, { metoda: 'POST', dane: cel });
          if (wpis) window.alert(odp.ostrzezenie ? odp.komunikat + '\n\n' + odp.ostrzezenie : odp.komunikat);
          await wczytajTresci();
        } catch (err) {
          window.alert(err.message);
          btn.disabled = false;
        }
      });
    }

    sesjaGotowa.then(() => {
      const admin = FWAuth.czyAdmin();
      pokazPulpit(admin);
      if (admin) { wczytajKolejke(); wczytajKonta(); wczytajTresci(); }
    });
  }

  // ---------- 6. Pasek administratora na stronie wątku forum ----------
  // Strona wątku jest publiczna i cache'owana, więc przyciski dokłada JS
  // dopiero po sprawdzeniu sesji. Uprawnienia i tak weryfikuje serwer.
  const watekSerwerowy = document.getElementById('watek-serwerowy');
  if (watekSerwerowy) {
    sesjaGotowa.then(() => {
      if (!FWAuth.czyAdmin()) return;
      const watekId = Number(watekSerwerowy.dataset.watekId);
      const pasek = (typ, id, etykieta) => {
        const el = document.createElement('div');
        el.className = 'admin-pasek';
        el.style.cssText = 'display:flex;gap:6px;flex-wrap:wrap;margin:8px 0;';
        el.innerHTML = `<span class="badge badge-orange">ADMIN · ${etykieta}</span>
          <button class="btn btn-outline" data-akcja="edytuj">✏️ Edytuj</button>
          <button class="btn btn-outline" data-akcja="ukryj">🙈 Ukryj</button>
          <button class="btn btn-outline" data-akcja="usun">🗑️ Usuń</button>`;
        el.addEventListener('click', async (e) => {
          const btn = e.target.closest('button');
          if (!btn) return;
          const akcja = btn.dataset.akcja;
          if (akcja === 'edytuj') {
            // Edycja w miejscu. Tekst z akapitów odtwarza oryginał: serwer
            // zamienia puste linie na <p>, a pojedyncze na <br>.
            const blok = typ === 'watek'
              ? document.querySelector('.watek-tresc')
              : document.querySelector('#odp-' + id + ' .watek-odp-tresc');
            const naglowek = document.querySelector('.watek-glowa h1');
            const tekst = Array.from(blok.querySelectorAll('p')).map(p => p.innerText).join('\n\n');
            blok.innerHTML = `
              ${typ === 'watek' ? `<input class="form-control" maxlength="160" value="${esc(naglowek.textContent)}" style="margin-bottom:8px;">` : ''}
              <textarea class="form-control" rows="10">${esc(tekst)}</textarea>
              <button class="btn btn-primary" style="margin-top:8px;">Zapisz</button>
              <span class="komunikat"></span>`;
            blok.querySelector('.btn-primary').addEventListener('click', async () => {
              try {
                await api('/moderacja.php?akcja=edytuj', {
                  metoda: 'POST',
                  dane: { typ, id, tresc: blok.querySelector('textarea').value,
                          tytul: blok.querySelector('input')?.value || '' }
                });
                // Zmiana tytułu zmienia adres wątku — strona sama przekieruje.
                window.location.reload();
              } catch (err) {
                komunikat(blok.querySelector('.komunikat'), err.message, 'blad');
              }
            });
            return;
          }
          if (akcja === 'usun' && !window.confirm('Usunąć bezpowrotnie? „Ukryj" tylko chowa.')) return;
          try {
            await api('/moderacja.php?akcja=' + akcja, { metoda: 'POST', dane: { typ, id } });
            if (typ === 'watek') window.location.href = '/forum/';
            else document.getElementById('odp-' + id)?.remove();
          } catch (err) {
            window.alert(err.message);
          }
        });
        return el;
      };
      document.querySelector('.watek-glowa')?.append(pasek('watek', watekId, 'wątek'));
      document.querySelectorAll('.watek-odpowiedzi > li[id^="odp-"]').forEach(li => {
        li.append(pasek('odpowiedz', Number(li.id.slice(4)), 'odpowiedź'));
      });
    });
  }
});
