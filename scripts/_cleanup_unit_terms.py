# -*- coding: utf-8 -*-
"""Remove os termos de unidade criados por engano (nome == slug, ex. 'ipanema').

Antes de apagar, confere que NENHUM produto/variacao usa o termo — se usar, o termo
fica e o produto entra no relatorio.

Uso: python scripts/_cleanup_unit_terms.py [--write]
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
        self.h = {"Authorization": "Basic " + tok, "User-Agent": "pm-terms-clean"}

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
            return err.code, err.read().decode("utf-8", "replace")[:200]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    api = Api()
    st, terms = api.call("GET", f"/wp-json/wc/v3/products/attributes/{ATTR_ID}/terms?per_page=100")
    junk = [t for t in terms if " - " not in str(t.get("name") or "")]
    print(f"termos totais: {len(terms)} | candidatos a remocao: {len(junk)}")

    # mapeia uso: qualquer opção de produto/variacao que bata com nome do termo lixo
    usados = set()
    page = 1
    prods = []
    while True:
        st, chunk = api.call("GET", f"/wp-json/wc/v3/products?per_page=100&page={page}&status=any")
        if st != 200 or not chunk:
            break
        prods += chunk
        if len(chunk) < 100:
            break
        page += 1
    for p in prods:
        for a in p.get("attributes") or []:
            for o in a.get("options") or []:
                usados.add(str(o))
    print("produtos varridos:", len(prods))

    remover, manter = [], []
    for t in junk:
        if t["name"] in usados:
            manter.append(t)
        else:
            remover.append(t)
    print("a remover:", len(remover), "| mantidos (em uso):", len(manter))
    for t in manter[:10]:
        print("   MANTIDO", t["id"], t["slug"], t["name"])

    if not args.write:
        print("\n(dry-run; use --write)")
        return

    ok = 0
    for t in remover:
        st, body = api.call("DELETE", f"/wp-json/wc/v3/products/attributes/{ATTR_ID}/terms/{t['id']}?force=true")
        if st in (200, 204):
            ok += 1
        else:
            print("  ERRO", t["id"], t["slug"], st, str(body)[:100])
    print("removidos:", ok)


if __name__ == "__main__":
    main()