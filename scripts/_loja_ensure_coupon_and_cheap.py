# -*- coding: utf-8 -*-
"""Garante PRIMEIRACOMPRA5 + produto R$1,99 na loja para testes."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "loja.env"
OUT = Path(__file__).resolve().parents[1] / "scripts" / "_loja_cheap_fixture.json"


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def call(method, path, payload=None):
    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    data = None if payload is None else json.dumps(payload).encode()
    headers = {
        "Authorization": "Basic " + auth,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "pm-loja-fixture",
    }
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode()
            return r.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode()
        try:
            return err.code, json.loads(body)
        except json.JSONDecodeError:
            return err.code, {"raw": body[:400]}


def main():
    # coupon
    st, rows = call("GET", "/wp-json/wc/v3/coupons?" + urllib.parse.urlencode({"search": "PRIMEIRACOMPRA5", "per_page": 10}))
    coupon = None
    for c in rows if isinstance(rows, list) else []:
        if str(c.get("code") or "").lower() == "primeiracompra5":
            coupon = c
            break
    payload = {
        "code": "PRIMEIRACOMPRA5",
        "discount_type": "percent",
        "amount": "5",
        "individual_use": True,
        "usage_limit_per_user": 1,
        "exclude_sale_items": False,
        "description": "Ensaio / primeira compra 5%",
    }
    if coupon:
        st, coupon = call("PUT", f"/wp-json/wc/v3/coupons/{coupon['id']}", payload)
    else:
        st, coupon = call("POST", "/wp-json/wc/v3/coupons", payload)
    print("coupon", st, coupon.get("id") if isinstance(coupon, dict) else coupon, coupon.get("code") if isinstance(coupon, dict) else None)

    # cheap product
    st, rows = call("GET", "/wp-json/wc/v3/products?" + urllib.parse.urlencode({"sku": "produto-r-1", "per_page": 5}))
    prod = rows[0] if isinstance(rows, list) and rows else None
    pp = {
        "name": "Produto R$ 1,99",
        "type": "simple",
        "sku": "produto-r-1",
        "regular_price": "1.99",
        "status": "publish",
        "catalog_visibility": "hidden",
        "virtual": True,
        "description": "Produto de ensaio checkout. Hidden.",
        "meta_data": [{"key": "_pm_test_cheap", "value": "1"}],
    }
    if prod:
        st, prod = call("PUT", f"/wp-json/wc/v3/products/{prod['id']}", pp)
    else:
        st, prod = call("POST", "/wp-json/wc/v3/products", pp)
    print("product", st, prod.get("id") if isinstance(prod, dict) else prod, prod.get("price") if isinstance(prod, dict) else None)

    out = {
        "coupon_id": coupon.get("id") if isinstance(coupon, dict) else None,
        "product_id": prod.get("id") if isinstance(prod, dict) else None,
        "product_price": prod.get("price") if isinstance(prod, dict) else None,
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
