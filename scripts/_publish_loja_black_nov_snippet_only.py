# -*- coding: utf-8 -*-
"""Publica só o snippet pm-black-nov-pricing na loja (FORCE vazio)."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
SNIPPET_SRC = ROOT / "scripts" / "pm_black_nov_snippet.php"


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
    token = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + token,
            "User-Agent": "pm-loja-black-nov/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body[:1] in "[{" else body)


def main() -> None:
    c = cfg()
    code = SNIPPET_SRC.read_text(encoding="utf-8")
    assert "define('PM_BLACK_NOV_FORCE', '');" in code
    assert "SKU Woo compartilhado" in code
    st, rows = call(c, "GET", "/wp-json/code-snippets/v1/snippets")
    sn_id = None
    if isinstance(rows, list):
        for row in rows:
            if (row.get("name") or "") == "pm-black-nov-pricing":
                sn_id = row.get("id")
                break
    payload = {
        "name": "pm-black-nov-pricing",
        "code": code,
        "scope": "global",
        "active": True,
    }
    if sn_id:
        st, saved = call(c, "PUT", f"/wp-json/code-snippets/v1/snippets/{sn_id}", payload)
    else:
        st, saved = call(c, "POST", "/wp-json/code-snippets/v1/snippets", payload)
    print(
        "black-nov",
        st,
        saved.get("id") if isinstance(saved, dict) else saved,
        "active",
        saved.get("active") if isinstance(saved, dict) else None,
    )


if __name__ == "__main__":
    main()
