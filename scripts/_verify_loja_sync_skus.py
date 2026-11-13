# -*- coding: utf-8 -*-
import base64
import json
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "loja.env"
IDS = Path(__file__).resolve().parents[1] / "scripts" / "_loja_esquenta_test_skus.json"


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def get(path):
    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()
    req = urllib.request.Request(
        base + path,
        headers={"Authorization": "Basic " + auth, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def main():
    sn = get("/wp-json/code-snippets/v1/snippets/11")
    print(
        "snippet",
        sn.get("id"),
        sn.get("name"),
        "active=",
        sn.get("active"),
        "bytes=",
        len(sn.get("code") or ""),
        "lines_synced_meta=",
        "_pm_accesstage_lines_synced" in (sn.get("code") or ""),
    )
    for sku, pid in json.loads(IDS.read_text(encoding="utf-8")).items():
        p = get(f"/wp-json/wc/v3/products/{pid}")
        print(
            "product",
            pid,
            p.get("sku"),
            p.get("status"),
            p.get("catalog_visibility"),
            "price",
            p.get("price"),
        )


if __name__ == "__main__":
    main()
