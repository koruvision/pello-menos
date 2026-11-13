# -*- coding: utf-8 -*-
"""Re-export only planos + body splash product pages (and listagens)."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("PM_HOME_ORIGIN", "http://127.0.0.1:3456")
os.environ.setdefault(
    "PM_ASSET_BASE",
    "https://loja.pellomenos.com.br/wp-content/uploads/pm-home",
)

import export_wp_home as exp

CACHE = ROOT / "wordpress-loja" / "pm-home" / "woo-slugs.json"
IDS = [
    "plano-silver",
    "plano-gold",
    "plano-prepago",
    "plano-clube-laser",
    "plano-silver-masc",
    "plano-gold-masc",
    "plano-prepago-masc",
    "body-splash-livre",
    "body-splash-marcante",
    "body-splash-autentica",
    "body-splash-livre-masc",
    "body-splash-marcante-masc",
    "body-splash-autentica-masc",
]


def woo_slugs_cached():
    if CACHE.is_file():
        return set(json.loads(CACHE.read_text(encoding="utf-8")))
    return exp.woo_slugs()


exp.woo_slugs = woo_slugs_cached


def main() -> None:
    OUT = exp.OUT
    slugs = exp.woo_slugs()
    copied = set()
    product_scripts = (
        f'<script src="{exp.ASSET_BASE}/product.js?v=units3"></script>\n',
    )
    pages = [
        ("/produtos", "pages/produtos.html", None, ()),
        ("/masculino/produtos", "pages/masculino-produtos.html", None, ()),
        ("/planos", "pages/planos.html", None, ()),
        ("/masculino/planos", "pages/masculino-planos.html", None, ()),
    ]
    for pid in IDS:
        pages.append((f"/produto/{pid}", f"products/{pid}.html", None, product_scripts))

    for path, name, title, scripts in pages:
        raw = exp.fetch(exp.ORIGIN + path).decode("utf-8", "replace")
        if title is None:
            m = re.search(r"<title>(.*?)</title>", raw)
            title = m.group(1) if m else "Pello Menos"
        product_id = Path(name).stem if name.startswith("products/") else None
        document = exp.extract_document(raw, title, scripts, product_id=product_id)
        document = exp.unwrap_react_hidden(document)
        document = exp.collect_and_rewrite_assets(document, copied)
        document = exp.rewrite_links(document, slugs)
        dest = OUT / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(document, encoding="utf-8")
        print(name, len(document), flush=True)


if __name__ == "__main__":
    main()
