# -*- coding: utf-8 -*-
"""Publish masc laser price update to loja (no home.html)."""
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
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"

LASER_MASC = [
    "abdomen-laser-masc",
    "axilas-laser-masc",
    "bracos-laser-masc",
    "antebraco-laser-masc",
    "costas-laser-masc",
    "coxa-laser-masc",
    "nadegas-laser-masc",
    "meia-nadega-laser-masc",
    "meia-perna-laser-masc",
    "perna-laser-masc",
    "mamilo-laser-masc",
    "peito-laser-masc",
    "torax-abdomen-laser-masc",
    "pescoco-laser-masc",
    "intergluteos-laser-masc",
    "virilha-laser-masc",
    "virilha-total-laser-masc",
    "barba-laser-masc",
    "bigode-laser-masc",
    "nariz-laser-masc",
    "orelhas-laser-masc",
    "queixo-laser-masc",
    "rosto-inteiro-laser-masc",
    "psd-p-laser-masc",
    "psd-m-laser-masc",
    "psd-g-laser-masc",
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


def main() -> None:
    c = cfg()
    assert "loja.pellomenos.com.br" in c["url"]
    dest = c["url"] + "/wp-content/uploads/pm-home"
    files = [
        "woo-bridge.json",
        "cart-related.json",
        "routes.json",
        "masculino.html",
        "carrinho.html",
        "pages/masculino-servicos.html",
        "pages/masculino-servicos-laser.html",
        "home.css",
    ]
    for pid in LASER_MASC:
        files.append(f"products/{pid}.html")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            path = PM / rel
            if not path.is_file():
                raise SystemExit(f"missing {rel}")
            raw = path.read_bytes()
            if rel.endswith((".html", ".css", ".js", ".json")):
                text = raw.decode("utf-8").replace(CLONE, dest)
                raw = text.encode("utf-8")
            z.writestr(rel, raw)
            print("zip+", rel, path.stat().st_size)

    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "Accept": "application/json",
            "User-Agent": "pm-masc-laser-prices",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        print("bundle", r.status, r.read()[:200])

    bridge = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(
                dest + "/woo-bridge.json?v=masclaser1",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode()
    )
    ax = bridge["axilas-laser-masc"]["rj"]["regularCents"]
    vt = bridge["virilha-total-laser-masc"]["rj"]["regularCents"]
    ba = bridge["barba-laser-masc"]["rj"]["regularCents"]
    print("live bridge", ax, vt, ba)
    if (ax, vt, ba) != (98000, 217000, 107000):
        raise SystemExit("bridge prices mismatch")

    home = (
        urllib.request.urlopen(
            urllib.request.Request(
                c["url"] + "/?v=masclaser1",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode("utf-8", "replace")
    )
    print(
        "home still campaign",
        "hero-campaign" in home,
        "desktop-fw" in home,
    )
    if "hero-campaign" not in home or "desktop-fw" in home:
        raise SystemExit("home.html was corrupted")

    prod = (
        urllib.request.urlopen(
            urllib.request.Request(
                dest + "/products/axilas-laser-masc.html?v=masclaser1",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode("utf-8", "replace")
    )
    print("axilas html has 392", "392" in prod, "has 980", "980" in prod)
    print("LOJA_MASC_LASER_PRICES_OK", c["url"] + "/masculino/?v=masclaser1")


if __name__ == "__main__":
    main()
