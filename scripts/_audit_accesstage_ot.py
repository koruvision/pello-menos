# -*- coding: utf-8 -*-
"""Readonly: CF7 #1831 + pedidos Accesstage no OficialTeste."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
OUT = ROOT / "scripts" / "_audit_accesstage_ot.json"


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


def call(c, path):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        headers={"Authorization": "Basic " + tok, "User-Agent": "pm-acc-audit/1.0", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body[:1] in "[{" else body)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body[:800]}
        return err.code, parsed


def main():
    c = cfg()
    report = {"url": c["url"], "cf7": {}, "orders": []}
    for path in (
        "/wp-json/contact-form-7/v1/contact-forms/1831",
        "/wp-json/wp/v2/pages?search=finalizar&per_page=5",
    ):
        st, body = call(c, path)
        print(path, st, type(body).__name__)
        if "1831" in path and isinstance(body, dict):
            props = body.get("properties") or {}
            form = props.get("form") if isinstance(props, dict) else None
            mail = props.get("mail") if isinstance(props, dict) else None
            report["cf7"] = {
                "status": st,
                "title": body.get("title"),
                "form_has_totalamount": isinstance(form, str) and "totalamount" in form,
                "form_has_fullvalue": isinstance(form, str) and "fullvalue" in form,
                "form_snippet": (form or "")[:1200] if isinstance(form, str) else None,
                "mail_snippet": str(mail)[:800] if mail else None,
            }
            print("hiddens", report["cf7"]["form_has_totalamount"], report["cf7"]["form_has_fullvalue"])

    st, orders = call(c, "/wp-json/wc/v3/orders?per_page=8&orderby=date&order=desc")
    if isinstance(orders, list):
        for o in orders:
            meta = {m.get("key"): m.get("value") for m in (o.get("meta_data") or [])}
            acc = meta.get("Pedido Accesstage") or meta.get("pedido_accesstage")
            lines = [
                {
                    "name": li.get("name"),
                    "total": li.get("total"),
                    "subtotal": li.get("subtotal"),
                }
                for li in (o.get("line_items") or [])
            ]
            row = {
                "id": o.get("id"),
                "status": o.get("status"),
                "total": o.get("total"),
                "discount_total": o.get("discount_total"),
                "accesstage": acc,
                "lines": lines,
            }
            report["orders"].append(row)
            print("order", row["id"], row["status"], row["total"], "acc", bool(acc), "disc", row["discount_total"])

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
