# -*- coding: utf-8 -*-
import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/loja.env")
e = {}
for line in ENV.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        e[k.strip().lstrip("\ufeff")] = v.strip()
base = e["PM_LOJA_URL"].rstrip("/")
auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()

html = urllib.request.urlopen(base + "/wp-content/uploads/pm-home/products/produto-1-real.html", timeout=60).read().decode("utf-8", "replace")
ids = re.findall(r'data-product-id="(\d+)"', html)
print("live html data-product-id", ids[:5], "has48409", "48409" in html, "has49394", "49394" in html)

bridge = urllib.request.urlopen(base + "/wp-content/uploads/pm-home/woo-bridge.json", timeout=60).read().decode()
bj = json.loads(bridge)
print("live bridge", bj.get("produto-1-real"))

for pid in (48409, 49394):
    req = urllib.request.Request(
        base + f"/wp-json/wc/v3/products/{pid}",
        headers={"Authorization": "Basic " + auth, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            p = json.loads(r.read().decode())
            print("product", pid, p.get("status"), p.get("sku"), p.get("price"), p.get("purchasable"))
    except urllib.error.HTTPError as err:
        print("product", pid, "HTTP", err.code)
