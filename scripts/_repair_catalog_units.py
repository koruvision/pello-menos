# -*- coding: utf-8 -*-
"""Repara os vinculos produto<->variacao do catalogo PM.

Regra: para cada produto do catalogo, o productId tem que ser um produto variavel REAL
do WooCommerce e cada unit.variationId tem que ser uma variacao DESSE produto, cujo
rotulo de atributo bata com o `option` da unit.

Corrige dois bugs:
  1. productId inexistente (242xx) -> resolve pelo pai real das variacoes atuais.
  2. productId certo, mas variacoes de outro produto (ex.: Virilha Total usando as
     variacoes da Virilha Comum => pedido registrava o servico errado).

Uso: python scripts/_repair_catalog_units.py [--write]
"""
from __future__ import annotations

import argparse
import base64
import json
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CR = ROOT / "wordpress-loja" / "pm-home" / "cart-related.json"
BRIDGE = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
REPORT = ROOT / "scripts" / "_catalog_repair_report.json"


def env() -> dict:
    e = {}
    p = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
    for line in p.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


def normalize(s: str) -> str:
    s = str(s or "").lower().strip()
    for a, b in (("á", "a"), ("à", "a"), ("â", "a"), ("ã", "a"), ("é", "e"), ("ê", "e"),
                 ("í", "i"), ("ó", "o"), ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")):
        s = s.replace(a, b)
    return " ".join(s.split())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    tok = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    h = {"Authorization": "Basic " + tok, "User-Agent": "pm-repair"}

    def get(path: str):
        req = urllib.request.Request(base + path, headers=h)
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)

    # 1. produtos
    products = {}
    page = 1
    while True:
        chunk = get(f"/wp-json/wc/v3/products?per_page=100&page={page}&status=any")
        if not chunk:
            break
        for p in chunk:
            products[str(p["id"])] = p
        if len(chunk) < 100:
            break
        page += 1
    print("produtos:", len(products))

    # 2. variacoes por produto variavel: parent -> {rotulo_normalizado: varId}
    var_parent = {}
    by_parent_label = {}
    variables = [pid for pid, p in products.items() if p.get("type") == "variable"]
    for pid in variables:
        try:
            vs = get(f"/wp-json/wc/v3/products/{pid}/variations?per_page=100")
        except Exception:
            continue
        table = {}
        for v in vs:
            var_parent[str(v["id"])] = pid
            label = ""
            for a in v.get("attributes") or []:
                opt = a.get("option")
                if opt:
                    label = str(opt).strip()
                    break
            if label:
                table[normalize(label)] = str(v["id"])
        by_parent_label[pid] = table
    print("variacoes mapeadas:", len(var_parent))

    cr = json.loads(CR.read_text(encoding="utf-8"))
    cat = cr["products"]
    changes, problems = [], []

    for key, row in cat.items():
        units = row.get("units") or {}
        if not units:
            continue
        declared = str(row.get("productId") or "")
        vids = [str(m.get("variationId")) for m in units.values() if m.get("variationId")]
        parents = Counter(var_parent[v] for v in vids if v in var_parent)

        # escolhe o pai alvo
        # 1) productId declarado e um produto variavel REAL e cobre os rotulos das units
        #    -> mantem o pai e apenas religa as variacoes (caso Virilha Total x Comum).
        labels = [normalize(str(m.get("option") or "")) for m in units.values()]
        target = ""
        if declared in products and products[declared].get("type") == "variable":
            table_d = by_parent_label.get(declared, {})
            cover = sum(1 for lb in labels if lb in table_d)
            if table_d and cover >= max(1, int(len(labels) * 0.6)):
                target = declared
        # 2) senao, o pai real das variacoes atuais
        if not target and parents:
            target = parents.most_common(1)[0][0]
        # 3) senao, o declarado se existir
        if not target and declared in products:
            target = declared

        if not target:
            problems.append({"key": key, "why": "sem produto pai resolvivel", "declared": declared})
            continue

        table = by_parent_label.get(target, {})
        new_units = {}
        unmapped = []
        changed_units = 0
        for uid, meta in units.items():
            label = str(meta.get("option") or "").strip()
            vid = table.get(normalize(label))
            if not vid:
                new_units[uid] = meta  # mantem, mas reporta
                unmapped.append(label)
                continue
            if str(meta.get("variationId") or "") != vid:
                changed_units += 1
            new_units[uid] = {"variationId": vid, "option": label}

        if target != declared or changed_units:
            changes.append({
                "key": key,
                "name": row.get("name"),
                "from_pid": declared,
                "to_pid": target,
                "to_name": (products.get(target) or {}).get("name"),
                "units_relinked": changed_units,
                "units_total": len(units),
                "unmapped": unmapped,
            })
        if unmapped:
            problems.append({"key": key, "why": "unidades sem variacao no pai", "pid": target, "labels": unmapped[:6]})
        if args.write:
            row["productId"] = target
            row["wooId"] = target
            row["units"] = new_units

    print()
    print("produtos corrigidos:", len(changes))
    for c in changes[:50]:
        print(f"  {c['key']}: {c['from_pid']} -> {c['to_pid']} ({c['to_name']}) "
              f"| unidades religadas {c['units_relinked']}/{c['units_total']}")
    print()
    print("pendencias:", len(problems))
    for p in problems[:25]:
        print("  ", p)

    REPORT.write_text(json.dumps({
        "products": len(products),
        "variations": len(var_parent),
        "changes": changes,
        "problems": problems,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nrelatorio:", REPORT)

    if not args.write:
        print("(diagnostico; use --write para aplicar)")
        return

    CR.write_text(json.dumps(cr, ensure_ascii=False, indent=2), encoding="utf-8")
    print("cart-related.json gravado")

    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    n = 0
    for c in changes:
        if c["key"] in bridge:
            bridge[c["key"]]["productId"] = int(c["to_pid"])
            n += 1
    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2), encoding="utf-8")
    print("woo-bridge.json atualizado:", n)


if __name__ == "__main__":
    main()