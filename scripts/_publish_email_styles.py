# -*- coding: utf-8 -*-
"""Publish pm_email_styles_snippet.php to Code Snippets (active). Default: loja."""
from __future__ import annotations

import argparse
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "scripts" / "pm_email_styles_snippet.php"
NAME = "pm-email-styles"


def env_file(prefix: str) -> Path:
    return ROOT / "projeto-migracao" / ".secrets" / (
        "loja.env" if prefix == "PM_LOJA" else "oficialteste.env"
    )


def load_env(prefix: str) -> dict:
    values = {}
    for line in env_file(prefix).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def call(prefix: str, method: str, path: str, payload=None):
    cfg = load_env(prefix)
    base = cfg[f"{prefix}_URL"].rstrip("/")
    token = base64.b64encode(
        f"{cfg[f'{prefix}_USER']}:{cfg[f'{prefix}_APP_PASSWORD']}".encode()
    ).decode()
    data = None if payload is None else json.dumps(payload).encode()
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
        "User-Agent": "pm-email-styles/2.0",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body.strip()[:1] in "{[" else body
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:800]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="PM_LOJA", choices=("PM_LOJA", "PM_OFICIALTESTE"))
    args = parser.parse_args()
    raw = SRC.read_text(encoding="utf-8")
    code = raw.lstrip()
    if code.startswith("<?php"):
        code = code[5:].lstrip("\r\n")
    st, rows = call(args.prefix, "GET", "/wp-json/code-snippets/v1/snippets")
    sid = None
    if isinstance(rows, list):
        for row in rows:
            if row.get("name") == NAME:
                sid = row.get("id")
    payload = {"name": NAME, "code": code, "scope": "global", "active": True}
    if sid is None:
        st, saved = call(args.prefix, "POST", "/wp-json/code-snippets/v1/snippets", payload)
    else:
        st, saved = call(args.prefix, "PUT", f"/wp-json/code-snippets/v1/snippets/{sid}", payload)
    print("prefix", args.prefix)
    print("snippet", st, saved.get("id") if isinstance(saved, dict) else saved)
    print("active", saved.get("active") if isinstance(saved, dict) else None)
    print("len", len(code))
    if st not in (200, 201):
        raise SystemExit(1)
    print("DONE — CSS only, texts untouched")


if __name__ == "__main__":
    main()
