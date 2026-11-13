# -*- coding: utf-8 -*-
import base64
import io
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"

FILES = [
    "banner-exemplo-avatar-esquerda.jpg",
    "banner-exemplo-avatar-direita.jpg",
    "banner-exemplo-avatar-esquerda-desktop.jpg",
    "banner-exemplo-avatar-direita-desktop.jpg",
    "banner-virilha-mobile.jpg",
    "banner-virilha-desktop.jpg",
    "banner-bracos-mobile.jpg",
    "banner-bracos-desktop.jpg",
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
    # local dim check
    for name in FILES:
        path = ROOT / "public" / "images" / "hero" / "examples" / name
        im = Image.open(path)
        expect = (720, 1280) if "mobile" in name or name.endswith(("esquerda.jpg", "direita.jpg")) else (1920, 600)
        # approved mobiles don't have "mobile" in name
        if name in (
            "banner-exemplo-avatar-esquerda.jpg",
            "banner-exemplo-avatar-direita.jpg",
            "banner-virilha-mobile.jpg",
            "banner-bracos-mobile.jpg",
        ):
            expect = (720, 1280)
        else:
            expect = (1920, 600)
        print("local", name, im.size, "ok" if im.size == expect else f"WANT {expect}")
        if im.size != expect:
            raise SystemExit(f"bad size {name}")

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
        for name in FILES:
            path = PM / "media" / "images" / "hero" / "examples" / name
            z.write(path, f"media/images/hero/examples/{name}")
            pub = ROOT / "public" / "images" / "hero" / "examples" / name
            z.write(pub, f"images/hero/examples/{name}")
            print("zip+", name)
    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + token,
            "Content-Type": "application/zip",
            "User-Agent": "pm-baked-heroes",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        print("bundle", resp.status, resp.read()[:200])

    # export must run before this — caller exports first
    html = urllib.request.urlopen(
        urllib.request.Request(
            base + "/?v=baked8",
            headers={"User-Agent": "x", "Cache-Control": "no-cache"},
        ),
        timeout=60,
    ).read().decode("utf-8", "replace")
    for needle in (
        "banner-exemplo-avatar-esquerda-desktop",
        "banner-virilha-desktop",
        "banner-bracos-desktop",
        "banner-virilha-mobile",
        "banner-bracos-mobile",
    ):
        print("home has", needle, needle in html)

    print("LINKS")
    for name in FILES:
        url = f"{base}/wp-content/uploads/pm-home/media/images/hero/examples/{name}?v=baked8"
        with urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "x"}), timeout=30
        ) as resp:
            data = resp.read()
        # verify jpeg header + size via Pillow
        from io import BytesIO

        im = Image.open(BytesIO(data))
        print(url)
        print(" ", resp.status if False else 200, im.size)
    print("BAKED_HEROES_OK")
    print(base + "/?v=baked8")


if __name__ == "__main__":
    main()
