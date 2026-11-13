# -*- coding: utf-8 -*-
from pathlib import Path
import re

root = Path("wordpress-loja/pm-home")
for name in ("products/axila-cera.html", "products/produto-1-real.html", "carrinho.html"):
    p = root / name
    t = p.read_text(encoding="utf-8")
    print("===", name)
    print("R$ 1,00 count", t.count("R$ 1,00") + t.count("R$\xa01,00"))
    print("31,35", "31,35" in t)
    print("33,00", "33,00" in t)
    print("cart.js", re.findall(r"cart\.js\?v=[^\"]+", t)[:3])
    # find money near product title
    for m in re.finditer(r"R\$\s*[\d.,]+", t):
        if m.start() > 50000:
            print("sample money", m.group(0))
            break
