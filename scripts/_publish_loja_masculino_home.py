# -*- coding: utf-8 -*-
"""Publish masculino.html (+ home.css) to loja. Does not touch home.html."""
from __future__ import annotations

import base64
import io
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"


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
    files = ["masculino.html", "home.css"]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            path = PM / rel
            text = path.read_text(encoding="utf-8").replace(CLONE, dest)
            z.writestr(rel, text.encode("utf-8"))
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
            "User-Agent": "pm-masc-hero-same",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        print("bundle", r.status, r.read()[:160])

    html = (
        urllib.request.urlopen(
            urllib.request.Request(
                c["url"] + "/masculino/?v=maschero1",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode("utf-8", "replace")
    )
    checks = {
        "peitoDesktop": "hero-peito.jpg" in html,
        "peitoMobileCrop": "hero-peito-m.jpg" in html,
        "promoLaserOld": "promo-laser-v5" in html,
        "laserTitle": "Laser masculino" in html,
        "femHomeSafe": True,
    }
    fem = (
        urllib.request.urlopen(
            urllib.request.Request(
                c["url"] + "/?v=maschero1",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode("utf-8", "replace")
    )
    checks["femHomeSafe"] = "hero-campaign" in fem and "desktop-fw" not in fem
    print("live", checks)
    if not checks["peitoDesktop"] or checks["peitoMobileCrop"] or checks["promoLaserOld"]:
        raise SystemExit("masculino hero/promo not updated")
    if not checks["femHomeSafe"]:
        raise SystemExit("feminino home corrupted")
    print("LOJA_MASC_HERO_OK", c["url"] + "/masculino/?v=maschero1")


if __name__ == "__main__":
    main()
