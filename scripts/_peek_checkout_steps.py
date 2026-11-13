# -*- coding: utf-8 -*-
import re
import urllib.request

html = urllib.request.urlopen(
    "https://pellomenosoficialteste.companygenesis.com.br/finalizar-pagamento/?pm=steps",
    timeout=60,
).read().decode("utf-8", "replace")
# Find the actual checkout nav (inside wpcf7)
idx = html.find('id="pills-tab"')
if idx < 0:
    idx = html.find("pills-dados-tab")
print("idx", idx)
print(html[max(0, idx - 200) : idx + 900])
print("--- panes ids ---")
print(re.findall(r'id="(pills-[^"]+)"', html))
print("aria-controls", re.findall(r'aria-controls="(pills-[^"]+)"', html))
