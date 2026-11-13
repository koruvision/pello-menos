# -*- coding: utf-8 -*-
"""Smoke: cupom PM1LTEST01 <=20, legado longo ausente, pedido 49516 completed."""
from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/loja.env")
SECRET = Path("projeto-migracao/.secrets/linha-1real-coupon.json")


def main():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    base = e["PM_LOJA_URL"].rstrip("/")

    def get(path):
        req = urllib.request.Request(
            base + path,
            headers={"Authorization": "Basic " + auth, "Accept": "application/json", "User-Agent": "pm"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())

    sec = json.loads(SECRET.read_text(encoding="utf-8"))
    code = str(sec.get("code") or "")
    print("secret_code", code, "len", len(code))
    assert len(code) <= 20, code
    assert code.upper() == "PM1LTEST01"

    rows = get("/wp-json/wc/v3/coupons?" + urllib.parse.urlencode({"search": "PM1L", "per_page": 50}))
    long_left = [c for c in rows if len(str(c.get("code") or "")) > 20]
    short = [c for c in rows if str(c.get("code") or "").upper() == "PM1LTEST01"]
    print(
        "pm1l_count",
        len(rows),
        "long_left",
        len(long_left),
        "short_id",
        short[0].get("id") if short else None,
    )
    assert not long_left, [(c.get("id"), c.get("code")) for c in long_left]
    assert short

    rows_sn = get("/wp-json/code-snippets/v1/snippets?per_page=100")
    sn = next((x for x in rows_sn if x.get("name") == "pm-home (front do projeto)"), None)
    full = get(f"/wp-json/code-snippets/v1/snippets/{sn['id']}")
    code_sn = full.get("code") or ""
    print(
        "guardrail",
        "woocommerce_before_coupon_object_save" in code_sn,
        "substr20",
        "substr($code, 0, 20)" in code_sn,
    )
    assert "woocommerce_before_coupon_object_save" in code_sn

    o = get("/wp-json/wc/v3/orders/49516")
    print(
        "order_49516",
        o.get("status"),
        "coupons",
        [(c.get("code"), len(c.get("code") or "")) for c in (o.get("coupon_lines") or [])],
    )
    assert o.get("status") == "completed", o.get("status")
    print("SMOKE_OK")


if __name__ == "__main__":
    main()
