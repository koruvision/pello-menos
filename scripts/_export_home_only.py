# -*- coding: utf-8 -*-
"""Export only / -> home.html."""
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


def main():
    raw = exp.fetch(exp.ORIGIN + "/").decode("utf-8", "replace")
    title = "Pello Menos - Depilação"  # UTF-8
    scripts = ()
    if not (OUT / "home.css").is_file():
        css = exp.pull_css(raw)
        (OUT / "home.css").write_text(css, encoding="utf-8")
    document = exp.extract_document(raw, title, scripts)
    document = exp.unwrap_react_hidden(document)
    document = exp.collect_and_rewrite_assets(document, set())
    slugs = {}
    slugs_path = OUT / "woo-slugs.json"
    if slugs_path.is_file():
        slugs = json.loads(slugs_path.read_text(encoding="utf-8"))
    document = exp.rewrite_links(document, slugs)
    document = exp.apply_hero_backgrounds(document)
    dest = OUT / "home.html"
    dest.write_text(document, encoding="utf-8")
    print("home.html", "bytes", len(document))
    bad = ["Produto R$ 1,99", "produto-1-real", "pm-teste-esquenta", "ensaio-testes"]
    hits = {b: document.count(b) for b in bad}
    print("hits", hits)
    if any(hits.values()):
        sys.exit("test products still in home export")
    print("OK")


if __name__ == "__main__":
    main()
