# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for name in ("loja.env", "oficialteste.env"):
    p = ROOT / "projeto-migracao" / ".secrets" / name
    keys = []
    has_psi = False
    has_url = False
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k = line.split("=", 1)[0].strip()
        keys.append(k)
        if k == "PM_PAGESPEED_API_KEY":
            has_psi = True
        if k.endswith("_URL"):
            has_url = True
    print(name, "keys", len(keys), "psi", has_psi, "url_keys", [k for k in keys if k.endswith("_URL")])
