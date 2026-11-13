# -*- coding: utf-8 -*-
"""Baixa imagens oficiais PLANOS + BODY SPLASHS do Drive (pasta pai).

Mesma arte para feminino e masculino: grava só em public/images/products/
(não em male/). Body Splash: uma arte por fragrância.
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sync_drive_product_images as sync  # noqa: E402

PRODUCTS = ROOT / "public" / "images" / "products"
PM_MEDIA = ROOT / "wordpress-loja" / "pm-home" / "media" / "images" / "products"

# Drive folder IDs discovered under parent 1UMmUhjwJmyYfz8O6O-g0DpNB1Wp6GC29
PLANOS = {
    "plano-silver.png": "plano-silver",
    "plano-gold.png": "plano-gold",
    "plano-prepago.png": "plano-prepago",
    "plano-clube-laser.png": "plano-clube-laser",
}
SPLASH = {
    "bodysplash_livre.png": "body-splash-livre",
    "bodysplash_marcante.png": "body-splash-marcante",
    "bodysplash_autentica.png": "body-splash-autentica",
}


def find_files(folder_id: str) -> dict[str, str]:
    """name -> file_id"""
    return {name: fid for fid, name in sync.list_folder(folder_id)}


def save_official(file_id: str, dest_stem: str) -> Path:
    raw = sync.download(file_id)
    dest = PRODUCTS / f"{dest_stem}.webp"
    sync.to_webp(raw, dest)
    # mirror into pm-home media (export asset base)
    if PM_MEDIA.is_dir():
        PM_MEDIA.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dest, PM_MEDIA / dest.name)
    # remove stale male copies so twins don't pick a different file
    male = PRODUCTS / "male" / f"{dest_stem}.webp"
    male_masc = PRODUCTS / "male" / f"{dest_stem}-masc.webp"
    for p in (male, male_masc):
        if p.is_file():
            p.unlink()
            print("removed", p.relative_to(ROOT))
    h = hashlib.sha1(dest.read_bytes()).hexdigest()[:8]
    print(f"ok {dest_stem} {dest.stat().st_size}b v={h}")
    return dest


def main() -> None:
    parent_items = {name: fid for fid, name in sync.list_folder(sync.DRIVE_PARENT)}
    planos_id = parent_items.get("PLANOS")
    splash_id = parent_items.get("BODY SPLASHS")
    if not planos_id or not splash_id:
        raise SystemExit(f"missing folders in parent: {sorted(parent_items)}")

    planos = find_files(planos_id)
    splash = find_files(splash_id)
    print("planos", sorted(planos))
    print("splash", sorted(splash))

    for name, stem in PLANOS.items():
        if name not in planos:
            print("MISSING plano", name)
            continue
        save_official(planos[name], stem)

    splash_paths = {}
    for name, stem in SPLASH.items():
        if name not in splash:
            print("MISSING splash", name)
            continue
        dest = save_official(splash[name], stem)
        splash_paths[stem] = dest

    # Compat: body-splash.webp genérico = Livre (mesma arte compartilhada legada)
    if "body-splash-livre" in splash_paths:
        dest = PRODUCTS / "body-splash.webp"
        shutil.copy2(splash_paths["body-splash-livre"], dest)
        if PM_MEDIA.is_dir():
            shutil.copy2(dest, PM_MEDIA / "body-splash.webp")
        print("ok body-splash (alias livre)", dest.stat().st_size)


if __name__ == "__main__":
    main()
