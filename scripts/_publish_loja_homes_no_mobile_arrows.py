# -*- coding: utf-8 -*-
"""Export+publish loja home (HTML campaign) + masculino; hide mobile hero arrows.

Temporarily switches fem heroSlides to loja campaign mode for export only.
Keeps masculino (desktop art on mobile + peito promo). Restores OT fem after.
"""
from __future__ import annotations

import base64
import io
import re
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "lib" / "data.ts"
HERO = ROOT / "src" / "components" / "HeroBanner.tsx"
EXPORT = ROOT / "scripts" / "export_wp_home.py"
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"

# Reuse restore script constants
sys.path.insert(0, str(ROOT / "scripts"))
import _restore_loja_hero_normal as restore  # noqa: E402


def wait_next_loja_mode(timeout: float = 90.0) -> None:
    """Ping Next until / serves campaign heroes (not desktop-fw/tablet)."""
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        try:
            raw = urllib.request.urlopen(
                urllib.request.Request(
                    "http://127.0.0.1:3456/",
                    headers={"User-Agent": "x", "Cache-Control": "no-cache"},
                ),
                timeout=20,
            ).read().decode("utf-8", "replace")
            ok = (
                "hero-campaign-low" in raw
                and "banner-exemplo-avatar-esquerda-tablet" not in raw
                and "desktop-fw" not in raw
            )
            last = f"campaign={('hero-campaign-low' in raw)} tablet={('tablet' in raw and 'banner-exemplo-avatar-esquerda-tablet' in raw)} fw={('desktop-fw' in raw)}"
            print("next", last, flush=True)
            if ok:
                return
        except Exception as exc:
            print("next wait", exc, flush=True)
        time.sleep(2)
    raise SystemExit(f"Next did not switch to loja hero mode ({last})")


def publish() -> None:
    c = restore.load_env()
    dest = c["url"] + "/wp-content/uploads/pm-home"
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ("home.html", "masculino.html", "home.css"):
            path = PM / name
            raw = path.read_text(encoding="utf-8").replace(CLONE, dest).encode("utf-8")
            z.writestr(name, raw)
            print("zip+", name, path.stat().st_size)
    req = urllib.request.Request(
        c["url"] + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-homes-no-arrows",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        print("bundle", r.status, r.read()[:160])

    html = (
        urllib.request.urlopen(
            urllib.request.Request(
                c["url"] + "/?v=noarrows2",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode("utf-8", "replace")
    )
    masc = (
        urllib.request.urlopen(
            urllib.request.Request(
                c["url"] + "/masculino/?v=noarrows2",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode("utf-8", "replace")
    )
    checks = {
        "campaign": "hero-campaign-low" in html,
        "noTablet": "banner-exemplo-avatar-esquerda-tablet" not in html,
        "noFw": "desktop-fw" not in html,
        "femArrowsHidden": 'class="absolute top-1/2 z-20 hidden' in html,
        "mascPeito": "hero-peito.jpg" in masc,
        "mascNoPeitoM": "hero-peito-m.jpg" not in masc,
        "mascNoPromoV5": "promo-laser-v5" not in masc,
        "mascArrowsHidden": 'class="absolute top-1/2 z-20 hidden' in masc,
        "laserTitle": "Laser masculino" in masc,
    }
    print("live", checks)
    if not all(checks.values()):
        raise SystemExit("publish QA failed")
    print("OK", c["url"] + "/?v=noarrows2", c["url"] + "/masculino/?v=noarrows2")


def main() -> None:
    data = DATA.read_text(encoding="utf-8")
    hero = HERO.read_text(encoding="utf-8")
    export = EXPORT.read_text(encoding="utf-8")
    try:
        DATA.write_text(restore.replace_hero_slides(data, restore.LOJA_SLIDES), encoding="utf-8")
        if restore.HERO_CLASS_OT in hero:
            HERO.write_text(hero.replace(restore.HERO_CLASS_OT, restore.HERO_CLASS_LOJA), encoding="utf-8")
        if restore.CSS_OT in export:
            EXPORT.write_text(export.replace(restore.CSS_OT, restore.CSS_LOJA), encoding="utf-8")
        wait_next_loja_mode()
        subprocess.check_call(
            [sys.executable, str(ROOT / "scripts" / "_export_home_and_masc.py")],
            cwd=str(ROOT),
        )
        # local sanity
        home = (PM / "home.html").read_text(encoding="utf-8")
        if "hero-campaign-low" not in home:
            raise SystemExit("exported home missing campaign")
        if "banner-exemplo-avatar-esquerda-tablet" in home:
            raise SystemExit("exported home still has tablet hero")
        if 'class="absolute top-1/2 z-20 hidden' not in home:
            raise SystemExit("exported home missing hidden arrows")
        masc_html = (PM / "masculino.html").read_text(encoding="utf-8")
        if "hero-peito-m.jpg" in masc_html or "promo-laser-v5" in masc_html:
            raise SystemExit("exported masculino still has mobile crops/old promo")
        publish()
    finally:
        DATA.write_text(
            restore.replace_hero_slides(DATA.read_text(encoding="utf-8"), restore.OT_SLIDES),
            encoding="utf-8",
        )
        h = HERO.read_text(encoding="utf-8")
        if restore.HERO_CLASS_LOJA in h:
            HERO.write_text(h.replace(restore.HERO_CLASS_LOJA, restore.HERO_CLASS_OT), encoding="utf-8")
        e = EXPORT.read_text(encoding="utf-8")
        if restore.CSS_LOJA in e and restore.CSS_OT not in e:
            EXPORT.write_text(e.replace(restore.CSS_LOJA, restore.CSS_OT), encoding="utf-8")
        # keep arrow hide in HeroBanner (already in file)
        subprocess.check_call(
            [sys.executable, str(ROOT / "scripts" / "_export_home_and_masc.py")],
            cwd=str(ROOT),
        )
        print("code restored to OT fem hero; arrows stay hidden in component")


if __name__ == "__main__":
    main()
