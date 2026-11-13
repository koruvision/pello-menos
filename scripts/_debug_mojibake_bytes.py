# -*- coding: utf-8 -*-
from pathlib import Path

text = Path("wordpress-loja/pm-home/products/axila-cera.html").read_text(encoding="utf-8-sig")
bad = sorted({ch for ch in text if ord(ch) > 255})
print("chars_ord>255", len(bad))
print("sample", [hex(ord(c)) + " " + repr(c) for c in bad[:40]])

# try encode ignoring those by replacing temporarily
trans = {ord(c): "?" for c in bad}
tmp = text.translate(trans)
fixed = tmp.encode("latin-1").decode("utf-8")
print("after latin-1 roundtrip Início", "Início" in fixed, "InÃ­cio" in fixed)
print("Ã count before/after", text.count("Ã"), fixed.count("Ã"))
