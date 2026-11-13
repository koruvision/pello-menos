# -*- coding: utf-8 -*-
"""Smoke Esquenta com SKUs de ensaio R$5 no OficialTeste (FORCE no snippet 24)."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
BRIDGE = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
SKUS = json.loads((ROOT / "scripts" / "_ot_esquenta_test_skus.json").read_text(encoding="utf-8"))
SNIPPET_SRC = ROOT / "scripts" / "pm_black_nov_snippet.php"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": e["PM_OFICIALTESTE_URL"].rstrip("/"),
        "user": e["PM_OFICIALTESTE_USER"],
        "password": e["PM_OFICIALTESTE_APP_PASSWORD"],
    }


def main():
    c = cfg()
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    token = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    nonce = ""
    cart_token = ""
    ok = True

    def call(method, path, payload=None, auth=True):
        nonlocal nonce, cart_token
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "User-Agent": "pm-esquenta-smoke",
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

    def add(cid: str):
        pid = int((bridge.get(cid) or {}).get("productId") or SKUS[cid])
        st, cart = call(
            "POST",
            "/wp-json/wc/store/v1/cart/add-item",
            {"id": pid, "quantity": 1, "pm_catalog_id": cid},
        )
        print("add", cid, pid, st, "items", len(cart.get("items") or []))
        return cart

    def expect(label, cart, rate):
        nonlocal ok
        items = cart.get("items") or []
        totals = cart.get("totals") or {}
        print(label, "n", len(items), "total_price", totals.get("total_price"), "total_items", totals.get("total_items"))
        for item in items:
            prices = item.get("prices") or {}
            regular = int(prices.get("regular_price") or 0)
            price = int(prices.get("price") or 0)
            exp = round(regular * (1 - rate))
            if regular <= 0 or price != exp:
                print("FAIL", label, item.get("name"), "price", price, "exp", exp, "reg", regular)
                ok = False
                return
        print("OK", label, "rate", rate)

    put_force("esquenta")
    clear()
    expect("1 laser 60%", add("pm-teste-esquenta-laser"), 0.6)

    clear()
    for cid in ("pm-teste-esquenta-laser", "pm-teste-esquenta-laser-b", "pm-teste-esquenta-laser-c"):
        add(cid)
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    expect("3 laser 65%", cart, 0.65)

    clear()
    expect("1 cera 15%", add("pm-teste-esquenta-cera"), 0.15)

    clear()
    for cid in ("pm-teste-esquenta-cera", "pm-teste-esquenta-cera-b", "pm-teste-esquenta-cera-c"):
        add(cid)
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    expect("3 cera 20%", cart, 0.2)

    # hiddens-equivalent: total_items == sale sum
    totals = cart.get("totals") or {}
    sale_sum = sum(int((i.get("prices") or {}).get("price") or 0) * int(i.get("quantity") or 1) for i in (cart.get("items") or []))
    items_total = int(totals.get("total_items") or 0)
    if items_total != sale_sum:
        print("FAIL totals", items_total, sale_sum)
        ok = False
    else:
        print("OK hiddens fullvalue basis", items_total)

    if not ok:
        raise SystemExit(1)
    print("SMOKE_ESQUENTA_OK")


if __name__ == "__main__":
    main()
