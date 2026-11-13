# -*- coding: utf-8 -*-
"""Publica HTMLs pm-home com SAC → WhatsApp e confere home ao vivo."""
from __future__ import annotations

import base64
import io
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip().lstrip("\ufeff")] = v.strip()
    return values


def main():
    vals = env()
    base = vals["PM_LOJA_URL"].rstrip("/")
    dest = base + "/wp-content/uploads/pm-home"
    token = base64.b64encode(
        f"{vals['PM_LOJA_USER']}:{vals['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()

    # sanity local
    sample = (PM / "home.html").read_text(encoding="utf-8")
    if "tel:08002821233" in sample:
        raise SystemExit("home.html still has tel:0800")
    if "SAC WhatsApp (21) 2549-4265" not in sample:
        raise SystemExit("home.html missing SAC WhatsApp label")
    if "wa.me/552125494265" not in sample:
        raise SystemExit("home.html missing wa.me")

    buf = io.BytesIO()
    n = 0
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(PM.rglob("*.html")):
            rel = path.relative_to(PM).as_posix()
            text = path.read_text(encoding="utf-8").replace(CLONE, dest)
            z.writestr(rel, text.encode("utf-8"))
            n += 1
    print("zip files", n, "bytes", buf.tell())

    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + token,
            "Content-Type": "application/zip",
            "User-Agent": "pm-sac-whatsapp/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=1800) as resp:
        print("bundle", resp.status, resp.read()[:400])

    live = urllib.request.urlopen(
        urllib.request.Request(
            base + "/?v=sacwa1",
            headers={"User-Agent": "pm-sac-whatsapp", "Cache-Control": "no-cache"},
        ),
        timeout=60,
    ).read().decode("utf-8", "replace")

    has_wa = "wa.me/552125494265" in live and "SAC WhatsApp" in live
    has_tel = "tel:08002821233" in live or "SAC 0800 282 1233" in live
    print("live SAC WhatsApp", has_wa)
    print("live old tel SAC", has_tel)
    if has_tel:
        raise SystemExit("live still shows tel SAC")
    if not has_wa:
        # homepage may inject footer from file; dump a hint
        m = re.search(r"SAC.{0,40}", live)
        print("hint", m.group(0) if m else "no SAC")
        raise SystemExit("live missing SAC WhatsApp")
    print("SAC_WHATSAPP_OK")


if __name__ == "__main__":
    main()
