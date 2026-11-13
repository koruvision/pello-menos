# -*- coding: utf-8 -*-
"""READ-ONLY: Accesstage payment meta across orders + theme/plugin search hints."""
from __future__ import annotations

import base64
import json
import re
import urllib.request
from collections import Counter
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "oficialteste.env"
OUT = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "_audit_accesstage.json"


def main():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()

    def get(path):
        req = urllib.request.Request(
            base + path,
            headers={
                "Authorization": "Basic " + auth,
                "User-Agent": "pm-accesstage",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode("utf-8", "replace"))

    orders = get("/wp-json/wc/v3/orders?per_page=50&orderby=date&order=desc")
    print("orders", len(orders))
    rows = []
    units = Counter()
    modalidades = Counter()
    accesstage_ids = []
    for o in orders:
        meta = {m["key"]: m["value"] for m in (o.get("meta_data") or [])}
        unit = meta.get("Unidade") or ""
        mod = meta.get("Modalidade") or ""
        acc = meta.get("Pedido Accesstage")
        units[str(unit)] += 1
        modalidades[str(mod)] += 1
        line_unit = None
        for li in o.get("line_items") or []:
            for m in li.get("meta_data") or []:
                if "unidad" in (m.get("display_key") or m.get("key") or "").lower():
                    line_unit = m.get("display_value") or m.get("value")
        row = {
            "id": o.get("id"),
            "status": o.get("status"),
            "total": o.get("total"),
            "payment_method": o.get("payment_method"),
            "unit_meta": unit,
            "line_unit": line_unit,
            "modalidade": mod,
            "pedido_accesstage": acc,
            "cpf_present": bool(meta.get("CPF")),
            "all_meta_keys": sorted(meta.keys()),
        }
        rows.append(row)
        if acc:
            accesstage_ids.append(str(acc))
        print(
            f"#{o['id']} total={o['total']} unit_meta={unit!r} line={line_unit!r} "
            f"mod={mod!r} accesstage={acc!r}"
        )

    print("\nUnidade meta counts:", dict(units))
    print("Modalidade counts:", dict(modalidades))
    print("unique accesstage ids", len(set(accesstage_ids)), "sample", accesstage_ids[:10])

    # Same Accesstage id reused across different units?
    by_acc = {}
    for r in rows:
        a = r["pedido_accesstage"]
        if not a:
            continue
        by_acc.setdefault(str(a), set()).add(str(r["unit_meta"] or r["line_unit"]))
    multi = {k: sorted(v) for k, v in by_acc.items() if len(v) > 1}
    print("accesstage ids spanning multiple units:", len(multi))
    for k, v in list(multi.items())[:5]:
        print(" ", k, v)

    # Search page HTML / scripts for accesstage
    req = urllib.request.Request(
        base + "/finalizar-pagamento/?pm=acc",
        headers={"User-Agent": "pm"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        html = r.read().decode("utf-8", "replace")
    for kw in ("accesstage", "accessstage", "acces", "easyunit", "redirectSuccess", "removeitemcartpl"):
        print(f"html '{kw}' count", html.lower().count(kw.lower()))

    # Search all snippets for accesstage
    snips = get("/wp-json/code-snippets/v1/snippets?per_page=100")
    print("\nSNIPPETS accesstage/payment:")
    snip_hits = []
    for s in snips:
        code = s.get("code") or ""
        name = s.get("name") or ""
        blob = (name + code).lower()
        if any(
            k in blob
            for k in (
                "accesstage",
                "accessstage",
                "pedido",
                "cart-number",
                "redirectsuccess",
                "removeitemcartpl",
                "payment",
                "charge",
                "cielo",
                "token",
            )
        ):
            print(" HIT", s.get("id"), name, "active", s.get("active"), "len", len(code))
            snip_hits.append(
                {
                    "id": s.get("id"),
                    "name": name,
                    "active": s.get("active"),
                    "code": code,
                }
            )
            # print full if shortish
            if len(code) < 8000:
                print(code)
                print("---")

    # Try shopwise-core / theme via file manager? skip write. Try REST media search
    # Look for JS files mentioning accesstage in uploads
    # Probe common custom endpoints via admin-ajax action discovery from HTML
    actions = sorted(set(re.findall(r"action['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9_]+)['\"]", html)))
    print("ajax actions in html", actions)

    # Fetch CF7CF conditions summary focusing on unit
    m = re.search(r'name="_wpcf7cf_options"[^>]*value="([^"]*)"', html)
    cf7cf = None
    if m:
        import html as htmlmod

        raw = htmlmod.unescape(m.group(1))
        cf7cf = json.loads(raw)
        conds = cf7cf.get("conditions") if isinstance(cf7cf, dict) else cf7cf
        print("\nCF7CF conditions:")
        for c in conds or []:
            print(json.dumps(c, ensure_ascii=False)[:500])

    out = {
        "orders": rows,
        "unit_meta_counts": dict(units),
        "modalidade_counts": dict(modalidades),
        "accesstage_multi_unit": multi,
        "snippet_hits": [
            {"id": s["id"], "name": s["name"], "active": s["active"], "code_len": len(s["code"])}
            for s in snip_hits
        ],
        "snippet_codes": {str(s["id"]): s["code"] for s in snip_hits},
        "ajax_actions": actions,
        "cf7cf": cf7cf,
        "html_keyword_counts": {
            kw: html.lower().count(kw.lower())
            for kw in (
                "accesstage",
                "accessstage",
                "redirectSuccess",
                "removeitemcartpl",
                "easyunit",
            )
        },
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WROTE", OUT)


if __name__ == "__main__":
    main()
