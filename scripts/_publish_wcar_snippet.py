# -*- coding: utf-8 -*-
"""Publish pm-wcar snippet (+ ensure WCAR plugin active)."""
from __future__ import annotations

import argparse
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "scripts" / "pm_wcar_snippet.php"
NAME = "pm-wcar (carrinho abandonado)"
PLUGIN = "woo-cart-abandonment-recovery/woo-cart-abandonment-recovery"


def load_env(prefix: str) -> dict:
    path = ROOT / "projeto-migracao" / ".secrets" / (
        "loja.env" if prefix == "PM_LOJA" else "oficialteste.env"
    )
    e = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": e[f"{prefix}_URL"].rstrip("/"),
        "user": e[f"{prefix}_USER"],
        "password": e[f"{prefix}_APP_PASSWORD"],
    }


def call(c, method, path, payload=None, timeout=120):
    data = None if payload is None else json.dumps(payload).encode()
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + tok,
            "User-Agent": "pm-wcar/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body[:1] in "[{" else body)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="PM_OFICIALTESTE")
    args = ap.parse_args()
    c = load_env(args.prefix)
    print("destino", c["url"], args.prefix)

    try:
        st, plug = call(c, "GET", f"/wp-json/wp/v2/plugins/{PLUGIN}")
        print("plugin", plug.get("status") if isinstance(plug, dict) else plug)
        if isinstance(plug, dict) and plug.get("status") != "active":
            st, plug = call(c, "POST", f"/wp-json/wp/v2/plugins/{PLUGIN}", {"status": "active"})
            print("plugin activate", plug.get("status") if isinstance(plug, dict) else plug)
    except Exception as ex:
        print("plugin skip", type(ex).__name__, ex)

    code = SRC.read_text(encoding="utf-8")
    st, rows = call(c, "GET", "/wp-json/code-snippets/v1/snippets")
    sn_id = None
    if isinstance(rows, list):
        for row in rows:
            if (row.get("name") or "") == NAME:
                sn_id = row.get("id")
                break
    payload = {"name": NAME, "code": code, "scope": "global", "active": True}
    if sn_id:
        st, saved = call(c, "PUT", f"/wp-json/code-snippets/v1/snippets/{sn_id}", payload)
    else:
        st, saved = call(c, "POST", "/wp-json/code-snippets/v1/snippets", payload)
    print(
        "snippet",
        st,
        saved.get("id") if isinstance(saved, dict) else saved,
        "active",
        saved.get("active") if isinstance(saved, dict) else None,
    )


if __name__ == "__main__":
    main()
