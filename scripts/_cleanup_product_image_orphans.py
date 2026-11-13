# -*- coding: utf-8 -*-
"""Apaga ficheiros órfãos em public/images/products e pm-home/media/images/products.

Mantém apenas ficheiros cujo stem corresponde a um id do catálogo (ou alias /
gift / body-splash / hero-ish whitelisted) e brand/trust fora deste scope.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sync_drive_product_images as sync

PUBLIC = ROOT / "public" / "images" / "products"
MEDIA = ROOT / "wordpress-loja" / "pm-home" / "media" / "images" / "products"
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}

# Stems extra referenciados fora do product_ids() estrito (promo, 1 real, etc.).
EXTRA_KEEP = {
    "cartao-presente-80",
    "body-splash",
    "body-splash-marcante",
    "body-splash-livre",
    "body-splash-autentica",
    "body-splash-marcante-masc",
    "body-splash-livre-masc",
    "body-splash-autentica-masc",
}


def allowed_stems() -> set[str]:
    ids = set(sync.product_ids())
    ids |= EXTRA_KEEP
    # Aliases invertidos: ficheiro com nome alias também é válido se mapeia a id.
    for alias, target in sync.ALIASES.items():
        if target in ids:
            ids.add(alias)
    # Gift variants masc / sem sufixo
    gifts = {s for s in ids if s.startswith("cartao-presente")}
    for g in list(gifts):
        ids.add(g)
        if not g.endswith("-masc"):
            ids.add(f"{g}-masc")
    return ids


def orphan_in(folder: Path, allowed: set[str], dry: bool) -> list[Path]:
    if not folder.is_dir():
        return []
    found: list[Path] = []
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_EXT:
            continue
        stem = path.stem
        # male/ subfolder: stem already includes -masc usually
        if stem in allowed or sync.is_gift_card(stem):
            continue
        # strip common size suffixes? none expected
        found.append(path)
    if not dry:
        for path in found:
            print(f"DEL {path.relative_to(ROOT)}", path.stat().st_size)
            path.unlink()
    return found


def main() -> None:
    dry = "--dry" in sys.argv
    allowed = allowed_stems()
    print("allowed stems", len(allowed), "dry" if dry else "delete")
    public_orphans = orphan_in(PUBLIC, allowed, dry)
    media_orphans = orphan_in(MEDIA, allowed, dry)
    print("public_orphans", len(public_orphans))
    print("media_orphans", len(media_orphans))
    for path in public_orphans + media_orphans:
        if dry:
            print("ORPHAN", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
