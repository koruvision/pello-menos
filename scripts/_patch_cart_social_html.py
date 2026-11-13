# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "wordpress-loja" / "pm-home"
MINH = " min-h-[calc(100dvh-10.5rem)] sm:min-h-[calc(100dvh-11rem)] md:min-h-[calc(100dvh-9rem)]"
FLEX_OLD = 'class="flex-1"'
FLEX_NEW = 'class="flex flex-1 flex-col"'

n_home = n_cart = n_shell = n_minh = 0
for path in ROOT.rglob("*.html"):
    text = path.read_text(encoding="utf-8")
    orig = text
    if "home.js?v=premium3" in text:
        text = text.replace("home.js?v=premium3", "home.js?v=premium4")
        n_home += 1
    if "cart.js?v=cart11" in text or "cart.js?v=cart9" in text:
        text = text.replace("cart.js?v=cart11", "cart.js?v=cart12").replace(
            "cart.js?v=cart9", "cart.js?v=cart12"
        )
        n_cart += 1
    if FLEX_OLD in text and FLEX_NEW not in text:
        # Only the SiteShell children wrapper appears once as exact class="flex-1"
        text = text.replace(FLEX_OLD, FLEX_NEW, 1)
        n_shell += 1
    if MINH in text:
        text = text.replace(MINH, "")
        n_minh += 1
    if text != orig:
        path.write_text(text, encoding="utf-8")

print("home bump", n_home)
print("cart bump", n_cart)
print("shell flex", n_shell)
print("minh removed", n_minh)
