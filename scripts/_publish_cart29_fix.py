# -*- coding: utf-8 -*-
"""Publica cart.js cart29 + carrinho.html (fix SyntaxError aspas)."""
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


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def main():
    js = (PM / "cart.js").read_text(encoding="utf-8")
    if 'Não foi possível adicionar ""' in js or 'adicionar "" +' in js:
        raise SystemExit("cart.js still has broken quotes")
    if 'Não foi possível adicionar "' not in js and "Não foi possível adicionar '" not in js:
        # accept either quoting style
        if 'Adicionar "' not in js and "adicionar \\\"" not in js:
            if "Não foi possível adicionar" not in js:
                raise SystemExit("cart.js missing error string")
    html = (PM / "carrinho.html").read_text(encoding="utf-8")
    if "cart.js?v=cart29" not in html:
        raise SystemExit("carrinho.html missing cart29")

    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    tok = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("cart.js", (PM / "cart.js").read_bytes())
        z.writestr("carrinho.html", (PM / "carrinho.html").read_bytes())
    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-cart29",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        print("bundle", r.status, r.read()[:200])

    # verify live asset
    req2 = urllib.request.Request(
        base + "/wp-content/uploads/pm-home/cart.js?v=cart29",
        headers={"User-Agent": "pm", "Cache-Control": "no-cache"},
    )
    with urllib.request.urlopen(req2, timeout=60) as r:
        body = r.read().decode("utf-8", "replace")
    bad = 'adicionar "" +' in body or 'adicionar ""' in body
    good = "Não foi possível adicionar" in body and '"" +' not in body.split("Não foi possível adicionar", 1)[-1][:80]
    print("live cart29", "ok" if (not bad and "product.name" in body) else "FAIL", "len", len(body))

    req3 = urllib.request.Request(base + "/carrinho/?pm=cart29", headers={"User-Agent": "pm", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req3, timeout=60) as r:
        page = r.read().decode("utf-8", "replace")
    print("page cart29", "cart.js?v=cart29" in page)


if __name__ == "__main__":
    main()
