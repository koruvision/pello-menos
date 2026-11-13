# -*- coding: utf-8 -*-
"""Patch exported WP HTML: ensure produto-1-real card exists in home cera rail; inject doc links in plan pages."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
HOME = PM / "home.html"
COPY = json.loads((ROOT / "src" / "lib" / "product-copy.json").read_text(encoding="utf-8"))

# Minimal product card matching existing ProductGrid markup style in home.html
def inject_home() -> None:
    text = HOME.read_text(encoding="utf-8")
    if "produto-1-real" in text or 'href="/produto/produto-1-real/"' in text:
        print("home already has produto-1-real")
        return
    # Clone the first product card after "Cera em destaque" and retarget to produto-1-real.
    marker = "Cera em destaque"
    i = text.find(marker)
    if i < 0:
        raise SystemExit("Cera em destaque not found")
    k = text.find('href="/produto/', i)
    if k < 0:
        raise SystemExit("product href not found after cera destaque")
    a = text.rfind("<a ", 0, k)
    # end of this card: next sibling <a or closing of track — find matching by next href after this card's end
    # Prefer: find closing </a> of this card by scanning nested tags lightly via next <a class=
    next_a = text.find("<a ", k + 1)
    if next_a < 0:
        raise SystemExit("next card not found")
    card = text[a:next_a]
    # rewrite card
    new_card = re.sub(r'href="/produto/[^"]+"', 'href="/produto/produto-1-real/"', card, count=1)
    new_card = re.sub(
        r'alt="[^"]*"',
        'alt="Produto de teste de 1 real"',
        new_card,
        count=1,
    )
    # title h3
    new_card = re.sub(
        r"(<h3[^>]*>)(.*?)(</h3>)",
        r"\1Produto R$ 1\3",
        new_card,
        count=1,
        flags=re.S,
    )
    # price line common patterns
    new_card = re.sub(
        r"R\$\s*[0-9\.]+,[0-9]{2}",
        "R$ 1,00",
        new_card,
        count=1,
    )
    # image -> gift card 80 used by seed
    new_card = re.sub(
        r"/media/images/products/[^\"\s]+",
        "/media/images/products/cartao-presente-80.png",
        new_card,
        count=1,
    )
    text = text[:a] + new_card + text[a:]
    HOME.write_text(text, encoding="utf-8")
    print("injected 1real into home.html", "card_len", len(new_card))


def patch_plan(slug: str, html_name: str) -> None:
    path = PM / "products" / html_name
    if not path.exists():
        print("skip missing", html_name)
        return
    long = COPY[slug]["long"]
    # Escape for HTML text node - keep URLs as link tags
    def linkify(s: str) -> str:
        parts = re.split(r"(https?://\S+|/(?:images|docs)/\S+)", s)
        out = []
        for p in parts:
            if re.match(r"^(https?://|/(?:images|docs)/)", p or ""):
                # WP media path for /images/docs
                href = p
                if p.startswith("/images/"):
                    href = "/wp-content/uploads/pm-home/media" + p
                out.append(
                    f'<a class="font-semibold text-primary underline" href="{href}" target="_blank" rel="noreferrer">{p}</a>'
                )
            else:
                out.append(
                    (p or "")
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
        return "".join(out).replace("\n", "<br/>")

    html = path.read_text(encoding="utf-8")
    # Replace content inside data-pm-long paragraph if present
    m = re.search(
        r'(<p[^>]*data-pm-long[^>]*>)([\s\S]*?)(</p>)',
        html,
        re.I,
    )
    if not m:
        print("no data-pm-long", html_name)
        return
    new_inner = linkify(long)
    html = html[: m.start(2)] + new_inner + html[m.end(2) :]
    # also bump chars attr
    html = re.sub(
        r'(data-pm-chars=")(\d+)(")',
        rf'\g<1>{len(long)}\g<3>',
        html,
        count=1,
    )
    path.write_text(html, encoding="utf-8")
    print("patched", html_name)


def main() -> None:
    inject_home()
    for slug, name in [
        ("plano-silver", "plano-silver.html"),
        ("plano-silver", "plano-silver-masc.html"),
        ("plano-gold", "plano-gold.html"),
        ("plano-gold", "plano-gold-masc.html"),
        ("plano-clube-laser", "plano-clube-laser.html"),
        ("plano-prepago", "plano-prepago.html"),
        ("plano-prepago", "plano-prepago-masc.html"),
    ]:
        patch_plan(slug, name)


if __name__ == "__main__":
    main()
