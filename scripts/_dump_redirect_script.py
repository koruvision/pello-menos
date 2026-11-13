# -*- coding: utf-8 -*-
import re
import urllib.request

t = urllib.request.urlopen(
    urllib.request.Request("https://loja.pellomenos.com.br/finalizar-pagamento/", headers={"User-Agent": "Mozilla/5.0"}),
    timeout=60,
).read().decode("utf-8", "replace")
for i, m in enumerate(re.finditer(r"<script[^>]*>([\s\S]*?)</script>", t, re.I)):
    s = m.group(1)
    if "redirectSuccess" in s or "redirecturl" in s:
        print("=== script", i, "===")
        print(s)
        print()
