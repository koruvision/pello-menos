# -*- coding: utf-8 -*-
import base64
import io
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
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        text = (PM / "home.html").read_text(encoding="utf-8").replace(CLONE, dest)
        z.writestr("home.html", text.encode("utf-8"))
        for name in (
            "banner-exemplo-avatar-esquerda.jpg",
            "banner-exemplo-avatar-direita.jpg",
            "banner-exemplo-avatar-esquerda-desktop.jpg",
            "banner-exemplo-avatar-direita-desktop.jpg",
        ):
            path = PM / "media" / "images" / "hero" / "examples" / name
            z.write(path, f"media/images/hero/examples/{name}")
            pub = ROOT / "public" / "images" / "hero" / "examples" / name
            if pub.is_file():
                z.write(pub, f"images/hero/examples/{name}")
            print("zip+", name)
    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + token,
            "Content-Type": "application/zip",
            "User-Agent": "pm-banner-examples",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        print("bundle", resp.status, resp.read()[:200])

    html = urllib.request.urlopen(
        urllib.request.Request(
            base + "/?v=bake2",
            headers={"User-Agent": "x", "Cache-Control": "no-cache"},
        ),
        timeout=60,
    ).read().decode("utf-8", "replace")
    print(
        "live",
        "mobile L",
        "banner-exemplo-avatar-esquerda.jpg" in html,
        "desktop L",
        "banner-exemplo-avatar-esquerda-desktop" in html,
        "desktop R",
        "banner-exemplo-avatar-direita-desktop" in html,
    )
    if "banner-exemplo-avatar-esquerda-desktop" not in html:
        raise SystemExit("desktop left missing")
    print("BANNER_EXAMPLES_LIVE")
    print(base + "/?v=bake3")


if __name__ == "__main__":
    main()
