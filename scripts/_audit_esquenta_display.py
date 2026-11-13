# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
RELATED = ROOT / "wordpress-loja" / "pm-home" / "cart-related.json"
HOME = ROOT / "wordpress-loja" / "pm-home" / "home.html"
PDP = ROOT / "wordpress-loja" / "pm-home" / "products" / "axila-cera.html"
LASER = ROOT / "wordpress-loja" / "pm-home" / "products" / "axilas-laser.html"


def base():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e["PM_LOJA_URL"].rstrip("/")


def http(url):
    req = urllib.request.Request(url, headers={"User-Agent": "pm", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def main():
    related = json.loads(RELATED.read_text(encoding="utf-8"))
    products = related.get("products") or related
    for pid in ("axila-cera", "axilas-laser", "abdomen-cera", "buco-linha"):
        row = products.get(pid) or {}
        print(
            "cart-related",
            pid,
            "price",
            row.get("priceCents"),
            "original",
            row.get("originalCents"),
            "skip",
            row.get("skipDiscount"),
            "method",
            row.get("method"),
        )

    print("\n=== local home/PDP baked attrs ===")
    for path, label in ((HOME, "home"), (PDP, "axila-cera"), (LASER, "axilas-laser")):
        t = path.read_text(encoding="utf-8", errors="replace")
        print(label, "15% OFF", t.count("15% OFF"), "60% OFF", t.count("60% OFF"), "5% OFF", t.count("5% OFF"))
        attrs = re.findall(
            r'data-(?:product-id|id)="([^"]+)".{0,400}?data-rj-sale="(\d+)".{0,80}?data-rj-regular="(\d+)"',
            t,
            flags=re.S,
        )
        if not attrs:
            attrs = re.findall(r'data-rj-sale="(\d+)"[^>]*data-rj-regular="(\d+)"', t)
            print(label, "rj pairs", attrs[:5])
        else:
            print(label, "id-sale-reg", attrs[:5])

    # Visible price near product name in home
    t = HOME.read_text(encoding="utf-8", errors="replace")
    for name in ("Axila – Cera", "Axilas – Laser", "Buço – Linha"):
        i = t.find(name)
        chunk = t[i : i + 1200] if i >= 0 else ""
        prices = re.findall(r"R\$&nbsp;[\d.]+,\d{2}|R\$\s*[\d.]+,\d{2}", chunk)
        offs = re.findall(r"\d+%\s*OFF", chunk)
        print("home card", name, "prices", prices[:4], "offs", offs[:4])

    print("\n=== live vs local home 5%/15% ===")
    live = http(base() + "/")
    print("live 15%", live.count("15% OFF"), "60%", live.count("60% OFF"), "5%", live.count("5% OFF"))


if __name__ == "__main__":
    main()
