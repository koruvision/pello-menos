# -*- coding: utf-8 -*-
"""Mapa OT: cupons, produtos baratos, FORCE atual."""
from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "oficialteste.env"


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def call(path):
    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    req = urllib.request.Request(
        base + path,
        headers={"Authorization": "Basic " + auth, "Accept": "application/json", "User-Agent": "pm-map"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def main():
    for code in ("PRIMEIRACOMPRA5", "primeiracompra5", "AGOSTO15"):
        rows = call("/wp-json/wc/v3/coupons?" + urllib.parse.urlencode({"code": code, "per_page": 5}))
        print("COUPON", code, [(c.get("id"), c.get("code"), c.get("amount"), c.get("discount_type"), c.get("usage_count"), c.get("usage_limit_per_user")) for c in rows])

    # cheap products
    for q in ("1,99", "1.99", "Produto R$", "pm-teste", "produto-r-1", "produto-1-real"):
        rows = call("/wp-json/wc/v3/products?" + urllib.parse.urlencode({"search": q, "per_page": 20}))
        for p in rows:
            price = float(p.get("price") or 0)
            if price <= 5.01 or "teste" in (p.get("slug") or "") or "1-real" in (p.get("slug") or "") or "produto-r" in (p.get("slug") or ""):
                print(
                    "PROD",
                    p.get("id"),
                    p.get("slug"),
                    p.get("status"),
                    p.get("catalog_visibility"),
                    p.get("price"),
                    p.get("name"),
                )

    sn24 = call("/wp-json/code-snippets/v1/snippets/24")
    code = sn24.get("code") or ""
    print("FORCE_ACTIVE", sn24.get("active"), "esquenta" in code[:800], "define FORCE" , "PM_BLACK_NOV_FORCE" in code)

    sn25 = call("/wp-json/code-snippets/v1/snippets/25")
    print("SYNC25", sn25.get("name"), sn25.get("active"))


if __name__ == "__main__":
    main()
