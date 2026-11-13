# -*- coding: utf-8 -*-
"""Smoke multi laser Esquenta: 3 IDs → 65% sobre tabela."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
DATA = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")


def base_url():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e["PM_LOJA_URL"].rstrip("/")


def original_cents(pid: str) -> int:
    import re

    m = re.search(rf'id:\s*"{pid}"[^}}]*?originalCents:\s*(\d+)', DATA)
    if not m:
        raise SystemExit(f"no original for {pid}")
    return int(m.group(1))


def main():
    base = base_url()
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    laser_ids = ["axilas-laser", "bracos-laser", "perna-laser"]
    expect = sum(int(round(original_cents(pid) * 0.35)) for pid in laser_ids)

    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    nonce = token = None

    def call(method, path, payload=None):
        nonlocal nonce, token
        data = None if payload is None else json.dumps(payload).encode()
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-esquenta-multi",
        }
        if nonce:
            h["Nonce"] = nonce
        if token:
            h["Cart-Token"] = token
        req = urllib.request.Request(base + path, data=data, method=method, headers=h)
        try:
            with opener.open(req, timeout=90) as resp:
                body = resp.read().decode("utf-8", "replace")
                nonce = resp.headers.get("Nonce") or nonce
                token = resp.headers.get("Cart-Token") or token
                return resp.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body[:400]}
            nonce = err.headers.get("Nonce") or nonce
            token = err.headers.get("Cart-Token") or token
            return err.code, parsed

    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    for it in list(cart.get("items") or []):
        call("POST", "/wp-json/wc/store/v1/cart/remove-item", {"key": it["key"]})
    call("GET", "/wp-json/wc/store/v1/cart")

    for pid in laser_ids:
        var_id = next(iter((bridge[pid].get("units") or {}).values()))["variationId"]
        st, cart = call(
            "POST",
            "/wp-json/wc/store/v1/cart/add-item",
            {"id": var_id, "quantity": 1, "pm_catalog_id": pid},
        )
        print("add", pid, st, "items", len(cart.get("items") or []))
        if st >= 400:
            raise SystemExit(cart)

    totals = cart.get("totals") or {}
    total = int(totals.get("total_price") or 0)
    print("total", total, "expect65", expect)
    for it in cart.get("items") or []:
        print(
            " ",
            it.get("name"),
            (it.get("totals") or {}).get("line_total"),
            (it.get("prices") or {}).get("price"),
        )
    # allow 1 cent rounding per line
    if abs(total - expect) > 3:
        # maybe only 60% if count failed
        expect60 = sum(int(round(original_cents(pid) * 0.4)) for pid in laser_ids)
        print("expect60", expect60)
        raise SystemExit(1)
    print("SMOKE_ESQUENTA_MULTI_OK")


if __name__ == "__main__":
    main()
