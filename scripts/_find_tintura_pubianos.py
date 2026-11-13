# -*- coding: utf-8 -*-
"""Busca SKU/preço tintura pelos pubianos na loja e OT."""
from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRETS = ROOT / "projeto-migracao" / ".secrets"


def cfg(env_name: str, prefix: str) -> dict:
    values = {}
    for line in (SECRETS / env_name).read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": values[f"{prefix}_URL"].rstrip("/"),
        "user": values[f"{prefix}_USER"],
        "password": values[f"{prefix}_APP_PASSWORD"],
    }


def search(c: dict, q: str):
    token = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    path = "/wp-json/wc/v3/products?" + urllib.parse.urlencode(
        {"search": q, "per_page": 30, "status": "any"}
    )
    req = urllib.request.Request(
        c["url"] + path,
        headers={"Authorization": "Basic " + token, "User-Agent": "pm-tintura", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def main() -> None:
    for env, prefix in (("loja.env", "PM_LOJA"), ("oficialteste.env", "PM_OFICIALTESTE")):
        c = cfg(env, prefix)
        print("===", c["url"])
        for q in ("tintura", "pubian", "púbico", "pubico", "pelos pub"):
            rows = search(c, q)
            print(f"  search {q!r}: {len(rows)}")
            for o in rows[:15]:
                print(
                    f"    #{o.get('id')} {o.get('status')} sku={o.get('sku')!r} "
                    f"name={o.get('name')!r} price={o.get('regular_price')!r}/{o.get('price')!r}"
                )


if __name__ == "__main__":
    main()
