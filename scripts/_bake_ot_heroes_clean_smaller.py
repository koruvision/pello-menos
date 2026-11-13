# -*- coding: utf-8 -*-
"""Bake OT desktop heroes from loja originals: soft grade + smaller text."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "projeto-migracao" / ".secrets" / "hero-compare"
ASSETS = Path(r"C:\Users\GC1\.cursor\projects\c-Users-GC1-Desktop-pello-menos\assets")
OUT_PUBLIC = ROOT / "public" / "images" / "hero" / "examples"
OUT_MEDIA = ROOT / "wordpress-loja" / "pm-home" / "media" / "images" / "hero" / "examples"

TW, TH = 1920, 840
GOLD = (201, 154, 58)
GOLD_DARK = (120, 78, 28)
WHITE = (255, 255, 255)
BLACK = (28, 18, 16)

SERIF = r"C:\Windows\Fonts\georgia.ttf"
SERIF_B = r"C:\Windows\Fonts\georgiab.ttf"
SANS = r"C:\Windows\Fonts\segoeuib.ttf"
SANS_R = r"C:\Windows\Fonts\segoeui.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def soft_grade(im: Image.Image) -> Image.Image:
    im = im.convert("RGB")
    im = ImageEnhance.Color(im).enhance(0.62)
    im = ImageEnhance.Contrast(im).enhance(0.80)
    im = ImageEnhance.Brightness(im).enhance(1.08)
    im = ImageEnhance.Sharpness(im).enhance(0.85)
    return im


def sample_bg(im: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int, int]:
    crop = im.crop(box).resize((1, 1), Image.Resampling.BOX)
    return crop.getpixel((0, 0))


def cover_region(
    im: Image.Image,
    box: tuple[int, int, int, int],
    patch_box: tuple[int, int, int, int],
    *,
    feather: int = 56,
    side: str = "left",
) -> Image.Image:
    """Erase old baked text with solid bg + feathered edge into the photo."""
    bg = sample_bg(im, patch_box)
    base = im.convert("RGBA")
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    solid = Image.new("RGBA", (w, h), (*bg, 255))
    alpha = Image.new("L", (w, h), 255)
    ad = ImageDraw.Draw(alpha)
    if side == "left":
        for i in range(feather):
            a = int(255 * (1 - (i + 1) / feather))
            ad.line([(w - feather + i, 0), (w - feather + i, h)], fill=a)
    else:
        for i in range(feather):
            a = int(255 * ((i + 1) / feather))
            ad.line([(i, 0), (i, h)], fill=a)
    solid.putalpha(alpha)
    out = base.copy()
    out.alpha_composite(solid, (x0, y0))
    return out.convert("RGB")


def pill(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    *,
    fill_star: bool = True,
    pad_x: int = 20,
    pad_y: int = 9,
) -> tuple[int, int, int, int]:
    x, y = xy
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    star_w = 26 if fill_star else 0
    w = tw + pad_x * 2 + star_w
    h = max(th + pad_y * 2, 34)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=GOLD)
    tx = x + pad_x
    if fill_star:
        cy = y + h // 2
        r = 8
        draw.ellipse((x + 11, cy - r, x + 11 + 2 * r, cy + r), outline=GOLD_DARK, width=2)
        # tiny 4-point mark
        draw.ellipse((x + 16, cy - 3, x + 22, cy + 3), fill=GOLD_DARK)
        tx = x + 36
    draw.text((tx, y + (h - th) // 2 - 1), text, font=fnt, fill=BLACK)
    return (x, y, x + w, y + h)


def cta_pill(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
) -> None:
    x, y = xy
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 28, 12
    w, h = tw + pad_x * 2, th + pad_y * 2
    draw.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=GOLD)
    draw.text((x + pad_x, y + pad_y - 1), text, font=fnt, fill=BLACK)


def draw_price(draw: ImageDraw.ImageDraw, xy: tuple[int, int], price: str) -> None:
    """price like 'R$ 73,02' with smaller R$ and cents."""
    x, y = xy
    if price.startswith("R$ "):
        main = price[3:]
    else:
        main = price
    if "," in main:
        reais, cents = main.split(",", 1)
    else:
        reais, cents = main, "00"
    f_rs = font(SERIF_B, 22)
    f_main = font(SERIF_B, 50)
    f_cents = font(SERIF_B, 24)
    draw.text((x, y + 22), "R$", font=f_rs, fill=GOLD)
    rs_w = draw.textbbox((0, 0), "R$", font=f_rs)[2]
    draw.text((x + rs_w + 5, y), reais, font=f_main, fill=GOLD)
    main_w = draw.textbbox((0, 0), reais, font=f_main)[2]
    draw.text((x + rs_w + 5 + main_w + 2, y + 20), f",{cents}", font=f_cents, fill=GOLD)


def draw_stack(
    im: Image.Image,
    *,
    side: str,
    badge: str,
    title_lines: list[str],
    price: str,
    cta: str,
    brand: str | None = None,
    cover_box: tuple[int, int, int, int],
    patch_box: tuple[int, int, int, int],
) -> Image.Image:
    im = cover_region(im, cover_box, patch_box, side=side)
    draw = ImageDraw.Draw(im)

    if side == "right":
        x = 1180
    else:
        x = 130

    y = 195
    if brand:
        draw.text((x, y), brand, font=font(SERIF_B, 34), fill=GOLD)
        y += 48

    pill(draw, (x, y), badge.upper(), font(SANS, 13), fill_star=("ESQUENTA" not in badge.upper()))
    y += 50

    f_title = font(SERIF, 34)
    for line in title_lines:
        draw.text((x, y), line, font=f_title, fill=WHITE)
        y += 42
    y += 6
    draw.text((x, y), "por", font=font(SERIF, 18), fill=WHITE)
    y += 30
    draw_price(draw, (x, y), price)
    y += 88
    cta_pill(draw, (x, y), cta.upper() + " >", font(SANS, 14))
    return im


SPECS = [
    {
        "src": "loja-banner-perna-desktop-fw.jpg",
        "dest": "banner-perna-desktop-fw.jpg",
        "asset": "hero-clean-perna-md.jpg",
        "side": "right",
        "badge": "Cera 15% OFF",
        "title_lines": ["Pernas prontas", "pra viver"],
        "price": "R$ 73,02",
        "cta": "Ver cera",
        "cover_box": (1080, 0, 1920, 840),
        "patch_box": (1780, 10, 1900, 80),
        "aliases": (
            "banner-perna-desktop-vp.jpg",
            "banner-exemplo-avatar-esquerda-desktop.jpg",
        ),
    },
    {
        "src": "loja-banner-axilas-desktop-fw.jpg",
        "dest": "banner-axilas-desktop-fw.jpg",
        "asset": "hero-clean-axilas-md.jpg",
        "side": "left",
        "badge": "Laser 60% OFF",
        "title_lines": ["10 sessões de laser", "nas axilas"],
        "price": "R$ 359,96",
        "cta": "Ver laser",
        "cover_box": (0, 0, 1080, 840),
        "patch_box": (900, 10, 1040, 70),
        "aliases": (
            "banner-axilas-desktop-vp.jpg",
            "banner-exemplo-avatar-direita-desktop.jpg",
        ),
    },
    {
        "src": "loja-banner-virilha-desktop-fw.jpg",
        "dest": "banner-virilha-desktop-fw.jpg",
        "asset": "hero-clean-virilha-md.jpg",
        "side": "left",
        "badge": "Esquenta Black",
        "title_lines": ["Virilha total", "a laser"],
        "price": "R$ 836,00",
        "cta": "Ver serviços",
        "cover_box": (0, 0, 1060, 840),
        "patch_box": (880, 10, 1020, 70),
        "aliases": ("banner-virilha-desktop-vp.jpg", "banner-virilha-desktop.jpg"),
    },
    {
        "src": "loja-banner-bracos-desktop-fw.jpg",
        "dest": "banner-bracos-desktop-fw.jpg",
        "asset": "hero-clean-bracos-md.jpg",
        "side": "left",
        "badge": "Laser 60% OFF",
        "title_lines": ["Braços inteiros", "a laser"],
        "price": "R$ 576,00",
        "cta": "Ver braços",
        "brand": "Pello Menos",
        "cover_box": (0, 0, 1120, 840),
        "patch_box": (920, 10, 1080, 60),
        "aliases": ("banner-bracos-desktop-vp.jpg", "banner-bracos-desktop.jpg"),
    },
]


def save_all(name: str, im: Image.Image) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    OUT_PUBLIC.mkdir(parents=True, exist_ok=True)
    OUT_MEDIA.mkdir(parents=True, exist_ok=True)
    for dest in (OUT_PUBLIC / name, OUT_MEDIA / name):
        im.save(dest, "JPEG", quality=91, optimize=True)
        print("saved", dest.relative_to(ROOT), im.size)


def main() -> None:
    for spec in SPECS:
        src = SRC / spec["src"]
        if not src.is_file():
            raise SystemExit(f"missing {src}")
        im = soft_grade(Image.open(src))
        if im.size != (TW, TH):
            # cover-fill to canonical
            sw, sh = im.size
            scale = max(TW / sw, TH / sh)
            nw, nh = int(round(sw * scale)), int(round(sh * scale))
            im = im.resize((nw, nh), Image.Resampling.LANCZOS)
            left = (nw - TW) // 2
            top = int((nh - TH) * 0.38)
            im = im.crop((left, top, left + TW, top + TH))
        im = draw_stack(
            im,
            side=spec["side"],
            badge=spec["badge"],
            title_lines=spec["title_lines"],
            price=spec["price"],
            cta=spec["cta"],
            brand=spec.get("brand"),
            cover_box=spec["cover_box"],
            patch_box=spec["patch_box"],
        )
        # also keep asset name for finalize pipeline
        ASSETS.mkdir(parents=True, exist_ok=True)
        im.save(ASSETS / spec["asset"], "JPEG", quality=93)
        save_all(spec["dest"], im)
        for alias in spec.get("aliases", ()):
            save_all(alias, im)
        print("ok", spec["dest"])


if __name__ == "__main__":
    main()
