# -*- coding: utf-8 -*-
"""Compara preços Esquenta: home vs ficha vs Store API (loja)."""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

BASE = "https://loja.pellomenos.com.br"
UA = {"User-Agent": "pm-price-probe", "Cache-Control": "no-cache"}

# slugs que aparecem no hero / destaques
PRODUCTS = [
    ("perna-cera", "/produto/perna-cera/"),
    ("axilas-laser", "/produto/axilas-laser/"),
    ("virilha-laser", "/produto/virilha-laser/"),
    ("bracos-laser", "/produto/bracos-laser/"),
    ("axila-cera", "/produto/axila-cera/"),
]


def fetch(url: str) -> str:
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=60
    ).read().decode("utf-8", "replace")


def prices_in(html: str) -> list[str]:
    # R$ X,XX patterns near product
    return re.findall(r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}", html)


def extract_product_card_prices(html: str, needle: str) -> dict:
    i = html.lower().find(needle.lower())
    if i < 0:
        return {"found": False}
    chunk = html[max(0, i - 200) : i + 1200]
    prices = prices_in(chunk)
    return {"found": True, "prices": prices[:8], "snippet": re.sub(r"\s+", " ", chunk)[:280]}


def main() -> None:
    home = fetch(BASE + "/?v=price1")
    print("HOME phase hints", {
        "esquenta": home.lower().count("esquenta"),
        "__PM_BLACK_PHASE__": "__PM_BLACK_PHASE__" in home,
        "phase_json": re.search(r"__PM_BLACK_PHASE__\s*=\s*['\"]?(\w+)", home),
    })
    m = re.search(r"__PM_BLACK_PHASE__\s*=\s*['\"]([^'\"]+)", home)
    print("phase", m.group(1) if m else "missing")

    rows = []
    for pid, path in PRODUCTS:
        row = {"id": pid, "path": path}
        # home mentions
        row["home"] = extract_product_card_prices(home, pid)
        # also try name-based for hero baked
        # product page
        try:
            prod = fetch(BASE + path + "?v=price1")
            row["product"] = {
                "prices": prices_in(prod)[:12],
                "has_sale": "sale" in prod.lower() or "riscad" in prod.lower() or "line-through" in prod,
            }
            # look for data attrs
            for attr in ("data-price", "data-sale", "regularCents", "saleCents", "originalCents"):
                if attr in prod:
                    row["product"][attr] = True
        except Exception as e:
            row["product"] = {"err": str(e)}
        rows.append(row)
        print(pid, "home", row["home"].get("prices"), "product", row["product"].get("prices") or row["product"])

    # cart-related / bridge sample
    try:
        bridge = fetch(BASE + "/wp-content/uploads/pm-home/woo-bridge.json?v=price1")
        bj = json.loads(bridge)
        for pid, _ in PRODUCTS:
            entry = bj.get(pid) or bj.get("products", {}).get(pid) if isinstance(bj, dict) else None
            if entry is None and isinstance(bj, dict):
                # nested
                for k, v in bj.items():
                    if k == pid or (isinstance(v, dict) and v.get("id") == pid):
                        entry = v
                        break
            print("bridge", pid, entry if not isinstance(entry, dict) else {k: entry.get(k) for k in ("productId", "regularCents", "saleCents", "priceCents", "regular_price", "sale_price") if k in entry or True})
    except Exception as e:
        print("bridge fail", e)

    out = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "loja-esquenta-price-probe.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
