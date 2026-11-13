# -*- coding: utf-8 -*-
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "export_wp_home", ROOT / "scripts" / "export_wp_home.py"
)
exp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp)
OUT = exp.OUT


def export_one(path, name, title):
    raw = exp.fetch(exp.ORIGIN + path).decode("utf-8", "replace")
    document = exp.extract_document(raw, title, ())
    document = exp.unwrap_react_hidden(document)
    document = exp.collect_and_rewrite_assets(document, set())
    slugs = {}
    slugs_path = OUT / "woo-slugs.json"
    if slugs_path.is_file():
        slugs = json.loads(slugs_path.read_text(encoding="utf-8"))
    document = exp.rewrite_links(document, slugs)
    if name in ("home.html", "masculino.html"):
        document = exp.apply_hero_backgrounds(document)
    dest = OUT / name
    dest.write_text(document, encoding="utf-8")
    print(name, "bytes", len(document))
    return document


def main():
    home = export_one("/", "home.html", "Pello Menos - Depilação")
    masc = export_one("/masculino", "masculino.html", "Masculino | Pello Menos")
    for needle in (
        "banner-exemplo-avatar-esquerda",
        "banner-virilha",
        "banner-bracos",
        "baked",
    ):
        # baked images may not include the word baked; just print presence of key assets
        pass
    print(
        "baked assets",
        "esquerda-desktop" in home,
        "virilha-desktop" in home or "banner-virilha" in home,
        "bracos-desktop" in home or "banner-bracos" in home,
    )
    print(
        "mobile examples",
        "banner-exemplo-avatar-esquerda" in home,
        "banner-virilha-mobile" in home,
        "banner-bracos-mobile" in home,
    )
    print("OK")


if __name__ == "__main__":
    main()
