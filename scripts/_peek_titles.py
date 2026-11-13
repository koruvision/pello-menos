# -*- coding: utf-8 -*-
import re
import urllib.request

html = urllib.request.urlopen(
    "https://pellomenosoficialteste.companygenesis.com.br/finalizar-pagamento/?pm=titles",
    timeout=60,
).read().decode("utf-8", "replace")
idx = html.find("Finalizar Pagamento")
print(html[max(0, idx - 120) : idx + 200])
print("---")
idx2 = html.find('id="pills-dados"')
print(html[idx2 : idx2 + 450])
print("---")
print("h2s", re.findall(r"<h2[^>]*>[^<]+", html)[:8])
print("h3s", re.findall(r"<h3[^>]*>[^<]+", html)[:8])
print("tabs", re.findall(r'id="pills-(dados|pagamento)-tab"[^>]*>([^<]+)', html))
