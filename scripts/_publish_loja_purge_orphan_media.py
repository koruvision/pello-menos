# -*- coding: utf-8 -*-
"""Publica endpoint purge-media no snippet e apaga órfãos na loja live."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
SNIPPET = ROOT / "scripts" / "pm_home_snippet.php"
REPORT = ROOT / "scripts" / "_orphan_media_report.json"


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
        "User-Agent": "pm-purge-media",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(c["url"] + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            body = r.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(body) if body else None
            except Exception:
                parsed = body
            return r.status, parsed
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body[:800]
        return err.code, parsed


def update_snippet(c) -> None:
    code = SNIPPET.read_text(encoding="utf-8")
    if "pm_home_purge_media" not in code:
        raise SystemExit("local snippet missing pm_home_purge_media")
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
    ok = isinstance(saved, dict) and "pm_home_purge_media" in (saved.get("code") or "")
    print("snippet", st, "purge_endpoint", ok)
    if st not in (200, 201) or not ok:
        raise SystemExit(1)


def purge_remote(c) -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    paths = []
    for row in report.get("orphans") or []:
        rel = row["rel"].replace("\\", "/").lstrip("/")
        if not rel.startswith("media/"):
            rel = "media/" + rel
        paths.append(rel)
    print("purge paths", len(paths))
    # chunk to stay under limit
    deleted = missing = rejected = 0
    for i in range(0, len(paths), 200):
        chunk = paths[i : i + 200]
        st, body = call(c, "POST", "/wp-json/pm-home/v1/purge-media", {"paths": chunk})
        print("chunk", i, st, body if not isinstance(body, dict) else {
            "deleted": body.get("deleted"),
            "missing": body.get("missing"),
            "rejected": body.get("rejected"),
        })
        if st != 200 or not isinstance(body, dict):
            raise SystemExit(f"purge failed {st} {body}")
        deleted += int(body.get("deleted") or 0)
        missing += int(body.get("missing") or 0)
        rejected += int(body.get("rejected") or 0)
        if body.get("rejected_paths"):
            print("rejected_paths", body.get("rejected_paths")[:10])
    print("REMOTE_PURGE", "deleted", deleted, "missing", missing, "rejected", rejected)
    if rejected:
        raise SystemExit(1)


def main() -> None:
    c = cfg()
    assert "loja.pellomenos.com.br" in c["url"]
    update_snippet(c)
    purge_remote(c)
    print("LOJA_PURGE_MEDIA_OK")


if __name__ == "__main__":
    main()
