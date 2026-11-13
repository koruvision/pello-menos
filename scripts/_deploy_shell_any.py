# -*- coding: utf-8 -*-
"""Publica checkout-shell-c24.js em loja ou ensaio e bumpa o ?v= no snippet correspondente.

Uso: python scripts/_deploy_shell_any.py --target loja|ot --ver c58 [--dry]
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
API_CONTAINERS = ("checkout-shell-c24.js",)


def config(target: str):
    env = ROOT / "projeto-migracao" / ".secrets" / ("loja.env" if target == "loja" else "oficialteste.env")
    prefix = "PM_LOJA" if target == "loja" else "PM_OFICIALTESTE"
    e = {}
    for line in env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e[f"{prefix}_URL"].rstrip("/"), e[f"{prefix}_USER"], e[f"{prefix}_APP_PASSWORD"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=("loja", "ot"), required=True)
    ap.add_argument("--ver", required=True)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    base, user, pwd = config(args.target)
    tok = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    auth = {"Authorization": "Basic " + tok, "User-Agent": "pm-deploy"}

    src = (PM / "checkout-shell-c24.js").read_bytes()
    print(f"alvo {base} | c24 {len(src)} bytes | versao {args.ver}")
    if args.dry:
        return

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("checkout-shell-c24.js", src)
    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(), method="POST",
        headers={**auth, "Content-Type": "application/zip", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        print("upload", r.status, r.read()[:100])

    rows = json.load(urllib.request.urlopen(
        urllib.request.Request(base + "/wp-json/code-snippets/v1/snippets?per_page=100", headers=auth), timeout=90))
    target = next((s for s in rows if "checkout-shell-c24.js" in (s.get("code") or "")), None)
    if not target:
        raise SystemExit(f"ERRO: nenhum snippet referencia checkout-shell-c24.js em {base}")
    print(f"snippet #{target['id']} {target.get('name')} | ativo={target.get('active')}")

    code = target["code"]
    before = code
    code = re.sub(r"checkout-shell-c24\.js\?v=[A-Za-z0-9._-]+", f"checkout-shell-c24.js?v={args.ver}", code)
    if code == before:
        print("aviso: nenhum ?v= encontrado para trocar")
    payload = {"name": target.get("name"), "code": code,
               "scope": target.get("scope") or "global", "active": target.get("active", True)}
    put = urllib.request.Request(
        base + f"/wp-json/code-snippets/v1/snippets/{target['id']}",
        data=json.dumps(payload).encode(), method="PUT",
        headers={**auth, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(put, timeout=90) as r:
        saved = json.load(r)
    ver_ok = f"checkout-shell-c24.js?v={args.ver}" in (saved.get("code") or "")
    print("snippet salvo | ativo", saved.get("active"), "| versao aplicada:", ver_ok)

    try:
        t = urllib.request.Request(
            base + "/wp-json/wc/v3/system_status/tools/clear_transients",
            data=b"{}", method="POST", headers={**auth, "Content-Type": "application/json"})
        with urllib.request.urlopen(t, timeout=90) as r:
            print("transients", r.status)
    except Exception as exc:
        print("transients erro", exc)


if __name__ == "__main__":
    main()