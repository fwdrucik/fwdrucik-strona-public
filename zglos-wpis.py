# -*- coding: utf-8 -*-
"""
Melduje świeżo wygenerowany szkic do kolejki akceptacji w panelu admina.

    python zglos-wpis.py

Czyta .ostatni-wpis.json (zostawia go agent-bloga.py) i wysyła POST na
/api/wpisy.php?akcja=zglos z nagłówkiem X-Agent-Token. Token bierze ze
zmiennej AGENT_TOKEN — w GitHub Actions z sekretu repozytorium.

Powtórne zgłoszenie tego samego wpisu jest bezpieczne: końcówka odświeża
opis i nie tworzy duplikatu.
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
RAPORT = os.path.join(BASE, ".ostatni-wpis.json")
KONCOWKA = os.environ.get("API_WPISY", "https://fwdrucik.pl/api/wpisy.php?akcja=zglos")


def main():
    token = os.environ.get("AGENT_TOKEN", "").strip()
    if not token:
        print("Brak zmiennej AGENT_TOKEN.", file=sys.stderr)
        return 1
    if not os.path.isfile(RAPORT):
        print(f"Brak pliku {os.path.basename(RAPORT)} — agent nic nie wygenerował?",
              file=sys.stderr)
        return 1

    with open(RAPORT, encoding="utf-8") as f:
        wpis = json.load(f)

    dane = json.dumps({
        "slug": wpis["slug"],
        "tytul": wpis["tytul"],
        "lead": wpis["lead"],
        "url": wpis["url"],
        "run_url": os.environ.get("RUN_URL", ""),
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        KONCOWKA, data=dane, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8",
                 "X-Agent-Token": token},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as odp:
            tresc = odp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        # Treść błędu jest istotna: API odpowiada JSON-em z powodem odmowy.
        print(f"API odrzuciło zgłoszenie (HTTP {e.code}): "
              f"{e.read().decode('utf-8', 'replace')}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"Nie udało się połączyć z API: {e.reason}", file=sys.stderr)
        return 1

    print("Zgłoszono szkic:", wpis["slug"])
    print(tresc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
