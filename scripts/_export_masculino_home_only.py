# -*- coding: utf-8 -*-
"""Export only masculino.html. Needs Next :3456."""
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
        return set(json.loads(CACHE.read_text(encoding="utf-8")))
    return exp.woo_slugs()


exp.woo_slugs = woo_slugs_cached


def main() -> None:
    OUT = exp.OUT
    OUT.mkdir(parents=True, exist_ok=True)
    slugs = exp.woo_slugs()
    copied: set[str] = set()
    raw = exp.fetch(exp.ORIGIN + "/masculino").decode("utf-8", "replace")
    css = exp.pull_css(raw)
    (OUT / "home.css").write_text(css, encoding="utf-8")
    document = exp.extract_document(raw, "Masculino | Pello Menos", ())
    document = exp.unwrap_react_hidden(document)
    document = exp.collect_and_rewrite_assets(document, copied)
    document = exp.rewrite_links(document, slugs)
    document = exp.apply_hero_backgrounds(document)
    (OUT / "masculino.html").write_text(document, encoding="utf-8")
    print("masculino.html", len(document))
    # sanity: mobile hero should reference desktop hero-peito (not hero-peito-m)
    if "hero-peito-m" in document:
        print("WARN still has hero-peito-m")
    peito = document.count("hero-peito.jpg")
    print("hero-peito.jpg refs", peito)


if __name__ == "__main__":
    main()
