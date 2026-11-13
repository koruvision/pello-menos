# -*- coding: utf-8 -*-
"""Recompress heavy PNGs in public/ + sync to pm-home/media (keep paths)."""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public" / "images"
MEDIA = ROOT / "wordpress-loja" / "pm-home" / "media" / "images"
MIN_BYTES = 800_000


def compress_png(path: Path) -> tuple[int, int]:
    before = path.stat().st_size
    im = Image.open(path)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
    # High-quality palette/optimize for opaque product shots; keep RGBA if alpha.
    tmp = path.with_suffix(path.suffix + ".tmp")
    if im.mode == "RGBA" and im.getextrema()[-1][0] < 255:
        im.save(tmp, format="PNG", optimize=True, compress_level=9)
    else:
        rgb = im.convert("RGB")
        # Keep .png extension but write optimized PNG (not JPEG) to avoid path churn.
        rgb.save(tmp, format="PNG", optimize=True, compress_level=9)
    after = tmp.stat().st_size
    if after < before * 0.98:
        tmp.replace(path)
        return before, after
    tmp.unlink(missing_ok=True)
    return before, before


def main() -> None:
    targets: list[Path] = []
    for folder in (
        PUBLIC / "hero",
        PUBLIC / "products",
        PUBLIC / "products" / "male",
        PUBLIC / "categories",
        PUBLIC / "social",
    ):
        if not folder.exists():
            continue
        for p in folder.glob("*.png"):
            if p.stat().st_size >= MIN_BYTES:
                targets.append(p)

    print("targets", len(targets))
    saved = 0
    for p in sorted(targets):
        before, after = compress_png(p)
        delta = before - after
        saved += max(0, delta)
        print(f"{p.relative_to(ROOT)} {before} -> {after} (-{delta})")
        # sync into media mirror if parallel path exists
        rel = p.relative_to(PUBLIC)
        dest = MEDIA / rel
        if dest.parent.exists() or True:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
    print("saved_bytes", saved)


if __name__ == "__main__":
    main()
