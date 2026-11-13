# -*- coding: utf-8 -*-
"""Desktop hero 1920x720 full-bleed (sem faixa central / blur lateral).

O slot lg+ é w=100% com altura viewport-capped. object-cover corta laterais
em telas mais 'altas'; a arte precisa preencher o canvas inteiro com conteúdo
real (não letterbox 16:9 no meio).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(r"C:\Users\GC1\.cursor\projects\c-Users-GC1-Desktop-pello-menos\assets")
OUT = ROOT / "public" / "images" / "hero" / "examples"
MEDIA = ROOT / "wordpress-loja" / "pm-home" / "media" / "images" / "hero" / "examples"

# ~2.29:1 — alinha melhor com slots 1280–1440×~630–680 (menos corte lateral)
TW, TH = 1920, 840

# source gen → dest publicado (nomes -fw; full-bleed, sem blur lateral)
MAP = {
    "hero-clean-perna-md.jpg": "banner-perna-desktop-fw.jpg",
    "hero-clean-axilas-md.jpg": "banner-axilas-desktop-fw.jpg",
    "hero-clean-virilha-md.jpg": "banner-virilha-desktop-fw.jpg",
    "hero-clean-bracos-md.jpg": "banner-bracos-desktop-fw.jpg",
}

FALLBACK = {
    "banner-perna-desktop-fw.jpg": "hero-clean-perna.jpg",
    "banner-axilas-desktop-fw.jpg": "hero-clean-axilas.jpg",
    "banner-virilha-desktop-fw.jpg": "hero-clean-virilha.jpg",
    "banner-bracos-desktop-fw.jpg": "hero-clean-bracos.jpg",
}


def cover_fill(src: Image.Image, tw: int = TW, th: int = TH, focus_y: float = 0.38) -> Image.Image:
    """Preenche 100% do canvas (cover). focus_y favorece topo (rosto/badge)."""
    src = src.convert("RGB")
    sw, sh = src.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(round(sw * scale)), int(round(sh * scale))
    im = src.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - tw) // 2)
    max_top = max(0, nh - th)
    top = int(round(max_top * max(0.0, min(1.0, focus_y))))
    top = min(max_top, max(0, top))
    return im.crop((left, top, left + tw, top + th))


def save_both(name: str, im: Image.Image) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    MEDIA.mkdir(parents=True, exist_ok=True)
    for dest in (OUT / name, MEDIA / name):
        im.save(dest, "JPEG", quality=91, optimize=True)
        print("saved", dest.relative_to(ROOT), im.size)


def main() -> None:
    for src_name, dest_name in MAP.items():
        src = ASSETS / src_name
        if not src.is_file():
            src = ASSETS / FALLBACK[dest_name]
        if not src.is_file():
            raise SystemExit(f"missing source for {dest_name}")
        im = cover_fill(Image.open(src))
        if im.size != (TW, TH):
            raise SystemExit(f"bad size {dest_name}: {im.size}")
        save_both(dest_name, im)
        # espelhos legados / vp (mesmo bytes full-bleed)
        aliases = {
            "banner-perna-desktop-fw.jpg": (
                "banner-perna-desktop-vp.jpg",
                "banner-exemplo-avatar-esquerda-desktop.jpg",
            ),
            "banner-axilas-desktop-fw.jpg": (
                "banner-axilas-desktop-vp.jpg",
                "banner-exemplo-avatar-direita-desktop.jpg",
            ),
            "banner-virilha-desktop-fw.jpg": (
                "banner-virilha-desktop-vp.jpg",
                "banner-virilha-desktop.jpg",
            ),
            "banner-bracos-desktop-fw.jpg": (
                "banner-bracos-desktop-vp.jpg",
                "banner-bracos-desktop.jpg",
            ),
        }[dest_name]
        for alias in aliases:
            save_both(alias, im)
    print("HERO_DESKTOP_FULLBLEED_OK")


if __name__ == "__main__":
    main()
