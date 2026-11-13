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
base = e["PM_LOJA_URL"].rstrip("/")


def get(path):
    req = urllib.request.Request(base + path, headers={"Authorization": "Basic " + auth, "Accept": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())


s = get("/wp-json/code-snippets/v1/snippets/6")
r = get("/wp-json/code-snippets/v1/snippets/12")
p = get("/wp-json/wp/v2/plugins/wpcf7-recaptcha/wpcf7-recaptcha")
print("maint#6", s.get("active"), "recaptcha_snip#12", r.get("active"), "plugin", p.get("status"))
