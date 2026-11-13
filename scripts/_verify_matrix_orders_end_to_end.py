# -*- coding: utf-8 -*-
"""Verifica pedidos da matriz: total Woo, meta Accesstage, cupom, notas."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "oficialteste.env"

ORDERS = {
    48512: {"case": "normal", "expect": "1.99", "coupon": False},
    48508: {"case": "normal+cupom", "expect": "1.89", "coupon": True},
    48509: {"case": "esquenta", "expect": "2.00", "coupon": False},
    48510: {"case": "black_week", "expect": "1.50", "coupon": False},
    48511: {"case": "esquenta+cupom", "expect": "1.90", "coupon": True},
}


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def get(path):
    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    req = urllib.request.Request(
        base + path,
        headers={"Authorization": "Basic " + auth, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def main():
    rows = []
    for oid, spec in ORDERS.items():
        o = get(f"/wp-json/wc/v3/orders/{oid}")
        meta = {m.get("key"): m.get("value") for m in (o.get("meta_data") or [])}
        notes = get(f"/wp-json/wc/v3/orders/{oid}/notes?type=any")
        note_texts = [
            (n.get("note") or "")[:200]
            for n in (notes if isinstance(notes, list) else [])[:8]
        ]
        coupons = [
            {"code": c.get("code"), "discount": c.get("discount")}
            for c in (o.get("coupon_lines") or [])
        ]
        row = {
            "id": oid,
            "case": spec["case"],
            "status": o.get("status"),
            "total": o.get("total"),
            "expect": spec["expect"],
            "total_ok": str(o.get("total")) == spec["expect"],
            "pm_cf7_totalamount": meta.get("_pm_cf7_totalamount"),
            "meta_ok": str(meta.get("_pm_cf7_totalamount")) == spec["expect"],
            "accesstage": meta.get("Pedido Accesstage"),
            "has_accesstage": bool(meta.get("Pedido Accesstage")),
            "unidade": meta.get("Unidade"),
            "modalidade": meta.get("Modalidade"),
            "cartao": meta.get("Cartão"),
            "coupons": coupons,
            "coupon_ok": (len(coupons) > 0) == spec["coupon"]
            if spec["coupon"]
            else True,
            "lines": [
                {"name": li.get("name"), "total": li.get("total")}
                for li in (o.get("line_items") or [])
            ],
            "notes": note_texts,
            "transaction_id": o.get("transaction_id"),
            "payment_method": o.get("payment_method"),
            "payment_method_title": o.get("payment_method_title"),
        }
        rows.append(row)
        print(
            oid,
            spec["case"],
            "total",
            row["total"],
            "meta",
            row["pm_cf7_totalamount"],
            "acces",
            row["accesstage"],
            "cupom",
            row["coupons"],
            "status",
            row["status"],
        )
    out = Path(__file__).resolve().parents[1] / "scripts" / "_verify_matrix_orders_end_to_end.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
