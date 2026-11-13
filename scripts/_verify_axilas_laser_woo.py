# -*- coding: utf-8 -*-
"""Verifica estado final dos preços do axilas-laser no WooCommerce."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return {
        "url": e["PM_LOJA_URL"].rstrip("/"),
        "user": e["PM_LOJA_USER"],
        "password": e["PM_LOJA_APP_PASSWORD"],
    }


def call(c, method, path, payload=None):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        c["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-verify",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body[:1] in "[{" else body)


def main():
    c = cfg()
    product_id = 8650

    status, variations = call(c, "GET", f"/wp-json/wc/v3/products/{product_id}/variations?per_page=100")
    print(f"Status: {status}, Total: {len(variations) if isinstance(variations, list) else 'erro'}")

    all_ok = True
    for v in variations:
        sale = v.get("sale_price", "")
        reg = v.get("regular_price", "")
        status_str = "OK" if (sale == "359.96" and reg == "899.90") else "MISMATCH"
        if status_str != "OK":
            all_ok = False
        print(f"  #{v['id']:>6} | sale={sale} | regular={reg} | {status_str}")

    print(f"\nRESULTADO: {'TODAS CORRETAS' if all_ok else 'AINDA HÁ ERROS'}")


if __name__ == "__main__":
    main()