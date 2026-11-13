# -*- coding: utf-8 -*-
"""Resolve o produto-pai real de cada variationId e compara com o productId do catalogo.

Gera scripts/_unit_parent_report.json com o diagnostico completo.
NAO altera nada por padrao; use --write para corrigir cart-related.json e woo-bridge.json.
"""
from __future__ import annotations

import argparse
import base64
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CR = ROOT / "wordpress-loja" / "pm-home" / "cart-related.json"
BRIDGE = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
REPORT = ROOT / "scripts" / "_unit_parent_report.json"


def env() -> dict:
    e = {}
    for line in (ROOT / "projeto-migracao" / ".secrets" / "loja.env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    tok = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    h = {"Authorization": "Basic " + tok, "User-Agent": "pm-unit-audit"}

    def get(path: str):
        req = urllib.request.Request(base + path, headers=h)
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)

    # 1. Todos os produtos variáveis
    products = {}
    page = 1
    while True:
        chunk = get(f"/wp-json/wc/v3/products?per_page=100&page={page}&status=any")
        if not chunk:
            break
        for p in chunk:
            products[str(p["id"])] = {
                "name": p.get("name"),
                "type": p.get("type"),
                "parent_id": p.get("parent_id"),
                "slug": p.get("slug"),
                "status": p.get("status"),
            }
        if len(chunk) < 100:
            break
        page += 1
    print("produtos no Woo:", len(products))

    # 2. Variacoes de cada produto variavel -> varId => parent
    var_parent = {}
    variables = [pid for pid, p in products.items() if p["type"] == "variable"]
    print("produtos variaveis:", len(variables))
    for pid in variables:
        try:
            vs = get(f"/wp-json/wc/v3/products/{pid}/variations?per_page=100")
        except Exception:
            continue
        for v in vs:
            var_parent[str(v["id"])] = pid
    print("variacoes mapeadas:", len(var_parent))

    # 3. Compara com o catalogo
    cr = json.loads(CR.read_text(encoding="utf-8"))
    cat = cr["products"]
    rows = []
    for key, row in cat.items():
        pid = str(row.get("productId") or "")
        units = row.get("units") or {}
        vids = [str(m.get("variationId")) for m in units.values() if m.get("variationId")]
        parents = Counter(var_parent[v] for v in vids if v in var_parent)
        resolved = parents.most_common(1)[0][0] if parents else ""
        missing = [v for v in vids if v not in var_parent]
        status = "OK"
        if not pid:
            status = "SEM_PID"
        elif pid not in products:
            status = "PID_INEXISTENTE"
        elif products[pid]["type"] == "variation":
            status = "PID_E_VARIACAO"
        elif resolved and resolved != pid:
            status = "PID_ERRADO"
        elif missing:
            status = "VARIACAO_INEXISTENTE"
        rows.append({
            "key": key,
            "name": row.get("name"),
            "declared": pid,
            "declared_name": products.get(pid, {}).get("name"),
            "resolved": resolved,
            "resolved_name": products.get(resolved, {}).get("name"),
            "units": len(vids),
            "missing": missing[:8],
            "status": status,
        })

    by_status = defaultdict(list)
    for r in rows:
        by_status[r["status"]].append(r)
    print()
    for st in ("PID_INEXISTENTE", "PID_E_VARIACAO", "PID_ERRADO", "VARIACAO_INEXISTENTE", "SEM_PID"):
        print(f"{st}: {len(by_status[st])}")
    print()
    for st in ("PID_INEXISTENTE", "PID_E_VARIACAO", "PID_ERRADO"):
        for r in by_status[st][:40]:
            print(f"  [{st}] {r['key']}: pid={r['declared']} ({r['declared_name']}) -> real={r['resolved']} ({r['resolved_name']})")

    # 4. Colisoes: mesmo variationId usado por produtos de SERVICOS diferentes
    vuse = defaultdict(list)
    for key, row in cat.items():
        for uid, m in (row.get("units") or {}).items():
            v = str(m.get("variationId") or "")
            if v:
                vuse[v].append(key)
    collide = {}
    for v, keys in vuse.items():
        # ignora twins fem/masc do MESMO servico (sufixo -masc)
        core = {k[:-5] if k.endswith("-masc") else k for k in keys}
        if len(core) > 1:
            collide[v] = keys
    print()
    print("variationIds compartilhados por SERVICOS DIFERENTES:", len(collide))
    for v, keys in list(collide.items())[:15]:
        print("  ", v, "->", keys)

    REPORT.write_text(json.dumps({
        "products_total": len(products),
        "variations_total": len(var_parent),
        "by_status": {k: len(v) for k, v in by_status.items()},
        "rows": rows,
        "collisions": collide,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print("relatorio:", REPORT)

    if not args.write:
        print("(somente diagnostico; use --write para corrigir)")
        return

    fixed = 0
    for r in rows:
        if r["status"] in ("PID_ERRADO", "PID_INEXISTENTE") and r["resolved"]:
            cat[r["key"]]["productId"] = r["resolved"]
            cat[r["key"]]["wooId"] = r["resolved"]
            fixed += 1
    CR.write_text(json.dumps(cr, ensure_ascii=False, indent=2), encoding="utf-8")
    print("cart-related.json corrigido:", fixed, "produtos")

    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    bfixed = 0
    for r in rows:
        if r["status"] in ("PID_ERRADO", "PID_INEXISTENTE") and r["resolved"] and r["key"] in bridge:
            bridge[r["key"]]["productId"] = int(r["resolved"])
            bfixed += 1
    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2), encoding="utf-8")
    print("woo-bridge.json corrigido:", bfixed, "produtos")


if __name__ == "__main__":
    main()