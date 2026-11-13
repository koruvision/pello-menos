# -*- coding: utf-8 -*-
"""Publica assets Esquenta + snippet FORCE no OficialTeste."""
from __future__ import annotations

import base64
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
SNIPPET = ROOT / "scripts" / "pm_black_nov_snippet.php"
PUB = ROOT / "scripts" / "pm_publicar_destino.py"
HOME_SNIP = ROOT / "scripts" / "pm_home_snippet.php"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": e["PM_OFICIALTESTE_URL"].rstrip("/"),
        "user": e["PM_OFICIALTESTE_USER"],
        "password": e["PM_OFICIALTESTE_APP_PASSWORD"],
    }


def call(c, method, path, payload=None, raw=None, content_type="application/json", timeout=300):
    data = raw if raw is not None else (None if payload is None else json.dumps(payload).encode("utf-8"))
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + tok,
            "User-Agent": "pm-esquenta-pub/1.0",
            "Content-Type": content_type,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body[:1] in "[{" else body)


def put_black_nov(c, force: str):
    code = SNIPPET.read_text(encoding="utf-8").replace(
        "define('PM_BLACK_NOV_FORCE', '');",
        f"define('PM_BLACK_NOV_FORCE', '{force}');",
        1,
    )
    st, rows = call(c, "GET", "/wp-json/code-snippets/v1/snippets")
    sn_id = None
    if isinstance(rows, list):
        for row in rows:
            if (row.get("name") or "") == "pm-black-nov-pricing":
                sn_id = row.get("id")
                break
    payload = {"name": "pm-black-nov-pricing", "code": code, "scope": "global", "active": True}
    if sn_id:
        st, saved = call(c, "PUT", f"/wp-json/code-snippets/v1/snippets/{sn_id}", payload)
    else:
        st, saved = call(c, "POST", "/wp-json/code-snippets/v1/snippets", payload)
    print("black-nov", st, saved.get("id") if isinstance(saved, dict) else saved, "FORCE", force)


def put_pm_home_snippet(c):
    # Reaplica rotas com shell c36 via pm_publicar_destino
    subprocess.check_call(
        [
            sys.executable,
            str(PUB),
            "--env",
            str(ENV),
            "snippet",
            "--routes",
            "home,masculino,produto,carrinho,conta,shell,loja",
        ],
        cwd=str(ROOT),
    )


def main():
    force = "esquenta"
    if len(sys.argv) > 1:
        force = sys.argv[1]
    c = cfg()
    print("destino", c["url"], "force", force)
    subprocess.check_call(
        [sys.executable, str(PUB), "--env", str(ENV), "bundle"],
        cwd=str(ROOT),
    )
    put_pm_home_snippet(c)
    put_black_nov(c, force)
    # probes
    for path in (
        "/wp-content/uploads/pm-home/black-nov-campaign.json",
        "/wp-content/uploads/pm-home/checkout-shell-c24.js?v=c36",
        "/wp-content/uploads/pm-home/cart-related.json",
        "/wp-content/uploads/pm-home/woo-bridge.json",
    ):
        st, body = call(c, "GET", path)
        text = body if isinstance(body, str) else json.dumps(body)
        print(path, st, "11-23" in text or "c36" in path or "pm-teste" in text, len(text) if isinstance(text, str) else "")


if __name__ == "__main__":
    main()
