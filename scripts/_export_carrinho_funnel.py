# -*- coding: utf-8 -*-
"""Export carrinho.html + checkout-header.html without audience switch."""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("export_wp_home", ROOT / "scripts" / "export_wp_home.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

PUBLICO_RE = re.compile(
    r'<div[^>]*border-b[^>]*>\s*<div[^>]*aria-label="Público"[^>]*>[\s\S]*?</div>\s*</div>',
    re.I,
)


def strip_publico(html: str) -> str:
    return PUBLICO_RE.sub("", html, count=1)


def main():
    path = "/carrinho"
    print("fetching", path)
    raw = mod.fetch(mod.ORIGIN + path).decode("utf-8", "replace")
    match = re.search(r"<title>(.*?)</title>", raw)
    title = match.group(1) if match else "Carrinho | Pello Menos"
    cart_scripts = (
        f'<script src="{mod.ASSET_BASE}/product.js?v=units1"></script>\n',
        f'<script src="{mod.ASSET_BASE}/cart.js?v=cart13"></script>\n',
    )
    document = mod.extract_document(raw, title, cart_scripts, product_id=None)
    document = mod.unwrap_react_hidden(document)
    document = mod.collect_and_rewrite_assets(document, set())
    document = mod.rewrite_links(document, mod.woo_slugs())
    document = strip_publico(document)
    out = mod.OUT / "carrinho.html"
    out.write_text(document, encoding="utf-8")
    print("wrote", out.name, "publico", 'aria-label="Público"' in document)

    match = re.search(r"<header[\s\S]*?</header>", document)
    if match:
        hdr = strip_publico(match.group(0))
        (mod.OUT / "checkout-header.html").write_text(hdr, encoding="utf-8")
        print(
            "wrote checkout-header.html",
            "publico",
            'aria-label="Público"' in hdr,
        )


if __name__ == "__main__":
    main()
