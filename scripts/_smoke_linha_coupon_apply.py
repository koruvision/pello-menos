# -*- coding: utf-8 -*-
"""Smoke: aplica cupom linha-1real num carrinho Store API (sessao efemera)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
COUPON = ROOT / "projeto-migracao" / ".secrets" / "linha-1real-coupon.json"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e["PM_LOJA_URL"].rstrip("/")


def main() -> None:
    base = cfg()
    info = json.loads(COUPON.read_text(encoding="utf-8"))
    code = info["code"]
    # buco-linha parent + first variation from bridge would be better;
    # use parent add-item with variation if required.
    product_id = int(info["products"][0]["id"])
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def req(method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-linha-coupon-smoke",
            "Nonce": "pm",
        }
        # Store API needs nonce from cart token — get cart first
        r = urllib.request.Request(base + path, data=data, method=method, headers=headers)
        try:
            with opener.open(r, timeout=60) as resp:
                body = resp.read().decode("utf-8", "replace")
                nonce = resp.headers.get("Nonce") or resp.headers.get("nonce")
                cart_token = resp.headers.get("Cart-Token") or resp.headers.get("cart-token")
                return resp.status, json.loads(body) if body else {}, nonce, cart_token, resp.headers
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body[:400]}
            return err.code, parsed, err.headers.get("Nonce"), err.headers.get("Cart-Token"), err.headers

    # Bootstrap cart
    st, cart, nonce, token, headers = req("GET", "/wp-json/wc/store/v1/cart")
    print("cart_get", st, "nonce", bool(nonce), "token", bool(token))
    nonce = nonce or headers.get("Nonce")
    token = token or headers.get("Cart-Token")

    def authed(method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-linha-coupon-smoke",
        }
        if nonce:
            h["Nonce"] = nonce
        if token:
            h["Cart-Token"] = token
        r = urllib.request.Request(base + path, data=data, method=method, headers=h)
        try:
            with opener.open(r, timeout=60) as resp:
                body = resp.read().decode("utf-8", "replace")
                return resp.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            try:
                return err.code, json.loads(body)
            except Exception:
                return err.code, {"raw": body[:500]}

    # Need a variation — fetch product
    st, prod = authed("GET", f"/wp-json/wc/store/v1/products/{product_id}")
    print("product", st, type(prod), (prod.get("type") if isinstance(prod, dict) else None))
    variation_id = None
    if isinstance(prod, dict):
        variations = prod.get("variations") or []
        if variations:
            variation_id = variations[0] if isinstance(variations[0], int) else variations[0].get("id")
        add_ids = prod.get("add_to_cart") or {}
    print("variation", variation_id)

    # Try add from bridge first variation via wc/v3 if store fails
    bridge = json.loads((ROOT / "src/lib/woo-bridge.json").read_text(encoding="utf-8"))
    units = (bridge.get("buco-linha") or {}).get("units") or {}
    first_unit = next(iter(units.values()), {})
    variation_id = variation_id or first_unit.get("variationId")
    print("using variation", variation_id)

    st, added = authed(
        "POST",
        "/wp-json/wc/store/v1/cart/add-item",
        {"id": variation_id or product_id, "quantity": 1},
    )
    print("add", st, added.get("items") if isinstance(added, dict) else added)
    if st >= 400:
        print("ADD_FAIL", added)
        raise SystemExit(1)

    st, applied = authed(
        "POST",
        "/wp-json/wc/store/v1/cart/apply-coupon",
        {"code": code},
    )
    print("apply", st)
    if isinstance(applied, dict):
        totals = applied.get("totals") or {}
        print(
            "total_items",
            totals.get("total_items"),
            "total_price",
            totals.get("total_price"),
            "discount",
            totals.get("total_discount"),
            "coupons",
            applied.get("coupons"),
        )
        # minor units: 100 = R$1.00
        total = int(totals.get("total_price") or 0)
        if total != 100:
            print("WARN expected total_price 100 (R$1), got", total)
        else:
            print("SMOKE_LINHA_1REAL_OK")
    else:
        print(applied)


if __name__ == "__main__":
    main()
