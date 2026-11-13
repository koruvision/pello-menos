# -*- coding: utf-8 -*-
"""Smoke multi cera Esquenta: 3 IDs → 20%."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
DATA = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")


def cfg_url():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e["PM_LOJA_URL"].rstrip("/")


def original(pid: str) -> int:
    m = re.search(rf'id:\s*"{pid}"[^}}]*?originalCents:\s*(\d+)', DATA)
    return int(m.group(1))


def main():
    base = cfg_url()
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    ids = ["axila-cera", "abdomen-cera", "bracos-cera"]
    expect20 = sum(int(round(original(pid) * 0.8)) for pid in ids)
    expect15 = sum(int(round(original(pid) * 0.85)) for pid in ids)
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    nonce = token = None

    def call(method, path, payload=None):
        nonlocal nonce, token
        data = None if payload is None else json.dumps(payload).encode()
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-esq-multi-cera",
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
                parsed = {"raw": body[:500]}
            nonce = err.headers.get("Nonce") or nonce
            token = err.headers.get("Cart-Token") or token
            return err.code, parsed

    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    for it in list(cart.get("items") or []):
        call("POST", "/wp-json/wc/store/v1/cart/remove-item", {"key": it["key"]})
    call("GET", "/wp-json/wc/store/v1/cart")

    for pid in ids:
        var_id = next(iter(bridge[pid]["units"].values()))["variationId"]
        st, cart = call(
            "POST",
            "/wp-json/wc/store/v1/cart/add-item",
            {"id": int(var_id), "quantity": 1, "pm_catalog_id": pid},
        )
        print("add", pid, st, "n", len(cart.get("items") or []))
        if st >= 400:
            raise SystemExit(cart)

    total = int((cart.get("totals") or {}).get("total_price") or 0)
    print("total", total, "expect20", expect20, "expect15", expect15)
    for it in cart.get("items") or []:
        print(" ", it.get("name"), (it.get("totals") or {}).get("line_total"))
    if abs(total - expect20) > 3:
        raise SystemExit("multi20 fail")
    print("SMOKE_ESQUENTA_MULTI_CERA_OK")


if __name__ == "__main__":
    main()
