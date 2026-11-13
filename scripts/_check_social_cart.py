# -*- coding: utf-8 -*-
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
base = "https://pellomenosoficialteste.companygenesis.com.br"

print("=== local social ===")
social = ROOT / "public/images/social"
if social.exists():
    for p in sorted(social.iterdir()):
        print(p.name, p.stat().st_size)
else:
    print("NO public/images/social")

media = ROOT / "wordpress-loja/pm-home/media/images/social"
print("=== export media social ===")
if media.exists():
    for p in sorted(media.iterdir()):
        print(p.name, p.stat().st_size)
else:
    print("NO media/images/social")

print("=== remote social ===")
for i in range(1, 6):
    url = f"{base}/wp-content/uploads/pm-home/media/images/social/cliente-{i}.png"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read()
            print(f"cliente-{i}", r.status, len(data), r.headers.get("Content-Type"))
    except Exception as e:
        print(f"cliente-{i}", "ERR", e)

print("=== cart page ===")
html = urllib.request.urlopen(base + "/carrinho/", timeout=60).read().decode("utf-8", "replace")
for needle in [
    "100dvh-10.5rem",
    "data-pm-cart-state",
    "carrinho está vazio",
    "cart.js",
    "min-h-[",
]:
    print(needle, needle in html)

# cart.js remote
js = urllib.request.urlopen(base + "/wp-content/uploads/pm-home/cart.js", timeout=60).read().decode(
    "utf-8", "replace"
)
print("cart.js has SHELL min-h", "100dvh-10.5rem" in js)
print("cart.js len", len(js))
