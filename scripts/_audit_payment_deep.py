# -*- coding: utf-8 -*-
"""Deeper READ-ONLY dig: inline checkout JS, order meta, theme hooks."""
from __future__ import annotations

import base64
import html as htmlmod
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
OUT = ROOT / "projeto-migracao" / ".secrets" / "_audit_payment_deep.json"


def env():
    d = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def api(base, auth, path):
    req = urllib.request.Request(
        base + path,
        headers={
            "Authorization": "Basic " + auth,
            "User-Agent": "pm-pay-deep",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def main():
    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    report = {}

    # Full checkout HTML inline scripts
    req = urllib.request.Request(
        base + "/finalizar-pagamento/?pm=pay-deep",
        headers={"User-Agent": "pm-pay-deep"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        page = r.read().decode("utf-8", "replace")

    inlines = re.findall(
        r"<script(?![^>]+src=)[^>]*>(.*?)</script>", page, flags=re.I | re.S
    )
    saved = []
    for i, code in enumerate(inlines):
        low = code.lower()
        if any(
            k in low
            for k in (
                "unit",
                "cart-number",
                "wpcf7",
                "redirect",
                "ajax",
                "payment",
                "pedido",
                "order",
                "token",
                "charge",
                "installment",
                "easyunit",
                "stripe",
                "cielo",
                "pagarme",
                "stone",
                "fetch(",
                "admin-ajax",
                "wc-ajax",
            )
        ):
            saved.append({"i": i, "len": len(code), "code": code})
            print(f"\n===== INLINE {i} len={len(code)} =====")
            print(code)
            print("===== END =====")
    report["inlines"] = saved

    # stripe context
    for m in re.finditer(r".{0,80}stripe.{0,80}", page, flags=re.I):
        print("STRIPE CTX:", m.group(0).replace("\n", " ")[:200])

    # CF7 form unit options full extract
    st_form = api(base, auth, "/wp-json/contact-form-7/v1/contact-forms/1831")
    content = ((st_form.get("properties") or {}).get("form") or {}).get("content") or ""
    # unit select options
    m = re.search(r'\[select\*?\s+unit[^\]]*\](.*?)(?:\[/select\]|\n|$)', content, re.S)
    # CF7 shortcode is single line-ish
    m2 = re.search(r'\[select\*? unit[^\]]*\]', content)
    if m2:
        print("\nUNIT SELECT SHORTCODE:\n", m2.group(0)[:3000])
        report["unit_select"] = m2.group(0)
    # all select unit pipes
    opts = re.findall(r'"([^"|]+)\|([^"]+)"', content)
    unit_opts = [(a, b) for a, b in opts if not a.startswith("Selecione")]
    # filter ones near unit - crude: all pipes in form
    print("pipe options count", len(opts))
    report["all_pipes"] = opts

    # groups allunits laserunits etc
    groups = re.findall(r'data-id="([^"]+)"', content)
    print("cf7cf group ids", groups)
    report["groups"] = groups

    # Order detail: compare flamengo vs copacabana
    for oid in (48239, 48238, 48214):
        o = api(base, auth, f"/wp-json/wc/v3/orders/{oid}")
        meta = {m["key"]: m["value"] for m in o.get("meta_data") or []}
        print("\nORDER", oid)
        print(" payment_method=", repr(o.get("payment_method")))
        print(" payment_method_title=", repr(o.get("payment_method_title")))
        print(" transaction_id=", repr(o.get("transaction_id")))
        print(" created_via=", o.get("created_via"))
        print(" status=", o.get("status"))
        print(" total=", o.get("total"))
        print(" meta_keys sample:", list(meta.keys())[:40])
        for k in sorted(meta):
            if any(
                x in k.lower()
                for x in (
                    "pay",
                    "unit",
                    "loja",
                    "trans",
                    "cielo",
                    "stone",
                    "pag",
                    "card",
                    "nsu",
                    "tid",
                    "auth",
                    "gateway",
                    "cpf",
                    "install",
                )
            ):
                v = meta[k]
                vs = str(v)
                if len(vs) > 120:
                    vs = vs[:60] + "…" + vs[-40:]
                print(f"  META {k} = {vs}")
        for li in o.get("line_items") or []:
            print(
                "  LINE",
                li.get("name"),
                "var",
                li.get("variation_id"),
                "meta",
                [
                    (m.get("display_key") or m.get("key"), m.get("display_value") or m.get("value"))
                    for m in (li.get("meta_data") or [])
                ],
            )
        report.setdefault("orders", {})[str(oid)] = {
            "payment_method": o.get("payment_method"),
            "payment_method_title": o.get("payment_method_title"),
            "transaction_id": o.get("transaction_id"),
            "created_via": o.get("created_via"),
            "status": o.get("status"),
            "total": o.get("total"),
            "meta_paymentish": {
                k: meta[k]
                for k in meta
                if any(
                    x in k.lower()
                    for x in (
                        "pay",
                        "unit",
                        "loja",
                        "trans",
                        "cielo",
                        "stone",
                        "pag",
                        "card",
                        "nsu",
                        "tid",
                        "gateway",
                        "cpf",
                        "install",
                    )
                )
            },
            "line_items": [
                {
                    "name": li.get("name"),
                    "variation_id": li.get("variation_id"),
                    "meta": [
                        {
                            "key": m.get("display_key") or m.get("key"),
                            "value": m.get("display_value") or m.get("value"),
                        }
                        for m in (li.get("meta_data") or [])
                    ],
                }
                for li in (o.get("line_items") or [])
            ],
        }

    # media / theme file search via plugins list all names
    plugins = api(base, auth, "/wp-json/wp/v2/plugins?per_page=100")
    print("\nALL PLUGINS:")
    for p in plugins:
        print(
            " ",
            p.get("status"),
            p.get("plugin"),
            "|",
            p.get("name"),
            p.get("version"),
        )
    report["all_plugins"] = [
        {"status": p.get("status"), "plugin": p.get("plugin"), "name": p.get("name")}
        for p in plugins
    ]

    # try find custom REST routes
    req = urllib.request.Request(
        base + "/wp-json/",
        headers={"Authorization": "Basic " + auth, "User-Agent": "pm"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        idx = json.loads(r.read().decode("utf-8", "replace"))
    routes = list((idx.get("routes") or {}).keys())
    pay_routes = [
        rt
        for rt in routes
        if any(
            k in rt.lower()
            for k in (
                "pay",
                "pag",
                "cielo",
                "stone",
                "checkout",
                "order",
                "cf7",
                "wpcf7",
                "charge",
                "gateway",
            )
        )
    ]
    print("\nPAY-ISH ROUTES", len(pay_routes))
    for rt in sorted(pay_routes)[:80]:
        print(" ", rt)
    report["pay_routes"] = sorted(pay_routes)

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
