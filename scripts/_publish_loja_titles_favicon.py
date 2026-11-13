# -*- coding: utf-8 -*-
import base64
import io
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
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
        values[k.strip()] = v.strip()
    return values


def main():
    vals = env()
    base = vals["PM_LOJA_URL"].rstrip("/")
    dest = base + "/wp-content/uploads/pm-home"
    token = base64.b64encode(
        f"{vals['PM_LOJA_USER']}:{vals['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()
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
            "User-Agent": "pm-titles-favicon",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=1800) as resp:
        print("bundle", resp.status, resp.read()[:300])

    html = urllib.request.urlopen(
        urllib.request.Request(
            base + "/?v=titlefix1",
            headers={"User-Agent": "x", "Cache-Control": "no-cache"},
        ),
        timeout=60,
    ).read().decode("utf-8", "replace")
    title = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
    t = title.group(1) if title else ""
    print("live title codepoints", [hex(ord(c)) for c in t])
    print("live favicon", "cropped-favicon-50x50.png" in html)
    if "Ã§" in t or "Ã£" in t:
        raise SystemExit("mojibake still present")
    if "Depilação" not in t and "Depila" not in t:
        # allow if encoding display differs; check codepoints
        if not (0xe7 in map(ord, t) and 0xe3 in map(ord, t)):
            raise SystemExit(f"unexpected title {t!r}")
    if "cropped-favicon-50x50.png" not in html:
        raise SystemExit("favicon missing")
    print("TITLES_FAVICON_OK")


if __name__ == "__main__":
    main()
