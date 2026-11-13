# -*- coding: utf-8 -*-
"""Corrige preço promocional do axilas-laser em TODAS as variações no WooCommerce.

Problema: Woo cobra R$ 94,90 mas frontend mostra R$ 359,96.
Atualiza todas as variações do produto 8650 para sale_price=359.96, regular_price=899.90.
"""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return {
        "url": e["PM_LOJA_URL"].rstrip("/"),
        "user": e["PM_LOJA_USER"],
        "password": e["PM_LOJA_APP_PASSWORD"],
    }


def call(c, method, path, payload=None):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        c["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-fix-price",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body[:1] in "[{" else body)


def main():
    c = cfg()
    assert "loja.pellomenos.com.br" in c["url"]

    product_id = 8650
    TARGET_SALE = "359.96"
    TARGET_REGULAR = "899.90"

    print("=== 1. Buscar todas as variações do axilas-laser ===")
    status, variations = call(c, "GET", f"/wp-json/wc/v3/products/{product_id}/variations?per_page=100")
    print(f"Status: {status}, Total variações: {len(variations) if isinstance(variations, list) else 'erro'}")

    if not isinstance(variations, list):
        print("ERRO ao buscar variações:", variations)
        return

    # Mostrar estado atual
    print("\nEstado atual:")
    for v in variations:
        print(f"  #{v['id']:>6} | {v.get('option_1',''):<45} | regular={v.get('regular_price')} | sale={v.get('sale_price')} | price={v.get('price')}")

    # Atualizar cada variação que tem sale_price != 359.96
    print(f"\n=== 2. Atualizando variações (sale_price -> {TARGET_SALE}, regular -> {TARGET_REGULAR}) ===")
    updated_count = 0
    for v in variations:
        vid = v["id"]
        current_sale = v.get("sale_price", "")
        current_regular = v.get("regular_price", "")

        # Só atualiza se houver diferença
        if current_sale == TARGET_SALE and current_regular == TARGET_REGULAR:
            print(f"  #{vid}: já correto (sale={current_sale}, regular={current_regular}) - pulando")
            continue

        payload = {
            "sale_price": TARGET_SALE,
            "regular_price": TARGET_REGULAR,
        }
        status, result = call(c, "PUT", f"/wp-json/wc/v3/products/{product_id}/variations/{vid}", payload)
        if status in (200, 201):
            updated_count += 1
            print(f"  #{vid}: ATUALIZADO -> sale={TARGET_SALE}, regular={TARGET_REGULAR}")
        else:
            print(f"  #{vid}: ERRO status={status} -> {json.dumps(result, ensure_ascii=False)[:200]}")

    # Verificação final
    print(f"\n=== 3. Verificação final ===")
    status, final_vars = call(c, "GET", f"/wp-json/wc/v3/products/{product_id}/variations?per_page=100")
    print(f"Status: {status}, Total: {len(final_vars) if isinstance(final_vars, list) else 'erro'}")

    all_ok = True
    for v in final_vars:
        sale_ok = v.get("sale_price") == TARGET_SALE
        reg_ok = v.get("regular_price") == TARGET_REGULAR
        if not sale_ok or not reg_ok:
            all_ok = False
            print(f"  #{v['id']:>6} | {v.get('option_1',''):<45} | sale={v.get('sale_price')} regular={v.get('regular_price')} ❌")
        else:
            print(f"  #{v['id']:>6} | {v.get('option_1',''):<45} | sale={v.get('sale_price')} regular={v.get('regular_price')} ✅")

    print(f"\n{'✅ TODAS CORRETAS' if all_ok else '❌ AINDA HÁ ERROS'}")
    print(f"Variações atualizadas: {updated_count}")


if __name__ == "__main__":
    main()