# -*- coding: utf-8 -*-
"""Gera cart-affinity.json para as recomendacoes do carrinho.

Le os pedidos reais da loja (somente leitura) e produz:
  - pairs   : combinacoes realmente vendidas juntas (co-ocorrencia por pedido)
  - top     : produtos mais vendidos (unidades)
  - unitTop : mais vendidos por unidade (unidade do pedido = pa_unidade)

Nada e inventado: produto sem venda no periodo simplesmente nao aparece.
A disponibilidade por unidade vem de cart-related.json (units), nao daqui.

Uso: python scripts/_build_cart_affinity.py [--days 180]
"""
from __future__ import annotations

import argparse
import base64
import collections
import datetime as dt
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
CATALOG = PM / "cart-related.json"
OUT = PM / "cart-affinity.json"
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"

# Status que representam compra efetiva (carrinho abandonado nao conta)
STATUS = "processing,completed,on-hold"
PAIR_MIN = 2  # combinacao vista uma unica vez nao vira recomendacao


def env() -> dict:
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


def api(base: str, headers: dict, path: str):
    req = urllib.request.Request(base + path, headers=headers)
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=180)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    tok = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    h = {"Authorization": "Basic " + tok, "User-Agent": "pm-affinity"}

    # slug de pa_unidade -> uid do catalogo (o nome do termo e o mesmo `option`)
    terms = api(base, h, "/wp-json/wc/v3/products/attributes/4/terms?per_page=100")
    term_to_uid = {}
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))["products"]
    option_to_uid = {}
    for row in cat.values():
        for unit_id, meta in (row.get("units") or {}).items():
            opt = str(meta.get("option") or "")
            if opt:
                option_to_uid.setdefault(opt, unit_id)
    for t in terms:
        uid = option_to_uid.get(str(t.get("name") or ""))
        if uid:
            term_to_uid[str(t["slug"])] = uid

    pid_to_cat = {}
    for cid, row in cat.items():
        for key in ("productId", "wooId"):
            pid = str(row.get(key) or "")
            if pid:
                pid_to_cat.setdefault(pid, cid)

    now = dt.datetime.now(dt.timezone.utc)
    since = (now - dt.timedelta(days=args.days)).strftime("%Y-%m-%dT%H:%M:%S")
    orders, page = [], 1
    while page <= 40:
        batch = api(
            base,
            h,
            f"/wp-json/wc/v3/orders?per_page=100&page={page}&after={since}&status={STATUS}",
        )
        if not batch:
            break
        orders += batch
        if len(batch) < 100:
            break
        page += 1

    print(f"pedidos analisados ({args.days}d, status {STATUS}): {len(orders)}")

    pair = collections.defaultdict(collections.Counter)
    sold = collections.Counter()
    unit_sold = collections.defaultdict(collections.Counter)
    orders_used = 0

    for o in orders:
        seen, units = set(), set()
        for li in o.get("line_items") or []:
            cid = pid_to_cat.get(str(li.get("product_id")))
            if not cid:
                continue
            qty = int(li.get("quantity") or 0)
            seen.add(cid)
            sold[cid] += qty
            for m in li.get("meta_data") or []:
                if m.get("key") == "pa_unidade":
                    uid = term_to_uid.get(str(m.get("value") or ""))
                    if uid:
                        units.add(uid)
        if not seen:
            continue
        orders_used += 1
        ids = sorted(seen)
        for i, a in enumerate(ids):
            for b in ids[i + 1 :]:
                pair[a][b] += 1
                pair[b][a] += 1
        for uid in units:
            for cid in ids:
                unit_sold[uid][cid] += 1

    pairs = {
        a: {b: n for b, n in c.items() if n >= PAIR_MIN}
        for a, c in pair.items()
        if any(n >= PAIR_MIN for n in c.values())
    }

    data = {
        "generatedAt": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "windowDays": args.days,
        "ordersAnalyzed": orders_used,
        "top": [cid for cid, _ in sold.most_common(60)],
        "unitsSold": {cid: sold[cid] for cid in [c for c, _ in sold.most_common(120)]},
        "pairs": pairs,
        "unitTop": {
            uid: [cid for cid, _ in counter.most_common(25)]
            for uid, counter in unit_sold.items()
        },
    }

    comuns = sorted(
        ((n, a, b) for a, m in pair.items() for b, n in m.items() if a < b),
        reverse=True,
    )[:12]
    print(f"produtos com venda: {len(sold)} | pares >= {PAIR_MIN}: "
          f"{sum(len(v) for v in pairs.values()) // 2}")
    for n, a, b in comuns:
        print(f"  {n:3d}x  {a} + {b}")

    if not args.write:
        print("\n(dry-run; use --write)")
        return
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"\ngravado {OUT.name}: {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
