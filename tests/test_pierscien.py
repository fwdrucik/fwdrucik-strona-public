# -*- coding: utf-8 -*-
"""Pierścień usług 3D na stronie głównej — kontrola w Chrome (Playwright).

    py build.py
    py tests/test_pierscien.py                 same asercje
    py tests/test_pierscien.py --zrzuty KATALOG   dodatkowo zrzuty ekranu

Sam podaje dist/ po HTTP na wolnym porcie. Sprawdza: obrót wejściowy, przeciąganie
myszą i palcem, przyciski, komunikat dla czytników, klik w boczną płytę (obrót bez
nawigacji), klawiaturę, przejście z przedniej płyty, brak poziomego przewijania,
siatkę przy prefers-reduced-motion i odnośniki bez JS.
"""
import functools
import http.server
import json
import sys
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

DIST = Path(__file__).resolve().parent.parent / "dist"
OUT = Path(sys.argv[sys.argv.index("--zrzuty") + 1]) if "--zrzuty" in sys.argv else None
if OUT:
    OUT.mkdir(parents=True, exist_ok=True)


class Cichy(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


serwer = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Cichy, directory=str(DIST)))
threading.Thread(target=serwer.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{serwer.server_address[1]}"
errors = []


def shot(page, name):
    if OUT:
        page.screenshot(path=str(OUT / name))


def front(page):
    return page.evaluate("document.querySelector('.ring-item[data-d=\"0\"] h3')?.textContent")


def settle(page):
    """Czeka, aż orbita stanie w zapadce (script.js zdejmuje wtedy klasę is-spinning)."""
    page.wait_for_timeout(150)
    page.wait_for_function("!document.querySelector('.ring').classList.contains('is-spinning')", timeout=10000)
    page.wait_for_timeout(80)


def to_ring(page, offset=120):
    page.evaluate(f"window.scrollTo({{top: document.querySelector('.ring').getBoundingClientRect().top + scrollY - {offset}, behavior: 'instant'}})")
    page.wait_for_timeout(400)
    settle(page)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)

    # ---------- desktop ----------
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(f"desktop: {e}"))
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(1100)
    shot(page, "d1-hero.png")
    eb = page.locator('.workbench-viewport').bounding_box()
    for i in range(0, 9):
        page.mouse.move(eb['x'] + eb['width'] * (0.25 + i * 0.07), eb['y'] + eb['height'] * (0.35 + i * 0.03))
        page.wait_for_timeout(30)
    page.wait_for_timeout(120)
    shot(page, "d6-emblem.png")
    page.mouse.move(10, 500)
    to_ring(page)
    shot(page, "d2-ring.png")
    first = front(page)
    assert first == "Elektromechanika pojazdowa i przemysłowa", first

    box = page.locator(".ring-stage").bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    # przeciągnięcie w lewo = kolejne usługi
    page.mouse.move(cx, cy)
    page.mouse.down()
    for i in range(1, 13):
        page.mouse.move(cx - i * 30, cy, steps=1)
        page.wait_for_timeout(16)
    shot(page, "d3-dragging.png")
    page.mouse.up()
    settle(page)
    after_drag = front(page)
    assert after_drag != first, "drag did not rotate"
    assert page.url.rstrip("/") == BASE.rstrip("/"), "drag navigated away"

    # przyciski
    page.click("[data-ring-step='1']")
    settle(page)
    after_btn = front(page)
    assert after_btn != after_drag
    shot(page, "d8-dock.png")
    status = page.text_content("[data-ring-status]")
    assert after_btn in status, status

    # klik w boczną płytę obraca, nie nawiguje
    side = page.locator(".ring-item[data-d='1'] a").first
    side_title = side.locator("h3").text_content()
    sb = side.bounding_box()
    page.mouse.click(sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2)
    settle(page)
    assert page.url.rstrip("/") == BASE.rstrip("/"), "side click navigated"
    assert front(page) == side_title, (front(page), side_title)

    # klawiatura
    page.locator(".ring-item[data-d='0'] a").focus()
    page.keyboard.press("ArrowRight")
    settle(page)
    kb = front(page)
    assert kb != side_title
    assert page.evaluate("document.activeElement.querySelector('h3')?.textContent") == kb
    shot(page, "d4-focus.png")

    geo = page.evaluate("""(() => {
      const f = document.querySelector('.ring-item[data-d="0"] a').getBoundingClientRect();
      const s = document.querySelector('.ring-stage').getBoundingClientRect();
      const a = document.querySelector('.ring-item[data-d="0"] a');
      return {frontW: Math.round(f.width), frontH: Math.round(f.height), frontTop: Math.round(f.top - s.top),
              stageH: Math.round(s.height), overflowX: document.documentElement.scrollWidth - innerWidth,
              clipped: [...document.querySelectorAll('.ring-item a')].map(x => x.scrollHeight - x.clientHeight)};
    })()""")
    print("desktop", json.dumps(geo), "| front:", kb)
    assert geo["overflowX"] <= 0, geo

    # Pauza wyłącza iskry i sprężynę, przyciski nadal przełączają usługi.
    page.get_by_role("button", name="Zatrzymaj animacje").click()
    assert page.locator('html').evaluate("node => node.classList.contains('niebo-stop')")
    wire = "getComputedStyle(document.querySelector('.ring-list'), '::before').transform"
    before = page.evaluate(wire)
    page.click("[data-ring-step='1']")
    assert front(page) != kb
    assert page.evaluate(wire) != before, "impuls nie obrócił się z płytami"
    assert not page.locator(".ring").evaluate("(ring) => ring.classList.contains('is-spinning')")
    page.get_by_role("button", name="Wznów animacje").click()
    page.locator(".ring-item[data-d='0'] a").focus()
    settle(page)
    page.locator("#assistant-launch").click(trial=True, timeout=3000)

    # przednia płyta: Enter przechodzi na podstronę
    href = page.locator(".ring-item[data-d='0'] a").get_attribute("href")
    page.keyboard.press("Enter")
    page.wait_for_url("**" + href)
    page.wait_for_timeout(700)
    shot(page, "d5-subpage.png")
    ctx.close()

    # ---------- telefon ----------
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, has_touch=True, is_mobile=True)
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(f"mobile: {e}"))
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(1100)
    shot(page, "m1-hero.png")
    to_ring(page, 90)
    shot(page, "m2-ring.png")
    m_first = front(page)
    box = page.locator(".ring-stage").bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    cdp = ctx.new_cdp_session(page)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": cx + 90, "y": cy}]})
    for i in range(1, 10):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": cx + 90 - i * 22, "y": cy}]})
        page.wait_for_timeout(16)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    settle(page)
    assert front(page) != m_first, "swipe did not rotate"
    shot(page, "m3-after-swipe.png")
    m_geo = page.evaluate("({overflowX: document.documentElement.scrollWidth - innerWidth, clipped: [...document.querySelectorAll('.ring-item a')].map(x => x.scrollHeight - x.clientHeight)})")
    print("mobile", json.dumps(m_geo), "| front:", front(page))
    assert m_geo["overflowX"] <= 0, m_geo
    page.locator("#assistant-launch").click(trial=True, timeout=3000)
    ctx.close()

    # ---------- ograniczony ruch: zwykła siatka ----------
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(f"reduced: {e}"))
    page.goto(BASE + "/", wait_until="networkidle")
    assert not page.evaluate("document.querySelector('.ring').classList.contains('is-ring')")
    assert page.evaluate("document.querySelector('.ring-controls').hidden")
    assert not page.get_by_role("button", name="Przyspiesz mechanizm").is_visible()
    page.evaluate("window.scrollTo({top: document.querySelector('.ring').getBoundingClientRect().top + scrollY - 100, behavior: 'instant'})")
    page.wait_for_timeout(300)
    shot(page, "r1-grid.png")
    ctx.close()

    # ---------- bez JS ----------
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, java_script_enabled=False)
    page = ctx.new_page()
    page.goto(BASE + "/", wait_until="load")
    assert page.locator(".ring-item a").count() == 12
    assert page.locator(".ring-item a").first.is_visible()
    ctx.close()
    browser.close()

assert not errors, errors
serwer.shutdown()
print("OK: pierścień — desktop, telefon, reduced motion, bez JS")
