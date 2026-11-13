# -*- coding: utf-8 -*-
"""Publica em producao os HTMLs de produto corrigidos (somente os alterados).

Le scripts/_patch_product_pages_report.json e envia os arquivos em lotes de 25.
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
REPORT = ROOT / "scripts" / "_patch_product_pages_report.json"
BATCH = 25


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
    auth = {"Authorization": "Basic " + tok, "User-Agent": "pm-pages-deploy"}

    plano = json.loads(REPORT.read_text(encoding="utf-8"))["plano"]
    files = [p["pagina"].replace("\\", "/") for p in plano]
    print("arquivos a publicar:", len(files))

    enviados = 0
    for i in range(0, len(files), BATCH):
        lote = files[i:i + BATCH]
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for rel in lote:
                z.writestr(rel, (PM / rel).read_bytes())
        req = urllib.request.Request(
            base + "/wp-json/pm-home/v1/bundle",
            data=buf.getvalue(), method="POST",
            headers={**auth, "Content-Type": "application/zip", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=600) as r:
            body = r.read()
        n = i // BATCH + 1
        print(f"  lote {n}: {len(lote)} arquivos | {len(buf.getvalue())//1024} KB | {r.status} {body[:50]}")
        enviados += len(lote)

    print("publicados:", enviados)

    t = urllib.request.Request(
        base + "/wp-json/wc/v3/system_status/tools/clear_transients",
        data=b"{}", method="POST", headers={**auth, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(t, timeout=90) as r:
            print("transients", r.status)
    except Exception as exc:
        print("transients erro", exc)


if __name__ == "__main__":
    main()