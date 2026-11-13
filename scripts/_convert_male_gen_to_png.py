# -*- coding: utf-8 -*-
"""Convert GenerateImage JPG outputs to public PNG product paths."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(
    r"C:\Users\GC1\.cursor\projects\c-Users-GC1-Desktop-pello-menos\assets"
)
OUT_DIR = ROOT / "public" / "images" / "products" / "male"


def convert_id(product_id: str) -> bool:
    for name in (f"{product_id}-gen.jpg", f"{product_id}-gen.png", f"{product_id}.jpg"):
        src = ASSETS / name
        if src.is_file():
            break
    else:
        return False
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im.convert("RGB").save(OUT_DIR / f"{product_id}.png", "PNG")
    return True


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--ids-file":
        ids = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    else:
        ids = [a for a in sys.argv[1:] if a]
    ok, fail = [], []
    for pid in ids:
        (ok if convert_id(pid) else fail).append(pid)
    print(json.dumps({"written": len(ok), "ok": ok, "failed": fail}))


if __name__ == "__main__":
    main()
