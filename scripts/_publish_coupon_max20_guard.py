# -*- coding: utf-8 -*-
"""Publica guardrail code<=20 no snippet pm-home."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
SNIP = ROOT / "scripts" / "pm_home_snippet.php"


def main():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    base = e["PM_LOJA_URL"].rstrip("/")

    def call(method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(
            base + path,
            data=data,
            method=method,
            headers={
                "Authorization": "Basic " + auth,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "pm-coupon-max20",
            },
        )
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read().decode()
            return r.status, (json.loads(body) if body else {})

    code = SNIP.read_text(encoding="utf-8")
    if code.startswith("<?php"):
        code = code[5:].lstrip()
    if "woocommerce_before_coupon_object_save" not in code:
        raise SystemExit("missing guardrail")

    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    sn = next((x for x in rows if x.get("name") == "pm-home (front do projeto)"), None)
    if not sn:
        raise SystemExit("pm-home missing")
    st, cur = call("GET", f"/wp-json/code-snippets/v1/snippets/{sn['id']}")
    live = cur.get("code") or ""
    routes = ""
    for line in live.splitlines():
        if line.startswith("define('PM_HOME_ROUTES'") or line.startswith('define("PM_HOME_ROUTES"'):
            routes = line
            break
    final = (routes + "\n\n" + code) if routes else code
    st, saved = call(
        "PUT",
        f"/wp-json/code-snippets/v1/snippets/{sn['id']}",
        {
            "name": sn["name"],
            "code": final,
            "scope": cur.get("scope") or "global",
            "active": True,
        },
    )
    ok = "woocommerce_before_coupon_object_save" in (saved.get("code") or "")
    print("snippet", st, sn["id"], "guard", ok, "routes", bool(routes))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
