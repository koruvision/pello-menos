# -*- coding: utf-8 -*-
import base64
import json
import urllib.request
from pathlib import Path

e = {}
for line in Path("projeto-migracao/.secrets/oficialteste.env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        e[k.strip()] = v.strip().strip('"').strip("'")
url = e["PM_OFICIALTESTE_URL"].rstrip("/")
tok = base64.b64encode(f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()).decode()
req = urllib.request.Request(
    url + "/wp-json/wc/v3/orders/48504",
    headers={"Authorization": "Basic " + tok, "User-Agent": "pm"},
)
with urllib.request.urlopen(req, timeout=60) as r:
    o = json.loads(r.read().decode())
meta = {m["key"]: m["value"] for m in o.get("meta_data") or []}
print(json.dumps({
    "id": o["id"],
    "status": o["status"],
    "total": o["total"],
    "discount_total": o["discount_total"],
    "lines": [{"name": li["name"], "total": li["total"], "subtotal": li["subtotal"]} for li in o.get("line_items") or []],
    "accesstage": meta.get("Pedido Accesstage"),
    "customer_note": o.get("customer_note"),
}, ensure_ascii=False, indent=2))
