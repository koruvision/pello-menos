# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "loja.env"


def main():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    base = e["PM_LOJA_URL"].rstrip("/")
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    req = urllib.request.Request(
        base + "/wp-json/code-snippets/v1/snippets/9",
        headers={
            "Authorization": "Basic " + auth,
            "Accept": "application/json",
            "User-Agent": "pm-verify-demo",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())
    code = data.get("code") or ""
    print(
        "has_filter",
        "wpcf7_contact_form_properties" in code,
        "active",
        data.get("active"),
        "c43",
        "checkout-shell-c24.js?v=c43" in code,
    )


if __name__ == "__main__":
    main()
