# -*- coding: utf-8 -*-
import base64
import json
import urllib.parse
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


cats = get("/wp-json/wc/v3/products/categories?per_page=100")
for c in cats:
    name = c.get("name", "")
    if any(x in name.lower() for x in ("masc", "cera", "servi")):
        print(c["id"], c["slug"], name)

print("--- terms pa_unidade (first 50) ---")
terms = get("/wp-json/wc/v3/products/attributes/4/terms?per_page=100")
print("count", len(terms))
for t in terms[:5]:
    print(t["id"], t["slug"], t["name"])

# Map bridge unit option names to term slugs via queixo variations
bridge = json.loads(Path("src/lib/woo-bridge.json").read_text(encoding="utf-8"))
units = bridge["queixo-cera-masc"]["units"]
prods = get("/wp-json/wc/v3/products?slug=queixo-cera&per_page=1")
pid = prods[0]["id"]
vars_ = get(f"/wp-json/wc/v3/products/{pid}/variations?per_page=100")
by_opt = {}
for v in vars_:
    opt = (v.get("attributes") or [{}])[0].get("option")
    by_opt[opt] = v["id"]
print("--- matching bridge options to variation attribute options ---")
for uid, meta in units.items():
    opt_name = meta["option"]
    # find variation whose attributes option matches name OR slug of name
    hit = None
    for v in vars_:
        if v["id"] == meta["variationId"]:
            hit = (v.get("attributes") or [{}])[0].get("option")
            break
    print(uid, "bridge_opt=", opt_name, "var_attr_option=", hit, "vid=", meta["variationId"])
