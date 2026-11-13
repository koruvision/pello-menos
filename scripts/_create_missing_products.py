# -*- coding: utf-8 -*-
"""Regulariza produtos do catalogo que nao tem cadastro proprio no WooCommerce.

Cria um produto variavel por item que hoje compartilha o productId com outro servico
(esfoliacao usando o produto da cera; masculino usando o feminino) e religa as
variacoes no cart-related.json / woo-bridge.json.

Precos vem da propria pagina do produto (data-rj-regular / data-sp-regular), nao de
valores inventados:
  - unidades "SP - Capital *" e "DF - *" -> preco SP
  - demais (RJ + SP Interior) -> preco RJ

Uso: python scripts/_create_missing_products.py [--write] [--limit N]
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
CR = PM / "cart-related.json"
BRIDGE = PM / "woo-bridge.json"
REPORT = ROOT / "scripts" / "_missing_products_report.json"
ATTR_ID = 4  # pa_unidade


def env() -> dict:
    e = {}
    for line in (ROOT / "projeto-migracao" / ".secrets" / "loja.env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


def norm(s: str) -> str:
    s = str(s or "").lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def core(key: str) -> str:
    return key[:-5] if key.endswith("-masc") else key


class Api:
    def __init__(self) -> None:
        e = env()
        self.base = e["PM_LOJA_URL"].rstrip("/")
        tok = base64.b64encode(
            f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()
        ).decode()
        self.h = {"Authorization": "Basic " + tok, "User-Agent": "pm-regulariza"}
        self.terms = {}

    def call(self, method: str, path: str, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        hh = dict(self.h)
        if payload is not None:
            hh["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=hh)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read().decode("utf-8", "replace")
                return r.status, (json.loads(body) if body.strip()[:1] in "{[" else body)
        except urllib.error.HTTPError as err:
            raw = err.read().decode("utf-8", "replace")
            try:
                return err.code, json.loads(raw)
            except json.JSONDecodeError:
                return err.code, raw[:400]

    def load_terms(self):
        st, terms = self.call("GET", f"/wp-json/wc/v3/products/attributes/{ATTR_ID}/terms?per_page=100")
        assert st == 200 and isinstance(terms, list), (st, terms)
        for t in terms:
            self.terms[norm(t["name"])] = {"slug": t["slug"], "name": t["name"], "id": t["id"]}
        return self.terms


def prices_from_page(key: str):
    f = PM / "products" / f"{key}.html"
    if not f.exists():
        return None
    h = f.read_text(encoding="utf-8", errors="replace")

    def pick(attr: str):
        m = re.search(rf'data-{attr}="(\d+)"', h)
        return int(m.group(1)) if m else None

    rj, sp = pick("rj-regular"), pick("sp-regular")
    if not rj:
        return None
    return {"rj": rj / 100.0, "sp": (sp or rj) / 100.0}


def is_sp_df(label: str) -> bool:
    n = norm(label)
    return n.startswith("sp capital") or n.startswith("df ")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    api = Api()
    api.load_terms()
    cr = json.loads(CR.read_text(encoding="utf-8"))
    cat = cr["products"]

    st, products = api.call("GET", "/wp-json/wc/v3/products?per_page=100&page=1&status=any")
    by_name = {}
    by_id = {}
    page = 1
    allp = []
    while True:
        st, chunk = api.call("GET", f"/wp-json/wc/v3/products?per_page=100&page={page}&status=any")
        if st != 200 or not chunk:
            break
        allp += chunk
        if len(chunk) < 100:
            break
        page += 1
    for p in allp:
        by_id[str(p["id"])] = p
        by_name.setdefault(norm(p.get("name")), str(p["id"]))
    print("produtos no Woo:", len(allp))

    # agrupa por productId e identifica quem NAO e o dono legitimo
    groups = defaultdict(list)
    for key, row in cat.items():
        if row.get("units"):
            groups[str(row.get("productId"))].append(key)

    alvos = []
    for pid, keys in groups.items():
        prod = by_id.get(pid) or {}
        owner_name = norm(prod.get("name"))
        cores = {core(k) for k in keys}
        if len(cores) == 1 and pid in by_id:
            continue  # so twins fem/masc do mesmo servico -> ok
        # dono = item cujo nome do catalogo mais se parece com o nome do produto Woo
        owner = None
        best = 0.0
        for k in keys:
            a = set(norm(k).split())
            b = set(owner_name.split())
            sc = len(a & b) / max(1, len(a | b))
            if sc > best:
                best, owner = sc, k
        for k in keys:
            if k != owner:
                alvos.append({"key": k, "share_pid": pid, "owner": owner})

    # tambem os itens sem nenhuma variacao
    for key, row in cat.items():
        units = row.get("units") or {}
        if units and not any(m.get("variationId") for m in units.values()):
            if not any(a["key"] == key for a in alvos):
                alvos.append({"key": key, "share_pid": str(row.get("productId")), "owner": None})

    print("itens para produto dedicado:", len(alvos))
    planejados = []
    for a in alvos:
        key = a["key"]
        row = cat[key]
        pr = prices_from_page(key)
        units = []
        for uid, meta in (row.get("units") or {}).items():
            label = meta.get("option") or ""
            term = api.terms.get(norm(label))
            if not term:
                continue
            units.append({
                "uid": uid,
                "term": term["slug"],
                "label": term["name"],
                "price": (pr or {}).get("sp" if is_sp_df(label) else "rj"),
            })
        planejados.append({
            "key": key,
            "name": row.get("name"),
            "price": pr,
            "units": units,
            "unmapped_units": [m.get("option") for uid, m in (row.get("units") or {}).items()
                               if norm(m.get("option")) not in api.terms],
        })

    sem_preco = [p for p in planejados if not p["price"]]
    sem_units = [p for p in planejados if not p["units"]]
    print("sem pagina/preco:", len(sem_preco), [p["key"] for p in sem_preco][:20])
    print("sem unidades mapeadas:", len(sem_units), [p["key"] for p in sem_units][:20])
    print()
    for p in planejados[:12]:
        print(f"  {p['key']:30s} preco={p['price']} units={len(p['units'])}")

    REPORT.write_text(json.dumps({"planned": planejados}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nrelatorio:", REPORT)

    if not args.write:
        print("(dry-run; use --write para criar)")
        return

    criados = {}
    for i, p in enumerate(planejados, 1):
        if args.limit and i > args.limit:
            break
        if not p["price"] or not p["units"]:
            continue
        payload = {
            "name": p["name"],
            "type": "variable",
            "status": "publish",
            "catalog_visibility": "hidden",
            "attributes": [{
                "id": ATTR_ID,
                "variation": True,
                "visible": True,
                "options": sorted({u["term"] for u in p["units"]}),
            }],
        }
        st, created = api.call("POST", "/wp-json/wc/v3/products", payload)
        if st not in (200, 201) or not isinstance(created, dict):
            print("ERRO criar", p["key"], st, str(created)[:200])
            continue
        pid = created["id"]
        vid_map = {}
        for u in p["units"]:
            stv, var = api.call("POST", f"/wp-json/wc/v3/products/{pid}/variations", {
                "regular_price": f"{u['price']:.2f}",
                "attributes": [{"id": ATTR_ID, "option": u["term"]}],
            })
            if stv in (200, 201) and isinstance(var, dict):
                vid_map[u["uid"]] = str(var["id"])
            else:
                print("  erro variacao", p["key"], u["term"], stv, str(var)[:120])
        criados[p["key"]] = {"productId": str(pid), "units": vid_map}
        print(f"criado {p['key']} -> pid {pid} com {len(vid_map)} variacoes")
        time.sleep(0.15)

    if not criados:
        print("nada criado")
        return

    for key, info in criados.items():
        row = cat[key]
        row["productId"] = info["productId"]
        row["wooId"] = info["productId"]
        for uid, vid in info["units"].items():
            if uid in row["units"]:
                row["units"][uid]["variationId"] = vid
    CR.write_text(json.dumps(cr, ensure_ascii=False, indent=2), encoding="utf-8")

    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    for key, info in criados.items():
        if key in bridge:
            bridge[key]["productId"] = int(info["productId"])
            for uid, vid in info["units"].items():
                if uid in (bridge[key].get("units") or {}):
                    bridge[key]["units"][uid]["variationId"] = int(vid)
    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2), encoding="utf-8")
    print("criados:", len(criados), "| mapeamentos atualizados")


if __name__ == "__main__":
    main()