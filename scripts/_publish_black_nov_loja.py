# -*- coding: utf-8 -*-
"""Black Nov na loja SEM FORCE (calendário real)."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
SRC = ROOT / "scripts" / "pm_black_nov_snippet.php"
NAME = "pm-black-nov-pricing"


def main() -> None:
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    url = e["PM_LOJA_URL"].rstrip("/")
    tok = base64.b64encode(
        f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()
    code = SRC.read_text(encoding="utf-8")
    assert "define('PM_BLACK_NOV_FORCE', '');" in code

    def call(method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(
            url + path,
            data=data,
            method=method,
            headers={
                "Authorization": "Basic " + tok,
                "User-Agent": "pm-bn-loja/1.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            return json.loads(body) if body[:1] in "[{" else body

    rows = call("GET", "/wp-json/code-snippets/v1/snippets")
    sn_id = None
    for row in rows if isinstance(rows, list) else []:
        if (row.get("name") or "") == NAME:
            sn_id = row.get("id")
            break
    payload = {"name": NAME, "code": code, "scope": "global", "active": True}
    if sn_id:
        saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{sn_id}", payload)
    else:
        saved = call("POST", "/wp-json/code-snippets/v1/snippets", payload)
    print(
        "black-nov",
        saved.get("id") if isinstance(saved, dict) else saved,
        "FORCE empty",
        "define('PM_BLACK_NOV_FORCE', '');" in code,
        "active",
        saved.get("active") if isinstance(saved, dict) else None,
    )

    # Ensure campaign assets exist (already in full bundle)
    for probe in (
        "/wp-content/uploads/pm-home/black-nov-campaign.json",
        "/wp-content/uploads/pm-home/checkout-shell-c24.js",
        "/wp-content/uploads/pm-home/checkout-loading.js",
    ):
        req = urllib.request.Request(
            url + probe,
            headers={"Authorization": "Basic " + tok, "User-Agent": "pm-bn-loja/1.0"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            print(probe, r.status, len(r.read()))


if __name__ == "__main__":
    main()
