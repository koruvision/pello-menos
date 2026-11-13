# -*- coding: utf-8 -*-
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "wordpress-loja" / "pm-home" / "products"
for name in [
    "plano-silver",
    "plano-silver-masc",
    "body-splash-livre",
    "body-splash-livre-masc",
    "plano-gold",
]:
    t = (ROOT / f"{name}.html").read_text(encoding="utf-8")
    imgs = re.findall(r"/images/products/[^\"']*(?:plano|body-splash)[^\"']*", t)
    print(name, imgs[:5])
