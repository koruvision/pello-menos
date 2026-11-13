# -*- coding: utf-8 -*-
"""Publica home com banners mobile baked na loja (desktop permanece fotos antigas)."""
from __future__ import annotations

import base64
import io
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"

MOBILE = [
    "banner-exemplo-avatar-esquerda.jpg",
    "banner-exemplo-avatar-direita.jpg",
    "banner-virilha-mobile.jpg",
    "banner-bracos-mobile.jpg",
]


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def main():
    for name in MOBILE:
        path = ROOT / "public" / "images" / "hero" / "examples" / name
        im = Image.open(path)
        print("local", name, im.size)
        if im.size != (720, 1280):
            raise SystemExit(f"bad size {name}: {im.size}")

    vals = env()
    base = vals["PM_LOJA_URL"].rstrip("/")
    dest = base + "/wp-content/uploads/pm-home"
    token = base64.b64encode(
        f"{vals['PM_LOJA_USER']}:{vals['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        text = (PM / "home.html").read_text(encoding="utf-8").replace(CLONE, dest)
        z.writestr("home.html", text.encode("utf-8"))
        for name in MOBILE:
            pub = ROOT / "public" / "images" / "hero" / "examples" / name
            media = PM / "media" / "images" / "hero" / "examples" / name
            if media.is_file():
                z.write(media, f"media/images/hero/examples/{name}")
            z.write(pub, f"images/hero/examples/{name}")
            # also under media from public if export didn't copy yet
            if not media.is_file():
                z.write(pub, f"media/images/hero/examples/{name}")
            print("zip+", name)

    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + token,
            "Content-Type": "application/zip",
            "User-Agent": "pm-mobile-baked",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        print("bundle", resp.status, resp.read()[:200])

    html = (
        urllib.request.urlopen(
            urllib.request.Request(
                base + "/?v=mobake1",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode("utf-8", "replace")
    )
    print("hero-campaign-low", "hero-campaign-low" in html)
    print("js-hero-copy", "js-hero-copy" in html)
    for name in MOBILE:
        stem = name.replace(".jpg", "")
        print("has", stem, stem in html)
        url = f"{base}/wp-content/uploads/pm-home/media/images/hero/examples/{name}?v=mobake1"
        with urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "x"}), timeout=30
        ) as r:
            im = Image.open(io.BytesIO(r.read()))
        print(" ", url, im.size)
    print("LOJA_MOBILE_BAKED_OK", base + "/?v=mobake1")


if __name__ == "__main__":
    main()
