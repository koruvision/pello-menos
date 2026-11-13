# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import re
from pathlib import Path

PM = Path(__file__).resolve().parents[1] / "wordpress-loja" / "pm-home"
MEDIA = PM / "media" / "images" / "products"

hashes = {}
for path in list(MEDIA.glob("*.webp")) + list((MEDIA / "male").glob("*.webp")):
    key = f"male/{path.name}" if path.parent.name == "male" else path.name
    hashes[key] = hashlib.md5(path.read_bytes()).hexdigest()[:8]

pat = re.compile(
    r"media/images/products/((?:male/)?[A-Za-z0-9._\-]+\.webp)(?:\?v=([a-f0-9]{8}))?",
    re.I,
)

stale = []
pages = 0
for path in PM.rglob("*.html"):
    text = path.read_text(encoding="utf-8", errors="replace")
    if "images/products/" not in text:
        continue
    pages += 1
    for m in pat.finditer(text):
        rel, ver = m.group(1), m.group(2)
        want = hashes.get(rel)
        if want and ver != want:
            stale.append((str(path.relative_to(PM)), rel, ver, want))

print("html_with_product_imgs", pages)
print("stale_refs", len(stale))
for row in stale[:20]:
    print("STALE", row)
print("sample hash axila-cera", hashes.get("axila-cera.webp"))
print("sample hash axilas-laser", hashes.get("axilas-laser.webp"))
