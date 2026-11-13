# -*- coding: utf-8 -*-
"""Probe loja products related to R$1,99 / PM-0001 / produto1real."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "loja.env"


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def call(path):
    e = env()
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    req = urllib.request.Request(
        e["PM_LOJA_URL"].rstrip("/") + path,
        headers={"Authorization": "Basic " + auth, "Accept": "application/json", "User-Agent": "pm-probe"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode()[:400]


def main():
    queries = [
        ("sku", "produto-r-1"),
        ("sku", "PM-0001"),
        ("search", "1,99"),
        ("search", "Produto R$"),
        ("search", "produto1real"),
        ("search", "PEL-PRODUTO"),
    ]
    seen = set()
    for key, val in queries:
        st, rows = call("/wp-json/wc/v3/products?" + urllib.parse.urlencode({key: val, "per_page": 20}))
        print("===", key, val, st, "count", len(rows) if isinstance(rows, list) else rows)
        if isinstance(rows, list):
            for p in rows:
                if p["id"] in seen:
                    continue
                seen.add(p["id"])
                metas = {m.get("key"): m.get("value") for m in (p.get("meta_data") or [])}
                print(
                    json.dumps(
                        {
                            "id": p.get("id"),
                            "name": p.get("name"),
                            "sku": p.get("sku"),
                            "price": p.get("price"),
                            "status": p.get("status"),
                            "catalog_visibility": p.get("catalog_visibility"),
                            "purchasable": p.get("purchasable"),
                            "stock_status": p.get("stock_status"),
                            "pm_catalog_id": metas.get("_pm_catalog_id") or metas.get("pm_catalog_id"),
                        },
                        ensure_ascii=False,
                    )
                )

    # try add-item for known fixture if present
    fix = Path(__file__).resolve().parents[1] / "scripts" / "_loja_cheap_fixture.json"
    if fix.is_file():
        pid = int(json.loads(fix.read_text(encoding="utf-8")).get("product_id") or 0)
        print("fixture", pid)
        if pid:
            # Store API guest cart add
            e = env()
            base = e["PM_LOJA_URL"].rstrip("/")
            # get cart
            req = urllib.request.Request(base + "/wp-json/wc/store/v1/cart", headers={"Accept": "application/json", "User-Agent": "pm"})
            with urllib.request.urlopen(req, timeout=60) as r:
                nonce = r.headers.get("Nonce") or r.headers.get("nonce")
                cart_token = r.headers.get("Cart-Token") or r.headers.get("cart-token")
            payload = json.dumps({"id": pid, "quantity": 1, "pm_catalog_id": "produto-1-real"}).encode()
            req = urllib.request.Request(
                base + "/wp-json/wc/store/v1/cart/add-item",
                data=payload,
                method="POST",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Nonce": nonce or "",
                    "Cart-Token": cart_token or "",
                    "User-Agent": "pm",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = json.loads(r.read().decode())
                    print("add-item ok", (body.get("totals") or {}).get("total_price"), len(body.get("items") or []))
            except urllib.error.HTTPError as err:
                print("add-item fail", err.code, err.read().decode()[:500])


if __name__ == "__main__":
    main()
