"""Strona /filmy/ i odtwarzacze w artykułach: dane z filmy.json (rolki na serwerze w /wideo/, filmy YouTube).
Generuje src/filmy.html i wstawia blok filmu do src/blog-<slug>.html artykułów, o których mówi film
(między znacznikami <!-- FILM:start --> ... <!-- FILM:end -->, więc ponowne uruchomienie tylko odświeża blok).
python filmy_strona.py"""
import html
import json
import pathlib
import re

R = pathlib.Path(__file__).resolve().parent
dane = json.loads((R / "filmy.json").read_text(encoding="utf-8"))
pages = (R / "pages.py").read_text(encoding="utf-8")


def artykul(slug):
    """(plik źródłowy, tytuł) artykułu z pages.py — nazwa pliku nie zawsze równa się slugowi"""
    m = re.search(r'strona\(\s*"/blog/' + re.escape(slug) + r'/",\s*"([^"]+)",\s*"([^"]+)"', pages)
    return (m.group(1), m.group(2).split(" | ")[0]) if m else (f"blog-{slug}.html", slug)


def tytul_artykulu(slug):
    """nagłówek H1 artykułu (tytuł SEO ma dopiski typu „| F.W. DRUCIK”)"""
    p = R / "src" / artykul(slug)[0]
    if p.exists():
        m = re.search(r"<h1[^>]*>(.*?)</h1>", p.read_text(encoding="utf-8"), re.S)
        if m:
            return html.unescape(re.sub("<[^>]+>", "", m.group(1))).strip()
    return artykul(slug)[1]


def rolka(f, szer="100%"):
    return (f'<video controls preload="none" playsinline poster="/wideo/{f["plik"]}.jpg" width="540" height="960" '
            f'style="width:{szer};max-width:320px;aspect-ratio:9/16;border-radius:12px;background:#000;display:block;margin:0 auto;">'
            f'<source src="/wideo/{f["plik"]}.mp4" type="video/mp4">Twoja przeglądarka nie odtwarza wideo.</video>')


def youtube(f):
    return (f'<div style="position:relative;padding-top:56.25%;border-radius:12px;overflow:hidden;">'
            f'<iframe src="https://www.youtube-nocookie.com/embed/{f["yt"]}" title="{html.escape(f["tytul"])}" loading="lazy" '
            f'style="position:absolute;inset:0;width:100%;height:100%;border:0;" allow="accelerometer; encrypted-media; gyroscope; '
            f'picture-in-picture; fullscreen" allowfullscreen></iframe></div>')


def linki(f):
    out = []
    if f.get("artykul"):
        out.append(f'<a href="/blog/{f["artykul"]}/">Artykuł na blogu</a>')
    if f.get("yt"):
        out.append(f'<a href="https://www.youtube.com/watch?v={f["yt"]}" target="_blank" rel="noopener">YouTube</a>')
    if f.get("ig"):
        out.append(f'<a href="{f["ig"]}" target="_blank" rel="noopener">Instagram</a>')
    if f.get("fb"):
        out.append(f'<a href="{f["fb"]}" target="_blank" rel="noopener">Facebook</a>')
    return " · ".join(out)


# --- strona /filmy/ -------------------------------------------------------------------------------------------------
sekcje = []
for kat in dane["kategorie"]:
    karty = []
    for f in kat["filmy"]:
        f.setdefault("tytul", tytul_artykulu(f.get("artykul", "")))
        if f["typ"] == "youtube":
            karty.append(f'<article class="blog-card card-glow" style="grid-column:1/-1;padding:18px;">{youtube(f)}'
                         f'<h3 class="blog-card-title" style="margin-top:14px;">{html.escape(f["tytul"])}</h3>'
                         f'<p class="blog-card-excerpt">{html.escape(f.get("opis", ""))}</p><p>{linki(f)}</p></article>')
        else:
            karty.append(f'<article class="blog-card card-glow" style="padding:16px;">{rolka(f)}'
                         f'<h3 class="blog-card-title" style="margin-top:12px;font-size:1.02rem;">{html.escape(f["tytul"])}</h3>'
                         f'<p style="font-size:0.9rem;">{linki(f)}</p></article>')
    sekcje.append(f'<section style="margin:44px 0;"><h2 id="{kat["id"]}">{html.escape(kat["nazwa"])}</h2>'
                  f'<p style="color:var(--metal-light);">{html.escape(kat["opis"])}</p>'
                  f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:22px;align-items:start;">'
                  f'{"".join(karty)}</div></section>')
