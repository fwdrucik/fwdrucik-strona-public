/* Reviews, moderation and account reputation. User content is escaped before markup. */
(() => {
  'use strict';
  const $ = (s, r=document) => r.querySelector(s);
  const esc = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const stars = n => '★'.repeat(Math.max(0,Math.min(5,Number(n)||0)))+'☆'.repeat(Math.max(0,5-Math.min(5,Number(n)||0)));
  let user=null;
  async function api(action, data, query='') {
    const headers={}; if(data) { headers['Content-Type']='application/json'; headers['X-FW-CSRF']=decodeURIComponent((document.cookie.match(/(?:^|; )fw_csrf=([^;]*)/)||[])[1]||''); }
    const response=await fetch('/api/spolecznosc.php?akcja='+action+query,{method:data?'POST':'GET',credentials:'same-origin',headers,body:data?JSON.stringify(data):undefined,signal:AbortSignal.timeout(15000)});
    const r=await response.json();if(!response.ok||!r.ok){const error=new Error(r.komunikat||r.blad||'Nie udało się zapisać. Spróbuj ponownie.');error.status=response.status;throw error;}return r;
  }
  function note(el, text, bad=false) {if(el){el.textContent=text;el.classList.toggle('community-error',bad);}}
  const reviews=$('#opinie'); let page=1; let preview=reviews?.dataset.preview==='true';
  async function loadReviews() {
    if(!reviews)return;
    const subject=$('[name="przedmiot"]',reviews).value;
    const out=$('.review-list',reviews), status=$('.review-summary',reviews);
    try {
      const r=await api('lista',null,'&przedmiot='+subject+'&page='+page);
      note(status,r.liczba?`${r.srednia.toFixed(1)} / 5 · ${r.liczba} opinii`:'Nie ma jeszcze ocen. Podziel się swoją opinią.');
      out.innerHTML=(preview?r.opinie.slice(0,3):r.opinie).map(o=>`<article class="review-card"><header><strong>${esc(o.autor)}</strong><span class="review-stars" aria-label="Ocena ${o.ocena} na 5">${stars(o.ocena)}</span></header><small>${esc(o.data.slice(0,10))} · ${esc(o.poziom.nazwa)} — poziom ${o.poziom.gwiazdki}/5${o.potwierdzony_zakup?' · Potwierdzony zakup':''}</small><p class="community-pre">${esc(o.tresc)}</p>${o.odpowiedz?`<blockquote><strong>Odpowiedź F.W. DRUCIK</strong><p class="community-pre">${esc(o.odpowiedz)}</p></blockquote>`:''}</article>`).join('');
      $('.reviews-prev',reviews).disabled=page<=1;$('.reviews-next',reviews).disabled=page*10>=r.liczba;
      $('.reviews-page',reviews).textContent='Strona '+page; $('.reviews-all',reviews).hidden=!preview||r.liczba<=3; $('.reviews-pager',reviews).hidden=preview;
    } catch(e) {note(status,e.message,true);out.replaceChildren();}
  }
  async function loadMine() {
    if(!reviews)return;
    const form=$('form',reviews);form.hidden=!user;
    $('.review-login',reviews).hidden=!!user;
    if(!user)return;
    try {const r=await api('moja');const subject=$('[name="przedmiot"]',reviews).value;
      const mine=r.opinie.find(o=>o.przedmiot===subject);form.reset();
      if(mine){$('[name="tresc"]',form).value=mine.tresc;const radio=$(`[name="ocena"][value="${Number(mine.ocena)}"]`,form);if(radio)radio.checked=true;}
      note($('.review-note',reviews),mine?'Twoja opinia: '+({oczekuje:'czeka na sprawdzenie',opublikowany:'opublikowana',odrzucony:'ukryta'}[mine.status]||mine.status)+'. Możesz ją poprawić.':'');
    }catch(e){note($('.review-note',reviews),e.message,true);}
  }
  if(reviews){
    $('.reviews-all',reviews).onclick=()=>{preview=false;loadReviews();};
    $('[name="przedmiot"]',reviews).addEventListener('change',()=>{page=1;loadReviews();loadMine();});
    $('.reviews-prev',reviews).onclick=()=>{page=Math.max(1,page-1);loadReviews();};$('.reviews-next',reviews).onclick=()=>{page++;loadReviews();};
    $('form',reviews).addEventListener('submit',async e=>{e.preventDefault();const button=$('[type="submit"]',e.target);button.disabled=true;
      try{const data=Object.fromEntries(new FormData(e.target));data.przedmiot=$('[name="przedmiot"]',reviews).value;const r=await api('zapisz',data);await loadReviews();note($('.review-note',reviews),r.komunikat);}catch(err){note($('.review-note',reviews),err.message,true);}finally{button.disabled=false;}
    });loadReviews();
  }
  async function profile(){const box=$('#community-profile');if(!box)return;box.hidden=!user;if(!user)return;
    try{const {profil:p}=await api('profil');$('.profile-detail',box).innerHTML=`<p class="review-stars" aria-label="Poziom ${p.poziom.gwiazdki} z 5">${stars(p.poziom.gwiazdki)}</p><h3>${esc(p.poziom.nazwa)} · ${p.poziom.punkty} pkt</h3><p>${p.poziom.nastepny_prog===null?'Najwyższy poziom aktywności.':`Do kolejnego poziomu: ${p.poziom.nastepny_prog-p.poziom.punkty} pkt.`}</p><dl class="profile-stats"><div><dt>Zakończone zakupy</dt><dd>${p.zakupy}</dd></div><div><dt>Wątki / odpowiedzi</dt><dd>${p.watki} / ${p.odpowiedzi}</dd></div><div><dt>Potwierdzone polecenia</dt><dd>${p.polecenia}</dd></div><div><dt>Dni z próbą udostępnienia</dt><dd>${p.udostepnienia}</dd></div></dl>`;
    }catch(e){note($('.profile-detail',box),e.message,true);}}
  const share=$('#community-share');if(share)share.onclick=async()=>{share.disabled=true;try{
    const r=await api('kod',{});const url=location.origin+'/?polecenie='+r.kod;
    if(navigator.share)await navigator.share({title:'F.W. DRUCIK',url});else{await navigator.clipboard.writeText(url);}
    await api('udostepnij',{});note($('#share-note'),'Link gotowy. Punkty pojawią się po zakończonym zakupie nowego klienta z Twojego polecenia.');await profile();
  }catch(e){if(e.name!=='AbortError')note($('#share-note'),e.message,true);}finally{share.disabled=false;}};
  // The referral lives only within this browsing session and is bound before the first order.
  const ref=new URLSearchParams(location.search).get('polecenie');try{if(/^[a-f0-9]{24}$/.test(ref||''))sessionStorage.setItem('fw_polecenie',ref);}catch{}
  async function bindReferral(){if(!user)return;let code;try{code=sessionStorage.getItem('fw_polecenie');}catch{return;}if(!code)return;
    try{await api('polecenie',{kod:code});sessionStorage.removeItem('fw_polecenie');}catch(e){if(e.status===422){try{sessionStorage.removeItem('fw_polecenie');}catch{}}}}
  const admin=$('#community-admin');let adminPage=1;
  async function loadAdmin(){if(!admin||user?.rola!=='admin')return;const out=$('.community-admin-list',admin);const typ=$('[name="typ"]',admin).value;
    try{const r=await api('admin',null,`&typ=${typ}&status=${$('[name="status"]',admin).value}&przedmiot=${$('[name="przedmiot"]',admin).value}&page=${adminPage}`);
      out.innerHTML=r.pozycje.map(o=>`<article class="review-card" data-id="${Number(o.id)}"><strong>${esc(o.autor)} · ${esc(o.przedmiot||o.slug||'')} ${o.ocena?stars(o.ocena):''}</strong><small>${esc(o.status)} · ${esc(o.data)}</small><p class="community-pre">${esc(o.tresc)}</p><div class="community-actions"><button type="button" data-decision="opublikowany">Opublikuj</button><button type="button" data-decision="odrzucony">Ukryj</button><button type="button" data-decision="usun">Usuń</button></div><form class="company-reply"><label>Odpowiedź firmy<textarea name="tresc" maxlength="3000" rows="3">${esc(o.odpowiedz||'')}</textarea></label><button type="submit">Zapisz odpowiedź</button><button type="button" class="reply-delete">Usuń odpowiedź</button></form><p class="item-note" role="status"></p></article>`).join('')||'<p>Brak treści w tym filtrze.</p>';
      $('.admin-prev',admin).disabled=adminPage<=1;$('.admin-next',admin).disabled=!r.wiecej;
      out.querySelectorAll('[data-decision]').forEach(b=>b.onclick=async()=>{if(b.dataset.decision==='usun'&&!confirm('Usunąć tę treść i odpowiedź firmy?'))return;const card=b.closest('[data-id]');b.disabled=true;try{await api('moderuj',{typ,id:card.dataset.id,decyzja:b.dataset.decision});await loadAdmin();}catch(e){note($('.item-note',card),e.message,true);b.disabled=false;}});
      out.querySelectorAll('.company-reply').forEach(form=>{async function save(remove=false){const card=form.closest('[data-id]');form.querySelectorAll('button').forEach(b=>b.disabled=true);try{await api('odpowiedz',{typ,id:card.dataset.id,tresc:remove?'':$('[name="tresc"]',form).value});note($('.item-note',card),'Zapisano.');if(remove)$('[name="tresc"]',form).value='';}catch(e){note($('.item-note',card),e.message,true);}finally{form.querySelectorAll('button').forEach(b=>b.disabled=false);}}
        form.onsubmit=e=>{e.preventDefault();save();};$('.reply-delete',form).onclick=()=>{if(confirm('Usunąć odpowiedź firmy?'))save(true);};});
    }catch(e){note(out,e.message,true);}}
  if(admin){admin.querySelectorAll('select').forEach(s=>s.onchange=()=>{adminPage=1;loadAdmin();});$('.admin-prev',admin).onclick=()=>{adminPage=Math.max(1,adminPage-1);loadAdmin();};$('.admin-next',admin).onclick=()=>{adminPage++;loadAdmin();};}
  async function authChanged(){user=window.FWAuth?.getUser()||null;loadMine();profile();if(admin){admin.hidden=user?.rola!=='admin';loadAdmin();}await bindReferral();}
  document.addEventListener('fw-auth-change',authChanged);authChanged();

  // Fetch badges only when their authors scroll into view; private counters never leave the API.
  const pending=new Set();let badgeTimer;
  const watcher=new IntersectionObserver(entries=>{for(const e of entries){if(!e.isIntersecting)continue;watcher.unobserve(e.target);const id=Number(e.target.dataset.authorId);if(id>0)pending.add(id);}clearTimeout(badgeTimer);badgeTimer=setTimeout(loadBadges,80);});
  async function loadBadges(){const ids=[...pending].slice(0,30);ids.forEach(id=>pending.delete(id));if(!ids.length)return;try{const r=await api('poziomy',null,'&ids='+ids.join(','));for(const a of r.poziomy)document.querySelectorAll('[data-author-id="'+a.id+'"]').forEach(el=>{el.textContent=stars(a.poziom.gwiazdki)+' '+a.poziom.nazwa;el.setAttribute('aria-label','Poziom '+a.poziom.gwiazdki+' na 5: '+a.poziom.nazwa);});}catch{}if(pending.size)loadBadges();}
  function watchBadges(){document.querySelectorAll('[data-author-id]:not([data-level-watched])').forEach(el=>{el.dataset.levelWatched='1';watcher.observe(el);});}
  new MutationObserver(watchBadges).observe(document.body,{childList:true,subtree:true});watchBadges();

  // Lazy-load the assistant implementation only when requested.
  const chat=$('#assistant-launch');if(chat)chat.addEventListener('click',()=>{if(window.FWChat){window.FWChat.open();return;}chat.disabled=true;const s=document.createElement('script');s.src=chat.dataset.script;s.onload=()=>{chat.disabled=false;window.FWChat.open();};s.onerror=()=>{chat.disabled=false;chat.textContent='Czat niedostępny — Kontakt';chat.onclick=()=>location.href='/kontakt/';};document.head.append(s);});
})();