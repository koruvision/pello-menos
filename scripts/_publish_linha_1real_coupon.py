# -*- coding: utf-8 -*-
"""Publica hook no snippet pm-home e cria o cupom linha R$1."""
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
SNIPPET = ROOT / "scripts" / "pm_home_snippet.php"
CREATE = ROOT / "scripts" / "_create_linha_1real_coupon.py"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return {
        "url": e["PM_LOJA_URL"].rstrip("/"),
        "user": e["PM_LOJA_USER"],
        "password": e["PM_LOJA_APP_PASSWORD"],
    }


def call(c, method, path, payload=None):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    data = None
    headers = {
        "Authorization": "Basic " + tok,
        "User-Agent": "pm-linha-1real-pub",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(c["url"] + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(body) if body else None
            except Exception:
                return r.status, body
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            return err.code, json.loads(body)
        except Exception:
            return err.code, body[:500]


def update_snippet(c) -> None:
    code = SNIPPET.read_text(encoding="utf-8")
    if "pm_linha_1real_cart_has_coupon" not in code:
        raise SystemExit("local snippet missing linha 1real hook")
    st, rows = call(c, "GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    if st != 200 or not isinstance(rows, list):
        raise SystemExit(f"snippets list {st}")
    sn = next((r for r in rows if r.get("name") == "pm-home (front do projeto)"), None)
    if not sn:
        raise SystemExit("pm-home snippet missing")
    st, current = call(c, "GET", f"/wp-json/code-snippets/v1/snippets/{sn['id']}")
    live = current.get("code") or "" if isinstance(current, dict) else ""
    routes_line = ""
    for line in live.splitlines():
        if line.startswith("define('PM_HOME_ROUTES'") or line.startswith('define("PM_HOME_ROUTES"'):
            routes_line = line
            break
    final_code = (routes_line + "\n\n" + code) if routes_line else code
    payload = {
        "name": "pm-home (front do projeto)",
        "code": final_code,
        "scope": (current.get("scope") if isinstance(current, dict) else None) or "global",
        "active": True,
    }
    st, saved = call(c, "PUT", f"/wp-json/code-snippets/v1/snippets/{sn['id']}", payload)
    ok = isinstance(saved, dict) and "pm_linha_1real_cart_has_coupon" in (saved.get("code") or "")
    print("snippet", st, "linha_hook", ok)
    if st not in (200, 201) or not ok:
        raise SystemExit(1)


def main() -> None:
    c = cfg()
    assert "loja.pellomenos.com.br" in c["url"]
    update_snippet(c)
    rc = subprocess.call([sys.executable, str(CREATE)], cwd=str(ROOT / "scripts"))
    if rc != 0:
        raise SystemExit(rc)
    print("LINHA_1REAL_READY")


if __name__ == "__main__":
    main()
