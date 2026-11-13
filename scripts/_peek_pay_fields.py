# -*- coding: utf-8 -*-
import re
import urllib.request

html = urllib.request.urlopen(
    "https://pellomenosoficialteste.companygenesis.com.br/finalizar-pagamento/?pm=payfields",
    timeout=60,
).read().decode("utf-8", "replace")

names = re.findall(r'name="([^"]+)"', html)
payish = [n for n in names if any(k in n.lower() for k in ("install", "parc", "cart", "holder", "expir", "secur", "declara", "submit"))]
print("payish", sorted(set(payish)))

for key in ("installments", "allinstallments", "cerainstallments", "siteinstallment", "declaracao", "cart-number", "holder"):
    for m in re.finditer(r".{0,120}name=\"%s\".{0,200}" % re.escape(key), html):
        print("---", key, "---")
        print(m.group(0)[:320])

# parcelas labels
for m in re.finditer(r"Parcelas|parcela|installment", html, re.I):
    print("ctx", html[max(0, m.start() - 80) : m.start() + 160].replace("\n", " ")[:240])
    break

idx = html.find("Dados de Pagamento")
print("dados pag", html[idx : idx + 800] if idx >= 0 else "no")
