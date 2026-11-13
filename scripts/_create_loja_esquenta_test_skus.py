# -*- coding: utf-8 -*-
"""Cria SKUs de ensaio Esquenta (R$ 5,00) na LOJA oficial (hidden)."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
OUT = ROOT / "scripts" / "_loja_esquenta_test_skus.json"

SKUS = [
    ("pm-teste-esquenta-laser", "laser", "PM Teste Esquenta Laser A"),
    ("pm-teste-esquenta-laser-b", "laser", "PM Teste Esquenta Laser B"),
    ("pm-teste-esquenta-laser-c", "laser", "PM Teste Esquenta Laser C"),
    ("pm-teste-esquenta-cera", "cera", "PM Teste Esquenta Cera A"),
    ("pm-teste-esquenta-cera-b", "cera", "PM Teste Esquenta Cera B"),
    ("pm-teste-esquenta-cera-c", "cera", "PM Teste Esquenta Cera C"),
]


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return {
        "url": e["PM_LOJA_URL"].rstrip("/"),
        "user": e["PM_LOJA_USER"],
        "password": e["PM_LOJA_APP_PASSWORD"],
    }


def call(c, method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-loja-esquenta-sku/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body[:1] in "[{" else body)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body[:500]}
        return err.code, parsed


def find_by_sku(c, sku):
    st, rows = call(c, "GET", f"/wp-json/wc/v3/products?sku={urllib.parse.quote(sku)}&per_page=5")
    if st == 200 and isinstance(rows, list) and rows:
        return rows[0]
    return None


def upsert(c, catalog_id, method, name):
    existing = find_by_sku(c, catalog_id)
    payload = {
        "name": name,
        "type": "simple",
        "regular_price": "5.00",
        "sale_price": "",
        "sku": catalog_id,
        "status": "publish",
        "catalog_visibility": "hidden",
        "virtual": True,
        "meta_data": [
            {"key": "_pm_catalog_id", "value": catalog_id},
            {"key": "pm_catalog_id", "value": catalog_id},
            {"key": "_pm_test_esquenta", "value": "1"},
        ],
        "description": f"Produto de ensaio Esquenta ({method}). Nao listar / nao usar em venda normal.",
    }
    if existing:
        st, saved = call(c, "PUT", f"/wp-json/wc/v3/products/{existing['id']}", payload)
    else:
        st, saved = call(c, "POST", "/wp-json/wc/v3/products", payload)
    if st not in (200, 201) or not isinstance(saved, dict):
        raise SystemExit(f"fail {catalog_id}: {st} {saved}")
    return int(saved["id"]), saved.get("status"), saved.get("catalog_visibility")


def main():
    c = cfg()
    print("destino", c["url"], "user", c["user"])
    # auth check
    st, me = call(c, "GET", "/wp-json/wp/v2/users/me")
    print("auth", st, me.get("slug") if isinstance(me, dict) else me)
    if st != 200:
        raise SystemExit("loja auth failed")

    ids = {}
    for catalog_id, method, name in SKUS:
        pid, status, vis = upsert(c, catalog_id, method, name)
        ids[catalog_id] = pid
        print("ok", catalog_id, pid, status, vis)

    OUT.write_text(json.dumps(ids, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
