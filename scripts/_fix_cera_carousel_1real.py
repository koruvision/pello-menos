# -*- coding: utf-8 -*-
"""Remove broken produto-1-real card and insert a clean clone of a valid cera card."""
from __future__ import annotations

import re
from pathlib import Path

HOME = Path("wordpress-loja/pm-home/home.html")
text = HOME.read_text(encoding="utf-8")

marker = "Cera em destaque"
i = text.find(marker)
if i < 0:
    raise SystemExit("section not found")

# First two articles after marker
art1 = text.find('<article data-carousel-card="true"', i)
art2 = text.find('<article data-carousel-card="true"', art1 + 10)
art3 = text.find('<article data-carousel-card="true"', art2 + 10)
broken = text[art1:art2]
good = text[art2:art3]

print("broken divs", broken.count("<div"), broken.count("</div"), "len", len(broken))
print("good divs", good.count("<div"), good.count("</div"), "len", len(good))

# Build new card from good template
new = good
# hrefs - replace product slug carefully (3 links typically)
new = re.sub(
    r'href="/produto/[^"]+"',
    'href="/produto/produto-1-real/"',
    new,
)
new = re.sub(
    r'alt="[^"]*"',
    'alt="Produto de teste de 1 real"',
    new,
    count=1,
)
new = re.sub(
    r"(<h3[^>]*>)([\s\S]*?)(</h3>)",
    r"\1Produto R$ 1\3",
    new,
    count=1,
)
# image path
new = re.sub(
    r"/media/images/products/[^\"\s]+",
    "/media/images/products/cartao-presente-80.jpg",
    new,
    count=1,
)
# price: first currency-like occurrence(s) — replace sale price displays
# Match R$ X,XX patterns - replace first 1-2 (installment + total or just total)
prices = list(re.finditer(r"R\$\s*[0-9\.]+,[0-9]{2}", new))
if prices:
    # Replace all price displays in card with R$ 1,00 for simplicity
    new = re.sub(r"R\$\s*[0-9\.]+,[0-9]{2}", "R$ 1,00", new)

# duration line often has ~15 min — leave or set Teste
new = re.sub(
    r"(clock[^<]*</svg>\s*)([^<]+)",
    r"\1Teste · Avulso",
    new,
    count=1,
    flags=re.I,
)

print("new divs", new.count("<div"), new.count("</div"), "balanced", new.count("<div") == new.count("</div>"))
print("1real hrefs", new.count("produto-1-real"))

# Replace broken with new
text2 = text[:art1] + new + text[art2:]
# Verify section balance improved
sec_i = text2.find(marker)
sec_start = text2.rfind("<section", 0, sec_i)
# find matching section end - approximate first </section> after cera track's parent
# Just check first carousel track's articles
art_a = text2.find('<article data-carousel-card="true"', sec_i)
art_b = text2.find('<article data-carousel-card="true"', art_a + 10)
card0 = text2[art_a:art_b]
print("after card0 divs", card0.count("<div"), card0.count("</div"))

HOME.write_text(text2, encoding="utf-8")
print("wrote", HOME)
