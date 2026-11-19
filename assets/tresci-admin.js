/* Plain text CMS. Never renders source HTML or user text as markup. */
(()=>{
'use strict';
const root=document.querySelector('#panel-tresci');if(!root)return;
root.innerHTML='<h2>Teksty na stronie</h2><p>Edytujesz źródła strony. Zapis tworzy wersję w GitHub. Publikacja przebudowuje stronę i może potrwać kilka minut. Kod, linki i formularze pozostają chronione.</p><label>Strona <select class="cms-pages" aria-label="Strona do edycji"></select></label> <button type="button" class="btn cms-load">Wczytaj</button> <button type="button" class="btn cms-save" disabled>Zapisz zmiany</button> <button type="button" class="btn cms-publish">Publikuj zapisane treści</button><p role="status" class="cms-status"></p><p><a href="https://github.com/fwdrucik/fwdrucik-strona/actions/workflows/wysylka.yml" target="_blank" rel="noopener">Stan publikacji w GitHub</a> · <a class="cms-history" href="https://github.com/fwdrucik/fwdrucik-strona/commits/main/src" target="_blank" rel="noopener">Historia wersji</a></p><div class="cms-blocks"></div>';
const q=s=>root.querySelector(s);let sha='',page='',original=new Map(),busy=false,initialized=false;
const dirty=()=>[...q('.cms-blocks').querySelectorAll('textarea')].some(t=>t.value!==original.get(t.dataset.id));
function message(text){q('.cms-status').textContent=text;}
function lock(value){busy=value;root.querySelectorAll('button,select,textarea').forEach(el=>el.disabled=value);q('.cms-save').disabled=value||!sha;}
async function api(action,data,selected=''){
 const response=await fetch('/api/tresci.php?akcja='+action+'&strona='+encodeURIComponent(selected),{credentials:'same-origin',method:data?'POST':'GET',headers:data?{'Content-Type':'application/json','X-FW-CSRF':decodeURIComponent((document.cookie.match(/(?:^|; )fw_csrf=([^;]*)/)||[])[1]||'')}:{},body:data?JSON.stringify(data):undefined,signal:AbortSignal.timeout(35000)});
 const result=await response.json();if(!response.ok||!result.ok)throw new Error(result.blad||'Nie udało się wykonać operacji.');return result;
}
async function load(){if(busy||dirty()&&!confirm('Odrzucić niezapisane zmiany?'))return;lock(true);message('Wczytuję źródło…');
 try{const selected=q('.cms-pages').value,r=await api('czytaj',null,selected);sha=r.sha;page=selected;original=new Map();q('.cms-blocks').replaceChildren();
 for(const block of r.bloki){const box=document.createElement('details'),title=document.createElement('summary'),label=document.createElement('label'),input=document.createElement('textarea'),preview=document.createElement('p'),clear=document.createElement('button');
 title.textContent=(block.id+1)+'. '+block.element+' — '+block.tekst.trim().slice(0,90);input.value=block.tekst;input.dataset.id=String(block.id);input.maxLength=12000;input.rows=3;input.style.width='100%';label.textContent='Treść fragmentu '+(block.id+1);label.append(input);original.set(String(block.id),block.tekst);
 preview.style.whiteSpace='pre-wrap';preview.textContent=block.tekst;input.addEventListener('input',()=>{preview.textContent=input.value;});clear.type='button';clear.className='btn';clear.textContent='Wyczyść tekst';clear.onclick=()=>{if(confirm('Wyczyścić ten fragment? Zmiana nastąpi po zapisie i publikacji.')){input.value='';preview.textContent='';}};
 box.append(title,label,clear,preview);q('.cms-blocks').append(box);}
 q('.cms-history').href='https://github.com/fwdrucik/fwdrucik-strona/commits/main/src/'+encodeURIComponent(page);message('Wczytano '+r.bloki.length+' fragmentów. Rozwiń fragment, aby edytować tekst i zobaczyć podgląd.');
 }catch(e){message(e.message);}finally{lock(false);}}
q('.cms-load').onclick=load;
q('.cms-save').onclick=async()=>{if(busy||!sha)return;const changes={};q('.cms-blocks').querySelectorAll('textarea').forEach(t=>{if(t.value!==original.get(t.dataset.id))changes[t.dataset.id]=t.value;});if(!Object.keys(changes).length){message('Brak zmian.');return;}lock(true);message('Zapisuję…');try{const r=await api('zapisz',{sha,zmiany:changes},page);sha=r.sha;for(const[id,text]of Object.entries(changes))original.set(id,text);message(r.komunikat);}catch(e){message(e.message);}finally{lock(false);}};
q('.cms-publish').onclick=async()=>{if(busy)return;if(dirty()){message('Najpierw zapisz zmiany lub wczytaj stronę ponownie, aby je odrzucić.');return;}if(!confirm('Opublikować aktualne zapisane źródła strony?'))return;lock(true);message('Zlecam publikację…');try{const r=await api('publikuj',{});message(r.komunikat);}catch(e){message(e.message);}finally{lock(false);}};
async function init(){if(initialized||window.FWAuth?.uzytkownik?.rola!=='admin')return;initialized=true;try{const r=await api('lista');for(const name of r.strony){const o=document.createElement('option');o.value=name;o.textContent=name.replace(/\.html$/,'');q('.cms-pages').append(o);}}catch(e){initialized=false;message(e.message);}}
document.addEventListener('fw-auth-change',init);window.addEventListener('beforeunload',e=>{if(dirty()){e.preventDefault();e.returnValue='';}});init();
})();
