# -*- coding: utf-8 -*-
"""Probe Cache-Control / CDN headers na loja."""
from __future__ import annotations

import json
import ssl
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "scripts" / "_audit_loja_cache_headers.json"
BASE = "https://loja.pellomenos.com.br"

PATHS = [
    "/",
    "/masculino/",
    "/minha-conta/",
    "/carrinho/",
    "/wp-content/uploads/pm-home/home.css",
    "/wp-content/uploads/pm-home/home.js",
    "/wp-content/uploads/pm-home/account.js?v=conta-check2",
    "/wp-content/uploads/pm-home/media/brand/logo-female.png",
]

INTEREST = (
    "Cache-Control",
    "Vary",
    "Age",
    "CF-Cache-Status",
    "X-Cache",
    "X-LiteSpeed-Cache",
    "X-LS-Cache",
    "X-HC-Cache",
    "X-CDN-Cache",
    "Server",
    "CDN-Cache-Control",
    "X-Hostinger-Cache",
)


def probe(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "pm-cache-audit/1.0", "Accept": "*/*"},
        method="GET",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        headers = {k: v for k, v in r.headers.items()}
        body = r.read(64)
        picked = {k: headers.get(k) for k in INTEREST if headers.get(k)}
        # also catch any header with cache/cdn in name
        for k, v in headers.items():
            lk = k.lower()
            if ("cache" in lk or "cdn" in lk or lk == "age" or lk == "server") and k not in picked:
                picked[k] = v
        return {
            "url": url,
            "status": r.status,
            "headers": picked,
            "bytes_peek": len(body),
        }


def main():
    rows = []
    for path in PATHS:
        url = BASE.rstrip("/") + path
        try:
            row = probe(url)
        except Exception as err:
            row = {"url": url, "error": f"{type(err).__name__}:{err}"}
        rows.append(row)
        print(
            path,
            row.get("status") or "ERR",
            row.get("headers") or row.get("error"),
        )
    OUT.write_text(json.dumps({"base": BASE, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
