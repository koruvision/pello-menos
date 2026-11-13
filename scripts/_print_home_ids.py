# -*- coding: utf-8 -*-
import re
from pathlib import Path
from scripts._home_image_specs import prompt_for, method_of

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "src/lib/data.ts").read_text(encoding="utf-8")
chunk = text.split("const catalogItems")[1].split("function defaultDescription")[0]
ids = re.findall(r'id: "([^"]+)"', chunk)
home = [
    i
    for i in ids
    if i != "produto-1-real"
    and not i.startswith(("plano-", "cartao-", "body-splash"))
    and any(
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
    )
]
print("COUNT", len(home))
for i in home:
    print(f"{i}\t{method_of(i)}")
