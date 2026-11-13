# -*- coding: utf-8 -*-
import base64
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
SRC = ROOT / "scripts" / "pm_black_nov_snippet.php"
force = sys.argv[1] if len(sys.argv) > 1 else "esquenta"
if force in ("clear", "empty", "none", "''", '""'):
    force = ""

e = {}
for line in ENV.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        e[k.strip()] = v.strip().strip('"').strip("'")
url = e["PM_OFICIALTESTE_URL"].rstrip("/")
tok = base64.b64encode(f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()).decode()
code = SRC.read_text(encoding="utf-8").replace(
    "define('PM_BLACK_NOV_FORCE', '');",
    f"define('PM_BLACK_NOV_FORCE', '{force}');",
    1,
)
req = urllib.request.Request(
    url + "/wp-json/code-snippets/v1/snippets/24",
    data=json.dumps(
        {"name": "pm-black-nov-pricing", "code": code, "scope": "global", "active": True}
    ).encode(),
    method="PUT",
    headers={
        "Authorization": "Basic " + tok,
        "Content-Type": "application/json",
        "User-Agent": "pm-force",
    },
)
with urllib.request.urlopen(req, timeout=120) as r:
    print(r.status, "FORCE", force)
