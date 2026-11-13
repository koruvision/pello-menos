# -*- coding: utf-8 -*-
"""Smoke Black Nov no OficialTeste (FORCE no snippet)."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
BRIDGE = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
CAMPAIGN = ROOT / "wordpress-loja" / "pm-home" / "black-nov-campaign.json"
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


def main() -> None:
    c = cfg()
    camp = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    token = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    nonce = ""
    cart_token = ""
    ok = True

    def call(method, path, payload=None, auth=True, parse_json=True):
        nonlocal nonce, cart_token
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "User-Agent": "pm-black-smoke",
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
                if not parse_json:
                    return r.status, body
                if not body:
                    return r.status, {}
                try:
                    return r.status, json.loads(body)
                except json.JSONDecodeError:
                    return r.status, {"raw": body[:400]}
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(body) if body else {}
            except json.JSONDecodeError:
                parsed = {"raw": body[:400]}
            return err.code, parsed

    def put_snippet(force: str) -> None:
        code = SNIPPET_SRC.read_text(encoding="utf-8").replace(
            "define('PM_BLACK_NOV_FORCE', '');",
            f"define('PM_BLACK_NOV_FORCE', '{force}');",
            1,
        )
        st, sn = call("GET", "/wp-json/code-snippets/v1/snippets/24")
        if st != 200 or not isinstance(sn, dict):
            raise SystemExit(f"snippet GET fail {st}")
        payload = {
            "name": sn.get("name") or "pm-black-nov-pricing",
            "code": code,
            "scope": "global",
            "active": True,
        }
        st, saved = call("PUT", "/wp-json/code-snippets/v1/snippets/24", payload)
        print("snippet FORCE", force, st, "active", saved.get("active") if isinstance(saved, dict) else saved)

    def clear_cart():
        st, cart0 = call("GET", "/wp-json/wc/store/v1/cart")
        for item in list(cart0.get("items") or []):
            key = item.get("key")
            if key:
                call("POST", "/wp-json/wc/store/v1/cart/remove-item", {"key": key})

    def variation_id(catalog_id: str) -> int:
        entry = bridge.get(catalog_id) or {}
        units = entry.get("units") or {}
        for meta in units.values():
            if isinstance(meta, dict) and meta.get("variationId"):
                return int(meta["variationId"])
        pid = entry.get("productId")
        if pid:
            return int(pid)
        raise SystemExit(f"sem id {catalog_id}")

    def add(catalog_id: str):
        add_id = variation_id(catalog_id)
        st, cart = call(
            "POST",
            "/wp-json/wc/store/v1/cart/add-item",
            {"id": add_id, "quantity": 1, "pm_catalog_id": catalog_id},
        )
        n = len(cart.get("items") or [])
        print("add", catalog_id, add_id, "→", st, "items", n)
        return cart

    def refresh():
        st, cart = call("GET", "/wp-json/wc/store/v1/cart")
        return cart

    def line_prices(cart):
        out = []
        for item in cart.get("items") or []:
            prices = item.get("prices") or {}
            out.append(
                {
                    "id": item.get("id"),
                    "name": (item.get("name") or "")[:40],
                    "price": int(prices.get("price") or 0),
                    "regular": int(prices.get("regular_price") or 0),
                }
            )
        return out

    def expect_rate(label, cart, rate):
        nonlocal ok
        lp = line_prices(cart)
        print(label, lp)
        if not lp or lp[0]["regular"] <= 0:
            print("FAIL", label, "empty")
            ok = False
            return
        for x in lp:
            expected = round(x["regular"] * (1 - rate))
            if x["price"] != expected:
                print("FAIL", label, "price", x["price"], "expected", expected, "rate", rate)
                ok = False
                return
        print("OK", label, "rate", rate)

    for path in (
        "/wp-content/uploads/pm-home/black-nov-campaign.json",
        "/wp-content/uploads/pm-home/black-nov-campaign.js?v=black1",
        "/wp-content/uploads/pm-home/woo-bridge.json",
        "/wp-content/uploads/pm-home/cart.js?v=cart25",
    ):
        st, _ = call("GET", path, auth=False, parse_json=False)
        print("GET", path, st)
        if st != 200:
            ok = False

    assert abs(camp["laser"]["esquenta"]["any"] - 0.6) < 1e-9
    assert abs(camp["laser"]["esquenta"]["multi"] - 0.65) < 1e-9
    assert abs(camp["ceraEsf"]["black_week_cera"]["P"] - 0.4) < 1e-9
    assert abs(camp["ceraEsf"]["black_week_cera"]["G"] - 0.25) < 1e-9
    assert "tintura-pelos-pubianos" in camp["ceraTierM"]
    print("config OK")

    # --- Esquenta: 1 laser → 60% ---
    put_snippet("esquenta")
    clear_cart()
    add("axilas-laser")
    expect_rate("1 laser esquenta", refresh(), 0.6)

    # --- Esquenta multi via 3 ceras (OT só mantém 1 laser por vez) ---
    clear_cart()
    for cid in ("axila-cera", "buco-cera", "queixo-cera"):
        add(cid)
    cart = refresh()
    n = len(cart.get("items") or [])
    print("3 cera items", n)
    if n >= 3:
        expect_rate("3 cera esquenta multi 20%", cart, 0.2)
    else:
        print("FAIL need 3 cera lines, got", n)
        ok = False

    # --- Black Week: laser 70% ---
    put_snippet("black_week")
    clear_cart()
    add("axilas-laser")
    expect_rate("1 laser black_week", refresh(), 0.7)

    # --- Black Week: cera P + G ---
    clear_cart()
    add("axila-cera")
    add("perna-cera")
    cart = refresh()
    lp = line_prices(cart)
    print("cera P+G", lp)
    if len(lp) >= 2:
        by_id = {x["id"]: x for x in lp}
        p = by_id.get(variation_id("axila-cera"))
        g = by_id.get(variation_id("perna-cera"))
        if p and g:
            exp_p = round(p["regular"] * 0.6)
            exp_g = round(g["regular"] * 0.75)
            if p["price"] == exp_p and g["price"] == exp_g:
                print("OK cera P/G black_week", exp_p, exp_g)
            else:
                print("FAIL P/G", p["price"], exp_p, g["price"], exp_g)
                ok = False
        else:
            print("FAIL missing P/G lines")
            ok = False
    else:
        print("FAIL cera cart size", len(lp))
        ok = False

    put_snippet("esquenta")
    if ok:
        print("SMOKE_OK")
    else:
        print("SMOKE_PARTIAL")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
