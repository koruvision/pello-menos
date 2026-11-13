# -*- coding: utf-8 -*-
"""Refaz só as artes desktop do hero em 16:9 (1920x1080) a partir dos gens aprovados.

Motivo: 1600x500 (3.2:1) cortava badge/rosto/CTA. O designer original e os novos
gens são 1280x720; o slot lg+ passa a aspect-ratio 16/9.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(r"C:\Users\GC1\.cursor\projects\c-Users-GC1-Desktop-pello-menos\assets")
OUT = ROOT / "public" / "images" / "hero" / "examples"
MEDIA = ROOT / "wordpress-loja" / "pm-home" / "media" / "images" / "hero" / "examples"

TW, TH = 1920, 1080

MAP = {
    "hero-desktop-perna-16x9.jpg": "banner-exemplo-avatar-esquerda-desktop.jpg",
    "hero-desktop-axilas-16x9.jpg": "banner-exemplo-avatar-direita-desktop.jpg",
    "hero-desktop-virilha-16x9.jpg": "banner-virilha-desktop.jpg",
    "hero-desktop-bracos-16x9.jpg": "banner-bracos-desktop.jpg",
}


def fit_cover(im: Image.Image, tw: int, th: int) -> Image.Image:
    """Cover into target — sources are already 16:9 so this is mostly upscale."""
    im = im.convert("RGB")
    sw, sh = im.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(round(sw * scale)), int(round(sh * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return im.crop((left, top, left + tw, top + th))


def save_both(name: str, im: Image.Image) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    MEDIA.mkdir(parents=True, exist_ok=True)
    for dest in (OUT / name, MEDIA / name):
        im.save(dest, "JPEG", quality=90, optimize=True)
        print("saved", dest.relative_to(ROOT), im.size)


def main() -> None:
    for src_name, dest_name in MAP.items():
        src = ASSETS / src_name
        if not src.is_file():
            # fallback to previous wide designer asset
            alt = {
                "banner-exemplo-avatar-esquerda-desktop.jpg": "banner-cera-perna-desktop-wide.jpg",
                "banner-exemplo-avatar-direita-desktop.jpg": "banner-laser-axilas-desktop-wide.jpg",
                "banner-virilha-desktop.jpg": "banner-virilha-desktop-wide.jpg",
                "banner-bracos-desktop.jpg": "banner-bracos-desktop-wide.jpg",
            }[dest_name]
            src = ASSETS / alt
        if not src.is_file():
            raise SystemExit(f"missing {src_name}")
        im = fit_cover(Image.open(src), TW, TH)
        if im.size != (TW, TH):
            raise SystemExit(f"bad size {dest_name}: {im.size}")
        save_both(dest_name, im)
    print("HERO_DESKTOP_16X9_OK")


if __name__ == "__main__":
    main()
