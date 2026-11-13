# -*- coding: utf-8 -*-
"""Publica cart-related.json + woo-bridge.json + checkout-shell-c24.js em producao.

O endpoint /wp-json/pm-home/v1/bundle extrai qualquer arquivo do zip para
wp-content/uploads/pm-home/, entao basta mandar os tres juntos.
"""
from __future__ import annotations

import base64
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
NEW_VER = "c57"
OLD_VERS = ("c56", "c55", "c54")
FILES = ["cart-related.json", "woo-bridge.json", "checkout-shell-c24.js"]


def env() -> dict:
    e = {}
    for line in (ROOT / "projeto-migracao" / ".secrets" / "loja.env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


def main() -> None:
    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    tok = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    auth = {"Authorization": "Basic " + tok, "User-Agent": "pm-catalog-deploy"}

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            data = (PM / name).read_bytes()
            z.writestr(name, data)
            print("zip", name, len(data), "bytes")
    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={**auth, "Content-Type": "application/zip", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        print("upload", r.status, r.read()[:120])

    # bump cache-buster no snippet que enfileira o checkout
    sreq = urllib.request.Request(base + "/wp-json/code-snippets/v1/snippets?per_page=100", headers=auth)
    with urllib.request.urlopen(sreq, timeout=90) as r:
        rows = json.load(r)
    target = next((x for x in rows if "checkout-shell-c24.js" in (x.get("code") or "")), None)
    if not target:
        print("ERRO: snippet do checkout nao encontrado")
        return
    code = target["code"]
    for v in OLD_VERS:
        code = code.replace(f"checkout-shell-c24.js?v={v}", f"checkout-shell-c24.js?v={NEW_VER}")
    payload = {"name": target.get("name"), "code": code,
               "scope": target.get("scope") or "global", "active": target.get("active", True)}
    put = urllib.request.Request(
        base + f"/wp-json/code-snippets/v1/snippets/{target['id']}",
        data=json.dumps(payload).encode(), method="PUT",
        headers={**auth, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(put, timeout=90) as r:
        saved = json.load(r)
    print("snippet", target["id"], "| v=" + NEW_VER if f"?v={NEW_VER}" in (saved.get("code") or "") else "| VERSAO NAO APLICADA")

    t = urllib.request.Request(
        base + "/wp-json/wc/v3/system_status/tools/clear_transients",
        data=b"{}", method="POST", headers={**auth, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(t, timeout=90) as r:
            print("transients", r.status)
    except Exception as exc:
        print("transients erro", exc)


if __name__ == "__main__":
    main()