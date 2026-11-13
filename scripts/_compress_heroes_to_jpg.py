# -*- coding: utf-8 -*-
"""Convert heavy opaque hero PNGs to high-quality JPEG; update data.ts + pm-home HTML."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_HERO = ROOT / "public" / "images" / "hero"
MEDIA_HERO = ROOT / "wordpress-loja" / "pm-home" / "media" / "images" / "hero"
DATA_TS = ROOT / "src" / "lib" / "data.ts"
PM_HOME = ROOT / "wordpress-loja" / "pm-home"

# Priority from plan: campaign heroes + other huge desktop heroes
TARGETS = [
    "hero-campaign-center.png",
    "hero-campaign-left.png",
    "hero-campaign-low.png",
    "hero-campaign-right.png",
    "hero-cera.png",
    "hero-laser.png",
    "hero-verao.png",
    "destaque-combo.png",
    "destaque-kits.png",
    "destaque-presente.png",
    "destaque-verao.png",
    "destaque-olhar.png",
]

QUALITY = 85


def to_jpg(png_name: str) -> tuple[str, int, int] | None:
    src = PUBLIC_HERO / png_name
    if not src.exists():
        print("missing", png_name)
        return None
    before = src.stat().st_size
    jpg_name = png_name.rsplit(".", 1)[0] + ".jpg"
    dest = PUBLIC_HERO / jpg_name
    im = Image.open(src)
    if im.mode not in ("RGB", "L"):
        # flatten alpha on white
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
    im.save(dest, format="JPEG", quality=QUALITY, optimize=True, progressive=True)
    after = dest.stat().st_size
    MEDIA_HERO.mkdir(parents=True, exist_ok=True)
    shutil.copy2(dest, MEDIA_HERO / jpg_name)
    # keep PNG as fallback but prefer smaller; do not delete PNG (whitelist)
    print(f"{png_name} {before} -> {jpg_name} {after} (-{before - after})")
    return png_name, jpg_name, before - after


def rewrite_refs(replacements: list[tuple[str, str]]) -> None:
    # data.ts
    text = DATA_TS.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(f"/images/hero/{old}", f"/images/hero/{new}")
    DATA_TS.write_text(text, encoding="utf-8")

    # all html/js under pm-home
    for path in list(PM_HOME.rglob("*.html")) + list(PM_HOME.rglob("*.js")):
        raw = path.read_text(encoding="utf-8")
        orig = raw
        for old, new in replacements:
            raw = raw.replace(f"/images/hero/{old}", f"/images/hero/{new}")
            raw = raw.replace(f"media/images/hero/{old}", f"media/images/hero/{new}")
        if raw != orig:
            path.write_text(raw, encoding="utf-8")
            print("rewrote", path.relative_to(ROOT))


def main() -> None:
    reps: list[tuple[str, str]] = []
    saved = 0
    for name in TARGETS:
        result = to_jpg(name)
        if not result:
            continue
        old, new, delta = result
        reps.append((old, new))
        saved += max(0, delta)
    if reps:
        rewrite_refs(reps)
    print("saved_bytes", saved, "files", len(reps))


if __name__ == "__main__":
    main()
