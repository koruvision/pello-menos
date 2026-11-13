# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return {
        "url": e["PM_LOJA_URL"].rstrip("/"),
        "user": e["PM_LOJA_USER"],
        "password": e["PM_LOJA_APP_PASSWORD"],
    }


def call(c, path):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        headers={
            "Authorization": "Basic " + tok,
            "Accept": "application/json",
            "User-Agent": "pm",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def main():
    c = cfg()
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    for sku in ("buco-linha", "queixo-linha", "faixa-linha"):
        info = bridge.get(sku) or {}
        print("bridge", sku, {k: info.get(k) for k in ("wooId", "productId", "id", "sku", "slug") if k in info or True})
        print("bridge keys", list(info.keys())[:20], "sample", json.dumps(info)[:300])
        q = urllib.parse.urlencode({"search": "linha", "per_page": 50, "status": "publish"})
    rows = call(c, "/wp-json/wc/v3/products?" + q)
    for p in rows:
        name = (p.get("name") or "").lower()
        sku = (p.get("sku") or "").lower()
        slug = (p.get("slug") or "").lower()
        if "linha" in name or "linha" in sku or "linha" in slug:
            print(
                "hit",
                p.get("id"),
                "sku=",
                p.get("sku"),
                "slug=",
                p.get("slug"),
                "price=",
                p.get("price"),
                "name=",
                p.get("name"),
            )


if __name__ == "__main__":
    main()
