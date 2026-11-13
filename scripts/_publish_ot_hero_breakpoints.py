# -*- coding: utf-8 -*-
"""Export home + publish hero breakpoint arts to OficialTeste."""
from __future__ import annotations

import base64
import io
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
PUBLIC = ROOT / "public" / "images" / "hero" / "examples"
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"

FILES = [
    "banner-exemplo-avatar-esquerda.jpg",
    "banner-exemplo-avatar-esquerda-tablet.jpg",
    "banner-perna-desktop-fw.jpg",
    "banner-exemplo-avatar-direita.jpg",
    "banner-exemplo-avatar-direita-tablet.jpg",
    "banner-axilas-desktop-fw.jpg",
    "banner-virilha-mobile.jpg",
    "banner-virilha-tablet.jpg",
    "banner-virilha-desktop-fw.jpg",
    "banner-bracos-mobile.jpg",
    "banner-bracos-tablet.jpg",
    "banner-bracos-desktop-fw.jpg",
]

EXPECT = {
    "mobile": (750, 1000),
    "tablet": (1536, 960),
    "desktop": (1920, 840),
}


def expect_for(name: str):
    if "tablet" in name:
        return EXPECT["tablet"]
    if "desktop" in name:
        return EXPECT["desktop"]
    return EXPECT["mobile"]


def dims_ok(name: str, size: tuple[int, int]) -> bool:
    want = expect_for(name)
    if size == want:
        return True
    # Hostinger pode limitar largura ~1600 mantendo proporção
    if "desktop" in name and size in ((1600, 700), (1600, 600)):
        return True
    return False


def load_env():
    vals = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": vals["PM_OFICIALTESTE_URL"].rstrip("/"),
        "user": vals["PM_OFICIALTESTE_USER"],
        "password": vals["PM_OFICIALTESTE_APP_PASSWORD"],
    }


def main() -> None:
    for name in FILES:
        path = PUBLIC / name
        im = Image.open(path)
        want = expect_for(name)
        print("local", name, im.size)
        if not dims_ok(name, im.size) and im.size != want:
            raise SystemExit(f"bad size {name}: {im.size} want {want}")

    subprocess.check_call(
        [sys.executable, str(ROOT / "scripts" / "_export_home_and_masc.py")],
        cwd=str(ROOT),
    )

    c = load_env()
    dest = c["url"] + "/wp-content/uploads/pm-home"
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        html = (PM / "home.html").read_text(encoding="utf-8").replace(CLONE, dest)
        z.writestr("home.html", html.encode("utf-8"))
        for name in FILES:
            pub = PUBLIC / name
            media = PM / "media" / "images" / "hero" / "examples" / name
            z.write(pub, f"images/hero/examples/{name}")
            z.write(media if media.is_file() else pub, f"media/images/hero/examples/{name}")
            print("zip+", name)

    req = urllib.request.Request(
        c["url"] + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-ot-hero-bp",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        print("bundle", r.status, r.read()[:160])

    page = (
        urllib.request.urlopen(
            urllib.request.Request(
                c["url"] + "/?pm=hero-bp1",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode("utf-8", "replace")
    )
    checks = {
        "desktop": "banner-perna-desktop-fw" in page,
        "tablet": "banner-exemplo-avatar-esquerda-tablet" in page,
        "mobile": "banner-exemplo-avatar-esquerda.jpg" in page,
        "virilhaDesktop": "banner-virilha-desktop-fw" in page,
        "bracosTablet": "banner-bracos-tablet" in page,
        "viewportCap": "min(680px" in page and "100dvh" in page,
        "campaignOld": "hero-campaign-low.jpg" in page,
        "min1024": "min-width: 1024px" in page or "(min-width:1024px)" in page.replace(" ", ""),
    }
    print("live", checks)
    if checks["campaignOld"] or not all(
        checks[k]
        for k in ("desktop", "tablet", "mobile", "virilhaDesktop", "bracosTablet", "viewportCap")
    ):
        raise SystemExit("home smoke failed")

    # verify remote dims
    for name in FILES:
        url = f"{c['url']}/wp-content/uploads/pm-home/media/images/hero/examples/{name}?v=hero-bp1"
        data = urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "x"}), timeout=60
        ).read()
        im = Image.open(io.BytesIO(data))
        want = expect_for(name)
        ok = dims_ok(name, im.size)
        print("remote", name, im.size, "ok" if ok else f"WANT {want}")
        if not ok:
            raise SystemExit(f"remote bad {name}")

    print("OT_HERO_BP_OK", c["url"] + "/?pm=hero-bp1")


if __name__ == "__main__":
    main()
