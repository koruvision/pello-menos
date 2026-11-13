# -*- coding: utf-8 -*-
"""Inspect and fix broken produto-1-real card in Cera em destaque carousel."""
from __future__ import annotations

import re
from pathlib import Path

HOME = Path("wordpress-loja/pm-home/home.html")
text = HOME.read_text(encoding="utf-8")

marker = "Cera em destaque"
i = text.find(marker)
assert i > 0
# Find track after marker
track = text.find("carousel-track", i)
print("track", track)
# First article in this rail
art = text.find("<article data-carousel-card", i)
print("first article at", art)
# Extract until next article
art2 = text.find("<article data-carousel-card", art + 10)
card = text[art:art2]
print("card len", len(card))
print("open div", card.count("<div"), "close", card.count("</div>"))
print("open a", card.count("<a "), "close", card.count("</a>"))
print("open article", card.count("<article"), "close", card.count("</article>"))
# Show end of card
print("TAIL:\n", card[-500:])
print("HEAD:\n", card[:500])

# Compare with second card (abdomen)
card2 = text[art2 : text.find("<article data-carousel-card", art2 + 10)]
print("card2 len", len(card2), "div", card2.count("<div"), card2.count("</div>"))
