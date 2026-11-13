# -*- coding: utf-8 -*-
import base64
import json
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/oficialteste.env")
e = {}
for line in ENV.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        e[k.strip()] = v.strip()
base = e["PM_OFICIALTESTE_URL"].rstrip("/")
auth = base64.b64encode(f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()).decode()
bridge = json.loads(Path("src/lib/woo-bridge.json").read_text(encoding="utf-8"))
wid = bridge["buco-linha"]["productId"]
req = urllib.request.Request(
    f"{base}/wp-json/wc/v3/products/{wid}/variations?per_page=100",
    headers={"Authorization": "Basic " + auth, "User-Agent": "pm"},
)
with urllib.request.urlopen(req, timeout=90) as r:
    vars_ = json.loads(r.read().decode())
print("count", len(vars_))
for v in vars_:
    attrs = v.get("attributes") or []
    print(v["id"], attrs, "price", v.get("regular_price"), v.get("status"))
