# -*- coding: utf-8 -*-
"""Baixa só produtos cujo WebP dedicado ainda não existe."""
from __future__ import annotations

import sync_drive_product_images as sync

ids = sync.product_ids()
files = []
for audience, folder_id in sync.resolve_drive_roots().items():
    files.extend(sync.walk(folder_id, audience, audience.upper()))

used = set()
n = 0
for file in files:
    pid = sync.target_id(file, ids)
    if not pid or pid in used:
        continue
    audience = ids[pid]
    folder = sync.PRODUCTS / "male" if audience == "masculino" else sync.PRODUCTS
    dest = folder / f"{pid}.webp"
    used.add(pid)
    if dest.is_file() and dest.stat().st_size > 1000:
        continue
    try:
        raw = sync.download(file["id"])
        size = sync.to_webp(raw, dest)
        print(f"ok {pid} {size} {dest.stat().st_size}")
        n += 1
    except Exception as err:
        print(f"fail {pid} {err}")
print(f"downloaded {n}")
