# -*- coding: utf-8 -*-
import base64
import json
import urllib.request
from pathlib import Path

vals = {}
for line in Path("projeto-migracao/.secrets/oficialteste.env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    vals[k.strip()] = v.strip()

url = vals["PM_OFICIALTESTE_URL"].rstrip("/")
auth = base64.b64encode(
    f"{vals['PM_OFICIALTESTE_USER']}:{vals['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
).decode()
headers = {
    "Authorization": "Basic " + auth,
    "Accept": "application/json",
    "User-Agent": "pm-create/1",
}


def get(path: str):
    req = urllib.request.Request(url + path, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


prods = get("/wp-json/wc/v3/products?slug=queixo-cera&per_page=1")
p = prods[0]
print("id", p["id"], "type", p["type"], "status", p["status"])
print(
    "attrs",
    json.dumps(
        [
            {k: a.get(k) for k in ("id", "name", "slug", "variation", "visible", "options")}
            for a in p.get("attributes", [])
        ],
        ensure_ascii=False,
    )[:1200],
)
print("variations_count", len(p.get("variations", [])))
print("categories", p.get("categories"))
vid = p["variations"][0]
v = get(f"/wp-json/wc/v3/products/{p['id']}/variations/{vid}")
print(
    "var sample",
    {k: v.get(k) for k in ("id", "sku", "regular_price", "sale_price", "stock_status", "attributes", "status")},
)

# global attribute unidade?
attrs = get("/wp-json/wc/v3/products/attributes")
print("global attrs", [{k: a.get(k) for k in ("id", "name", "slug")} for a in attrs])

# how many units does bridge expect for masc cera?
bridge = json.loads(Path("src/lib/woo-bridge.json").read_text(encoding="utf-8"))
print("queixo-cera-masc units", len(bridge.get("queixo-cera-masc", {}).get("units", {})))
print("sample unit keys", list(bridge.get("queixo-cera-masc", {}).get("units", {}).keys())[:8])
