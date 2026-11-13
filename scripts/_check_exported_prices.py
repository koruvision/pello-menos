# -*- coding: utf-8 -*-
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "wordpress-loja" / "pm-home" / "products"
for name in [
    "axilas-laser",
    "perna-cera",
    "virilha-laser",
    "bracos-laser",
    "axila-cera",
]:
    html = (ROOT / f"{name}.html").read_text(encoding="utf-8")
    sale = re.search(r'data-rj-sale="(\d+)"', html)
    reg = re.search(r'data-rj-regular="(\d+)"', html)
    print(name, sale.group(1) if sale else None, reg.group(1) if reg else None)
