# -*- coding: utf-8 -*-
"""Corrige os produtos criados na regularizacao: atributo Unidade deve usar o NOME do
termo, nao o slug — tanto no produto quanto em cada variacao.

Evidencia: com option='ipanema' (slug), adicionar essa variacao ESVAZIAVA o carrinho
dos outros itens (pedidos 51248/51243). Com option='RJ - Ipanema' (nome, como nos
produtos antigos), a mistura passou a funcionar.

Uso: python scripts/_fix_unit_term_names.py [--write] [--dry]
"""
from __future__ import annotations

import argparse
import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTR_ID = 4


def env() -> dict:
    e = {}
    for line in (ROOT / "projeto-migracao" / ".secrets" / "loja.env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


class Api:
    def __init__(self) -> None:
        e = env()
        self.base = e["PM_LOJA_URL"].rstrip("/")
        tok = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
        self.h = {"Authorization": "Basic " + tok, "User-Agent": "pm-terms"}

    def call(self, method: str, path: str, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        hh = dict(self.h)
        if payload is not None:
            hh["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=hh)
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body.strip()[:1] in "{[" else body)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    api = Api()
    st, terms = api.call("GET", f"/wp-json/wc/v3/products/attributes/{ATTR_ID}/terms?per_page=100")
    assert st == 200 and isinstance(terms, list), (st, terms)
    # So os termos canonicos (nome com " - ", ex. "RJ - Ipanema"). Os termos criados
    # por engano na regularizacao tem nome igual ao slug e ficam de fora.
    slug2name = {t["slug"]: t["name"] for t in terms if " - " in str(t.get("name") or "")}
    print("termos pa_unidade canonicos:", len(slug2name), "| total:", len(terms))

    produtos = []
    page = 1
    while True:
        st, chunk = api.call("GET", f"/wp-json/wc/v3/products?per_page=100&page={page}&status=any")
        if st != 200 or not chunk:
            break
        produtos += chunk
        if len(chunk) < 100:
            break
        page += 1
    print("produtos:", len(produtos))

    alvos = []
    for p in produtos:
        attrs = p.get("attributes") or []
        if not attrs:
            continue
        opts = attrs[0].get("options") or []
        if not opts:
            continue
        # só mexe se alguma opção estiver em formato de slug
        if any(o in slug2name for o in opts):
            alvos.append(p)

    print("produtos com option em slug:", len(alvos))
    for p in alvos[:8]:
        print(f"   {p['id']:6d} {p['name'][:40]} -> {p['attributes'][0]['options'][:3]}")

    if not alvos:
        print("nada a corrigir")
        return
    if not args.write:
        print("\n(dry-run; use --write)")
        return

    ok_prod = ok_var = 0
    for p in alvos:
        pid = p["id"]
        opts = p["attributes"][0]["options"]
        novas = sorted({slug2name.get(o, o) for o in opts})
        st, saved = api.call("PUT", f"/wp-json/wc/v3/products/{pid}", {
            "attributes": [{"id": ATTR_ID, "variation": True, "visible": True, "options": novas}],
        })
        if st == 200:
            ok_prod += 1
        else:
            print("  ERRO produto", pid, st, str(saved)[:120])
            continue

        st, vs = api.call("GET", f"/wp-json/wc/v3/products/{pid}/variations?per_page=100")
        if st != 200 or not isinstance(vs, list):
            continue
        for v in vs:
            attrs = v.get("attributes") or []
            if not attrs:
                continue
            cur = str(attrs[0].get("option") or "")
            if cur not in slug2name:
                continue
            st2, _ = api.call("PUT", f"/wp-json/wc/v3/products/{pid}/variations/{v['id']}", {
                "attributes": [{"id": ATTR_ID, "option": slug2name[cur]}],
            })
            if st2 == 200:
                ok_var += 1
        if ok_prod % 10 == 0:
            print(f"  ... {ok_prod}/{len(alvos)} produtos, {ok_var} variacoes")

    print(f"\nprodutos corrigidos: {ok_prod} | variacoes corrigidas: {ok_var}")


if __name__ == "__main__":
    main()