# -*- coding: utf-8 -*-
import re
import urllib.request

html = urllib.request.urlopen(
    "https://pellomenosoficialteste.companygenesis.com.br/finalizar-pagamento/",
    timeout=60,
).read().decode("utf-8", "replace")
for m in re.findall(r"checkout-shell\.js[^\"']*", html):
    print("script", m)
print("shell9", "shell9" in html)
print("shell10", "shell10" in html)
