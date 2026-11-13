# -*- coding: utf-8 -*-
"""Exporta /busca e publica layout de filtros no OficialTeste."""
from __future__ import annotations

import base64
import io
import json
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"


def load_env():
    vals = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": vals["PM_OFICIALTESTE_URL"].rstrip("/"),
        "user": vals["PM_OFICIALTESTE_USER"],
        "password": vals["PM_OFICIALTESTE_APP_PASSWORD"],
    }


def main():
    subprocess.check_call(
        [sys.executable, str(ROOT / "scripts" / "_export_busca_only.py")],
        cwd=str(ROOT),
    )
    # keep local busca.js as source of truth
    src_js = PM / "busca.js"
    if not src_js.is_file():
        raise SystemExit("missing busca.js")

    c = load_env()
    dest = c["url"] + "/wp-content/uploads/pm-home"
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        html = (PM / "busca.html").read_text(encoding="utf-8").replace(CLONE, dest)
        # force busca3 cache bump in exported html
        html = html.replace("busca.js?v=busca2", "busca.js?v=busca3")
        html = html.replace("busca.js?v=busca1", "busca.js?v=busca3")
        html = html.replace("home.css?v=premium6", "home.css?v=premium7")
        z.writestr("busca.html", html.encode("utf-8"))
        z.write(src_js, "busca.js")
        css = PM / "home.css"
        if css.is_file():
            z.write(css, "home.css")
            print("zip+ home.css", css.stat().st_size)
        print("zip+ busca.html", len(html))
        print("zip+ busca.js", src_js.stat().st_size)

    req = urllib.request.Request(
        c["url"] + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-ot-busca-layout",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        print("bundle", r.status, r.read()[:160])

    page = (
        urllib.request.urlopen(
            urllib.request.Request(
                c["url"] + "/busca/?pm=busca-layout1",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode("utf-8", "replace")
    )
    checks = {
        "title": "Encontre o tratamento ideal" in page,
        "quick": "Filtros rápidos" in page or "data-pm-search-quick" in page,
        "drawer": "data-pm-search-drawer" in page,
        "layout": "data-pm-search-layout" in page,
        "sessions": "data-sessions=" in page,
        "units": "data-units=" in page,
        "promo": "data-promo=" in page,
        "js": "busca.js?v=busca3" in page,
        "tratamentos": "Tratamentos (" in page,
        "cssBump": "home.css?v=premium7" in page or "data-pm-search-layout" in page,
    }
    print("live", checks)
    if not all(checks.values()):
        raise SystemExit("smoke failed")
    print("OT_BUSCA_LAYOUT_OK", c["url"] + "/busca/?pm=busca-layout1")


if __name__ == "__main__":
    main()
