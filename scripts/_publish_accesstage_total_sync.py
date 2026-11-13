# -*- coding: utf-8 -*-
"""Publica o snippet pm-accesstage-order-total-sync no OficialTeste."""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
SRC = ROOT / "wordpress-loja" / "pm-home" / "pm-accesstage-order-total-sync.php"
NAME = "pm-accesstage-order-total-sync"


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def call(method, path, payload=None):
    cfg = env()
    base = cfg["PM_OFICIALTESTE_URL"].rstrip("/")
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
        "User-Agent": "pm-accesstage-total-sync/1.0",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body.strip()[:1] in "{[" else body
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8", "replace")
        try:
            return err.code, json.loads(raw)
        except json.JSONDecodeError:
            return err.code, raw[:800]


def snippet_code() -> str:
    text = SRC.read_text(encoding="utf-8")
    # Code Snippets stores PHP without opening tag
    text = re.sub(r"^\s*<\?php\s*", "", text)
    return text.strip() + "\n"


def find_id():
    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    if st != 200 or not isinstance(rows, list):
        raise SystemExit(f"list snippets failed {st} {rows}")
    for row in rows:
        if row.get("name") == NAME:
            return row.get("id")
    return None


def main():
    code = snippet_code()
    payload = {
        "name": NAME,
        "code": code,
        "scope": "global",
        "active": True,
        "priority": 10,
    }
    sid = find_id()
    if sid is None:
        st, saved = call("POST", "/wp-json/code-snippets/v1/snippets", payload)
    else:
        st, saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{sid}", payload)
    print("publish", st, saved.get("id") if isinstance(saved, dict) else saved)
    if st not in (200, 201) or not isinstance(saved, dict):
        raise SystemExit(f"publish failed: {saved}")
    print(
        "ok",
        {
            "id": saved.get("id"),
            "name": saved.get("name"),
            "active": saved.get("active"),
            "bytes": len(saved.get("code") or ""),
        },
    )


if __name__ == "__main__":
    main()
