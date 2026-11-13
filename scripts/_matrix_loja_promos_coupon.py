# -*- coding: utf-8 -*-
"""Matriz Store API na LOJA: Esquenta calendário + cupom (sem FORCE black_week)."""
from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
SKUS = json.loads((ROOT / "scripts" / "_loja_esquenta_test_skus.json").read_text(encoding="utf-8"))
OUT = ROOT / "scripts" / "_matrix_loja_promos_coupon_result.json"
COUPON = "PRIMEIRACOMPRA5"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return {
        "url": e["PM_LOJA_URL"].rstrip("/"),
        "user": e["PM_LOJA_USER"],
        "password": e["PM_LOJA_APP_PASSWORD"],
    }


def main():
    c = cfg()
    token = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    nonce = ""
    cart_token = ""
    results = []
    ok = True

    def call(method, path, payload=None, auth=True):
        nonlocal nonce, cart_token
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "User-Agent": "pm-loja-matrix",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if auth:
            headers["Authorization"] = "Basic " + token
        if nonce:
            headers["Nonce"] = nonce
        if cart_token:
            headers["Cart-Token"] = cart_token
        req = urllib.request.Request(c["url"] + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read().decode("utf-8", "replace")
                n = r.headers.get("Nonce") or r.headers.get("nonce")
                ct = r.headers.get("Cart-Token") or r.headers.get("cart-token")
                if n:
                    nonce = n
                if ct:
                    cart_token = ct
                return r.status, (json.loads(body) if body else {})
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(body) if body else {}
            except json.JSONDecodeError:
                parsed = {"raw": body[:400]}
            return err.code, parsed

    def clear():
        st, cart = call("GET", "/wp-json/wc/store/v1/cart")
        for item in list(cart.get("items") or []):
            if item.get("key"):
                call("POST", "/wp-json/wc/store/v1/cart/remove-item", {"key": item["key"]})
        st, cart = call("GET", "/wp-json/wc/store/v1/cart")
        for coup in list(cart.get("coupons") or []):
            code = coup.get("code")
            if code:
                call("POST", "/wp-json/wc/store/v1/cart/remove-coupon", {"code": code})

    def add(cid):
        pid = int(SKUS[cid])
        return call(
            "POST",
            "/wp-json/wc/store/v1/cart/add-item",
            {"id": pid, "quantity": 1, "pm_catalog_id": cid},
        )

    def snap(label, cart, expect_total=None, expect_rate=None):
        nonlocal ok
        totals = cart.get("totals") or {}
        items = cart.get("items") or []
        total = int(totals.get("total_price") or 0)
        discount = int(totals.get("total_discount") or 0)
        lines = []
        rate_ok = True
        for it in items:
            prices = it.get("prices") or {}
            reg = int(prices.get("regular_price") or 0)
            price = int(prices.get("price") or 0)
            lines.append({"name": (it.get("name") or "")[:40], "price": price, "regular": reg})
            if expect_rate is not None and reg > 0:
                exp = int(reg * (1 - expect_rate) + 0.5)
                if abs(price - exp) > 1:
                    rate_ok = False
        passed = True
        if expect_total is not None and total != expect_total:
            passed = False
        if expect_rate is not None and not rate_ok:
            passed = False
        row = {
            "label": label,
            "total": total,
            "discount": discount,
            "coupons": [x.get("code") for x in (cart.get("coupons") or [])],
            "lines": lines,
            "ok": passed,
        }
        results.append(row)
        print(("OK" if passed else "FAIL"), label, "total", total, "disc", discount, lines)
        if not passed:
            ok = False

    # cheap normal product (fixture or search)
    normal_id = None
    fixture = ROOT / "scripts" / "_loja_cheap_fixture.json"
    if fixture.is_file():
        try:
            normal_id = int(json.loads(fixture.read_text(encoding="utf-8")).get("product_id") or 0) or None
        except Exception:
            normal_id = None
    if not normal_id:
        st, prods = call(
            "GET",
            "/wp-json/wc/v3/products?" + urllib.parse.urlencode({"sku": "produto-r-1", "per_page": 5}),
        )
        if st == 200 and isinstance(prods, list) and prods:
            normal_id = int(prods[0]["id"])
    print("normal_id", normal_id)

    clear()
    add("pm-teste-esquenta-laser")
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("esquenta laser 60%", cart, expect_total=200, expect_rate=0.6)

    clear()
    for cid in ("pm-teste-esquenta-laser", "pm-teste-esquenta-laser-b", "pm-teste-esquenta-laser-c"):
        add(cid)
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("esquenta laser multi 65%", cart, expect_total=525, expect_rate=0.65)

    clear()
    add("pm-teste-esquenta-cera")
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("esquenta cera 15%", cart, expect_total=425, expect_rate=0.15)

    clear()
    for cid in ("pm-teste-esquenta-cera", "pm-teste-esquenta-cera-b", "pm-teste-esquenta-cera-c"):
        add(cid)
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("esquenta cera multi 20%", cart, expect_total=1200, expect_rate=0.2)

    clear()
    add("pm-teste-esquenta-laser")
    st, cart = call("POST", "/wp-json/wc/store/v1/cart/apply-coupon", {"code": COUPON})
    total = int((cart.get("totals") or {}).get("total_price") or 0)
    snap("esquenta laser + PRIMEIRACOMPRA5", cart)
    if total not in (190,):
        print("WARN coupon total", total)
        if int((cart.get("totals") or {}).get("total_discount") or 0) <= 0:
            ok = False
            results[-1]["ok"] = False
    else:
        results[-1]["ok"] = True

    if normal_id:
        clear()
        call("POST", "/wp-json/wc/store/v1/cart/add-item", {"id": normal_id, "quantity": 1})
        st, cart = call("GET", "/wp-json/wc/store/v1/cart")
        snap("normal produto barato", cart)
        clear()
        call("POST", "/wp-json/wc/store/v1/cart/add-item", {"id": normal_id, "quantity": 1})
        st, cart = call("POST", "/wp-json/wc/store/v1/cart/apply-coupon", {"code": COUPON})
        disc = int((cart.get("totals") or {}).get("total_discount") or 0)
        snap("normal + PRIMEIRACOMPRA5", cart)
        if disc <= 0:
            ok = False
            results[-1]["ok"] = False
    else:
        results.append({"label": "normal produto-r-1", "ok": False, "skipped": "not found"})
        print("SKIP normal produto-r-1 not found")

    OUT.write_text(
        json.dumps({"ok": ok, "ts": int(time.time()), "normal_id": normal_id, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("wrote", OUT)
    if not ok:
        raise SystemExit("LOJA_MATRIX_FAIL")
    print("LOJA_MATRIX_OK")


if __name__ == "__main__":
    main()
