# -*- coding: utf-8 -*-
import re
import urllib.request

base = "https://pellomenosoficialteste.companygenesis.com.br"
html = urllib.request.urlopen(base + "/carrinho/?t=3", timeout=60).read().decode(
    "utf-8", "replace"
)
j = html.find("data-pm-cart-page")
print(html[max(0, j - 120) : j + 400])
print("---")
js = urllib.request.urlopen(
    base + "/wp-content/uploads/pm-home/cart.js?v=cart13probe", timeout=60
).read().decode("utf-8", "replace")
m = re.search(r'var SHELL =\s*"([^"]+)"', js)
print("SHELL:", m.group(1) if m else None)
m2 = re.search(r'data-audience="[^"]+" class="([^"]+)"', html)
print("shell:", m2.group(1) if m2 else None)
print("flex flex-1 flex-col", 'class="flex flex-1 flex-col"' in html)
