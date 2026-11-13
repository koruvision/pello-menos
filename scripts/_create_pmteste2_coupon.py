# -*- coding: utf-8 -*-
"""Cria cupom PMTESTE2 (fixed_cart R$2) para ensaio de checkout — usage limit baixo."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
CODE = "PMTESTE2"
AMOUNT = "2"


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
        "User-Agent": "pm-teste2-coupon",
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
    st, rows = call(
        "GET",
        "/wp-json/wc/v3/coupons?" + urllib.parse.urlencode({"search": CODE, "per_page": 10}),
    )
    coupon = None
    for c in rows if isinstance(rows, list) else []:
        if str(c.get("code") or "").lower() == CODE.lower():
            coupon = c
            break
    payload = {
        "code": CODE,
        "discount_type": "fixed_cart",
        "amount": AMOUNT,
        "individual_use": False,
        "usage_limit": 20,
        "usage_limit_per_user": 5,
        "exclude_sale_items": False,
        "description": "Cupom interno teste checkout R$2 — desativar após ensaio",
        "meta_data": [{"key": "_pm_test_coupon", "value": "1"}],
    }
    if coupon:
        st, coupon = call("PUT", f"/wp-json/wc/v3/coupons/{coupon['id']}", payload)
    else:
        st, coupon = call("POST", "/wp-json/wc/v3/coupons", payload)
    print(
        "coupon",
        st,
        coupon.get("id") if isinstance(coupon, dict) else coupon,
        coupon.get("code") if isinstance(coupon, dict) else None,
        coupon.get("amount") if isinstance(coupon, dict) else None,
    )
    if st not in (200, 201):
        raise SystemExit(1)
    print("PMTESTE2_OK")


if __name__ == "__main__":
    main()
