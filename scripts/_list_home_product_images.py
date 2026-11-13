# -*- coding: utf-8 -*-
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "src/lib/data.ts").read_text(encoding="utf-8")
chunk = text.split("const catalogItems")[1].split("function defaultDescription")[0]
ids = re.findall(r'id: "([^"]+)"', chunk)

skip_prefixes = ("plano-", "cartao-", "body-splash")
home = []
for i in ids:
    if i == "produto-1-real":
        continue
    if i.startswith(skip_prefixes):
        continue
    if any(
        x in i
        for x in (
            "cera",
            "laser",
            "linha",
            "esfolia",
            "sobrancelha",
            "henna",
            "realce",
            "tintura",
            "design",
            "plus",
        )
    ):
        home.append(i)

print("service_products", len(home))
miss = []
for i in home:
    if i.endswith("-masc"):
        p = ROOT / f"public/images/products/male/{i}.png"
    else:
        p = ROOT / f"public/images/products/{i}.png"
    if not p.exists():
        miss.append(i)
print("missing_png", len(miss))
for i in home:
    print(i)
