# -*- coding: utf-8 -*-
"""Publica account.js + conta.html (spinner centrado)."""
from __future__ import annotations

import base64
import io
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"


def main():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    base = e["PM_LOJA_URL"].rstrip("/")
    tok = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("account.js", (PM / "account.js").read_bytes())
        z.writestr("conta.html", (PM / "conta.html").read_bytes())
    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-conta-spinner",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        print("bundle", r.status, r.read()[:200])

    for path, needle in (
        ("/wp-content/uploads/pm-home/account.js?v=conta-check2", b"calc(100dvh - 200px)"),
        ("/wp-content/uploads/pm-home/conta.html", b"conta-check2"),
        ("/minha-conta/?v=conta-check2", b"conta-check2"),
    ):
        req = urllib.request.Request(
            base + path,
            headers={"User-Agent": "pm", "Cache-Control": "no-cache"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            print(path.split("/")[-1][:40], r.status, needle in body, "bytes", len(body))


if __name__ == "__main__":
    main()
