# -*- coding: utf-8 -*-
"""Lista no Drive qualquer pasta/arquivo ligado a planos ou body splash."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sync_drive_product_images as sync  # noqa: E402

NEEDLES = (
    "plano",
    "silver",
    "gold",
    "prepago",
    "pre-pago",
    "pre pago",
    "clube",
    "splash",
    "body",
    "produto",
    "assinatura",
)


def interesting(name: str) -> bool:
    low = name.lower()
    return any(n in low for n in NEEDLES)


def walk_all(folder_id: str, trail: str, depth: int = 0) -> None:
    try:
        items = sync.list_folder(folder_id)
    except Exception as err:
        print(f"FAIL {trail}: {err}")
        return
    for file_id, name in items:
        ext = Path(name).suffix.lower()
        is_img = ext in sync.IMAGE_EXT
        mark = "IMG" if is_img else "DIR"
        if interesting(name) or interesting(trail) or depth <= 1:
            if interesting(name) or interesting(trail):
                print(f"{mark}\t{trail}/{name}\t{file_id}")
        if not is_img:
            walk_all(file_id, f"{trail}/{name}", depth + 1)


def main() -> None:
    print("PARENT", sync.DRIVE_PARENT)
    for fid, name in sync.list_folder(sync.DRIVE_PARENT):
        print(f"ROOT\t{name}\t{fid}")
        walk_all(fid, name)
    # also scan fem/masc roots fully for needles
    roots = sync.resolve_drive_roots()
    for aud, fid in roots.items():
        print("=== walk", aud)
        walk_all(fid, aud.upper())


if __name__ == "__main__":
    main()
