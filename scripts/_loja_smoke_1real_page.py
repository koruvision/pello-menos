# -*- coding: utf-8 -*-
import re
import urllib.request

url = "https://loja.pellomenos.com.br/produto/produto-1-real/?v=fix1"
html = urllib.request.urlopen(url, timeout=60).read().decode("utf-8", "replace")
ids = re.findall(r'data-product-id="(\d+)"', html)
print("page", url)
print("data-product-id", ids[:5])
print("49394", "49394" in html, "48409", "48409" in html)
print("maintenance?", "manuten" in html.lower()[:2000])
