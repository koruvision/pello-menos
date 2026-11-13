# -*- coding: utf-8 -*-
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
t = (ROOT / "wordpress-loja/pm-home/home.html").read_text(encoding="utf-8")
imgs = sorted(set(re.findall(r"media/images/hero/[A-Za-z0-9_./\-]+", t)))
print("count", len(imgs))
for i in imgs:
    print(i)
d = (ROOT / "src/lib/data.ts").read_text(encoding="utf-8")
for name in ["hero-campaign-low", "hero-campaign-center", "destaque-combo"]:
    print(name, "png" if f"{name}.png" in d else "-", "jpg" if f"{name}.jpg" in d else "-")
