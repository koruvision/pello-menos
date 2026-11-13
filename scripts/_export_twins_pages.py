# -*- coding: utf-8 -*-
"""Export only chrome twins + key masculino pages (fast path)."""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("export_wp_home", ROOT / "scripts" / "export_wp_home.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

OUT = mod.OUT
ORIGIN = mod.ORIGIN
ASSET_BASE = mod.ASSET_BASE

TWINS = [
    "body-splash-livre-masc",
    "body-splash-marcante-masc",
    "body-splash-autentica-masc",
    "cartao-presente-masc",
    "cartao-presente-160-masc",
    "cartao-presente-215-masc",
    "cartao-presente-290-masc",
    "plano-silver-masc",
    "plano-gold-masc",
    "plano-prepago-masc",
]

PAGES = [
    ("/masculino", "masculino.html"),
    ("/masculino/planos", "pages/masculino-planos.html"),
    ("/masculino/produtos", "pages/masculino-produtos.html"),
    ("/masculino/cartao-presente", "pages/masculino-cartao-presente.html"),
    ("/produtos", "pages/produtos.html"),
    ("/planos", "pages/planos.html"),
    ("/cartao-presente", "pages/cartao-presente.html"),
]


def main():
    product_scripts = (f'<script src="{ASSET_BASE}/product.js?v=units1"></script>\n',)
    product_ids = list(
        dict.fromkeys(
            TWINS
            + [
                "body-splash-livre",
                "body-splash-marcante",
                "body-splash-autentica",
                "cartao-presente",
                "cartao-presente-160",
                "cartao-presente-215",
                "cartao-presente-290",
                "plano-silver",
                "plano-gold",
                "plano-prepago",
                "plano-clube-laser",
                "axila-cera",
                "axila-cera-masc",
                "abdomen-laser",
                "axilas-laser-masc",
            ]
        )
    )

    routes_path = OUT / "routes.json"
    pages_path = OUT / "pages.json"
    routes = json.loads(routes_path.read_text(encoding="utf-8")) if routes_path.exists() else {}
    pages = json.loads(pages_path.read_text(encoding="utf-8")) if pages_path.exists() else {}

    for path, name in PAGES:
        print("page", path)
        raw = mod.fetch(ORIGIN + path).decode("utf-8", "replace")
        match = re.search(r"<title>(.*?)</title>", raw)
        title = match.group(1) if match else "Pello Menos"
        product_id = None
        document = mod.extract_document(raw, title, (), product_id=product_id)
        document = mod.unwrap_react_hidden(document)
        if "masculino" in path:
            document = mod.force_masculino_audience(document)
        target = OUT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(document, encoding="utf-8")
        pages[path if path != "/masculino" else "/masculino"] = name.replace("\\", "/")
        if path == "/masculino":
            pages["/masculino"] = "masculino.html"

    pages["/masculino/cartao-presente"] = "pages/masculino-cartao-presente.html"

    for product_id in product_ids:
        path = f"/produto/{product_id}"
        print("product", product_id)
        raw = mod.fetch(ORIGIN + path).decode("utf-8", "replace")
        match = re.search(r"<title>(.*?)</title>", raw)
        title = match.group(1) if match else product_id
        document = mod.extract_document(raw, title, product_scripts, product_id=product_id)
        document = mod.unwrap_react_hidden(document)
        # extract_document already forces masculino chrome + head script for *-masc.
        target = OUT / "products" / f"{product_id}.html"
        target.write_text(document, encoding="utf-8")
        routes[product_id] = f"products/{product_id}.html"

    routes_path.write_text(json.dumps(routes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pages_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("done", "twins", len(TWINS), "products", len(product_ids))


if __name__ == "__main__":
    main()
