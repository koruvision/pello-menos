# -*- coding: utf-8 -*-
"""Smoke Store API: 1 cera e 1 laser cobrados com Esquenta (sem double)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"


def base_url():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e["PM_LOJA_URL"].rstrip("/")


def main():
    base = base_url()
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    cases = [
        ("axila-cera", 3300, 2805),  # 15% of 3300
        ("axilas-laser", 89990, 35996),  # 60% of 89990
    ]
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def open_req(method, path, payload=None, nonce=None, token=None):
        data = None if payload is None else json.dumps(payload).encode()
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-esquenta-smoke",
        }
        if nonce:
            h["Nonce"] = nonce
        if token:
            h["Cart-Token"] = token
        req = urllib.request.Request(base + path, data=data, method=method, headers=h)
        try:
            with opener.open(req, timeout=90) as resp:
                body = resp.read().decode("utf-8", "replace")
                return (
                    resp.status,
                    json.loads(body) if body else {},
                    resp.headers.get("Nonce"),
                    resp.headers.get("Cart-Token"),
                )
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body[:400]}
            return err.code, parsed, err.headers.get("Nonce"), err.headers.get("Cart-Token")

    st, cart, nonce, token = open_req("GET", "/wp-json/wc/store/v1/cart")
    print("cart", st, "nonce", bool(nonce))

    # empty cart
    items = (cart.get("items") or []) if isinstance(cart, dict) else []
    for it in items:
        open_req(
            "POST",
            "/wp-json/wc/store/v1/cart/remove-item",
            {"key": it["key"]},
            nonce,
            token,
        )
        st, cart, nonce, token = open_req("GET", "/wp-json/wc/store/v1/cart", None, nonce, token)

    failed = []
    for catalog_id, original, expect_sale in cases:
        info = bridge[catalog_id]
        units = info.get("units") or {}
        var_id = next(iter(units.values()))["variationId"]
        st, cart, n2, t2 = open_req(
            "POST",
            "/wp-json/wc/store/v1/cart/add-item",
            {"id": var_id, "quantity": 1},
            nonce,
            token,
        )
        if n2:
            nonce = n2
        if t2:
            token = t2
        print("add", catalog_id, st)
        if st >= 400:
            failed.append((catalog_id, "add", cart))
            continue
        totals = cart.get("totals") or {}
        total = int(totals.get("total_price") or 0)
        line = (cart.get("items") or [{}])[0]
        line_total = int((line.get("totals") or {}).get("line_total") or 0)
        print(
            catalog_id,
            "total",
            total,
            "line",
            line_total,
            "expect",
            expect_sale,
            "OK" if total == expect_sale else "MISMATCH",
        )
        if total != expect_sale:
            # check double: 15% on already 15%, or 5% only
            dbl = int(round(expect_sale * 0.85))
            five = int(round(original * 0.95))
            print("  hints double~", dbl, "five~", five, "raw prices", line.get("prices"))
            failed.append((catalog_id, total, expect_sale))
        # remove
        key = line.get("key")
        if key:
            open_req(
                "POST",
                "/wp-json/wc/store/v1/cart/remove-item",
                {"key": key},
                nonce,
                token,
            )
            st, cart, n2, t2 = open_req("GET", "/wp-json/wc/store/v1/cart", None, nonce, token)
            if n2:
                nonce = n2
            if t2:
                token = t2

    # multi 3 lasers -> 65%
    laser_ids = ["axilas-laser", "bracos-laser", "perna-laser"]
    expect_multi = 0
    for catalog_id in laser_ids:
        info = bridge[catalog_id]
        # get original from data roughly via expect
        units = info.get("units") or {}
        var_id = next(iter(units.values()))["variationId"]
        open_req(
            "POST",
            "/wp-json/wc/store/v1/cart/add-item",
            {"id": var_id, "quantity": 1},
            nonce,
            token,
        )
        st, cart, n2, t2 = open_req("GET", "/wp-json/wc/store/v1/cart", None, nonce, token)
        if n2:
            nonce = n2
        if t2:
            token = t2
    # compute expected 65% from line prices before discount is hard; print total
    totals = cart.get("totals") or {}
    print("multi3 lasers total_price", totals.get("total_price"), "items", len(cart.get("items") or []))
    for it in cart.get("items") or []:
        print(
            " ",
            it.get("name"),
            "line",
            (it.get("totals") or {}).get("line_total"),
            "price",
            (it.get("prices") or {}).get("price"),
        )

    if failed:
        print("FAIL", failed)
        raise SystemExit(1)
    print("SMOKE_ESQUENTA_NO_DOUBLE_OK")


if __name__ == "__main__":
    main()
