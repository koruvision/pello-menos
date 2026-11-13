# -*- coding: utf-8 -*-
"""Cache audit v2: 2 GETs por URL, Age / LiteSpeed / Cache-Control."""
from __future__ import annotations

import json
import ssl
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "scripts" / "_audit_loja_cache_headers_v2.json"
BASE = "https://loja.pellomenos.com.br"

PATHS = [
    "/",
    "/masculino/",
    "/produto/axila-cera/",
    "/carrinho/",
    "/minha-conta/",
    "/wp-content/uploads/pm-home/home.css",
    "/wp-content/uploads/pm-home/home.js",
]

INTEREST = (
    "Cache-Control",
    "Vary",
    "Age",
    "X-LiteSpeed-Cache",
    "X-LS-Cache",
    "X-Cache",
    "CF-Cache-Status",
    "Server",
    "X-HC-Cache",
)


def probe(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "pm-cache-v2/1.0", "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=60, context=ssl.create_default_context()) as r:
        headers = {k: v for k, v in r.headers.items()}
        r.read(32)
        picked = {k: headers.get(k) for k in INTEREST if headers.get(k)}
        for k, v in headers.items():
            lk = k.lower()
            if ("cache" in lk or lk == "age" or lk == "server") and k not in picked:
                picked[k] = v
        return {"status": r.status, "headers": picked}


def main():
    rows = []
    for path in PATHS:
        url = BASE.rstrip("/") + path
        try:
            first = probe(url)
            time.sleep(0.35)
            second = probe(url)
            row = {"path": path, "pass1": first, "pass2": second}
        except Exception as err:
            row = {"path": path, "error": f"{type(err).__name__}:{err}"}
        rows.append(row)
        h1 = (row.get("pass1") or {}).get("headers") or {}
        h2 = (row.get("pass2") or {}).get("headers") or {}
        print(
            path,
            "cc1",
            h1.get("Cache-Control"),
            "age1",
            h1.get("Age"),
            "age2",
            h2.get("Age"),
            "ls",
            h2.get("X-LiteSpeed-Cache") or h2.get("X-LS-Cache"),
        )
    OUT.write_text(json.dumps({"base": BASE, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
