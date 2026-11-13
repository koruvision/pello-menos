# -*- coding: utf-8 -*-
"""Inspeção read-only Accesstage/desconto no OficialTeste (Genesis)."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
OUT = ROOT / "projeto-migracao" / ".secrets" / "_audit_payment_ot_blacknov.json"


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
        "hostinger": e.get("PM_HOSTINGER_ACCOUNT", ""),
    }


def call(c, path):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        headers={
            "Authorization": "Basic " + tok,
            "User-Agent": "pm-audit-pay/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body[:1] in "[{" else body)


def main() -> None:
    c = cfg()
    report = {
        "site": c["url"],
        "hostinger_account_named": bool(c["hostinger"]),
        "accesstage_in_repo": False,
        "snippets": [],
        "plugins_paymentish": [],
        "orders_sample": [],
        "notes": [],
    }

    st, rows = call(c, "/wp-json/code-snippets/v1/snippets")
    if isinstance(rows, list):
        for row in rows:
            name = row.get("name") or ""
            code = ""
            try:
                _, full = call(c, f"/wp-json/code-snippets/v1/snippets/{row.get('id')}")
                code = (full.get("code") if isinstance(full, dict) else "") or ""
            except Exception:
                pass
            blob = (name + "\n" + code).lower()
            hit = any(
                k in blob
                for k in (
                    "accesstage",
                    "cf7",
                    "contact-form",
                    "black-nov",
                    "pm_black",
                    "cupom",
                    "coupon",
                    "totalamount",
                    "cupomamount",
                )
            )
            if hit or "pm-" in name.lower() or "pm_" in name.lower():
                report["snippets"].append(
                    {
                        "id": row.get("id"),
                        "name": name,
                        "active": row.get("active"),
                        "scope": row.get("scope"),
                        "mentions_accesstage": "accesstage" in blob,
                        "mentions_black_nov": "black" in blob and "nov" in blob,
                        "mentions_force": "pm_black_nov_force" in blob,
                        "code_len": len(code),
                    }
                )

    try:
        st, plugs = call(c, "/wp-json/wp/v2/plugins")
        if isinstance(plugs, list):
            for p in plugs:
                blob = json.dumps(p).lower()
                if any(k in blob for k in ("accesstage", "woocommerce", "contact-form", "recaptcha", "cpf")):
                    report["plugins_paymentish"].append(
                        {
                            "plugin": p.get("plugin"),
                            "status": p.get("status"),
                            "name": p.get("name"),
                        }
                    )
    except Exception as err:
        report["notes"].append(f"plugins list fail: {err}")

    try:
        st, orders = call(
            c,
            "/wp-json/wc/v3/orders?per_page=5&orderby=date&order=desc",
        )
        if isinstance(orders, list):
            for o in orders:
                meta = {
                    m.get("key"): m.get("value")
                    for m in (o.get("meta_data") or [])
                    if isinstance(m, dict)
                }
                acc_keys = [k for k in meta if "accesstage" in str(k).lower() or "pedido" in str(k).lower()]
                report["orders_sample"].append(
                    {
                        "id": o.get("id"),
                        "status": o.get("status"),
                        "total": o.get("total"),
                        "discount_total": o.get("discount_total"),
                        "coupon_lines": [
                            {"code": x.get("code"), "discount": x.get("discount")}
                            for x in (o.get("coupon_lines") or [])
                        ],
                        "accesstage_meta_keys": acc_keys[:12],
                        "has_accesstage_meta": any("accesstage" in str(k).lower() for k in meta),
                    }
                )
    except Exception as err:
        report["notes"].append(f"orders fail: {err}")

    report["notes"].append(
        "Accesstage/CF7 #1831 vivem só no hosting; repo tem checkout-shell + loading overlay."
    )
    report["notes"].append(
        "Desconto Black Nov no Woo: snippet pm-black-nov-pricing (set_price). UI labels no cart/shell."
    )
    report["notes"].append(
        "Se charge Accesstage ignora totais Woo/hiddens CF7, precisa do dev do gateway — não há fonte Accesstage no git."
    )

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
