# -*- coding: utf-8 -*-
"""Force-reupload hero example JPGs to OficialTeste and verify dims."""
from __future__ import annotations

import base64
import io
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public" / "images" / "hero" / "examples"
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"

FILES = [
    "banner-exemplo-avatar-esquerda.jpg",
    "banner-exemplo-avatar-esquerda-tablet.jpg",
    "banner-exemplo-avatar-esquerda-desktop.jpg",
    "banner-exemplo-avatar-direita.jpg",
    "banner-exemplo-avatar-direita-tablet.jpg",
    "banner-exemplo-avatar-direita-desktop.jpg",
    "banner-virilha-mobile.jpg",
    "banner-virilha-tablet.jpg",
    "banner-virilha-desktop.jpg",
    "banner-bracos-mobile.jpg",
    "banner-bracos-tablet.jpg",
    "banner-bracos-desktop.jpg",
]


def expect_for(name: str):
    if "tablet" in name:
        return (1536, 960)
    if "desktop" in name:
        return (1920, 720)
    return (750, 1000)


def dims_ok(name: str, size: tuple[int, int]) -> bool:
    want = expect_for(name)
    if size == want:
        return True
    if "desktop" in name and size == (1600, 600):
        return True
    return False


def main() -> None:
    vals = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    base = vals["PM_OFICIALTESTE_URL"].rstrip("/")
    tok = base64.b64encode(
        f"{vals['PM_OFICIALTESTE_USER']}:{vals['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            path = PUBLIC / name
            im = Image.open(path)
            want = expect_for(name)
            if im.size != want:
                raise SystemExit(f"local bad {name} {im.size}")
            data = path.read_bytes()
            z.writestr(f"images/hero/examples/{name}", data)
            z.writestr(f"media/images/hero/examples/{name}", data)
            print("zip", name, len(data), im.size)

    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-ot-hero-reup",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        print("bundle", r.status, r.read()[:120])

    bust = "hero-bp2"
    for name in FILES:
        want = expect_for(name)
        for prefix in ("media/images/hero/examples", "images/hero/examples"):
            url = f"{base}/wp-content/uploads/pm-home/{prefix}/{name}?v={bust}"
            req2 = urllib.request.Request(
                url,
                headers={"User-Agent": "x", "Cache-Control": "no-cache", "Pragma": "no-cache"},
            )
            data = urllib.request.urlopen(req2, timeout=60).read()
            im = Image.open(io.BytesIO(data))
            ok = dims_ok(name, im.size)
            print(prefix, name, im.size, len(data), "ok" if ok else f"WANT {want}")
            if not ok:
                raise SystemExit(f"still bad {prefix}/{name}")
    print("REUPLOAD_OK")


if __name__ == "__main__":
    main()
