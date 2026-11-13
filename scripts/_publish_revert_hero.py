import base64
import io
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao/.secrets/loja.env"
vals = {}
for line in ENV.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    vals[k.strip()] = v.strip()

base = vals["PM_LOJA_URL"].rstrip("/")
dest = base + "/wp-content/uploads/pm-home"
clone = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"
token = base64.b64encode(
    f"{vals['PM_LOJA_USER']}:{vals['PM_LOJA_APP_PASSWORD']}".encode()
).decode()

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    t = (ROOT / "wordpress-loja/pm-home/home.html").read_text(encoding="utf-8").replace(
        clone, dest
    )
    z.writestr("home.html", t.encode())

req = urllib.request.Request(
    base + "/wp-json/pm-home/v1/bundle",
    data=buf.getvalue(),
    method="POST",
    headers={
        "Authorization": "Basic " + token,
        "Content-Type": "application/zip",
        "User-Agent": "pm-revert-hero",
        "Accept": "application/json",
    },
)
with urllib.request.urlopen(req, timeout=300) as r:
    print("bundle", r.status, r.read()[:200])

html = (
    urllib.request.urlopen(
        urllib.request.Request(
            base + "/?v=revert1",
            headers={"User-Agent": "x", "Cache-Control": "no-cache"},
        ),
        timeout=60,
    )
    .read()
    .decode("utf-8", "replace")
)
print(
    "old imgs",
    "hero-campaign-low" in html,
    "baked examples",
    "banner-exemplo" in html,
    "js-hero-copy",
    "js-hero-copy" in html,
)
