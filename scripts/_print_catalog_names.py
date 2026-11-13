# -*- coding: utf-8 -*-
import json
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "catalog-loja-vs-oficialteste-full.json"
d = json.loads(p.read_text(encoding="utf-8"))

print("LOJA", len(d["loja_products"]))
for x in sorted(d["loja_products"], key=lambda i: i["name"].lower()):
    print(f"{x['id']}\t{x['type']}\t{x['kind']}\t{x['audience']}\t{x['name']}\t{x['slug']}")

print("\nOFICIALTESTE", len(d["oficialteste_products"]))
for x in sorted(d["oficialteste_products"], key=lambda i: i["name"].lower()):
    print(
        f"{x['id']}\t{x['status']}\t{x['type']}\t{x['kind']}\t{x['audience']}\t{x['name']}\t{x['slug']}"
    )

print("\nSO_NO_OFICIALTESTE")
for x in d["only_oficialteste_products"]:
    print(f"{x['id']}\t{x['status']}\t{x['name']}\t{x['slug']}")
