# -*- coding: utf-8 -*-
"""Convert heavy product/category PNGs (>800KB) to JPEG; rewrite path refs."""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public" / "images"
MEDIA = ROOT / "wordpress-loja" / "pm-home" / "media" / "images"
MIN = 800_000
QUALITY = 85
FOLDERS = ["products", "products/male", "categories"]


def convert(src: Path) -> tuple[str, str, int] | None:
    before = src.stat().st_size
    if before < MIN or src.suffix.lower() != ".png":
        return None
    dest = src.with_suffix(".jpg")
    im = Image.open(src)
    if im.mode == "RGBA":
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    elif im.mode != "RGB":
        im = im.convert("RGB")
    im.save(dest, format="JPEG", quality=QUALITY, optimize=True, progressive=True)
    after = dest.stat().st_size
    rel = src.relative_to(PUBLIC)
    media_dest = MEDIA / rel.with_suffix(".jpg")
    media_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(dest, media_dest)
    print(f"{rel} {before} -> {dest.name} {after} (-{before - after})")
    old_web = "/images/" + rel.as_posix()
    new_web = "/images/" + rel.with_suffix(".jpg").as_posix()
    return old_web, new_web, before - after


def main() -> None:
    path_reps: list[tuple[str, str]] = []
    saved = 0
    for folder in FOLDERS:
        base = PUBLIC / folder
        if not base.exists():
            continue
        for src in sorted(base.glob("*.png")):
            result = convert(src)
            if not result:
                continue
            old_web, new_web, delta = result
            path_reps.append((old_web, new_web))
            # media mirror paths used in exported HTML
            path_reps.append(
                (
                    "media" + old_web,  # media/images/...
                    "media" + new_web,
                )
            )
            saved += max(0, delta)

    files = [ROOT / "src/lib/data.ts"]
    files += list((ROOT / "wordpress-loja/pm-home").rglob("*.html"))
    files += list((ROOT / "wordpress-loja/pm-home").rglob("*.js"))
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        orig = text
        for old, new in path_reps:
            text = text.replace(old, new)
        if text != orig:
            path.write_text(text, encoding="utf-8")
            print("rewrote", path.relative_to(ROOT))
    print("saved_bytes", saved, "converted", len(path_reps) // 2)


if __name__ == "__main__":
    main()
