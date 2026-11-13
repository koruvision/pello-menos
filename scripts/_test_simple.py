# -*- coding: utf-8 -*-
"""Testa cenários de desconto - versao simplificada."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CR = ROOT / "wordpress-loja" / "pm-home" / "cart-related.json"

def money(cents):
    return f"R$ {cents/100:.2f}".replace(".", ",")

def main():
    with open(CR, "r", encoding="utf-8") as f:
        data = json.load(f)
    products = data.get("products") or data.get("byId") or {}

    print("=== TESTE DE DESCONTO - SEM RESTRIÇÕES ===\n")

    # Testes chave
    tests = [
        ("axilas-laser", 1, "Laser 1 área F"),
        ("axilas-laser", 2, "Laser 2 áreas F"),
        ("axilas-laser", 3, "Laser 3 áreas F"),
        ("axilas-laser-masc", 1, "Laser 1 área M"),
        ("axilas-laser-masc", 2, "Laser 2 áreas M"),
        ("axila-cera", 1, "Cera 1 área"),
        ("axila-cera", 2, "Cera 2 áreas"),
        ("axila-cera", 3, "Cera 3 áreas"),
        ("esfoliacao-axilas", 1, "Esfol 1 área"),
        ("esfoliacao-axilas", 3, "Esfol 3 áreas"),
    ]

    for pid, qty, desc in tests:
        p = products.get(pid)
        if not p:
            print(f"❌ {pid}: não encontrado")
            continue
        orig = p.get("originalCents") or 0
        sale = p.get("priceCents") or 0
        name = p.get("name", pid)

        # Calcular desconto unitário
        if orig > 0:
            disc_pct = round(((orig - sale) / orig) * 100, 2)
        else:
            disc_pct = 0

        total_orig = orig * qty
        total_sale = sale * qty

        print(f"{desc} ({pid}):")
        print(f"  Qty: {qty} | {name}")
        print(f"  Unitário - Original: {money(orig)} | Promo: {money(sale)}")
        print(f"   Desconto unitário: {disc_pct}%")
        print(f"   Total Original ({qty}×): {money(total_orig)}")
        print(f"   Total Promo ({qty}×): {money(total_sale)}")
        print()

if __name__ == "__main__":
    main()