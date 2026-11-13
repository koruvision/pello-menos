# -*- coding: utf-8 -*-
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
urls = [
    "https://loja.pellomenos.com.br/finalizar-pagamento/",
    "https://loja.pellomenos.com.br/finalizar-pagamento/undefined/",
    "https://loja.pellomenos.com.br/wp-content/themes/shopwise/style.css",
]
# also try common Accesstage fail paths
for extra in (
    "/pagamento-recusado/",
    "/compra-nao-realizada/",
    "/falha-pagamento/",
    "/checkout/order-pay/",
    "/finaliza-compra/undefined",
):
    urls.append("https://loja.pellomenos.com.br" + extra)

needle = re.compile(r"Compra\s+n[aã]o\s+realizada|Tente\s+novamente\s+mais\s+tarde", re.I)

for u in urls:
    try:
        req = urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r:
            t = r.read().decode("utf-8", "replace")
            print(u, r.status, "len", len(t), "hit", bool(needle.search(t)), "title", re.search(r"<title>([^<]+)", t, re.I) and re.search(r"<title>([^<]+)", t, re.I).group(1)[:60])
            if needle.search(t):
                m = needle.search(t)
                print("  ctx", t[max(0, m.start() - 80) : m.end() + 80].replace("\n", " ")[:200])
            # look for redirectFail / undefined patterns in scripts
            for pat in ["redirectFail", "redirectError", "undefined", "nao realizada", "não realizada"]:
                if pat.lower() in t.lower():
                    print("  has", pat, t.lower().count(pat.lower()))
    except Exception as e:
        print(u, type(e).__name__, e)
