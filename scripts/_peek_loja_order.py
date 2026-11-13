# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import sys
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "loja.env"


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def main():
    oid = sys.argv[1]
    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    req = urllib.request.Request(
        base + f"/wp-json/wc/v3/orders/{oid}",
        headers={"Authorization": "Basic " + auth, "Accept": "application/json"},
    )
    order = json.loads(urllib.request.urlopen(req, timeout=90).read().decode())
    meta = {m.get("key"): m.get("value") for m in (order.get("meta_data") or [])}
    print(
        json.dumps(
            {
                "id": order.get("id"),
                "status": order.get("status"),
                "total": order.get("total"),
                "email": (order.get("billing") or {}).get("email"),
                "accesstage": meta.get("Pedido Accesstage"),
                "pm_cf7_totalamount": meta.get("_pm_cf7_totalamount"),
                "lines_synced": meta.get("_pm_accesstage_lines_synced"),
                "amount_cents": meta.get("_pm_accesstage_amount_cents"),
                "unidade": meta.get("Unidade"),
                "discount_total": order.get("discount_total"),
                "coupons": [
                    {"code": c.get("code"), "discount": c.get("discount")}
                    for c in (order.get("coupon_lines") or [])
                ],
                "lines": [
                    {"name": li.get("name"), "total": li.get("total"), "subtotal": li.get("subtotal")}
                    for li in (order.get("line_items") or [])
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
