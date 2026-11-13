# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "loja.env"
SKUS = json.loads((Path(__file__).resolve().parents[1] / "scripts" / "_loja_esquenta_test_skus.json").read_text(encoding="utf-8"))


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def main():
    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    nonce = ""
    cart_token = ""

    def call(method, path, payload=None, use_auth=True):
        nonlocal nonce, cart_token
        data = None if payload is None else json.dumps(payload).encode()
        headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "pm"}
        if use_auth:
            headers["Authorization"] = "Basic " + auth
        if nonce:
            headers["Nonce"] = nonce
        if cart_token:
            headers["Cart-Token"] = cart_token
        req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode()
            nonce = r.headers.get("Nonce") or r.headers.get("nonce") or nonce
            cart_token = r.headers.get("Cart-Token") or r.headers.get("cart-token") or cart_token
            return r.status, json.loads(body) if body else {}

    for code in ("PRIMEIRACOMPRA5", "primeiracompra5"):
        st, rows = call("GET", "/wp-json/wc/v3/coupons?" + urllib.parse.urlencode({"code": code}))
        print("coupon", code, st, [(c.get("id"), c.get("code"), c.get("amount"), c.get("discount_type")) for c in (rows or [])])

    # cheap products
    st, rows = call("GET", "/wp-json/wc/v3/products?" + urllib.parse.urlencode({"search": "1,99", "per_page": 10}))
    for p in rows or []:
        print("prod", p.get("id"), p.get("slug"), p.get("price"), p.get("status"), p.get("catalog_visibility"))

    # cart flow guest-like (no basic auth on store?) with auth
    call("GET", "/wp-json/wc/store/v1/cart")
    st, cart = call("POST", "/wp-json/wc/store/v1/cart/add-item", {"id": SKUS["pm-teste-esquenta-laser"], "quantity": 1, "pm_catalog_id": "pm-teste-esquenta-laser"})
    print("add", st, "items", len(cart.get("items") or []), "total", (cart.get("totals") or {}).get("total_price"))
    try:
        st, cart2 = call("POST", "/wp-json/wc/store/v1/cart/apply-coupon", {"code": "PRIMEIRACOMPRA5"})
        print("apply", st, "items", len(cart2.get("items") or []), "total", (cart2.get("totals") or {}).get("total_price"), "disc", (cart2.get("totals") or {}).get("total_discount"), "coupons", cart2.get("coupons"), "errors", cart2.get("code") or cart2.get("message"))
    except Exception as err:
        print("apply err", err)


if __name__ == "__main__":
    main()
