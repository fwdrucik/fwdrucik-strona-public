"""Pracownia: obliczenia, dotyk, profil konta i brak wycieku między kontami."""
import functools
import http.server
import re
import sys
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
if out:
    out.mkdir(parents=True, exist_ok=True)

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=root / "dist"))
threading.Thread(target=server.serve_forever, daemon=True).start()
errors = []

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    for width in (320, 390, 1440):
        context = browser.new_context(viewport={"width": width, "height": 900}, reduced_motion="reduce")
        context.route(lambda url: not url.startswith(f"http://127.0.0.1:{server.server_port}/"), lambda route: route.abort())
        user = {"id": 17, "nick": "Warsztat", "rola": "user"}
        profiles = {}
        def route_api(route):
            url = route.request.url
            if "/auth.php" in url:
                route.fulfill(json={"ok": True, "uzytkownik": user, "csrf": "a" * 64})
            elif "/drucik.php" in url:
                assert "wlasciciel_id" not in (route.request.post_data or "")
                record = profiles.get(user["id"], {"wersja": 0, "profil": None})
                if route.request.method == "POST":
                    data = route.request.post_data_json
                    if data["wersja"] != record["wersja"]:
                        route.fulfill(status=409, json={"ok": False, "blad": "Profil zmienił się w innej karcie."})
                        return
                    record = {"wersja": record["wersja"] + 1, "profil": {k: v for k, v in data.items() if k != "wersja"}}
                    profiles[user["id"]] = record
                route.fulfill(json={"ok": True, **record})
            else:
                route.fulfill(json={"ok": False})
        context.route("**/api/**", route_api)
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{server.server_port}/pracownia/", wait_until="networkidle")
        mapa = page.get_by_role("navigation", name="Mapa kursu")
        assert mapa.locator('a[href^="#"]').count() == 31
        assert mapa.get_by_text("Sezon 2 · planowane lekcje", exact=True).count() >= 1
        assert page.get_by_role("heading", name="Sprawdźcie razem").count() == 30
        assert mapa.locator('a[href="#proba-e02"]').count() == 1
        mapa.get_by_role("link", name="Pierwsze obwody na płytce stykowej").click()
        assert page.url.endswith("#obwody")
        page.locator("#obwody").get_by_role("link", name="Wróć do mapy kursu").click()
        assert page.url.endswith("#kurs")
        assert page.locator("[data-obwody]").is_visible()
        page.wait_for_timeout(600)
        assert not errors, errors
        print(width, page.locator("#drucik-zapis").text_content(), flush=True)
        page.locator("#drucik-zapis").filter(has_text="pierwszego").wait_for()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
        assert page.locator(".lab-zarowka").count() == 3
        assert page.locator(".lab-swiatlo.swieci").count() == 0
        page.locator("#lab-bateria").click()
        assert "33,33 mA" in page.locator("#lab-odczyt").inner_text()
        assert page.locator(".lab-zarowka.swieci").count() == 3
        page.select_option("#lab-element-2", "puste")
        assert "Obwód otwarty" in page.locator("#lab-odczyt").inner_text()
        assert page.locator(".lab-swiatlo.swieci").count() == 0
        page.select_option("#lab-uklad", "rownolegle")
        assert "200 mA" in page.locator("#lab-odczyt").inner_text()
        assert page.locator(".lab-zarowka.swieci").count() == 2
        page.select_option("#lab-element-2", "zarowka")
        page.select_option("#lab-uklad", "mieszane")
        assert "66,67 mA" in page.locator("#lab-odczyt").inner_text()
        page.select_option("#lab-element-1", "puste")
        assert "Obwód otwarty" in page.locator("#lab-odczyt").inner_text()
        assert "0 mA" in page.locator("#lab-odczyt").inner_text()

        page.select_option("#lab-uklad", "rownolegle")
        page.select_option("#lab-element-2", "led")
        page.select_option("#lab-element-3", "puste")
        assert "14,89 mA" in page.locator("#lab-odczyt").inner_text()
        led = page.locator(".lab-led .lab-klosz")
        bright = float(led.get_attribute("fill-opacity"))
        page.get_by_role("button", name="Prawo Ohma").click()
        assert "470 Ω ≈ 14,89 mA" in page.locator("#lab-przyklad-ohma").inner_text()
        page.select_option("#lab-opor-2", "1000")
        assert "7 mA" in page.locator("#lab-odczyt").inner_text()
        assert "1000 Ω ≈ 7 mA" in page.locator("#lab-przyklad-ohma").inner_text()
        assert float(led.get_attribute("fill-opacity")) < bright
        assert page.locator("#lab-lekcja-ohm").evaluate("(p)=>getComputedStyle(p).animationName") == "none"
        page.get_by_role("button", name="Po co rezystor?").click()
        assert page.locator("#lab-lekcja-rezystor").is_visible()
        page.locator(".lab-dymek summary").click()
        assert not page.locator("#lab-lekcja-rezystor").is_visible()
        page.locator(".lab-dymek summary").click()
        assert page.locator("#lab-lekcja-rezystor").is_visible()

        page.select_option("#lab-uklad", "mieszane")
        page.select_option("#lab-element-1", "led")
        page.select_option("#lab-opor-1", "1000")
        page.select_option("#lab-element-3", "zarowka")
        assert "6,42 mA" in page.locator("#lab-odczyt").inner_text()
        assert page.locator(".lab-led.swieci").count() == 1
        page.locator("#lab-reset").click()
        assert page.locator("#lab-bateria").get_attribute("aria-pressed") == "false"
        assert page.locator(".lab-zarowka").count() == 3
        assert page.locator(".lab-swiatlo.swieci").count() == 0

        page.locator("#lab-jedna-led").click()
        assert page.locator("#lab-uklad").input_value() == "pojedynczy"
        assert page.locator(".lab-led").count() == 1
        assert not page.locator("#lab-element-2").is_visible()
        assert page.locator(".lab-led.swieci").count() == 0
        page.locator("#lab-bateria").click()
        assert page.locator(".lab-led.swieci").count() == 1
        assert "14,89 mA" in page.locator("#lab-odczyt").inner_text()
        page.locator("#lab-reset").click()

        mapa.get_by_role("link", name="Pierwsze mrugnięcie robota").click()
        assert page.url.endswith("#arduino")
        page.select_option("#blink-swiatlo", "250")
        assert "0,25 s światła i 1 s przerwy" in page.locator("#blink-wynik").inner_text()
        assert page.locator("#blink-kod-swiatlo").inner_text() == "250"
        page.select_option("#blink-przerwa", "250")
        page.select_option("#blink-swiatlo", "1000")
        assert "1 s światła i 0,25 s przerwy. Cały cykl trwa 1,25 s." in page.locator("#blink-wynik").inner_text()
        assert page.locator("#blink-podglad").is_disabled()

        mapa.get_by_role("link", name="Znajdź pierwszą warstwę").click()
        assert page.url.endswith("#druk-3d")
        page.get_by_role("button", name="Pas A").click()
        assert "leży wyżej" in page.locator("#druk-wynik").inner_text()
        page.get_by_role("button", name="Pas D").click()
        assert "dotyka stołu" in page.locator("#druk-wynik").inner_text()
        page.locator("#druk-warstwy").fill("1")
        assert page.locator("[data-warstwa]:visible").count() == 1
        assert page.get_by_role("button", name="Pas D").is_visible()
        assert page.locator("#druk-liczba").inner_text() == "1"

        if width == 390:
            for link in page.get_by_role("link", name=re.compile(r"Pobierz kartę")).all():
                response = context.request.get(f"http://127.0.0.1:{server.server_port}" + link.get_attribute("href"))
                assert response.ok and response.body().startswith(b"%PDF-")
                assert len(re.findall(rb"/Type\s*/Page\b", response.body())) == 1
            assert page.get_by_role("link", name=re.compile(r"Pobierz kartę")).count() == 3

        page.locator('[name="imie"]').fill("Miedziany")
        page.select_option('[name="kolor"]', "miedz")
        page.select_option('[name="paliwo"]', "lpg")
        page.locator("#drucik-kroki select").first.select_option("glowa")
        page.locator("#drucik-start").click()
        page.locator("[data-drucik-stan]").filter(has_text="Program zakończony").wait_for()
        assert "66/100" in page.locator("[data-drucik-stan]").inner_text()
        page.locator('[data-przekaska="srubka"]').click()
        assert "74/100" in page.locator("[data-drucik-stan]").inner_text()
        page.get_by_role("button", name="Zapisz na koncie").click()
        page.locator("#drucik-zapis").filter(has_text="Profil zapisany").wait_for()
        assert profiles[17]["profil"]["imie"] == "Miedziany"
        page.reload(wait_until="networkidle")
        page.locator("#drucik-zapis").filter(has_text="wczytany").wait_for()
        assert page.locator('[name="imie"]').input_value() == "Miedziany"
        assert page.locator(".robot-scena").get_attribute("data-kolor") == "miedz"

        user["id"] = 18
        page.evaluate("FWAuth.uzytkownik.id=18; FWAuth.updateUI()")
        page.locator("#drucik-zapis").filter(has_text="pierwszego").wait_for()
        assert page.locator('[name="imie"]').input_value() == "Drucik"
        assert page.locator(".robot-scena").get_attribute("data-kolor") == "mosiadz"
        assert profiles[17]["profil"]["imie"] == "Miedziany"
        assert 18 not in profiles
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
        assert page.locator(".brand img").get_attribute("src").endswith("fwdrucik-naglowek.webp")
        assert page.locator('link[rel="icon"]').get_attribute("href").endswith("fwdrucik-znak-64.png")
        if out:
            mapa.screenshot(path=str(out / f"mapa-{width}.png"), style="header{visibility:hidden}")
            page.locator(".brand img").screenshot(path=str(out / f"naglowek-{width}.png"))
            page.locator("#obwody").screenshot(path=str(out / f"obwody-{width}.png"), style="header{visibility:hidden}")
            page.locator("#arduino").screenshot(path=str(out / f"arduino-{width}.png"), style="header{visibility:hidden}")
            page.locator("#druk-3d").screenshot(path=str(out / f"druk-{width}.png"), style="header{visibility:hidden}")
            page.locator("#twoj-drucik").screenshot(path=str(out / f"drucik-{width}.png"), style="header{visibility:hidden}")
        if width == 1440:
            page.emulate_media(reduced_motion="no-preference")
            page.locator("#blink-podglad").click()
            assert page.locator(".lekcja-dioda").evaluate("(d)=>d.getAnimations()[0].effect.getTiming().duration") == 2000
            page.evaluate("document.documentElement.classList.add('niebo-stop')")
            assert page.locator("#blink-podglad").is_disabled()
            assert page.locator(".lekcja-dioda").evaluate("(d)=>d.getAnimations().length") == 0
            page.evaluate("document.documentElement.classList.remove('niebo-stop')")
            page.get_by_role("button", name="Prawo Ohma").click()
            assert page.locator("#lab-lekcja-ohm").evaluate("(p)=>getComputedStyle(p).animationName") == "lab-dymek-wejscie"
            for action in ("glowa", "spacer", "czysci", "puka", "spawa", "tnie", "silnik", "elektronika"):
                page.evaluate("(action) => { FWDrucik.show(document.querySelector('[data-drucik-model]'), action); }", action)
                assert page.locator("[data-drucik-model]").get_attribute("data-czynnosc") == action
                if action not in ("glowa", "spacer"):
                    assert page.locator("[data-drucik-model] .drucik-rekwizyt svg").count() == 1
                if out and action == "spawa":
                    page.locator("#twoj-drucik").screenshot(path=str(out / "spawanie.png"), style="header{visibility:hidden}")
                page.wait_for_function("!document.querySelector('[data-drucik-model]').hasAttribute('data-czynnosc')")
        mapa.get_by_role("link", name="Kompendium dla dzieci").click()
        page.wait_for_url("**/pracownia/kompendium/", wait_until="domcontentloaded")
        assert page.locator("[data-haslo]:visible").count() == 30
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
        assert page.locator(".kurs-rysunek").count() == 30
        assert page.locator(".kurs-klip video").count() == 3
        for kod in ("e01", "a02", "d10"):
            obraz = page.locator(f"#{kod} .kurs-rysunek")
            obraz.scroll_into_view_if_needed()
            obraz.evaluate("(img) => img.decode()")
            assert obraz.evaluate("(img) => img.naturalWidth") == 880
        search = page.get_by_role("searchbox", name="Znajdź hasło")
        if out:
            search.scroll_into_view_if_needed()
            page.evaluate("window.scrollTo(0, 0)")
            page.screenshot(path=str(out / f"kompendium-{width}.png"))
        search.fill("plytka stykowa")
        assert page.locator("[data-haslo]:visible").count() == 1
        assert page.locator("#e03").is_visible()
        search.fill("nie-ma-takiego-hasla")
        assert page.locator("[data-haslo]:visible").count() == 0
        assert "Nie ma takiego hasła" in page.locator("[data-licznik-wiedzy]").inner_text()
        page.get_by_role("navigation", name="Działy kompendium").get_by_role("link", name="Elektronika").click()
        assert page.locator("[data-haslo]:visible").count() == 30
        search.fill("INPUT_PULLUP")
        assert page.locator("[data-haslo]:visible").count() == 1
        page.get_by_role("link", name="Zrób próbę: Wejście i wyjście").click()
        assert page.url.endswith("/pracownia/#proba-a02")
        lekcja = page.locator("#proba-a02")
        lekcja.get_by_role("button", name="HIGH").click()
        assert "Spróbuj jeszcze raz" in lekcja.locator("[data-wynik]").inner_text()
        lekcja.get_by_role("button", name="LOW").press("Enter")
        assert "Po wciśnięciu jest LOW" in lekcja.locator("[data-wynik]").inner_text()
        assert lekcja.get_by_role("button", name="LOW").get_attribute("aria-pressed") == "true"
        lekcja.get_by_role("link", name="Przeczytaj w kompendium").click()
        page.wait_for_url("**/pracownia/kompendium/#a02", wait_until="domcontentloaded")
        page.locator("#a02").wait_for()
        page.get_by_role("link", name="Zrób próbę: Kolory światła RGB").click()
        assert page.url.endswith("/pracownia/#proba-a06")
        rgb = page.locator("[data-rgb]")
        rgb.wait_for()
        rgb.get_by_role("checkbox", name="Czerwone").check()
        rgb.get_by_role("checkbox", name="Zielone").check()
        assert rgb.get_by_role("status").inner_text().strip() == "Żółte światło"
        rgb.get_by_role("checkbox", name="Niebieskie").check()
        assert rgb.get_by_role("status").inner_text().strip() == "Białe światło"
        context.close()
    offline = browser.new_context(java_script_enabled=False, reduced_motion="reduce", viewport={"width": 390, "height": 900})
    offline.route(lambda url: not url.startswith(f"http://127.0.0.1:{server.server_port}/"), lambda route: route.abort())
    page = offline.new_page()
    page.goto(f"http://127.0.0.1:{server.server_port}/pracownia/kompendium/")
    assert page.locator("[data-haslo]:visible").count() == 30
    page.get_by_role("link", name="Zrób próbę: Droga przewodu").click()
    lekcja = page.locator("#proba-d04")
    page.wait_for_url("**/pracownia/#proba-d04", wait_until="domcontentloaded")
    lekcja.locator("summary").press("Enter")
    lekcja.locator("[data-odpowiedz]").wait_for()
    offline.close()
    browser.close()
server.shutdown()
assert not errors, errors
print("OK: mapa, kompendium, wyszukiwanie, próby, płytka, RGB, profil i reduced motion")
