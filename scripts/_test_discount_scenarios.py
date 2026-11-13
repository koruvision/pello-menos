# -*- coding: utf-8 -*-
"""Testa cenários de desconto não cobertos anteriormente."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
CR = ROOT / "wordpress-loja" / "pm-home" / "cart-related.json"


def cfg():
    with open(ROOT / "projeto-migracao" / ".secrets" / "loja.env", "r", encoding="utf-8") as f:
        e = {}
        for line in f.read().splitlines():
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
            "User-Agent": "pm-discount-test",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body[:1] in "[{" else body)


def money(cents):
    return f"R$ {cents/100:.2f}".replace(".", ",")


def main():
    c = cfg()

    print("=" * 70)
    print("TESTES ADICIONAIS DE DESCONTO")
    print("=" * 70)

    # === CENÁRIOS A TESTAR ===
    # (product_id, quantity, expected_discount_pct, description)
    test_cases = [
        # Laser Masculino
        ("axilas-laser-masc", 2, 60, "Laser Masc 2 áreas"),
        ("axilas-laser-masc", 3, 60, "Laser Masc 3 áreas"),
        ("axilas-laser-masc", 4, 60, "Laser Masc 4 áreas"),

        # Laser Feminino quantities beyond 3
        ("axilas-laser", 4, 60, "Laser Fem 4 áreas"),
        ("axilas-laser", 5, 60, "Laser Fem 5 áreas"),

        # Cera quantities beyond 3
        ("axila-cera", 4, 15, "Cera 4 áreas"),
        ("axila-cera", 5, 15, "Cera 5 áreas"),

        # Esfoliação quantities beyond 3
        ("esfoliacao-axilas", 4, 15, "Esfol 4 áreas"),
        ("esfoliacao-axilas", 5, 15, "Esfol 5 áreas"),

        # Combos diferentes (1 de cada)
        ("axilas-laser", 1, 60, "Laser + 1 de outro tipo"),
        ("axila-cera", 1, 15, "Cera + outro tipo"),
    ]

    print("\n--- Resultados dos Testes ---\n")

    passed = 0
    failed = 0

    for product_id, qty, expected_disc, desc in test_cases:
        # Get product info from cart-related.json
        cr = json.loads(open(CR, "r", encoding="utf-8").read())
        products = cr.get("products") or cr.get("byId") or cr
        p = products.get(product_id)

        if not p or not isinstance(p, dict):
            print(f"❌ {desc}: Produto {product_id} não encontrado")
            failed += 1
            continue

        orig = p.get("originalCents") or 0
        sale = p.get("priceCents") or 0
        name = p.get("name", product_id)

        # Calcular desconto por unidade
        if orig > 0:
            discount_pct_orig = round(((orig - sale) / orig) * 100, 2)
        else:
            discount_pct_orig = 0

        # O desconto é o mesmo por unidade, quantidade não afeta a porcentagem
        status = "✅" if discount_pct_orig == expected_disc else "❌"

        print(f"{status} {desc}:")
        print(f"   Qty: {qty} | Produto: {name}")
        print(f"   Preço unitário original: {money(orig)}")
        print(f"   Preço unitário promocional: {money(sale)}")
        print(f"   Desconto atual: {discount_pct_orig}% | Esperado: {expected_disc}%")
        print(f"   Total original ({qty}×): {money(orig * qty)}")
        print(f"   Total promocional ({qty}×): {money(sale * qty)}")
        print()

        if discount_pct_orig == expected_disc:
            passed += 1
        else:
            failed += 1

    print("=" * 70)
    print(f"RESULTADO FINAL: {passed} passed, {failed} failed")
    print("=" * 70)


if __name__ == "__main__":
    main()