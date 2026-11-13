# -*- coding: utf-8 -*-
"""Resize baked banners to canonical sizes and sync to public + pm-home media."""
from pathlib import Path
import shutil

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = Path(r"C:\Users\GC1\.cursor\projects\c-Users-GC1-Desktop-pello-menos\assets")
OUT = ROOT / "public" / "images" / "hero" / "examples"
MEDIA = ROOT / "wordpress-loja" / "pm-home" / "media" / "images" / "hero" / "examples"


def cover_resize(im: Image.Image, tw: int, th: int) -> Image.Image:
    im = im.convert("RGB")
    sw, sh = im.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(round(sw * scale)), int(round(sh * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return im.crop((left, top, left + tw, top + th))


def contain_resize(im: Image.Image, tw: int, th: int, bg=(58, 10, 60)) -> Image.Image:
    """Fit entire image into box (for mobile if needed)."""
    im = im.convert("RGB")
    sw, sh = im.size
    scale = min(tw / sw, th / sh)
    nw, nh = int(round(sw * scale)), int(round(sh * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (tw, th), bg)
    canvas.paste(im, ((tw - nw) // 2, (th - nh) // 2))
    return canvas


def save_pair(name: str, im: Image.Image):
    OUT.mkdir(parents=True, exist_ok=True)
    MEDIA.mkdir(parents=True, exist_ok=True)
    for dest in (OUT / name, MEDIA / name):
        im.save(dest, "JPEG", quality=90, optimize=True)
        print("saved", dest, im.size)


def main():
    # Desktop → exact 1920x600
    desktop_map = {
        "banner-cera-perna-desktop-wide.jpg": "banner-exemplo-avatar-esquerda-desktop.jpg",
        "banner-laser-axilas-desktop-wide.jpg": "banner-exemplo-avatar-direita-desktop.jpg",
        "banner-virilha-desktop-wide.jpg": "banner-virilha-desktop.jpg",
        "banner-bracos-desktop-wide.jpg": "banner-bracos-desktop.jpg",
    }
    for src_name, dest_name in desktop_map.items():
        src = ASSETS / src_name
        im = cover_resize(Image.open(src), 1920, 600)
        save_pair(dest_name, im)

    # Mobile → exact 720x1280 (approved style); keep existing 2, normalize new 2
    # Keep approved mobiles as-is if already 720x1280
    for name in (
        "banner-exemplo-avatar-esquerda.jpg",
        "banner-exemplo-avatar-direita.jpg",
    ):
        src = OUT / name
        if src.is_file():
            im = Image.open(src)
            if im.size != (720, 1280):
                im = contain_resize(im, 720, 1280)
                save_pair(name, im)
            else:
                shutil.copy2(src, MEDIA / name)
                print("keep", name, im.size)

    mobile_new = {
        "banner-virilha-mobile.jpg": "banner-virilha-mobile.jpg",
        "banner-bracos-mobile.jpg": "banner-bracos-mobile.jpg",
    }
    for src_name, dest_name in mobile_new.items():
        src = ASSETS / src_name
        im = Image.open(src)
        if im.size != (720, 1280):
            # Prefer cover to fill 9:16
            im = cover_resize(im, 720, 1280)
        else:
            im = im.convert("RGB")
        save_pair(dest_name, im)

    print("DONE")


if __name__ == "__main__":
    main()
