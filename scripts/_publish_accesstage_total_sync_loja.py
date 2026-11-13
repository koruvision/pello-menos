# -*- coding: utf-8 -*-
"""Tenta publicar pm-accesstage-order-total-sync na LOJA via Code Snippets REST."""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
SRC = ROOT / "wordpress-loja" / "pm-home" / "pm-accesstage-order-total-sync.php"
NAME = "pm-accesstage-order-total-sync"
OUT = ROOT / "scripts" / "_publish_accesstage_total_sync_loja_result.json"


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def call(method, path, payload=None):
    cfg = env()
    base = cfg["PM_LOJA_URL"].rstrip("/")
    token = base64.b64encode(
        f"{cfg['PM_LOJA_USER']}:{cfg['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
        "User-Agent": "pm-accesstage-loja/1.0",
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


def main():
    report = {"ok": False}
    st, me = call("GET", "/wp-json/wp/v2/users/me")
    report["me"] = {"status": st, "slug": me.get("slug") if isinstance(me, dict) else me}
    print("me", report["me"])
    if st != 200:
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit("auth fail")

    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    report["snippets_list_status"] = st
    if st != 200:
        report["error"] = "code-snippets API unavailable"
        report["snippets_body"] = rows
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("FAIL snippets API", st, rows)
        raise SystemExit("no snippets API")

    code = re.sub(r"^\s*<\?php\s*", "", SRC.read_text(encoding="utf-8")).strip() + "\n"
    sid = None
    for row in rows if isinstance(rows, list) else []:
        if row.get("name") == NAME:
            sid = row.get("id")
            break
    payload = {"name": NAME, "code": code, "scope": "global", "active": True}
    if sid is None:
        st, saved = call("POST", "/wp-json/code-snippets/v1/snippets", payload)
    else:
        st, saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{sid}", payload)
    report["publish_status"] = st
    report["saved"] = {
        "id": saved.get("id") if isinstance(saved, dict) else None,
        "active": saved.get("active") if isinstance(saved, dict) else None,
        "bytes": len(saved.get("code") or "") if isinstance(saved, dict) else 0,
        "raw": saved if not isinstance(saved, dict) else None,
    }
    report["ok"] = st in (200, 201) and isinstance(saved, dict) and saved.get("active")
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("publish", st, report["saved"])
    if not report["ok"]:
        raise SystemExit("publish failed")
    print("LOJA_SYNC_SNIPPET_OK")


if __name__ == "__main__":
    main()
