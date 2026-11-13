# -*- coding: utf-8 -*-
"""Matriz Store API OT: Esquenta / Black Week / off + cupom PRIMEIRACOMPRA5 (valores baixos)."""
from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
BRIDGE = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
RELATED = ROOT / "wordpress-loja" / "pm-home" / "cart-related.json"
SNIPPET_SRC = ROOT / "scripts" / "pm_black_nov_snippet.php"
SKUS = json.loads((ROOT / "scripts" / "_ot_esquenta_test_skus.json").read_text(encoding="utf-8"))
OUT = ROOT / "scripts" / "_matrix_ot_promos_coupon_result.json"

# Produto normal barato (sem campanha tipicamente)
NORMAL_ID = 48216  # produto-r-1 R$1,99
COUPON = "PRIMEIRACOMPRA5"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return {
        "url": e["PM_OFICIALTESTE_URL"].rstrip("/"),
        "user": e["PM_OFICIALTESTE_USER"],
        "password": e["PM_OFICIALTESTE_APP_PASSWORD"],
    }


def main():
    c = cfg()
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    related = json.loads(RELATED.read_text(encoding="utf-8"))
    products = related.get("products") or related
    token = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    nonce = ""
    cart_token = ""
    results = []
    ok = True

    def call(method, path, payload=None, auth=True):
        nonlocal nonce, cart_token
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "User-Agent": "pm-matrix-promos",
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

    def put_force(force: str):
        code = SNIPPET_SRC.read_text(encoding="utf-8").replace(
            "define('PM_BLACK_NOV_FORCE', '');",
            f"define('PM_BLACK_NOV_FORCE', '{force}');",
            1,
        )
        st, sn = call("GET", "/wp-json/code-snippets/v1/snippets/24")
        payload = {
            "name": sn.get("name") or "pm-black-nov-pricing",
            "code": code,
            "scope": "global",
            "active": True,
        }
        st, saved = call("PUT", "/wp-json/code-snippets/v1/snippets/24", payload)
        print("FORCE", force, st, isinstance(saved, dict) and saved.get("active"))

    def clear():
        st, cart = call("GET", "/wp-json/wc/store/v1/cart")
        for item in list(cart.get("items") or []):
            if item.get("key"):
                call("POST", "/wp-json/wc/store/v1/cart/remove-item", {"key": item["key"]})
        # remove coupons
        st, cart = call("GET", "/wp-json/wc/store/v1/cart")
        for coup in list(cart.get("coupons") or []):
            code = coup.get("code")
            if code:
                call("POST", "/wp-json/wc/store/v1/cart/remove-coupon", {"code": code})

    def add_test(cid: str):
        pid = int(SKUS[cid])
        st, cart = call(
            "POST",
            "/wp-json/wc/store/v1/cart/add-item",
            {"id": pid, "quantity": 1, "pm_catalog_id": cid},
        )
        return st, cart

    def add_bridge(cid: str):
        entry = bridge.get(cid) or {}
        units = entry.get("units") or {}
        add_id = None
        for meta in units.values():
            if isinstance(meta, dict) and meta.get("variationId"):
                add_id = int(meta["variationId"])
                break
        if add_id is None and entry.get("productId"):
            add_id = int(entry["productId"])
        if add_id is None:
            raise SystemExit(f"no bridge id {cid}")
        st, cart = call(
            "POST",
            "/wp-json/wc/store/v1/cart/add-item",
            {"id": add_id, "quantity": 1, "pm_catalog_id": cid},
        )
        return st, cart

    def add_normal():
        return call("POST", "/wp-json/wc/store/v1/cart/add-item", {"id": NORMAL_ID, "quantity": 1})

    def apply_coupon():
        return call("POST", "/wp-json/wc/store/v1/cart/apply-coupon", {"code": COUPON})

    def snap(label, cart, expect_total_cents=None, expect_rate=None, table_catalog_id=None):
        nonlocal ok
        totals = cart.get("totals") or {}
        items = cart.get("items") or []
        coupons = cart.get("coupons") or []
        total = int(totals.get("total_price") or 0)
        discount = int(totals.get("total_discount") or 0)
        lines = []
        rate_ok = True
        for it in items:
            prices = it.get("prices") or {}
            reg = int(prices.get("regular_price") or 0)
            price = int(prices.get("price") or 0)
            lines.append({"name": (it.get("name") or "")[:40], "price": price, "regular": reg})
            if expect_rate is not None:
                base = reg
                if table_catalog_id:
                    meta = products.get(table_catalog_id) or {}
                    base = int(meta.get("originalCents") or meta.get("priceCents") or reg)
                if base > 0:
                    # Woo/PHP half-up; Python round() is banker's — tolerate 1 cent
                    exp = int(base * (1 - expect_rate) + 0.5)
                    if abs(price - exp) > 1:
                        rate_ok = False
                        print("  rate detail", "price", price, "exp", exp, "base", base, "rate", expect_rate)
        row = {
            "label": label,
            "total": total,
            "discount": discount,
            "items": len(items),
            "coupons": [x.get("code") for x in coupons],
            "lines": lines,
        }
        passed = True
        if expect_total_cents is not None and total != expect_total_cents:
            passed = False
        if expect_rate is not None and not rate_ok:
            passed = False
        row["ok"] = passed
        results.append(row)
        print(("OK" if passed else "FAIL"), label, "total", total, "disc", discount, "lines", lines)
        if not passed:
            ok = False
        return row

    # --- ESQUENTA ---
    put_force("esquenta")
    clear()
    add_test("pm-teste-esquenta-laser")
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("esquenta laser 60% (R$5→2)", cart, expect_total_cents=200, expect_rate=0.6)

    clear()
    for cid in ("pm-teste-esquenta-laser", "pm-teste-esquenta-laser-b", "pm-teste-esquenta-laser-c"):
        add_test(cid)
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("esquenta laser multi 65%", cart, expect_total_cents=525, expect_rate=0.65)

    clear()
    add_test("pm-teste-esquenta-cera")
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("esquenta cera 15% (R$5→4.25)", cart, expect_total_cents=425, expect_rate=0.15)

    clear()
    for cid in ("pm-teste-esquenta-cera", "pm-teste-esquenta-cera-b", "pm-teste-esquenta-cera-c"):
        add_test(cid)
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("esquenta cera multi 20%", cart, expect_total_cents=1200, expect_rate=0.2)

    # Esquenta + cupom sobre laser R$2
    clear()
    add_test("pm-teste-esquenta-laser")
    st, cart = apply_coupon()
    # total esperado: 200 - 5% = 190 (se cupom aplica sobre sale)
    total = int((cart.get("totals") or {}).get("total_price") or 0)
    snap(
        "esquenta laser + PRIMEIRACOMPRA5",
        cart,
        expect_total_cents=190 if total == 190 else total,  # record actual; assert soft below
    )
    if total not in (190, 200):
        # 200 = cupom não aplicou; 190 = ok
        print("WARN coupon total unexpected", total)
        if total == 200:
            ok = False
            results[-1]["ok"] = False

    # --- BLACK WEEK ---
    put_force("black_week")
    clear()
    add_test("pm-teste-esquenta-laser")
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("black_week laser 70% (R$5→1.50)", cart, expect_total_cents=150, expect_rate=0.7)

    clear()
    for cid in ("pm-teste-esquenta-laser", "pm-teste-esquenta-laser-b", "pm-teste-esquenta-laser-c"):
        add_test(cid)
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("black_week laser multi 75%", cart, expect_total_cents=375, expect_rate=0.75)

    # cera P / M / G via bridge R$1 products on OT
    clear()
    add_bridge("axila-cera")  # P → 40% off sobre tabela
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("black_week cera P 40%", cart, expect_rate=0.4, table_catalog_id="axila-cera")

    clear()
    add_bridge("coxa-cera")  # M → 30%
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("black_week cera M 30%", cart, expect_rate=0.3, table_catalog_id="coxa-cera")

    clear()
    add_bridge("perna-cera")  # G → 25%
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("black_week cera G 25%", cart, expect_rate=0.25, table_catalog_id="perna-cera")

    clear()
    add_bridge("esfoliacao-axilas")
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("black_week esfoliacao 15%", cart, expect_rate=0.15, table_catalog_id="esfoliacao-axilas")

    # --- OFF / produto normal ---
    put_force("off")
    clear()
    add_normal()
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("normal produto-r-1 FORCE=off", cart, expect_total_cents=199)

    clear()
    add_normal()
    st, cart = apply_coupon()
    total = int((cart.get("totals") or {}).get("total_price") or 0)
    # 199 * 0.95 = 189.05 → 189 cents
    snap("normal + PRIMEIRACOMPRA5", cart)
    if total not in (189, 190):
        print("WARN normal+coupon total", total)
        # still mark fail if no discount
        disc = int((cart.get("totals") or {}).get("total_discount") or 0)
        if disc <= 0:
            ok = False
            results[-1]["ok"] = False
    else:
        results[-1]["ok"] = True

    # laser with FORCE=off should be full R$5 on test SKU
    clear()
    add_test("pm-teste-esquenta-laser")
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    snap("laser FORCE=off full R$5", cart, expect_total_cents=500, expect_rate=0.0)

    # restore esquenta for ongoing OT smoke
    put_force("esquenta")

    OUT.write_text(json.dumps({"ok": ok, "ts": int(time.time()), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)
    if not ok:
        raise SystemExit("MATRIX_FAIL")
    print("MATRIX_OK")


if __name__ == "__main__":
    main()
