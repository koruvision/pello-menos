# -*- coding: utf-8 -*-
"""Publica fix Isabelle/Beatriz na loja: black-nov (pm_catalog_id), pm-home snippet, bundle."""
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
BLACK = ROOT / "scripts" / "pm_black_nov_snippet.php"
HOME = ROOT / "scripts" / "pm_home_snippet.php"
PUB = ROOT / "scripts" / "pm_publicar_destino.py"


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
        "User-Agent": "pm-catalog-cart-fix",
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


def find_snippet(c, name_substr: str):
    st, rows = call(c, "GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    if st != 200 or not isinstance(rows, list):
        raise SystemExit(f"snippets list {st}")
    for r in rows:
        name = str(r.get("name") or "")
        if name_substr.lower() in name.lower():
            return r
    return None


def update_black_nov(c) -> None:
    code = BLACK.read_text(encoding="utf-8")
    if "woocommerce_get_item_data" not in code or "pm_catalog_id" not in code:
        raise SystemExit("local black-nov missing item_data expose")
    sn = find_snippet(c, "black-nov") or find_snippet(c, "pm-black-nov") or find_snippet(c, "black nov")
    if not sn:
        # fallback known id from OT scripts
        st, probe = call(c, "GET", "/wp-json/code-snippets/v1/snippets/24")
        if st == 200 and isinstance(probe, dict):
            sn = probe
        else:
            raise SystemExit("black-nov snippet not found")
    st, current = call(c, "GET", f"/wp-json/code-snippets/v1/snippets/{sn['id']}")
    payload = {
        "name": (current.get("name") if isinstance(current, dict) else None) or sn.get("name") or "pm-black-nov-pricing",
        "code": code,
        "scope": (current.get("scope") if isinstance(current, dict) else None) or "global",
        "active": True,
    }
    st, saved = call(c, "PUT", f"/wp-json/code-snippets/v1/snippets/{sn['id']}", payload)
    ok = isinstance(saved, dict) and "woocommerce_get_item_data" in (saved.get("code") or "")
    print("black-nov", sn["id"], st, "item_data", ok)
    if st not in (200, 201) or not ok:
        raise SystemExit(1)


def update_pm_home(c) -> None:
    code = HOME.read_text(encoding="utf-8")
    if "checkout-shell-c24.js?v=c43" not in code:
        raise SystemExit("local pm-home missing c43 bump")
    sn = find_snippet(c, "pm-home (front do projeto)")
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
    ok = isinstance(saved, dict) and "checkout-shell-c24.js?v=c43" in (saved.get("code") or "")
    print("pm-home", sn["id"], st, "c43", ok)
    if st not in (200, 201) or not ok:
        raise SystemExit(1)


def main() -> None:
    c = cfg()
    assert "loja.pellomenos.com.br" in c["url"]
    update_black_nov(c)
    update_pm_home(c)
    rc = subprocess.call(
        [
            sys.executable,
            str(PUB),
            "--env",
            str(ENV),
            "--prefix",
            "PM_LOJA",
            "--permitir-loja",
            "bundle",
        ],
        cwd=str(ROOT),
    )
    if rc != 0:
        raise SystemExit(rc)
    print("CATALOG_CART_FIX_PUBLISHED")


if __name__ == "__main__":
    main()
