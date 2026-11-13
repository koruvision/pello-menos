# -*- coding: utf-8 -*-
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
    vals = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            vals[k.strip().lstrip("\ufeff")] = v.strip()
    return {
        "url": vals["PM_LOJA_URL"].rstrip("/"),
        "user": vals["PM_LOJA_USER"],
        "password": vals["PM_LOJA_APP_PASSWORD"],
    }


def main():
    c = cfg()
    dest = c["url"] + "/wp-content/uploads/pm-home"
    files = []
    cart = PM / "carrinho.html"
    if cart.is_file():
        files.append(cart)
    for p in sorted(PM.glob("products/*.html")):
        t = p.read_text(encoding="utf-8", errors="replace")
        if "product.js?v=units4" in t:
            files.append(p)
    print("html files", len(files))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            rel = p.relative_to(PM).as_posix()
            text = p.read_text(encoding="utf-8").replace(CLONE, dest)
            z.writestr(rel, text.encode("utf-8"))
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-units4-html",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        print("bundle", r.status, r.read()[:160])
    print("OK")


if __name__ == "__main__":
    main()
