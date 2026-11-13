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

name = "banner-exemplo-avatar-direita-desktop.jpg"
# also try alternate filename to bypass any CDN/name-based transform
alt = "banner-laser-axilas-desktop-16x9.jpg"
local = Image.open(PUBLIC / name)
print("local", local.size, (PUBLIC / name).stat().st_size)

data = (PUBLIC / name).read_bytes()
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr(f"media/images/hero/examples/{name}", data)
    z.writestr(f"images/hero/examples/{name}", data)
    z.writestr(f"media/images/hero/examples/{alt}", data)
    z.writestr(f"images/hero/examples/{alt}", data)
    print("zip entries", name, alt, len(data))

req = urllib.request.Request(
    base + "/wp-json/pm-home/v1/bundle",
    data=buf.getvalue(),
    method="POST",
    headers={
        "Authorization": "Basic " + tok,
        "Content-Type": "application/zip",
        "User-Agent": "pm-desk-test",
        "Accept": "application/json",
    },
)
with urllib.request.urlopen(req, timeout=300) as r:
    print("bundle", r.status, r.read()[:160])

for fname in (name, alt):
    for prefix in ("media/images/hero/examples", "images/hero/examples"):
        url = f"{base}/wp-content/uploads/pm-home/{prefix}/{fname}?v=desk16b"
        raw = urllib.request.urlopen(
            urllib.request.Request(
                url,
                headers={"User-Agent": "x", "Cache-Control": "no-cache", "Pragma": "no-cache"},
            ),
            timeout=60,
        ).read()
        im = Image.open(io.BytesIO(raw))
        print(prefix, fname, im.size, len(raw))
