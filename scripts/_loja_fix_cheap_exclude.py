# -*- coding: utf-8 -*-
"""Marca produto barato como excluído da Black Nov (prefixo produto-1-real)."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "loja.env"
FIX = Path(__file__).resolve().parents[1] / "scripts" / "_loja_cheap_fixture.json"


def main():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    pid = int(json.loads(FIX.read_text(encoding="utf-8"))["product_id"])
    base = e["PM_LOJA_URL"].rstrip("/")
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    payload = {
        "meta_data": [
            {"key": "_pm_catalog_id", "value": "produto-1-real"},
            {"key": "pm_catalog_id", "value": "produto-1-real"},
            {"key": "_pm_test_cheap", "value": "1"},
        ]
    }
    req = urllib.request.Request(
        base + f"/wp-json/wc/v3/products/{pid}",
        data=json.dumps(payload).encode(),
        method="PUT",
        headers={
            "Authorization": "Basic " + auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        body = json.loads(r.read().decode())
    print("fixed", body.get("id"), body.get("price"), [m for m in body.get("meta_data") or [] if "pm_catalog" in str(m.get("key"))])


if __name__ == "__main__":
    main()
