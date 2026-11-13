# -*- coding: utf-8 -*-
"""PUT snippet 6 using local PHP + keep PM_HOME_ROUTES like the live copy."""
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/oficialteste.env")
PHP = Path("scripts/pm_home_snippet.php")
ROUTES = "home,masculino,produto,carrinho,conta,shell,loja"


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def call(method, path, payload=None):
    cfg = env()
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        cfg["PM_OFICIALTESTE_URL"].rstrip("/") + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode() or "{}"
            return r.status, json.loads(body) if body.strip().startswith(("{", "[")) else body
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw[:800]
        return e.code, parsed


def main():
    st, current = call("GET", "/wp-json/code-snippets/v1/snippets/6")
    print("GET", st, current.get("name") if isinstance(current, dict) else current)
    body = PHP.read_text(encoding="utf-8")
    if body.startswith("<?php"):
        body = body.split("\n", 1)[1]
    code = f"define('PM_HOME_ROUTES', '{ROUTES}');\n\n" + body
    payload = {
        "name": current.get("name") if isinstance(current, dict) else "pm-home (front do projeto)",
        "code": code,
        "scope": (current.get("scope") if isinstance(current, dict) else None) or "global",
        "active": True,
    }
    st2, saved = call("PUT", "/wp-json/code-snippets/v1/snippets/6", payload)
    print("PUT", st2)
    if isinstance(saved, dict):
        sc = saved.get("code") or ""
        print("active", saved.get("active"), "len", len(sc), "c10", "checkout-shell-c10" in sc)
    else:
        print(saved)


if __name__ == "__main__":
    main()
