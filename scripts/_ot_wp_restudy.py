# -*- coding: utf-8 -*-
"""Restudo OT via WP REST: snippets Black Nov, shell enqueue, pedidos recentes."""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OT = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
OUT = ROOT / "scripts" / "_ot_wp_restudy.json"


def env():
    e = {}
    for line in OT.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def call(base, auth, method, path):
    req = urllib.request.Request(
        base + path,
        method=method,
        headers={
            "Authorization": "Basic " + auth,
            "Accept": "application/json",
            "User-Agent": "pm-ot-restudy/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace") or "null")
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body[:400]}
        return err.code, parsed


def main():
    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    report = {"base": base}

    st, me = call(base, auth, "GET", "/wp-json/wp/v2/users/me")
    report["me"] = {"status": st, "slug": (me or {}).get("slug") if isinstance(me, dict) else me}
    print("me", report["me"])

    st, snippets = call(base, auth, "GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    report["snippets_status"] = st
    sn_summary = []
    if isinstance(snippets, list):
        for sn in snippets:
            code = sn.get("code") or ""
            name = sn.get("name") or sn.get("title") or ""
            active = sn.get("active")
            sid = sn.get("id")
            entry = {
                "id": sid,
                "name": name,
                "active": active,
                "bytes": len(code),
                "mentions": [],
            }
            for k in (
                "accesstage",
                "totalamount",
                "FORCE",
                "__PM_BLACK_PHASE__",
                "checkout-shell",
                "set_price",
                "pm-black",
                "black-nov",
                "pmBlackNov",
            ):
                if k.lower() in code.lower() or k.lower() in name.lower():
                    entry["mentions"].append(k)
            if "FORCE" in code:
                m = re.search(r"FORCE\s*=\s*['\"]([^'\"]*)['\"]", code)
                entry["force"] = m.group(1) if m else "?"
            if "checkout-shell" in code:
                m = re.search(r"checkout-shell[^\"'\s?]*\?v=([a-zA-Z0-9._-]+)", code)
                entry["shell_v"] = m.group(1) if m else None
                m2 = re.search(r"checkout-shell-c\d+\.js", code)
                entry["shell_file"] = m2.group(0) if m2 else None
            if entry["mentions"] or "pm" in name.lower() or "black" in name.lower() or "checkout" in name.lower():
                sn_summary.append(entry)
                print("SNIPPET", entry)
    report["snippets_of_interest"] = sn_summary

    # recent orders
    st, orders = call(
        base,
        auth,
        "GET",
        "/wp-json/wc/v3/orders?" + urllib.parse.urlencode({"per_page": 8, "orderby": "date", "order": "desc"}),
    )
    report["orders_status"] = st
    osum = []
    if isinstance(orders, list):
        for o in orders:
            meta = {m.get("key"): m.get("value") for m in (o.get("meta_data") or []) if isinstance(m, dict)}
            osum.append(
                {
                    "id": o.get("id"),
                    "status": o.get("status"),
                    "total": o.get("total"),
                    "date": o.get("date_created"),
                    "accesstage": meta.get("Pedido Accesstage"),
                    "unidade": meta.get("Unidade"),
                    "lines": [
                        {
                            "name": li.get("name"),
                            "total": li.get("total"),
                            "subtotal": li.get("subtotal"),
                        }
                        for li in (o.get("line_items") or [])[:6]
                    ],
                }
            )
            print("ORDER", osum[-1]["id"], osum[-1]["total"], osum[-1]["accesstage"], osum[-1]["lines"][:2])
    report["orders"] = osum

    # CF7 form 1831 if endpoint exists
    for path in (
        "/wp-json/contact-form-7/v1/contact-forms/1831",
        "/wp-json/wpcf7/v1/contact-forms/1831",
    ):
        st, form = call(base, auth, "GET", path)
        if st == 200 and isinstance(form, dict):
            props = form.get("properties") or {}
            form_html = (props.get("form") if isinstance(props, dict) else None) or form.get("form") or ""
            hiddens = re.findall(r'name=["\']([a-zA-Z0-9_-]+)["\']', form_html)
            report["cf7_1831"] = {
                "status": st,
                "title": form.get("title"),
                "fields_sample": sorted(set(hiddens))[:60],
                "has_totalamount": "totalamount" in form_html,
                "has_fullvalue": "fullvalue" in form_html,
            }
            print("CF7", report["cf7_1831"])
            break
        report.setdefault("cf7_tries", []).append({"path": path, "status": st})

    # Store API cart smoke: just check products with pm-teste
    st, products = call(
        base,
        auth,
        "GET",
        "/wp-json/wc/v3/products?"
        + urllib.parse.urlencode({"search": "pm-teste-esquenta", "per_page": 20}),
    )
    report["test_skus_status"] = st
    if isinstance(products, list):
        report["test_skus"] = [
            {
                "id": p.get("id"),
                "slug": p.get("slug"),
                "status": p.get("status"),
                "price": p.get("price"),
                "regular_price": p.get("regular_price"),
                "catalog_visibility": p.get("catalog_visibility"),
            }
            for p in products
        ]
        for p in report["test_skus"]:
            print("SKU", p)

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
