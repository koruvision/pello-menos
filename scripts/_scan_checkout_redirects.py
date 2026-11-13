# -*- coding: utf-8 -*-
import re
import urllib.request

url = "https://loja.pellomenos.com.br/finalizar-pagamento/"
t = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode(
    "utf-8", "replace"
)
# extract inline scripts mentioning redirect / undefined / realizada
for i, m in enumerate(re.finditer(r"<script[^>]*>([\s\S]*?)</script>", t, re.I)):
    s = m.group(1)
    if not s.strip():
        continue
    low = s.lower()
    if any(k in low for k in ("redirect", "undefined", "realizada", "order-received", "location.href", "accesstage")):
        print("--- script", i, "len", len(s))
        # print relevant lines
        for line in s.splitlines():
            ll = line.lower()
            if any(k in ll for k in ("redirect", "undefined", "realizada", "order", "location", "fail", "erro", "cookie")):
                print(line[:220])
        print()

# also linked scripts from theme that might set fail URL
srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', t, re.I)
for src in srcs:
    if any(k in src.lower() for k in ("checkout", "payment", "access", "cf7", "custom", "child")):
        print("SRC", src)
