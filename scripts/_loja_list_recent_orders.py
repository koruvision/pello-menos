# -*- coding: utf-8 -*-
import base64
import json
import urllib.request
from pathlib import Path

e = {}
for line in Path("projeto-migracao/.secrets/loja.env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        e[k.strip().lstrip("\ufeff")] = v.strip()
auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
req = urllib.request.Request(
    e["PM_LOJA_URL"].rstrip("/") + "/wp-json/wc/v3/orders?per_page=20&orderby=date&order=desc",
    headers={"Authorization": "Basic " + auth, "Accept": "application/json"},
)
orders = json.loads(urllib.request.urlopen(req, timeout=90).read().decode())
for o in orders:
    email = (o.get("billing") or {}).get("email") or ""
    print(o["id"], o["status"], o["total"], email[:70], o.get("date_created"))
