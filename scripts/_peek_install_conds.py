# -*- coding: utf-8 -*-
import json
import re
import urllib.request

html = urllib.request.urlopen(
    "https://pellomenosoficialteste.companygenesis.com.br/finalizar-pagamento/?pm=inst2",
    timeout=60,
).read().decode("utf-8", "replace")

m = re.search(r'name="_wpcf7cf_options"[^>]*value="([^"]*)"', html)
raw = (m.group(1) if m else "").replace("&quot;", '"').replace("&amp;", "&")
data = json.loads(raw)
for c in data.get("conditions") or []:
    then = c.get("then_field") or ""
    if then in ("productcera", "nosubscribe", "subscribe", "allunits", "laserunits"):
        print(json.dumps(c, ensure_ascii=False))
