# -*- coding: utf-8 -*-
"""Publica checkout-shell-c24.js em produção e bumpa ?v= no snippet pm-home.

O script antigo (_publish_loja_cart_js.py) enviava APENAS cart.js — por isso
nenhuma correção do checkout chegava a produção. Este envia o c24 e atualiza
a versão cache-buster no snippet 9.
"""
from __future__ import annotations

import base64
import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
NEW_VER = "c49"
OLD_VERS = ("c48", "c47", "c46")


def env() -> dict:
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


def main() -> None:
    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    tok = base64.b64encode(
        f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()
    auth = {"Authorization": "Basic " + tok, "User-Agent": "pm-ck-deploy"}

    files = ["checkout-shell-c24.js"]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in files:
            src = PM / name
            data = src.read_bytes()
            z.writestr(name, data)
            print("zip", name, len(data), "bytes")
    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={**auth, "Content-Type": "application/zip", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        print("upload", r.status, r.read()[:120])

    # Bump ?v=c46 -> ?v=c47 no snippet que enfileira o checkout.
    sreq = urllib.request.Request(
        base + "/wp-json/code-snippets/v1/snippets?per_page=100", headers=auth
    )
    with urllib.request.urlopen(sreq, timeout=60) as r:
        rows = json.load(r)
    target = None
    for row in rows:
        if "checkout-shell-c24.js" in (row.get("code") or ""):
            target = row
            break
    if not target:
        print("ERRO: snippet com checkout-shell-c24 nao encontrado")
        return
    sid = target["id"]
    code = target["code"]
    before = code
    for v in OLD_VERS:
        code = code.replace(f"checkout-shell-c24.js?v={v}", f"checkout-shell-c24.js?v={NEW_VER}")
    if code == before:
        print(f"aviso: ?v= nao mudou (ja em {NEW_VER}?)")
    payload = {
        "name": target.get("name"),
        "code": code,
        "scope": target.get("scope") or "global",
        "active": target.get("active", True),
    }
    put = urllib.request.Request(
        base + f"/wp-json/code-snippets/v1/snippets/{sid}",
        data=json.dumps(payload).encode(),
        method="PUT",
        headers={**auth, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(put, timeout=60) as r:
        saved = json.load(r)
    saved_code = saved.get("code") or ""
    ver_ok = f"checkout-shell-c24.js?v={NEW_VER}" in saved_code
    print("snippet", sid, "active", saved.get("active"), "| v=" + NEW_VER if ver_ok else "| VERSAO NAO APLICADA")

    # Limpa transients do WooCommerce.
    t = urllib.request.Request(
        base + "/wp-json/wc/v3/system_status/tools/clear_transients",
        data=b"{}",
        method="POST",
        headers={**auth, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(t, timeout=60) as r:
            print("transients", r.status)
    except Exception as exc:  # pragma: no cover
        print("transients erro", exc)


if __name__ == "__main__":
    main()