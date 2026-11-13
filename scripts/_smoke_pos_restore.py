# -*- coding: utf-8 -*-
"""Smoke pós-restore: manutenção anónima + assets auth + OT aberto."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, prefix: str) -> dict:
    e = {}
    for line in (ROOT / "projeto-migracao" / ".secrets" / name).read_text(
        encoding="utf-8"
    ).splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": e[f"{prefix}_URL"].rstrip("/"),
        "user": e[f"{prefix}_USER"],
        "password": e[f"{prefix}_APP_PASSWORD"],
    }


def get(url: str, auth: str | None = None, timeout=60):
    headers = {"User-Agent": "pm-smoke-restore/1.0"}
    if auth:
        headers["Authorization"] = "Basic " + auth
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read() if err.fp else b""


def main() -> None:
    loja = load("loja.env", "PM_LOJA")
    ot = load("oficialteste.env", "PM_OFICIALTESTE")
    tok = base64.b64encode(f"{loja['user']}:{loja['password']}".encode()).decode()

    print("=== LOJA anon ===")
    for path in ("/", "/carrinho/", "/masculino/", "/wp-admin/"):
        st, body = get(loja["url"] + path)
        text = body.decode("utf-8", "replace")
        print(
            path,
            st,
            "MAINT" if "E-commerce em Manutenção" in text else "other",
            "wp-admin-link" if "/wp-admin" in text else "-",
            "shopwise" if "shopwise" in text.lower() else "-",
            "pm-home" if "pm-home" in text else "-",
        )

    print("=== LOJA auth assets ===")
    for path in (
        "/wp-content/uploads/pm-home/home.html",
        "/wp-content/uploads/pm-home/checkout-shell-c24.js",
        "/wp-content/uploads/pm-home/checkout-loading.js",
        "/wp-content/uploads/pm-home/black-nov-campaign.json",
        "/wp-content/uploads/pm-home/cart.js",
    ):
        st, body = get(loja["url"] + path, tok)
        text = body.decode("utf-8", "replace") if body else ""
        flags = []
        if "openCheckoutLoading" in text:
            flags.append("openCheckoutLoading")
        if "pmCheckoutLoading" in text:
            flags.append("pmCheckoutLoading")
        print(path, st, len(body), flags or "")

    # Snippet enqueue via authenticated page fetch won't bypass maintenance
    # unless cookie session — REST snippets list
    st, body = get(loja["url"] + "/wp-json/code-snippets/v1/snippets", tok)
    rows = json.loads(body.decode())
    print("=== LOJA snippets ===")
    for row in rows:
        if row.get("active"):
            print(" ", row.get("id"), row.get("name"))

    print("=== OT public ===")
    st, body = get(ot["url"] + "/")
    text = body.decode("utf-8", "replace")
    print(
        "OT /",
        st,
        len(body),
        "pm-home" if "pm-home" in text else "NO",
        "maint" if "Manutenção" in text else "open",
    )
    for path in (
        "/wp-content/uploads/pm-home/checkout-shell-c24.js",
        "/wp-content/uploads/pm-home/black-nov-campaign.json",
        "/masculino/",
    ):
        st, body = get(ot["url"] + path)
        print("OT", path, st, len(body))


if __name__ == "__main__":
    main()
