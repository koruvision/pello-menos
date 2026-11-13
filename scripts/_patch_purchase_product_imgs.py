# -*- coding: utf-8 -*-
"""Replace social cliente-* first-paint refs with product catalog images in pm-home HTML."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"

REPLACEMENTS = [
    ("/images/social/cliente-1.png", "/images/products/axilas-laser.png"),
    ("/images/social/cliente-2.png", "/images/products/virilha-laser.png"),
    ("/images/social/cliente-3.png", "/images/products/perna-cera.png"),
    ("/images/social/cliente-4.png", "/images/products/design-sobrancelha.png"),
    ("/images/social/cliente-5.png", "/images/products/bracos-laser.png"),
]


def main() -> None:
    n_files = 0
    for path in PM.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        orig = text
        for old, new in REPLACEMENTS:
            text = text.replace(old, new)
        if text != orig:
            path.write_text(text, encoding="utf-8")
            n_files += 1
    print("patched_html_files", n_files)


if __name__ == "__main__":
    main()
