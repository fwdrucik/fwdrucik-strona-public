"""Reusable community UI injected into source renders, never manually into dist."""
import json
import re
from html import unescape

REVIEWS = '''<section id="opinie" class="community"><div class="container">
<p class="eyebrow">Wasze doświadczenia</p><h2>Opinie klientów</h2>
<p>Byłeś u nas lub korzystasz ze strony? Napisz, co działa, a co warto poprawić.</p>
<label>Co oceniasz? <select name="przedmiot"><option value="sklep">Sklep i obsługa</option><option value="strona">Strona internetowa</option></select></label>
<p class="review-summary" role="status">Wczytywanie ocen…</p><div class="review-list"></div>
<button type="button" class="reviews-all" hidden>Wszystkie opinie</button><div class="community-actions reviews-pager"><button type="button" class="reviews-prev">Poprzednie</button><span class="reviews-page">Strona 1</span><button type="button" class="reviews-next">Następne</button></div>
<p class="review-login"><a href="/konto/">Zaloguj się, żeby dodać opinię</a>.</p>
<form hidden><h3>Twoja opinia</h3><fieldset class="review-rating"><legend>Ocena od 1 do 5 gwiazdek</legend>''' + ''.join(f'<label><input type="radio" name="ocena" value="{n}" required>{n} ★</label>' for n in range(1,6)) + '''</fieldset>
<label>Opinia<textarea name="tresc" rows="4" minlength="5" maxlength="3000" required placeholder="Co cenisz? Co możemy poprawić?"></textarea></label><button type="submit">Zapisz opinię</button></form>
<p class="review-note" role="status"></p><small>Opinie sprawdzamy przed publikacją niezależnie od oceny. Jedno konto może wystawić po jednej opinii o sklepie i stronie. „Potwierdzony zakup” oznacza zakończone zamówienie na tym koncie.</small>
</div></section>'''
PROFILE = '''<section id="community-profile" class="community" hidden><div class="container"><h2>Twoja aktywność</h2><div class="profile-detail"></div>
<p>Poziom pokazuje aktywność, nie kwalifikacje. Zakup: 20 pkt, wątek: 5 pkt, odpowiedź: 2 pkt (forum maks. 20 pkt dziennie), potwierdzone polecenie: 3 pkt. Ukrycie wpisu lub anulowanie zakupu cofa punkty.</p>
<p>Twoje statystyki zakupów są prywatne. Inni widzą nick i poziom.</p><button type="button" id="community-share">Poleć stronę znajomym</button><p id="share-note" role="status"></p><small>Próby udostępnienia liczymy najwyżej raz dziennie, bez punktów. Polecenie premiujemy po zakończonym zakupie nowego klienta, który założył konto z Twojego linku.</small></div></section>'''
ADMIN = '''<section id="community-admin" class="community" hidden><div class="container"><h2>Opinie i odpowiedzi firmy</h2><div class="community-actions">
<label>Rodzaj<select name="typ"><option value="opinia">Opinie</option><option value="komentarz">Komentarze bloga</option></select></label>
<label>Status<select name="status"><option value="">Wszystkie</option><option value="oczekuje">Oczekujące</option><option value="opublikowany">Opublikowane</option><option value="odrzucony">Ukryte</option></select></label>
<label>Ocena dotyczy<select name="przedmiot"><option value="">Wszystkiego</option><option value="sklep">Sklepu</option><option value="strona">Strony</option></select></label></div>
<div class="community-admin-list"></div><div class="community-actions"><button type="button" class="admin-prev">Poprzednie</button><button type="button" class="admin-next">Następne</button></div></div></section>'''


def community_body(body, url):
    if url == '/':
        body = body.replace("{{HOME_REVIEWS}}", REVIEWS.replace('class="community"', 'class="community" data-preview="true"', 1), 1)
    elif url == '/sklep/':
        body += REVIEWS
    elif url == '/konto/':
        body += PROFILE
    elif url == '/admin/':
        body += ADMIN
        body = body.replace('<ul class="admin-menu">', '<ul class="admin-menu"><li><a href="#community-admin">Opinie i odpowiedzi firmy</a></li>', 1)
    return body


def public_knowledge(pages, base):
    # Only public offer/contact information. Never admin, accounts, private vault or user data.
    from pathlib import Path
    selected = [p for p in pages if p['url'] in ('/', '/kontakt/', '/uslugi/', '/sklep/', '/automatyzacje/') or p['url'].startswith('/uslugi/')]
    chunks = ['F.W. DRUCIK. Domosław 13A, 06-120 Winnica. Telefon 601 726 924. E-mail fwdrucik@gmail.com. Kontakt: /kontakt/. Wycena i termin wymagają uzgodnienia z firmą.']
    for p in selected:
        path = Path(base)/'src'/p.get('src','')
        if not path.is_file():
            continue
        content=path.read_text(encoding='utf-8')
        # Public opening paragraphs only; no JSON-LD, JavaScript or hidden controls.
        paragraphs=re.findall(r'<p(?:\s[^>]*)?>(.*?)</p>',content,re.S)
        text=' '.join(unescape(re.sub('<[^>]+>',' ',v)) for v in paragraphs[:3])
        text=re.sub(r'\s+',' ',text).strip()
        chunks.append(p['url']+' '+p['title']+' '+text[:600])
    return json.dumps('\n'.join(chunks)[:12000],ensure_ascii=False)