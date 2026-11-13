# -*- coding: utf-8 -*-
"""Re-export product (+ listing) pages for Esquenta price fix. Needs Next on :3456."""
from __future__ import annotations

import json
import os
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


def woo_slugs_cached():
    if CACHE.is_file():
        slugs = set(json.loads(CACHE.read_text(encoding="utf-8")))
        print("woo slugs cached", len(slugs), flush=True)
        return slugs
    return exp.woo_slugs()


exp.woo_slugs = woo_slugs_cached

# Narrow pages: homes + listings + all products (carrinho uses JS pricing).
_orig_main = exp.main


def main_focused():
    OUT = exp.OUT
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "products").mkdir(parents=True, exist_ok=True)
    slugs = exp.woo_slugs()
    bridge_path = ROOT / "src" / "lib" / "woo-bridge.json"
    bridge = json.loads(bridge_path.read_text(encoding="utf-8")) if bridge_path.is_file() else {}
    copied = set()
    css = ""
    product_scripts = (
        f'<script src="{exp.ASSET_BASE}/product.js?v=units3"></script>\n',
    )
    pages = [
        ("/", "home.html", "Pello Menos - Depilação", ()),
        ("/masculino", "masculino.html", "Masculino | Pello Menos", ()),
        ("/servicos", "pages/servicos.html", None, ()),
        ("/servicos/cera", "pages/servicos-cera.html", None, ()),
        ("/servicos/laser", "pages/servicos-laser.html", None, ()),
        ("/servicos/esfoliacao", "pages/servicos-esfoliacao.html", None, ()),
        ("/masculino/servicos", "pages/masculino-servicos.html", None, ()),
        ("/masculino/servicos/cera", "pages/masculino-servicos-cera.html", None, ()),
        ("/masculino/servicos/laser", "pages/masculino-servicos-laser.html", None, ()),
        ("/masculino/servicos/esfoliacao", "pages/masculino-servicos-esfoliacao.html", None, ()),
        ("/carrinho", "carrinho.html", "Carrinho | Pello Menos", product_scripts + (
            f'<script src="{exp.ASSET_BASE}/black-nov-campaign.js?v=black2"></script>\n',
            f'<script src="{exp.ASSET_BASE}/cart.js?v=cart26"></script>\n',
        )),
    ]
    ids = exp.catalog_ids()
    for product_id in ids:
        pages.append(
            (
                f"/produto/{product_id}",
                f"products/{product_id}.html",
                None,
                product_scripts,
            )
        )
    routes = {"carrinho": "carrinho.html"}
    page_files = {}
    import re
    from pathlib import Path as P

    for path, name, title, scripts in pages:
        raw = exp.fetch(exp.ORIGIN + path).decode("utf-8", "replace")
        if title is None:
            match = re.search(r"<title>(.*?)</title>", raw)
            title = match.group(1) if match else "Pello Menos"
        if not css:
            css = exp.pull_css(raw)
            (OUT / "home.css").write_text(css, encoding="utf-8")
        product_id = P(name).stem if name.startswith("products/") else None
        document = exp.extract_document(raw, title, scripts, product_id=product_id)
        document = exp.unwrap_react_hidden(document)
        document = exp.collect_and_rewrite_assets(document, copied)
        document = exp.rewrite_links(document, slugs)
        if name in ("home.html", "masculino.html"):
            document = exp.apply_hero_backgrounds(document)
        dest = OUT / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(document, encoding="utf-8")
        if name.startswith("products/"):
            routes[product_id] = name.replace("\\", "/")
        print(name, "bytes", len(document), flush=True)
        if name.startswith("pages/"):
            page_files[path] = name.replace("\\", "/")

    claimants = {}
    for pid, info in bridge.items():
        slug = (info or {}).get("slug") or ""
        if not slug or slug in routes:
            continue
        claimants.setdefault(slug, []).append(pid)
    for slug, pids in claimants.items():
        def score(pid: str) -> tuple:
            return (
                0 if pid.endswith("-masc") else 1,
                0 if str(pid).startswith("esfoliacao") else 1,
                -len(pid),
            )
        best = sorted(pids, key=score, reverse=True)[0]
        routes[slug] = f"products/{best}.html"
    (OUT / "routes.json").write_text(
        json.dumps(routes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("routes", len(routes), "page_files", len(page_files), flush=True)


if __name__ == "__main__":
    main_focused()
