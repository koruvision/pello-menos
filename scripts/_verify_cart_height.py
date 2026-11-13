# -*- coding: utf-8 -*-
import urllib.request
import re

base = "https://pellomenosoficialteste.companygenesis.com.br"
html = urllib.request.urlopen(base + "/carrinho/?nocache=1", timeout=60).read().decode(
    "utf-8", "replace"
)
print("has old minh", "100dvh-10.5rem" in html)
print("has flex flex-1 flex-col", 'class="flex flex-1 flex-col"' in html)
print("cart12", "cart.js?v=cart12" in html)
js = urllib.request.urlopen(base + "/wp-content/uploads/pm-home/cart.js?v=cart12", timeout=60).read().decode(
    "utf-8", "replace"
)
print("cart.js old minh", "100dvh-10.5rem" in js)
print("cart.js SHELL snippet:")
m = re.search(r"var SHELL =\s*\"([^\"]+)\"", js)
print(m.group(1) if m else "MISSING")

home = urllib.request.urlopen(base + "/wp-content/uploads/pm-home/home.js?v=premium4", timeout=60).read().decode(
    "utf-8", "replace"
)
print("home mediaBase uses location.origin", "location.origin" in home)
print("cliente-2 in home.js", "cliente-2.png" in home)
