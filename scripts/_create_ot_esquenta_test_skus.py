# -*- coding: utf-8 -*-
"""Cria SKUs de ensaio Esquenta (R$ 5,00) no OficialTeste + bridge/cart-related."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
BRIDGE = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
RELATED = ROOT / "wordpress-loja" / "pm-home" / "cart-related.json"

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
            e[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": e["PM_OFICIALTESTE_URL"].rstrip("/"),
        "user": e["PM_OFICIALTESTE_USER"],
        "password": e["PM_OFICIALTESTE_APP_PASSWORD"],
    }


def call(c, method, path, payload=None, timeout=120):
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
            "User-Agent": "pm-esquenta-sku/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
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


def upsert_product(c, catalog_id, method, name):
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
        "description": f"Produto de ensaio Esquenta ({method}). Não usar em produção.",
    }
    if existing:
        pid = existing["id"]
        st, saved = call(c, "PUT", f"/wp-json/wc/v3/products/{pid}", payload)
    else:
        st, saved = call(c, "POST", "/wp-json/wc/v3/products", payload)
    if st not in (200, 201) or not isinstance(saved, dict):
        raise SystemExit(f"fail {catalog_id}: {st} {saved}")
    return int(saved["id"])


def patch_local(ids_by_catalog: dict[str, int]):
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    related = json.loads(RELATED.read_text(encoding="utf-8"))
    products = related.setdefault("products", {})
    for catalog_id, method, name in SKUS:
        pid = ids_by_catalog[catalog_id]
        bridge[catalog_id] = {
            "slug": catalog_id,
            "productId": pid,
            "longText": name,
            "rj": {"regularCents": 500, "saleCents": 500},
            "spdf": {"regularCents": 500, "saleCents": 500},
            "units": {},
            "testEsquenta": True,
        }
        products[catalog_id] = {
            "id": catalog_id,
            "name": name,
            "method": method,
            "audience": "feminino",
            "originalCents": 500,
            "priceCents": 500,
            "skipDiscount": False,
            "duration": "Ensaio",
            "category": "corpo",
            "image": "/images/products/axila-cera.webp",
            "productId": str(pid),
            "wooId": str(pid),
        }
    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    RELATED.write_text(json.dumps(related, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("patched bridge+cart-related", len(ids_by_catalog))


def main():
    c = cfg()
    print("destino", c["url"])
    ids = {}
    for catalog_id, method, name in SKUS:
        pid = upsert_product(c, catalog_id, method, name)
        ids[catalog_id] = pid
        print("ok", catalog_id, pid)
    patch_local(ids)
    out = ROOT / "scripts" / "_ot_esquenta_test_skus.json"
    out.write_text(json.dumps(ids, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
