# -*- coding: utf-8 -*-
"""py tests/test_generatory.py [--zrzuty KATALOG] — 30 generatorów kompendium Pracowni w Chrome."""
import functools, http.server, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

DIST = Path(__file__).resolve().parent.parent / "dist"
OUT = Path(sys.argv[sys.argv.index("--zrzuty") + 1]) if "--zrzuty" in sys.argv else None


class Cichy(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Cichy, directory=str(DIST)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_address[1]}/pracownia/kompendium/"
bledy = []
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    for nazwa, opcje in (("desktop", {"viewport": {"width": 1440, "height": 900}}),
                         ("telefon", {"viewport": {"width": 390, "height": 844}, "is_mobile": True, "has_touch": True}),
                         ("spokojnie", {"viewport": {"width": 1440, "height": 900}, "reduced_motion": "reduce"})):
        ctx = b.new_context(**opcje)
        page = ctx.new_page()
        page.on("pageerror", lambda e, n=nazwa: bledy.append(f"{n}: {e}"))
        page.goto(BASE, wait_until="networkidle")
        gens = page.locator("[data-gen]")
        assert gens.count() == 30, gens.count()
        for i in range(30):
            g = gens.nth(i)
            kod = g.get_attribute("data-gen")
            assert g.is_visible(), kod
            assert g.locator("svg > *").count() > 0, f"{kod}: pusty rysunek"
            przed = g.locator(".gen-wynik").inner_text()
            assert przed.strip(), f"{kod}: brak opisu"
            for j in range(g.locator(".gen-ster button").count()):
                btn = g.locator(".gen-ster button").nth(j)
                if "Odtwórz" in btn.inner_text():
                    continue
                btn.click()
            for j in range(g.locator("input[type=range]").count()):
                g.locator("input[type=range]").nth(j).fill(g.locator("input[type=range]").nth(j).get_attribute("max"))
            assert g.locator(".gen-wynik").inner_text().strip(), f"{kod}: opis zniknął"
            if OUT and nazwa == "desktop" and kod in ("e02", "e04", "a01", "a06", "d06", "d09"):
                g.scroll_into_view_if_needed(); g.screenshot(path=str(OUT / f"gen-{kod}.png"))
        szer = page.evaluate("document.documentElement.scrollWidth - innerWidth")
        assert szer <= 0, f"{nazwa}: poziome przewijanie {szer}px"
        ctx.close()
    b.close()
srv.shutdown()
assert not bledy, bledy
print("OK: 30 generatorów — desktop, telefon, ograniczony ruch; przyciski, suwaki, opisy")
