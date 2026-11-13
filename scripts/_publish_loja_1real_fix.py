# -*- coding: utf-8 -*-
"""Publica bridge/HTML/cart-related do produto R$1,99 na loja (ID 49394)."""
from __future__ import annotations

import base64
import io
import json
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
FILES = [
    "woo-bridge.json",
    "cart-related.json",
    "products/produto-1-real.html",
]


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


def main():
    c = cfg()
    assert "loja.pellomenos.com.br" in c["url"]
    dest_base = c["url"] + "/wp-content/uploads/pm-home"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            path = PM / rel
            text = path.read_text(encoding="utf-8")
            if "49394" not in text and "produto-1-real" in rel.replace("\\", "/"):
                raise SystemExit(f"missing 49394 in {rel}")
            # rewrite clone base if present
            text = text.replace(
                "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home",
                dest_base,
            )
            z.writestr(rel, text.encode("utf-8"))
            print("zip+", rel, path.stat().st_size)
    blob = buf.getvalue()
    token = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + "/wp-json/pm-home/v1/bundle",
        data=blob,
        method="POST",
        headers={
            "Authorization": "Basic " + token,
            "Content-Type": "application/zip",
            "Accept": "application/json",
            "User-Agent": "pm-1real-fix/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            body = r.read().decode("utf-8", "replace")
            print("bundle", r.status, body[:500])
    except urllib.error.HTTPError as err:
        print("bundle FAIL", err.code, err.read().decode("utf-8", "replace")[:500])
        raise SystemExit(1)

    # verify live
    html = urllib.request.urlopen(
        dest_base + "/products/produto-1-real.html?v=fix1", timeout=60
    ).read().decode("utf-8", "replace")
    bridge = json.loads(
        urllib.request.urlopen(dest_base + "/woo-bridge.json?v=fix1", timeout=60).read().decode()
    )
    print("live html has 49394", "49394" in html, "has 48409", "48409" in html)
    print("live bridge productId", bridge.get("produto-1-real", {}).get("productId"))
    print("LOJA_1REAL_FIX_OK")


if __name__ == "__main__":
    main()
