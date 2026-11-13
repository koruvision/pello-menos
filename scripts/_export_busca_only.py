# -*- coding: utf-8 -*-
"""Export only /busca -> busca.html using export_wp_home helpers."""
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

ASSET_BASE = exp.ASSET_BASE
OUT = exp.OUT


def main():
    scripts = (f'<script src="{ASSET_BASE}/busca.js?v=busca3"></script>\n',)
    raw = exp.fetch(exp.ORIGIN + "/busca").decode("utf-8", "replace")
    title = "Busca | Pello Menos"
    # reuse css if present
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
    dest = OUT / "busca.html"
    dest.write_text(document, encoding="utf-8")
    print("busca.html", "bytes", len(document))
    if "data-pm-search-page" not in document:
        sys.exit("missing data-pm-search-page")
    if "busca.js" not in document:
        sys.exit("missing busca.js script")
    print("OK")


if __name__ == "__main__":
    main()
