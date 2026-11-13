# -*- coding: utf-8 -*-
"""Publica um ou mais arquivos de wordpress-loja/pm-home em producao (loja)."""
from __future__ import annotations

import base64
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"


def env() -> dict:
    e = {}
    for line in (ROOT / "projeto-migracao" / ".secrets" / "loja.env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    for line in (ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    target = "ot" if "--target" in sys.argv and sys.argv[sys.argv.index("--target") + 1] == "ot" else "loja"
    files = [a for a in args if a != "ot"] or ["home.html"]
    e = env()
    if target == "ot":
        base = e["PM_OFICIALTESTE_URL"].rstrip("/")
        user, pwd = e["PM_OFICIALTESTE_USER"], e["PM_OFICIALTESTE_APP_PASSWORD"]
        if "loja.pellomenos.com.br" in base:
            raise SystemExit("ABORTADO: destino de teste aponta para producao")
    else:
        base = e["PM_LOJA_URL"].rstrip("/")
        user, pwd = e["PM_LOJA_USER"], e["PM_LOJA_APP_PASSWORD"]
    tok = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    auth = {"Authorization": "Basic " + tok, "User-Agent": "pm-home-deploy"}
    print(f"destino: {base} | {len(files)} arquivo(s): {files}")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            z.writestr(rel, (PM / rel).read_bytes())
    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(), method="POST",
        headers={**auth, "Content-Type": "application/zip", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        print(f"upload {len(files)} arquivo(s) {len(buf.getvalue())//1024} KB -> {r.status} {r.read()[:200]}")

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
