# -*- coding: utf-8 -*-
"""List loja snippets; restore maintenance if overwritten by pm-home."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
MAINT = ROOT / "scripts" / "pm_maintenance_snippet.php"


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


def call(c, method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + tok,
            "User-Agent": "pm-fix/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read().decode("utf-8", "replace")
        return json.loads(body) if body[:1] in "[{" else body


def main() -> None:
    c = cfg()
    rows = call(c, "GET", "/wp-json/code-snippets/v1/snippets")
    for row in rows if isinstance(rows, list) else []:
        print(
            "id",
            row.get("id"),
            "active",
            row.get("active"),
            "name",
            row.get("name"),
        )

    maint_id = None
    home_id = None
    for row in rows if isinstance(rows, list) else []:
        name = row.get("name") or ""
        if name == "pm-ecommerce-maintenance":
            maint_id = row.get("id")
        if "pm-home" in name.lower() or name.startswith("pm-home"):
            home_id = row.get("id")

    # If id 6 is now pm-home, create/restore maintenance as its own snippet
    code = MAINT.read_text(encoding="utf-8")
    payload = {
        "name": "pm-ecommerce-maintenance",
        "code": code,
        "scope": "global",
        "active": True,
    }
    if maint_id:
        # verify code still maintenance
        full = call(c, "GET", f"/wp-json/code-snippets/v1/snippets/{maint_id}")
        blob = (full.get("code") if isinstance(full, dict) else "") or ""
        if "E-commerce em Manutenção" not in blob:
            print("maintenance overwritten; restoring id", maint_id)
            saved = call(c, "PUT", f"/wp-json/code-snippets/v1/snippets/{maint_id}", payload)
        else:
            print("maintenance ok id", maint_id, "active", full.get("active"))
            if not full.get("active"):
                saved = call(c, "PUT", f"/wp-json/code-snippets/v1/snippets/{maint_id}", payload)
                print("reactivated", saved.get("id"))
            return
    else:
        print("creating maintenance anew; pm-home id", home_id)
        saved = call(c, "POST", "/wp-json/code-snippets/v1/snippets", payload)
    print(
        "saved maintenance",
        saved.get("id") if isinstance(saved, dict) else saved,
        "active",
        saved.get("active") if isinstance(saved, dict) else None,
    )


if __name__ == "__main__":
    main()
