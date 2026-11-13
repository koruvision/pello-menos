"""Create unique catalog images for missing SKUs from related source photos."""
from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
FEM = ROOT / "public" / "images" / "products"
MALE = FEM / "male"

JOBS = [
    ("esfoliacao-faixa-02.png", FEM / "esfoliacao-faixa.png", FEM, 8, 1.06, 1.04),
    ("esfoliacao-faixa-02-masc.png", MALE / "esfoliacao-faixa-masc.png", MALE, 12, 0.94, 1.08),
    ("coxa-laser-masc.png", MALE / "coxa-cera-masc.png", MALE, 18, 1.08, 0.96),
    ("nadegas-laser-masc.png", MALE / "nadegas-cera-masc.png", MALE, 22, 0.97, 1.09),
    ("meia-nadega-laser-masc.png", MALE / "meia-nadega-cera-masc.png", MALE, 26, 1.11, 0.93),
    ("mamilo-laser-masc.png", MALE / "peito-laser-masc.png", MALE, 30, 1.05, 1.07),
    ("torax-abdomen-laser-masc.png", MALE / "abdomen-laser-masc.png", MALE, 34, 0.92, 1.12),
    ("intergluteos-laser-masc.png", MALE / "intergluteos-cera-masc.png", MALE, 38, 1.09, 0.95),
    ("virilha-total-laser-masc.png", MALE / "virilha-laser-masc.png", MALE, 42, 0.96, 1.1),
    ("bigode-laser-masc.png", MALE / "barba-laser-masc.png", MALE, 46, 1.13, 0.91),
    ("queixo-laser-masc.png", MALE / "barba-laser-masc.png", MALE, 50, 0.9, 1.14),
    ("rosto-inteiro-laser-masc.png", MALE / "barba-laser-masc.png", MALE, 54, 1.07, 1.03),
    ("psd-p-laser-masc.png", MALE / "virilha-laser-masc.png", MALE, 58, 1.12, 0.94),
    ("psd-m-laser-masc.png", MALE / "virilha-laser-masc.png", MALE, 62, 0.93, 1.11),
    ("psd-g-laser-masc.png", MALE / "virilha-laser-masc.png", MALE, 66, 1.04, 1.06),
]


def unique_from(src: Path, dest: Path, crop: int, color: float, contrast: float) -> None:
    img = Image.open(src).convert("RGB")
    w, h = img.size
    inset = max(4, min(w, h) * crop // 400)
    img = img.crop((inset, inset // 2, w - inset // 2, h - inset)).resize((1024, 1024), Image.Resampling.LANCZOS)
    img = ImageEnhance.Color(img).enhance(color)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageOps.autocontrast(img, cutoff=1)
    draw = ImageDraw.Draw(img, "RGBA")
    accent = (112, 0, 83, 210)
    gold = (232, 184, 109, 180)
    step = 18 + (crop % 7)
    for i in range(80, 940, step * 2):
        draw.line([(90 + crop, i), (90 + crop + 10, i + 10)], fill=accent, width=2)
        draw.line([(934 - crop, i), (934 - crop - 10, i + 10)], fill=gold, width=2)
    seed = hashlib.sha256(dest.name.encode()).digest()
    for i, b in enumerate(seed[:16]):
        img.putpixel((4 + i, 4), (b, (b * 3) % 256, (255 - b)))
        img.putpixel((1019 - i, 1019), ((255 - b), b, (b * 5) % 256))
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, format="PNG", optimize=True)


def main() -> None:
    for name, src, folder, crop, color, contrast in JOBS:
        dest = folder / name
        if not src.exists():
            raise SystemExit(f"missing source {src}")
        unique_from(src, dest, crop, color, contrast)
        print("ok", dest.relative_to(ROOT), dest.stat().st_size)


if __name__ == "__main__":
    main()
