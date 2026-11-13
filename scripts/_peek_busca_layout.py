# -*- coding: utf-8 -*-
import re
import urllib.request

base = "https://pellomenosoficialteste.companygenesis.com.br"
h = urllib.request.urlopen(
    urllib.request.Request(
        base + "/busca/?pm=side1",
        headers={"User-Agent": "x", "Cache-Control": "no-cache"},
    ),
    timeout=60,
).read().decode("utf-8", "replace")
i = h.find("data-pm-search-sidebar")
print("sidebar idx", i)
print(h[max(0, i - 350) : i + 180])
print("---css---")
for m in re.finditer(r"home\.css[^\"']+", h):
    print(m.group(0))
