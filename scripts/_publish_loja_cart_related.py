# -*- coding: utf-8 -*-
"""Publica cart-related.json (+ black-nov assets) na loja."""
from __future__ import annotations

import base64
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
FILES = (
    "cart-related.json",
    "black-nov-campaign.json",
    "black-nov-campaign.js",
)


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
    related = json.loads((PM / "cart-related.json").read_text(encoding="utf-8"))
    ax = (related.get("products") or {}).get("axila-cera") or {}
    laser = (related.get("products") or {}).get("axilas-laser") or {}
    assert int(ax.get("priceCents") or 0) == 2805, ax
    assert int(laser.get("priceCents") or 0) == 35996, laser
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            path = PM / name
            z.writestr(name, path.read_bytes())
            print("zip+", name, path.stat().st_size)
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-cart-related",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        print("bundle", r.status, r.read()[:200])
    # verify live
    live = urllib.request.urlopen(
        urllib.request.Request(
            c["url"] + "/wp-content/uploads/pm-home/cart-related.json?v=esq1",
            headers={"User-Agent": "pm", "Cache-Control": "no-cache"},
        ),
        timeout=60,
    ).read().decode("utf-8", "replace")
    data = json.loads(live)
    print(
        "live axila",
        data["products"]["axila-cera"]["priceCents"],
        "laser",
        data["products"]["axilas-laser"]["priceCents"],
    )
    print("CART_RELATED_ESQUENTA_OK")


if __name__ == "__main__":
    main()
