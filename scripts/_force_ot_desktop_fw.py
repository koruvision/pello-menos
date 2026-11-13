# -*- coding: utf-8 -*-
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
    "banner-perna-desktop-fw.jpg",
    "banner-axilas-desktop-fw.jpg",
    "banner-virilha-desktop-fw.jpg",
    "banner-bracos-desktop-fw.jpg",
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
            if im.size != (1920, 840):
                raise SystemExit(f"local bad {name}")
            data = path.read_bytes()
            z.writestr(f"media/images/hero/examples/{name}", data)
            z.writestr(f"images/hero/examples/{name}", data)

    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-force-fw",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        print("bundle", r.status, r.read()[:120])

    bad = []
    for name in FILES:
        url = f"{base}/wp-content/uploads/pm-home/media/images/hero/examples/{name}?v=fw840c"
        raw = urllib.request.urlopen(
            urllib.request.Request(
                url,
                headers={"User-Agent": "x", "Cache-Control": "no-cache", "Pragma": "no-cache"},
            ),
            timeout=60,
        ).read()
        im = Image.open(io.BytesIO(raw))
        ok = im.size in ((1920, 840), (1600, 700))
        print("remote", name, im.size, "ok" if ok else "BAD")
        if not ok:
            bad.append((name, im.size))
    if bad:
        raise SystemExit(f"still bad {bad}")
    print("FORCE_FW_OK")


if __name__ == "__main__":
    main()
