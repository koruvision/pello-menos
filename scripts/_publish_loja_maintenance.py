# -*- coding: utf-8 -*-
"""Ativa Code Snippets + publica pm-ecommerce-maintenance na loja."""
from __future__ import annotations

import base64
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
SRC = ROOT / "scripts" / "pm_maintenance_snippet.php"
PUB = ROOT / "scripts" / "pm_publicar_destino.py"
NAME = "pm-ecommerce-maintenance"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": e["PM_LOJA_URL"].rstrip("/"),
        "user": e["PM_LOJA_USER"],
        "password": e["PM_LOJA_APP_PASSWORD"],
    }


def call(c, method, path, payload=None, timeout=120):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + tok,
            "User-Agent": "pm-maint/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body[:1] in "[{" else body)
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")
        raise RuntimeError(f"{method} {path} -> {err.code} {detail[:400]}") from err


def main() -> None:
    c = cfg()
    print("loja", c["url"])
    subprocess.check_call(
        [
            sys.executable,
            str(PUB),
            "--env",
            str(ENV),
            "--prefix",
            "PM_LOJA",
            "--permitir-loja",
            "plugin",
        ],
        cwd=str(ROOT),
    )

    code = SRC.read_text(encoding="utf-8")
    st, rows = call(c, "GET", "/wp-json/code-snippets/v1/snippets")
    sn_id = None
    if isinstance(rows, list):
        for row in rows:
            if (row.get("name") or "") == NAME:
                sn_id = row.get("id")
                break
    payload = {
        "name": NAME,
        "code": code,
        "scope": "global",
        "active": True,
    }
    if sn_id:
        st, saved = call(c, "PUT", f"/wp-json/code-snippets/v1/snippets/{sn_id}", payload)
    else:
        st, saved = call(c, "POST", "/wp-json/code-snippets/v1/snippets", payload)
    print("maintenance", st, saved.get("id") if isinstance(saved, dict) else saved)

    # Anon probe — 503 is expected while maintenance is on
    req = urllib.request.Request(
        c["url"] + "/",
        headers={"User-Agent": "pm-maint-anon/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            status, html = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        status = err.code
        html = err.read().decode("utf-8", "replace")
    print(
        "anon /",
        status,
        "maint" if "E-commerce em Manutenção" in html else "NO_MAINT",
        "admin_link" if "/wp-admin" in html else "NO_ADMIN_LINK",
    )


if __name__ == "__main__":
    main()
