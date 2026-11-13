# -*- coding: utf-8 -*-
"""Ensure every /images/... path referenced in src or pm-home HTML exists under media/images."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public" / "images"
MEDIA = ROOT / "wordpress-loja" / "pm-home" / "media" / "images"
PM = ROOT / "wordpress-loja" / "pm-home"

pat = re.compile(r"/images/([A-Za-z0-9_./\-]+\.(?:png|jpg|jpeg|webp|gif|svg))", re.I)
refs: set[str] = set()
for base in (ROOT / "src", PM):
    for path in base.rglob("*"):
        if path.suffix.lower() not in {".ts", ".tsx", ".js", ".html", ".json", ".css"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        refs.update(pat.findall(text))

print("image refs", len(refs))
missing = []
restored = 0
for rel in sorted(refs):
    rel = rel.replace("\\", "/")
    src = PUBLIC / rel
    dest = MEDIA / rel
    if dest.exists():
        continue
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        restored += 1
        print("RESTORE", rel, src.stat().st_size)
    else:
        missing.append(rel)
        print("MISSING", rel)

print("restored", restored, "still_missing", len(missing))
