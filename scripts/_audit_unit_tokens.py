# -*- coding: utf-8 -*-
"""Audita se cada productId do cart-related.json e de fato o pai das variationIds das units."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CR = ROOT / "wordpress-loja" / "pm-home" / "cart-related.json"


def env() -> dict:
    e = {}
    p = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
    for line in p.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


def main() -> None:
    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    tok = base64.b64encode(
        f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()
    h = {"Authorization": "Basic " + tok, "User-Agent": "pm-audit"}

    def get(path: str):
        req = urllib.request.Request(base + path, headers=h)
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)

    products = json.loads(CR.read_text(encoding="utf-8"))["products"]
    parents: dict[str, list[str]] = {}
    for pid, row in products.items():
        p = str(row.get("productId") or "")
        if p:
            parents.setdefault(p, []).append(pid)

    print("produtos:", len(products), "| productIds distintos:", len(parents))
    bad_parent = []
    for p in sorted(parents):
        try:
            d = get(f"/wp-json/wc/v3/products/{p}")
        except Exception as exc:
            bad_parent.append((p, parents[p][:3], "HTTP " + str(exc)))
            continue
        if d.get("type") == "variation":
            bad_parent.append((p, parents[p][:3], "E UMA VARIACAO (pai=" + str(d.get("parent_id")) + ")"))
    print("\nproductId que NAO e produto variável:", len(bad_parent))
    for p, who, why in bad_parent[:40]:
        print(f"  {p}: {why}  <- {', '.join(who)}")

    mismatch = []
    checked = 0
    for p in sorted(parents):
        if any(x[0] == p for x in bad_parent):
            continue
        try:
            vs = get(f"/wp-json/wc/v3/products/{p}/variations?per_page=100")
        except Exception:
            continue
        vids = {str(v.get("id")) for v in vs}
        for pid in parents[p]:
            for uid, meta in (products[pid].get("units") or {}).items():
                vid = str(meta.get("variationId") or "")
                if not vid:
                    continue
                checked += 1
                if vid not in vids:
                    mismatch.append((pid, uid, vid, meta.get("option")))
    print(f"\nvariationIds checados: {checked} | fora do pai: {len(mismatch)}")
    for row in mismatch[:40]:
        print("  ", row)


if __name__ == "__main__":
    main()