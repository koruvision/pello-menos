# -*- coding: utf-8 -*-
"""Confirma home hero + fichas + data-* + cart-related alinhados à Esquenta."""
from __future__ import annotations

import json
import re
import urllib.request

BASE = "https://loja.pellomenos.com.br"
UA = {"User-Agent": "pm-align", "Cache-Control": "no-cache"}

EXPECT = {
    "perna-cera": (7302, 8590),
    "axilas-laser": (35996, 89990),
    "virilha-laser": (83600, 209000),
    "bracos-laser": (57600, 144000),
    "axila-cera": (2805, 3300),
}


def fetch(url: str) -> str:
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=60
    ).read().decode("utf-8", "replace")


def main() -> None:
    home = fetch(BASE + "/?v=align3")
    hero_ok = all(
        f">{reais}" in home
        for reais in ("73", "359", "836", "576")
    )
    print("hero_markers", hero_ok)

    cr = json.loads(fetch(BASE + "/wp-content/uploads/pm-home/cart-related.json?v=align3"))
    by_id = cr.get("byId") or cr.get("products") or cr
    print("cart-related keys sample", list(by_id)[:3] if isinstance(by_id, dict) else type(by_id))

    for pid, (sale, reg) in EXPECT.items():
        html = fetch(BASE + f"/produto/{pid}/?v=align3")
        ds = re.search(r'data-rj-sale="(\d+)"', html)
        dr = re.search(r'data-rj-regular="(\d+)"', html)
        got_s = int(ds.group(1)) if ds else None
        got_r = int(dr.group(1)) if dr else None
        row = None
        if isinstance(by_id, dict):
            row = by_id.get(pid)
            if not row and "items" in cr:
                row = (cr.get("items") or {}).get(pid)
        orig = row.get("originalCents") if isinstance(row, dict) else None
        ok = got_s == sale and got_r == reg
        print(pid, "page", got_s, got_r, "expect", sale, reg, "ok", ok, "cartOrig", orig)


if __name__ == "__main__":
    main()
