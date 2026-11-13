# -*- coding: utf-8 -*-
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
home = (ROOT / "wordpress-loja/pm-home/home.html").read_text(encoding="utf-8")
print("has 1real", "produto-1-real" in home)
i = home.find("produto-1-real")
print(home[max(0, i - 100) : i + 350])
# ensure gift image exists as jpg in media
p = ROOT / "wordpress-loja/pm-home/media/images/products/cartao-presente-80.jpg"
print("gift jpg", p.exists(), p.stat().st_size if p.exists() else 0)
# fix card image if still png
if "cartao-presente-80.png" in home:
    home = home.replace("cartao-presente-80.png", "cartao-presente-80.jpg")
    (ROOT / "wordpress-loja/pm-home/home.html").write_text(home, encoding="utf-8")
    print("fixed png->jpg in home")
# plan docs sample
silver = (ROOT / "wordpress-loja/pm-home/products/plano-silver.html").read_text(encoding="utf-8")
print("silver docs", "contrato-planos-assinaturas-vip" in silver)
print("ScrollTrigger idle", "requestIdleCallback" in (ROOT / "wordpress-loja/pm-home/home.js").read_text(encoding="utf-8"))
