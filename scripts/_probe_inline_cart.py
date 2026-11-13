# -*- coding: utf-8 -*-
import re
import urllib.request

html = urllib.request.urlopen(
    "https://pellomenosoficialteste.companygenesis.com.br/finalizar-pagamento/?pm=inline",
    timeout=60,
).read().decode("utf-8", "replace")

print("cart_ids count", html.count("cart_ids"))
for m in re.finditer(r"cart_ids[\s\S]{0,4000}", html):
    print("---HIT---")
    print(m.group(0)[:4000])
    print("---END---")

# also search for how values are written to inputs
for pat in [
    r"input\[name=[\"']cart[\"']\][\s\S]{0,120}",
    r"name=[\"']cartqtd[\"'][\s\S]{0,120}",
    r"cart_ids\.push\([^)]+\)",
    r"cart_qtd\.push\([^)]+\)",
    r"cart_ids\.join\([^)]+\)",
    r"cart_qtd\.join\([^)]+\)",
]:
    found = re.findall(pat, html)
    if found:
        print("PAT", pat, "=>", found[:8])
