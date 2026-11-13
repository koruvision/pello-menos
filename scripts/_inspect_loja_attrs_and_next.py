# -*- coding: utf-8 -*-
"""READ-ONLY: loja product attributes/categories + Next catalog audience split."""
import json
import re
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOJA = "https://loja.pellomenos.com.br"


def get(url):
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "pm-readonly", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def main():
    # Sample a few variable products for attributes
    products = get(f"{LOJA}/wp-json/wc/store/v1/products?per_page=100")
    print("loja_store_count", len(products))
    for slug in ("axila-cera", "axilas-laser-2", "plano-de-assinatura-vip-silver-copia-2"):
        hits = [p for p in products if p.get("slug") == slug]
        if not hits:
            print("missing slug", slug)
            continue
        p = hits[0]
        print("\n===", p.get("name"), "id", p.get("id"), "type", p.get("type"))
        print("categories", [c.get("name") for c in (p.get("categories") or [])])
        print("tags", [t.get("name") for t in (p.get("tags") or [])])
        attrs = p.get("attributes") or []
        for a in attrs:
            print(
                " attr",
                a.get("name") or a.get("taxonomy"),
                "terms",
                [t.get("name") if isinstance(t, dict) else t for t in (a.get("terms") or a.get("options") or [])][:20],
            )
        # variations endpoint if any
        vid = p.get("id")
        try:
            vars_ = get(f"{LOJA}/wp-json/wc/store/v1/products/{vid}")
            print(" keys", sorted(vars_.keys())[:30])
            if vars_.get("variations"):
                print(" variations_count", len(vars_["variations"]))
                v0 = vars_["variations"][0]
                print(" variation0 keys", sorted(v0.keys()) if isinstance(v0, dict) else type(v0))
                if isinstance(v0, dict):
                    print(" variation0 attrs", v0.get("attributes"))
        except Exception as e:
            print(" detail err", e)

    # Search gift / splash / esfol / masc in names
    blob = " | ".join((p.get("name") or "") + " " + (p.get("slug") or "") for p in products).lower()
    for term in ("gift", "presente", "cartao", "splash", "esfol", "mascul", "homem", "barba"):
        print("has_term", term, term in blob)

    # Next catalog from data.ts
    text = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")
    ids = re.findall(r'\bid:\s*"([^"]+)"', text.split("const catalogItems")[1].split("function defaultDescription")[0])
    masc = [i for i in ids if i.endswith("-masc") or "masc" in i]
    fem = [i for i in ids if i not in masc]
    print("\nNEXT catalogItems ids", len(ids), "masc_like", len(masc), "other", len(fem))
    print("sample masc", masc[:25])
    gifts = [i for i in ids if "cartao-presente" in i or "gift" in i]
    splash = [i for i in ids if "splash" in i]
    planos = [i for i in ids if i.startswith("plano-")]
    print("next gifts", gifts)
    print("next splash", splash)
    print("next planos", planos)


if __name__ == "__main__":
    main()