spis = "".join(f'<li><a href="#{k["id"]}">{html.escape(k["nazwa"])}</a></li>' for k in dane["kategorie"])
n_rolek = sum(1 for k in dane["kategorie"] for f in k["filmy"] if f["typ"] == "rolka")
n_yt = sum(1 for k in dane["kategorie"] for f in k["filmy"] if f["typ"] == "youtube")
(R / "src" / "filmy.html").write_text(f"""<section class="article-container" style="padding:60px 24px;">
  <header style="margin-bottom:24px;">
    <h1 style="font-size:clamp(1.8rem,3.5vw,2.6rem);color:#fff;line-height:1.15;margin-bottom:14px;">Filmy z warsztatu</h1>
    <p class="lead" style="color:var(--metal-light);font-size:1.1rem;">Krótkie rolki i dłuższe poradniki wideo z warsztatu F.W. DRUCIK, ułożone tematycznie: {n_rolek} rolek i {n_yt} filmy. Przy każdym filmie jest artykuł na blogu z pełnym opisem, wartościami i źródłami.</p>
  </header>
  <div class="toc-box"><div class="toc-title">🎬 Tematy</div><ol class="toc-list">{spis}</ol></div>
  {"".join(sekcje)}
  <p style="margin-top:40px;">Nowe filmy pojawiają się na <a href="https://www.instagram.com/fwdrucik/" target="_blank" rel="noopener">Instagramie @fwdrucik</a> i na <a href="https://www.youtube.com/@f.w.drucik" target="_blank" rel="noopener">kanale YouTube F.W. DRUCIK</a>. Pytania o naprawę albo projekt: <a href="/kontakt/">kontakt</a> albo <a href="/forum/">forum</a>.</p>
</section>
""", encoding="utf-8")

# --- odtwarzacze w artykułach -------------------------------------------------------------------------------------
wg_art = {}
for kat in dane["kategorie"]:
    for f in kat["filmy"]:
        if f.get("artykul") and not f.get("bez_wstawki"):
            wg_art.setdefault(f["artykul"], []).append(f)
zmienione = []
for slug, filmy in wg_art.items():
    p = R / "src" / artykul(slug)[0]
    if not p.exists():
        print("brak artykułu:", slug)
        continue
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"\s*<!-- FILM:start -->.*?<!-- FILM:end -->", "", s, flags=re.S)
    czesci = []
    for f in sorted(filmy, key=lambda f: f["typ"] != "youtube"):
        if f["typ"] == "youtube":
            czesci.append(f'<div style="flex:1 1 420px;min-width:280px;">{youtube(f)}<p style="font-size:0.9rem;margin-top:8px;">'
                          f'Film: {html.escape(f["tytul"])}</p></div>')
        else:
            czesci.append(f'<div style="flex:0 1 240px;">{rolka(f)}<p style="font-size:0.9rem;margin-top:8px;text-align:center;">'
                          f'Rolka · <a href="{f.get("ig") or "/filmy/"}" target="_blank" rel="noopener">Instagram</a></p></div>')
    blok = (f'\n  <!-- FILM:start -->\n  <div class="toc-box" style="margin-bottom:28px;"><div class="toc-title">🎬 Zobacz na filmie</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start;margin-top:12px;">{"".join(czesci)}</div>'
            f'<p style="font-size:0.88rem;margin-top:10px;">Więcej filmów z warsztatu: <a href="/filmy/">wszystkie filmy</a>.</p></div>\n  <!-- FILM:end -->')
    i = s.index("</header>") + len("</header>")
    s = s[:i] + blok + s[i:]
    p.write_text(s, encoding="utf-8")
    zmienione.append(slug)
print("src/filmy.html:", n_rolek, "rolek,", n_yt, "filmy YouTube; odtwarzacze w", len(zmienione), "artykułach")
