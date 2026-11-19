"""Ładuje końcówkę razem z biblioteką — sam php -l nie wykrywa duplikatów."""
import json
from pathlib import Path
import subprocess
import unittest


class WpisyTest(unittest.TestCase):
    def test_endpoint_loads_with_shared_library(self):
        result = subprocess.run(
            ["php", "api/wpisy.php"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout),
                         {"ok": False, "blad": "Nieznana akcja."})


if __name__ == "__main__":
    unittest.main()
