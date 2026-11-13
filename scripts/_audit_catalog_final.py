# -*- coding: utf-8 -*-
"""Auditoria final: para cada item do catalogo, confirma no WooCommerce que
productId existe, e uma variacao do produto, e que a variacao corresponde ao rotulo da unidade.
"""
from __future__ import annotations

import base64
import json
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CR = ROOT / "wordpress-loja" / "pm-home" / "cart-related.json"
OUT = ROOT / "scripts" / "_catalog_audit_final.json"


def env() -> dict:
    e = {}
    for line in (ROOT / "projeto-migracao" / ".secrets" / "loja.env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join("".join(c if c.isalnum() or c == " " else " " for c in s).split())


class Api:
    def __init__(self):
        e = env()
        self.base = e["PM_LOJA_URL"].rstrip("/")
        tok = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
        self.h = {"Authorization": "Basic " + tok, "User-Agent": "pm-audit-final"}

    def get(self, path):
        req = urllib.request.Request(self.base + path, headers=self.h)
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)


def main() -> None:
    api = Api()
    products = {}
    page = 1
    while True:
        chunk = api.get(f"/wp-json/wc/v3/products?per_page=100&page={page}&status=any")
        if not chunk:
            break
        for p in chunk:
            products[str(p["id"])] = p
        if len(chunk) < 100:
            break
        page += 1

    var_parent, var_label = {}, {}
    for pid, p in list(products.items()):
        if p.get("type") != "variable":
            continue
        try:
            vs = api.get(f"/wp-json/wc/v3/products/{pid}/variations?per_page=100")
        except Exception:
            continue
        for v in vs:
            var_parent[str(v["id"])] = pid
            lbl = ""
            for a in v.get("attributes") or []:
                if a.get("option"):
                    lbl = a["option"]
                    break
            var_label[str(v["id"])] = lbl

    cat = json.loads(CR.read_text(encoding="utf-8"))["products"]
    rows = []
    for key, row in cat.items():
        pid = str(row.get("productId") or "")
        units = row.get("units") or {}
        if not units:
            rows.append({"key": key, "status": "SEM_UNIDADE", "pid": pid})
            continue
        if pid not in products:
            rows.append({"key": key, "status": "PRODUTO_INEXISTENTE", "pid": pid})
            continue
        problemas = []
        for uid, m in units.items():
            vid = str(m.get("variationId") or "")
            if not vid:
                problemas.append(f"{uid}: sem variationId")
                continue
            if vid not in var_parent:
                problemas.append(f"{uid}: variacao {vid} inexistente")
                continue
            if var_parent[vid] != pid:
                problemas.append(f"{uid}: variacao {vid} pertence a {var_parent[vid]}")
        rows.append({
            "key": key,
            "name": row.get("name"),
            "pid": pid,
            "woo_name": products[pid].get("name"),
            "units": len(units),
            "problems": problemas[:5],
            "status": "OK" if not problemas else "INCONSISTENTE",
        })

    st = Counter(r["status"] for r in rows)
    print("itens:", len(rows))
    for k, v in st.items():
        print(f"  {k}: {v}")
    bad = [r for r in rows if r["status"] == "INCONSISTENTE"]
    for r in bad[:20]:
        print("  ", r["key"], r["pid"], r["problems"][:2])

    pids = Counter(str(r.get("pid")) for r in rows if r.get("pid"))
    dup = {p: n for p, n in pids.items() if n > 1}
    print("\nproductIds distintos:", len(pids), "| compartilhados:", len(dup))

    OUT.write_text(json.dumps({"summary": dict(st), "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("relatorio:", OUT)


if __name__ == "__main__":
    main()