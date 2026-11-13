# -*- coding: utf-8 -*-
import re
import urllib.request

html = urllib.request.urlopen(
    urllib.request.Request(
        "https://loja.pellomenos.com.br/carrinho/?v=x",
        headers={"User-Agent": "x"},
    ),
    timeout=60,
).read().decode("utf-8", "replace")
for m in re.findall(r"[^\s\"']+(?:checkout-shell[^\"'\s]*|product\.js\?v=[^\"'\s]+)", html):
    print(m)
print("checkout-shell count", html.count("checkout-shell"))
