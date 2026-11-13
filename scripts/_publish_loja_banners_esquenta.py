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
    files = ["home.html", "masculino.html"]
    media = list((PM / "media" / "images" / "hero").rglob("*-m.jpg"))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            text = (PM / rel).read_text(encoding="utf-8").replace(CLONE, dest)
            z.writestr(rel, text.encode("utf-8"))
            print("zip+", rel)
        for path in media:
            rel = path.relative_to(PM).as_posix()
            z.write(path, rel)
            print("zip+", rel, path.stat().st_size)
    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + token,
            "Content-Type": "application/zip",
            "User-Agent": "pm-esquenta-banners",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=1800) as resp:
        print("bundle", resp.status, resp.read()[:300])

    html = urllib.request.urlopen(
        urllib.request.Request(
            base + "/?v=esquenta1",
            headers={"User-Agent": "x", "Cache-Control": "no-cache"},
        ),
        timeout=60,
    ).read().decode("utf-8", "replace")
    print(
        "live",
        "73",
        html.count(">73<") + html.count("R$ 73"),
        "81,61",
        html.count("81,61"),
        "15%",
        "15%" in html,
        "60%",
        "60%" in html,
        "Esquenta",
        "Esquenta" in html,
        "5% OFF no e-commerce",
        "5% OFF no e-commerce" in html,
    )
    # 81,61 pode restar no Body Splash (excluído da campanha) — ok.
    if "Cera 15%" not in html and "15% OFF" not in html:
        raise SystemExit("cera 15 copy missing")
    if "Esquenta" not in html and "60%" not in html:
        raise SystemExit("esquenta/laser copy missing")
    if ">73<" not in html and "R$ 73" not in html:
        raise SystemExit("73 price missing on hero")
    print("ESQUENTA_BANNERS_OK")


if __name__ == "__main__":
    main()
