# -*- coding: utf-8 -*-
from pathlib import Path
import re
import shutil

root = Path("wordpress-loja/pm-home")
for name in ("products/axila-cera.html", "products/produto-1-real.html", "carrinho.html"):
    t = (root / name).read_text(encoding="utf-8")
    print("===", name)
    print("R$ 1,00", t.count("R$ 1,00") + t.count("R$\xa01,00"))
    moneys = re.findall(r"R\$\s*[\d.,]+", t)
    print("unique money sample", sorted(set(moneys))[:12])
    print("cart.js", re.findall(r"cart\.js\?v=[^\"]+", t)[:3])

# sync bridge + product-copy into pm-home
shutil.copy2("src/lib/woo-bridge.json", root / "woo-bridge.json")
pc = Path("src/lib/product-copy.json")
if pc.is_file():
    shutil.copy2(pc, root / "product-copy.json")
print("synced woo-bridge + product-copy")
