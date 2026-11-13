# -*- coding: utf-8 -*-
"""Gera artes mobile 750x1000, tablet 1536x960 e desktop 1920x1080 (16:9).

Mobile: cover-crop a partir do 720x1280 com foco no terço superior (texto/rosto).
Tablet: expande o strip wide para 1536x960 com blur nas faixas.
Desktop: 16:9 — não usar 1600x500 (corta badge/rosto/CTA no slot lg+).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "images" / "hero" / "examples"
MEDIA = ROOT / "wordpress-loja" / "pm-home" / "media" / "images" / "hero" / "examples"

SLIDES = [
    {
        "mobile": "banner-exemplo-avatar-esquerda.jpg",
        "tablet": "banner-exemplo-avatar-esquerda-tablet.jpg",
        "desktop": "banner-exemplo-avatar-esquerda-desktop.jpg",
    },
    {
        "mobile": "banner-exemplo-avatar-direita.jpg",
        "tablet": "banner-exemplo-avatar-direita-tablet.jpg",
        "desktop": "banner-exemplo-avatar-direita-desktop.jpg",
    },
    {
        "mobile": "banner-virilha-mobile.jpg",
        "tablet": "banner-virilha-tablet.jpg",
        "desktop": "banner-virilha-desktop.jpg",
    },
    {
        "mobile": "banner-bracos-mobile.jpg",
        "tablet": "banner-bracos-tablet.jpg",
        "desktop": "banner-bracos-desktop.jpg",
    },
]


def cover_crop(im: Image.Image, tw: int, th: int, focus_y: float = 0.5) -> Image.Image:
    im = im.convert("RGB")
    sw, sh = im.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(round(sw * scale)), int(round(sh * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - tw) // 2)
    max_top = max(0, nh - th)
    top = int(round(max_top * max(0.0, min(1.0, focus_y))))
    top = min(max_top, max(0, top))
    return im.crop((left, top, left + tw, top + th))


def ensure_desktop(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGB")
    if im.size != (1920, 1080):
        im = cover_crop(im, 1920, 1080, focus_y=0.45)
    return im


def tablet_from_desktop(desktop: Image.Image) -> Image.Image:
    """1536x960: faixa desktop centrada + blur das bordas da própria arte."""
    tw, th = 1536, 960
    # stretch strip to full tablet width, keep aspect of desktop band
    base = desktop.resize(
        (tw, int(round(desktop.size[1] * tw / desktop.size[0]))),
        Image.Resampling.LANCZOS,
    )
    bg = cover_crop(desktop, tw, th, focus_y=0.5).filter(ImageFilter.GaussianBlur(28))
    overlay = Image.new("RGB", (tw, th), (58, 10, 60))
    bg = Image.blend(bg, overlay, 0.22)
    strip_h = base.size[1]
    y = (th - strip_h) // 2
    bg.paste(base, (0, y))
    return bg


def save_both(name: str, im: Image.Image) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    MEDIA.mkdir(parents=True, exist_ok=True)
    for dest in (OUT / name, MEDIA / name):
        im.save(dest, "JPEG", quality=90, optimize=True)
        print("saved", dest.relative_to(ROOT), im.size)


def main() -> None:
    for slide in SLIDES:
        desk_path = OUT / slide["desktop"]
        mob_path = OUT / slide["mobile"]
        if not desk_path.is_file():
            raise SystemExit(f"missing desktop {desk_path}")
        if not mob_path.is_file():
            raise SystemExit(f"missing mobile {mob_path}")

        desktop = ensure_desktop(desk_path)
        save_both(slide["desktop"], desktop)

        mobile = cover_crop(Image.open(mob_path), 750, 1000, focus_y=0.28)
        save_both(slide["mobile"], mobile)

        tablet = tablet_from_desktop(desktop)
        save_both(slide["tablet"], tablet)

    print("HERO_BREAKPOINT_ARTS_OK")


if __name__ == "__main__":
    main()
