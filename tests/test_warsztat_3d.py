"""Sprawdza stany interakcji 3D, klawiaturę i brak WebGL w przeglądarce."""
import functools
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import expect, sync_playwright

dist = Path(__file__).resolve().parents[1] / "dist"
out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None


class PreviewHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def snapshot(page, name):
    if out:
        out.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out / name))


with ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(PreviewHandler, directory=dist)) as server:
    Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="chrome", args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
        )
        errors = []
        missing = []

        def new_page(**kwargs):
            page = browser.new_page(**kwargs)
            page.route("**/*", lambda route: route.continue_()
                       if route.request.url.startswith(base) else route.abort())
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("response", lambda res: missing.append(res.url)
                    if res.status == 404 and "/assets/" in res.url else None)
            return page

        def canvas_ready(page, name):
            node = page.locator(f'[data-scene="{name}"].scene-ready canvas')
            expect(node).to_be_visible(timeout=18000)
            assert node.evaluate("""canvas => canvas.width > 100 &&
                canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data
                    .some((value, i) => i % 4 === 3 && value > 100)""")
            return node

        page = new_page(viewport={"width": 1440, "height": 970})
        page.add_init_script("Math.random = () => .1")
        page.goto(base, wait_until="domcontentloaded")
        hero = canvas_ready(page, "hero")
        expect(page.get_by_role("link", name="Bezpłatna wycena", exact=True).last).to_have_attribute("href", "/kontakt/#formularz")
        snapshot(page, "strona-desktop.png")
        click = page.get_by_role("button", name="Przyspiesz mechanizm")
        click.focus()
        click.press("Enter")
        before = hero.evaluate("el => el.toDataURL()")
        page.wait_for_function("""previous =>
            document.querySelector('[data-scene=hero] canvas').toDataURL() !== previous""", arg=before)
        page.get_by_role("button", name="Zatrzymaj animacje").click()
        expect(click).to_be_hidden()
        page.evaluate("scrollTo(0, 0)")
        page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
        still = hero.evaluate("el => el.toDataURL()")
        page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
        assert still == hero.evaluate("el => el.toDataURL()")
        page.locator(".workbench-services").scroll_into_view_if_needed()
        for name in ("rotor", "tig", "cnc", "automation"):
            canvas_ready(page, name)
        snapshot(page, "uslugi-3d.png")
        page.get_by_role("button", name="Wznów animacje").click()

        page.get_by_role("button", name="Panel serwisowy").click()
        cabinet = canvas_ready(page, "cabinet")
        snapshot(page, "rozdzielnica.png")
        box = cabinet.bounding_box()
        for offset in (.26, .34, .42, .47, .51):
            x, y = box["x"] + box["width"] * offset, box["y"] + box["height"] * .50
            page.mouse.move(x, y)
            if cabinet.evaluate("node => node.classList.contains('wire-hover')"):
                page.mouse.click(x, y)
                break
        expect(page.get_by_role("status").filter(has_text="Zwarcie").or_(
            page.get_by_role("status").filter(has_text="5%"))).to_be_visible()
        page.get_by_role("button", name="Zresetuj bezpiecznik").click()
        page.get_by_role("button", name="Niebieski").press("Enter")
        expect(page.locator("#detonator-result")).to_contain_text("Zwarcie")
        page.get_by_role("button", name="Zresetuj bezpiecznik").click()
        page.get_by_role("button", name="Czerwony").press("Enter")
        expect(page.locator("#detonator-result")).to_contain_text("5%")
        page.keyboard.press("Escape")
        expect(page.get_by_role("button", name="Panel serwisowy")).to_be_focused()
        page.close()

        page = new_page(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        page.goto(base + "/uslugi/zywica-epoksydowa/", wait_until="domcontentloaded")
        page.locator(".workbench-resin").scroll_into_view_if_needed()
        table = canvas_ready(page, "table")
        initial = table.evaluate("el => el.toDataURL()")
        page.get_by_role("button", name="Głęboki bursztyn").click()
        expect(page.get_by_role("button", name="Głęboki bursztyn")).to_have_attribute("aria-pressed", "true")
        page.wait_for_function("""previous =>
            document.querySelector('[data-scene=table] canvas').toDataURL() !== previous""", arg=initial)
        page.get_by_role("button", name="Podświetlenie LED").press("Enter")
        expect(page.get_by_role("button", name="Podświetlenie LED")).to_have_attribute("aria-pressed", "true")
        page.get_by_role("button", name="Obróć widok w prawo").press("Enter")
        page.get_by_role("button", name="Przybliż widok").press("Enter")
        page.get_by_role("button", name="Widok startowy").press("Enter")
        snapshot(page, "river-table.png")
        page.close()

        for width in (320, 390):
            page = new_page(viewport={"width": width, "height": 900}, has_touch=True,
                            is_mobile=True, reduced_motion="reduce")
            page.goto(base, wait_until="domcontentloaded")
            canvas_ready(page, "hero")
            expect(page.get_by_role("button", name="Przyspiesz mechanizm")).to_be_hidden()
            assert page.evaluate("document.documentElement.scrollWidth === innerWidth"), width
            if width == 390:
                snapshot(page, "strona-telefon.png")
            page.close()

        page = new_page(java_script_enabled=False, viewport={"width": 390, "height": 844})
        page.goto(base, wait_until="load")
        expect(page.locator(".workbench-hero .scene-poster img")).to_be_visible()
        assert page.locator(".workbench-hero img").evaluate("img => img.complete && img.naturalWidth > 0")
        assert page.locator(".workbench-services-grid a").count() == 4
        assert not errors, errors
        assert not missing, missing
        browser.close()
    server.shutdown()

print("OK: mechanizm, cztery ikony, rozdzielnica, River Table, 320/390 px i wariant bez JS")
