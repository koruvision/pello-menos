# -*- coding: utf-8 -*-
from pathlib import Path
import re

t = Path("wordpress-loja/pm-home/home.html").read_text(encoding="utf-8")
i = t.find("Cera em destaque")
print("idx", i)
if i < 0:
    # try other encodings / titles
    for s in ["Cera em", "destaque", "ceraOfertas", "data-home-panel=\"cera\""]:
        print(s, t.find(s))
    raise SystemExit(0)
frag = t[i : i + 8000]
# count carousel cards
cards = len(re.findall(r"data-carousel-card", frag[:5000]))
print("cards near section", cards)
# produto-1-real
print("1real count in home", t.count("produto-1-real"))
# find broken tags around first card
j = t.find("produto-1-real")
print("around 1real:\n", t[max(0, j - 200) : j + 400])
# check unclosed / nested <a
section_start = t.rfind("<section", 0, i)
section_end = t.find("</section>", i)
sec = t[section_start:section_end]
print("section len", len(sec))
print("open a", sec.count("<a "), "close a", sec.count("</a>"))
print("open div", sec.count("<div"), "close div", sec.count("</div>"))
print("data-carousel-card", sec.count("data-carousel-card"))
# list product hrefs in section
hrefs = re.findall(r'href="(/produto/[^"]+)"', sec)
print("hrefs", hrefs[:20], "n=", len(hrefs))
