# -*- coding: utf-8 -*-
"""Remove sync ScrollTrigger tags; bump home.js?v=premium4 -> premium5."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "wordpress-loja" / "pm-home"
ST = '<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/ScrollTrigger.min.js"></script>\n'
ST2 = '<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/ScrollTrigger.min.js"></script>'
n = 0
for path in ROOT.rglob("*.html"):
    text = path.read_text(encoding="utf-8")
    orig = text
    text = text.replace(ST, "").replace(ST2, "")
    text = text.replace("home.js?v=premium4", "home.js?v=premium5")
    if text != orig:
        path.write_text(text, encoding="utf-8")
        n += 1
print("patched html", n)
