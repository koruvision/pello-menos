# -*- coding: utf-8 -*-
import re
import urllib.request

base = "https://pellomenosoficialteste.companygenesis.com.br"
js = urllib.request.urlopen(base + "/wp-content/uploads/pm-home/cart.js?v=cart13", timeout=60).read().decode(
    "utf-8", "replace"
)
m = re.search(r'var SHELL =\s*"([^"]+)"', js)
print("SHELL:", m.group(1) if m else "no")
html = urllib.request.urlopen(base + "/carrinho/?t=5", timeout=60).read().decode("utf-8", "replace")
print("cart13", "cart.js?v=cart13" in html)
print("100dvh-8rem", "100dvh-8rem" in html)
