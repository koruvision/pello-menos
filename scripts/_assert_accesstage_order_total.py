# -*- coding: utf-8 -*-
"""Assert último pedido Accesstage do email de teste tem total == totalamount esperado."""
from __future__ import annotations

import argparse
import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def call(path):
    cfg = env()
    base = cfg["PM_OFICIALTESTE_URL"].rstrip("/")
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    req = urllib.request.Request(
        base + path,
        headers={
            "Authorization": "Basic " + token,
            "Accept": "application/json",
            "User-Agent": "pm-assert-accesstage-total/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace") or "null")
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            return err.code, json.loads(body)
        except json.JSONDecodeError:
            return err.code, body[:400]


def meta_map(order):
    out = {}
    for m in order.get("meta_data") or []:
        if isinstance(m, dict) and m.get("key") is not None:
            out[str(m.get("key"))] = m.get("value")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True)
    ap.add_argument("--expect", default="2.00", help="Expected order total / _pm_cf7_totalamount")
    ap.add_argument("--minutes", type=int, default=30)
    args = ap.parse_args()

    q = urllib.parse.urlencode(
        {
            "search": args.email,
            "per_page": 10,
            "orderby": "date",
            "order": "desc",
        }
    )
    st, orders = call(f"/wp-json/wc/v3/orders?{q}")
    if st != 200 or not isinstance(orders, list):
        raise SystemExit(f"orders failed {st} {orders}")

    expect = f"{float(str(args.expect).replace(',', '.')):.2f}"
    hits = []
    for o in orders:
        billing = (o.get("billing") or {}).get("email") or ""
        if billing.lower() != args.email.lower():
            continue
        meta = meta_map(o)
        if not meta.get("Pedido Accesstage"):
            continue
        hits.append(
            {
                "id": o.get("id"),
                "status": o.get("status"),
                "total": o.get("total"),
                "date": o.get("date_created"),
                "accesstage": meta.get("Pedido Accesstage"),
                "pm_cf7_totalamount": meta.get("_pm_cf7_totalamount"),
                "lines": [
                    {"name": li.get("name"), "total": li.get("total")}
                    for li in (o.get("line_items") or [])[:4]
                ],
            }
        )

    print(json.dumps({"email": args.email, "expect": expect, "hits": hits}, ensure_ascii=False, indent=2))
    if not hits:
        raise SystemExit("no Accesstage order for email")

    top = hits[0]
    total_ok = f"{float(top['total']):.2f}" == expect
    meta_ok = top.get("pm_cf7_totalamount") is not None and f"{float(top['pm_cf7_totalamount']):.2f}" == expect
    print("assert", {"total_ok": total_ok, "meta_ok": meta_ok, "order": top["id"]})
    if not total_ok or not meta_ok:
        raise SystemExit("order total / _pm_cf7_totalamount mismatch")


if __name__ == "__main__":
    main()
