# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "wordpress-loja" / "pm-home" / "home.html"
text = path.read_text(encoding="utf-8")
old = (
    '<div class="absolute inset-0 bg-[linear-gradient(to_right,transparent_0%,'
    "transparent_40%,rgb(112_0_83_/_0.5)_64%,var(--brand-primary)_100%)]\"></div>"
)
new = (
    '<div class="absolute inset-0 bg-[linear-gradient(to_right,transparent_0%,'
    "transparent_0%,#70005380_0%,var(--brand-primary)_100%)] md:hidden\"></div>"
    '<div class="absolute inset-0 hidden bg-[linear-gradient(to_right,transparent_0%,'
    "transparent_40%,rgb(112_0_83_/_0.5)_64%,var(--brand-primary)_100%)] md:block\"></div>"
)
if old not in text:
    raise SystemExit("old overlay not found in home.html")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("patched home.html")
