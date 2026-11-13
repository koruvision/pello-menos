# -*- coding: utf-8 -*-
"""Publica assets Black Nov + snippet PHP no OficialTeste (FORCE esquenta para smoke)."""
from __future__ import annotations

import base64
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
SNIPPET_SRC = ROOT / "scripts" / "pm_black_nov_snippet.php"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"

FILES = [
    "black-nov-campaign.json",
    "black-nov-campaign.js",
    "woo-bridge.json",
    "cart.js",
    "product.js",
    "cart-related.json",
    "carrinho.html",
]


def read_env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": e["PM_OFICIALTESTE_URL"].rstrip("/"),
        "user": e["PM_OFICIALTESTE_USER"],
        "password": e["PM_OFICIALTESTE_APP_PASSWORD"],
    }


def call(cfg, method, path, payload=None, raw=None, content_type="application/json", timeout=180):
    data = raw if raw is not None else (None if payload is None else json.dumps(payload).encode("utf-8"))
    token = base64.b64encode(f"{cfg['user']}:{cfg['password']}".encode()).decode()
    req = urllib.request.Request(
        cfg["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + token,
            "User-Agent": "pm-black-nov/1.0",
            "Content-Type": content_type,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body[:1] in "[{" else body)


def main() -> None:
    cfg = read_env()
    dest = cfg["url"] + "/wp-content/uploads/pm-home"
    print("destino", cfg["url"])
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            text = (PM / name).read_text(encoding="utf-8")
            text = text.replace(CLONE, dest).replace(
                "https://loja.pellomenos.com.br/wp-content/uploads/pm-home", dest
            )
            z.writestr(name, text.encode("utf-8"))
    st, res = call(cfg, "POST", "/wp-json/pm-home/v1/bundle", raw=buf.getvalue(), content_type="application/zip", timeout=300)
    print("bundle", st, res)

    code = SNIPPET_SRC.read_text(encoding="utf-8")
    # Smoke: força Esquenta até a virada real (03/11).
    code = code.replace(
        "define('PM_BLACK_NOV_FORCE', '');",
        "define('PM_BLACK_NOV_FORCE', 'esquenta');",
        1,
    )
    st, rows = call(cfg, "GET", "/wp-json/code-snippets/v1/snippets")
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
        st, saved = call(cfg, "PUT", f"/wp-json/code-snippets/v1/snippets/{sn_id}", payload)
    else:
        st, saved = call(cfg, "POST", "/wp-json/code-snippets/v1/snippets", payload)
    print("snippet", st, saved.get("id") if isinstance(saved, dict) else saved, "active", saved.get("active") if isinstance(saved, dict) else None)

    for probe in (
        "/wp-content/uploads/pm-home/black-nov-campaign.json",
        "/wp-content/uploads/pm-home/black-nov-campaign.js?v=black1",
        "/wp-content/uploads/pm-home/cart.js?v=cart25",
    ):
        st, body = call(cfg, "GET", probe)
        print(probe, st, len(body) if isinstance(body, str) else body)


if __name__ == "__main__":
    main()
