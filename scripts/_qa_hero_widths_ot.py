# -*- coding: utf-8 -*-
"""QA hero arts on OficialTeste across viewport widths (Playwright)."""
from __future__ import annotations

import io
import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "projeto-migracao" / ".secrets" / "hero-width-qa-ot.json"
SHOTS = ROOT / "projeto-migracao" / ".secrets" / "hero-width-qa-shots"
BASE = "https://pellomenosoficialteste.companygenesis.com.br"

WIDTHS = [390, 768, 820, 1024, 1280, 1440, 1920]

EXPECT = {
    "mobile": (750, 1000),
    "tablet": (1536, 960),
    # ~2.29:1; host pode redimensionar 1920→1600 mantendo proporção
    "desktop": ((1920, 840), (1600, 700)),
}


def band(width: int) -> str:
    if width < 768:
        return "mobile"
    if width < 1024:
        return "tablet"
    return "desktop"


def band_from_src(src: str) -> str:
    if "tablet" in src:
        return "tablet"
    if "desktop" in src:
        return "desktop"
    if "examples/" in src:
        return "mobile"
    return "unknown"


def fetch_dims(url: str) -> tuple[int, int]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "x", "Cache-Control": "no-cache"},
    )
    data = urllib.request.urlopen(req, timeout=60).read()
    im = Image.open(io.BytesIO(data))
    return im.size


def main() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    rows = []
    fails = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for width in WIDTHS:
            vp_h = 900
            page = browser.new_page(viewport={"width": width, "height": vp_h})
            page.goto(
                BASE + f"/?pm=hero-w{width}-v4",
                wait_until="networkidle",
                timeout=90000,
            )
            page.wait_for_timeout(900)
            hero = page.locator("#inicio")
            hero.wait_for(state="visible", timeout=30000)
            box = hero.bounding_box()
            img = page.locator("#inicio [data-hero-slide='0'] img").first
            current = img.evaluate("el => el.currentSrc || el.src")
            fit = img.evaluate("el => getComputedStyle(el).objectFit")
            expected_band = band(width)
            got_band = band_from_src(current)

            file_dims = None
            dim_ok = False
            try:
                file_dims = fetch_dims(current.split("?")[0] + "?v=qa4")
                want = EXPECT[expected_band]
                dim_ok = file_dims == want or (
                    isinstance(want, tuple)
                    and want
                    and isinstance(want[0], tuple)
                    and file_dims in want
                )
            except Exception as exc:
                file_dims = str(exc)

            shot = SHOTS / f"hero-{width}.png"
            hero.screenshot(path=str(shot))
            im = Image.open(shot).convert("RGB")
            corners = [
                im.getpixel((2, 2)),
                im.getpixel((im.size[0] - 3, 2)),
                im.getpixel((2, im.size[1] - 3)),
                im.getpixel((im.size[0] - 3, im.size[1] - 3)),
            ]
            purpleish = 0
            for r, g, b in corners:
                if r > 70 and b > 45 and r > g + 25 and b > g + 10:
                    purpleish += 1

            # hero box aspect + viewport cap
            aspect_ok = True
            height_ok = True
            if box and box["height"] > 0:
                ar = box["width"] / box["height"]
                if width < 768:
                    aspect_ok = 0.65 <= ar <= 0.85  # ~3:4
                elif width < 1024:
                    aspect_ok = ar >= 1.4  # tablet faixa ~1.6
                else:
                    # viewport-capped: wider than 16:9, not taller than viewport
                    aspect_ok = ar >= 1.45
                    height_ok = box["height"] <= vp_h + 1 and box["height"] <= 680 + 1

            band_ok = got_band == expected_band
            fit_ok = fit == "cover"
            purple_ok = purpleish < 3
            ok = band_ok and fit_ok and purple_ok and aspect_ok and dim_ok and height_ok

            want = EXPECT[expected_band]
            expect_dims = (
                [list(x) for x in want]
                if isinstance(want, tuple) and want and isinstance(want[0], tuple)
                else list(want)
            )
            row = {
                "width": width,
                "heroBox": box,
                "bandExpected": expected_band,
                "bandGot": got_band,
                "currentSrc": current,
                "fileDims": file_dims,
                "expectDims": expect_dims,
                "fit": fit,
                "purpleCorners": purpleish,
                "bandOk": band_ok,
                "dimOk": dim_ok,
                "fitOk": fit_ok,
                "purpleOk": purple_ok,
                "aspectOk": aspect_ok,
                "heightOk": height_ok,
                "ok": ok,
                "shot": str(shot),
            }
            rows.append(row)
            print(
                f"{width}px band={got_band}/{expected_band} file={file_dims} "
                f"fit={fit} purple={purpleish} aspectOk={aspect_ok} "
                f"heightOk={height_ok} ok={ok}"
            )
            if not ok:
                fails.append(row)
            page.close()
        browser.close()

    OUT.write_text(
        json.dumps({"rows": rows, "fails": len(fails)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("wrote", OUT)
    if fails:
        print("FAILS", len(fails))
        sys.exit(1)
    print("HERO_WIDTH_QA_OK")


if __name__ == "__main__":
    main()
