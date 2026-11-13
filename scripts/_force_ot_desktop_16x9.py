# -*- coding: utf-8 -*-
"""Force-upload das 4 artes desktop 16:9 e confere dims remotas."""
from __future__ import annotations

import base64
import io
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
PUBLIC = ROOT / "public" / "images" / "hero" / "examples"

FILES = [
    "banner-exemplo-avatar-esquerda-desktop.jpg",
    "banner-exemplo-avatar-direita-desktop.jpg",
    "banner-virilha-desktop.jpg",
    "banner-bracos-desktop.jpg",
]


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
            print("local", name, im.size)
            if im.size != (1920, 720):
                raise SystemExit(f"local bad {name}")
            data = path.read_bytes()
            # unique cache-bust path segment via duplicate write + bust query later
            z.writestr(f"media/images/hero/examples/{name}", data)
            z.writestr(f"images/hero/examples/{name}", data)

    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-force-desk16",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        print("bundle", r.status, r.read()[:120])

    bust = "desk16c"
    bad = []
    for name in FILES:
        for prefix in ("media/images/hero/examples", "images/hero/examples"):
            url = f"{base}/wp-content/uploads/pm-home/{prefix}/{name}?v={bust}"
            raw = urllib.request.urlopen(
                urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "x",
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache",
                    },
                ),
                timeout=60,
            ).read()
            im = Image.open(io.BytesIO(raw))
            ok = im.size in ((1920, 720), (1600, 600))
            print(prefix, name, im.size, "ok" if ok else "BAD")
            if not ok:
                bad.append((prefix, name, im.size))
    if bad:
        raise SystemExit(f"still bad: {bad}")
    print("FORCE_DESKTOP_VIEWPORT_OK", base + "/?pm=" + bust)


if __name__ == "__main__":
    main()
