# -*- coding: utf-8 -*-
"""Lista Code Snippets no OT e procura Accesstage no código."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "oficialteste.env"


def main():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    url = e["PM_OFICIALTESTE_URL"].rstrip("/")
    tok = base64.b64encode(f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()).decode()
    req = urllib.request.Request(
        url + "/wp-json/code-snippets/v1/snippets?per_page=100",
        headers={"Authorization": "Basic " + tok, "User-Agent": "pm", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        rows = json.loads(r.read().decode())
    print("snippets", len(rows))
    keys = ("accesstage", "accessstage", "cart-number", "Pedido Accesstage", "totalamount", "securityCode", "redirectSuccess")
    for row in rows:
        code = row.get("code") or ""
        name = row.get("name") or ""
        blob = (name + "\n" + code).lower()
        hits = [k for k in keys if k.lower() in blob]
        print(
            f"id={row.get('id')} active={row.get('active')} scope={row.get('scope')} "
            f"name={name!r} len={len(code)} hits={hits}"
        )
        if hits:
            for k in hits:
                i = blob.find(k.lower())
                print("  context:", code[max(0, i - 40) : i + 80].replace("\n", " "))


if __name__ == "__main__":
    main()
