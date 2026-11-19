(() => {
  'use strict';
  const scenes = {
    glowa: ['Drapie się po głowie', ''],
    spacer: ['Przechadza się', ''],
    czysci: ['Czyści ekran', '<rect x="7" y="10" width="44" height="44" rx="7" fill="#92e3ed" fill-opacity=".26" stroke="#86edfa"/><path class="drucik-efekt" d="M13 39L40 16M20 46L46 25" stroke="#dbfffc" stroke-width="5" stroke-linecap="round"/>'],
    puka: ['Puka w ekran', '<circle cx="33" cy="26" r="5" fill="#f9cc7b"/><g class="drucik-efekt" fill="none" stroke="#f9cc7b" stroke-width="2"><circle cx="33" cy="26" r="11"/><circle cx="33" cy="26" r="19"/></g>'],
    spawa: ['Spawa stal', '<path d="M8 44h35v10H8zM25 20h10v24H25z" fill="#697a90" stroke="#bbccdd"/><path d="M30 43h13" stroke="#ffc677" stroke-width="3"/><path class="drucik-efekt" d="M40 43l12-15m-11 14l15 1m-16 1l9 10m-10-12l-2-14" stroke="#ffcb73" stroke-width="2"/>'],
    tnie: ['Przecina blachę', '<path d="M6 43h50v11H6z" fill="#748396" stroke="#ced8e1"/><path d="M30 42v13" stroke="#141d2d" stroke-width="2"/><circle cx="30" cy="31" r="13" fill="#263d58" stroke="#b8cbe3" stroke-width="3" stroke-dasharray="4 2"/><path class="drucik-efekt" d="M35 42l14-9m-15 10l20 1m-18 1l12 9" stroke="#ff974f" stroke-width="2"/>'],
    silnik: ['Naprawia silnik', '<path d="M10 30h8v-7h25v7h9v21H12V41H7V30z" fill="#697a90" stroke="#bdccdc" stroke-width="2"/><path d="M24 27v18m8-18v18m8-18v18" stroke="#253449" stroke-width="3"/><path class="drucik-efekt" d="M46 10l-4 9-8 4-4 8 4 3 7-4 4-9 9-4 3-8-7 5z" fill="#e7b75f"/>'],
    elektronika: ['Naprawia elektronikę', '<rect x="8" y="19" width="49" height="36" rx="4" fill="#17604b" stroke="#8ee8aa"/><path d="M12 28h16v15h21m-35 6h14m5-20h15" fill="none" stroke="#b6df84" stroke-width="2"/><rect x="30" y="31" width="15" height="11" rx="2" fill="#172337"/><path class="drucik-efekt" d="M52 9L39 35" stroke="#f6bb66" stroke-width="4"/><circle cx="39" cy="35" r="2" fill="#fff4b6"/>']
  };
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const current = new WeakMap();
  const defaults = () => ({ imie: 'Drucik', kolor: 'mosiadz', paliwo: 'diesel', energia: 72, kroki: [] });
  let request;
  let owner = 0;
  let load = Promise.resolve({ wersja: 0, profil: null });
  let profile = defaults();
  let next = 0;

  function apply(element, profile) {
    const p = profile || defaults();
    element.dataset.kolor = p.kolor;
    const trigger = element.querySelector('#assistant-launch');
    if (trigger) {
      const label = 'Zapytaj: ' + p.imie + ' · AI';
      trigger.setAttribute('aria-label', label);
      trigger.querySelector('.robot-etykieta').textContent = label;
    }
  }

  function show(element, action) {
    const scene = scenes[action];
    if (!scene) return Promise.resolve();
    const stamp = Symbol();
    current.set(element, stamp);
    let prop = element.querySelector('.drucik-rekwizyt');
    if (!prop) {
      prop = document.createElement('div');
      prop.className = 'drucik-rekwizyt';
      prop.setAttribute('aria-hidden', 'true');
      element.append(prop);
    }
    prop.innerHTML = scene[1] ? '<svg viewBox="0 0 64 64" aria-hidden="true">' + scene[1] + '</svg>' : '';
    delete element.dataset.czynnosc;
    const paused = motion.matches || document.documentElement.classList.contains('niebo-stop');
    if (!paused) {
      // Kolejne identyczne polecenie ma uruchomić pełny gest.
      void element.offsetWidth;
      element.dataset.czynnosc = action;
    }
    return new Promise((resolve) => setTimeout(() => {
      if (current.get(element) === stamp) {
        prop.replaceChildren();
        delete element.dataset.czynnosc;
        current.delete(element);
      }
      resolve();
    }, paused ? 700 : 1750));
  }

  function publish(saved) {
    profile = saved || defaults();
    next = 0;
    const floating = document.querySelector('.robot-scena');
    if (floating) apply(floating, profile);
  }

  window.FWDrucik = {
    scenes, defaults, apply, show,
    connect(api) { request = api; },
    load() { return load; },
    nextAction() {
      return profile.kroki.length ? profile.kroki[next++ % profile.kroki.length] : null;
    },
    async save(data) {
      const id = owner;
      if (!id || !request) throw new Error('Zaloguj się, aby zapisać Drucika.');
      const record = await request('/drucik.php', { metoda: 'POST', dane: data });
      if (owner !== id) throw new Error('Konto zmieniło się w trakcie zapisu.');
      load = Promise.resolve(record);
      publish(record.profil);
      return record;
    }
  };

  document.addEventListener('fw-auth-change', () => {
    const id = window.FWAuth?.getUser()?.id || 0;
    if (owner === id) return;
    owner = id;
    publish(null);
    load = id && request ? request('/drucik.php') : Promise.resolve({ wersja: 0, profil: null });
    load.then((record) => { if (owner === id) publish(record.profil); }, () => {});
  });
})();
