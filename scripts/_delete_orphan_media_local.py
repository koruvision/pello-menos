# -*- coding: utf-8 -*-
"""Apaga órfãos do relatório em media/ e espelho em public/images/."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "scripts" / "_orphan_media_report.json"
MEDIA = ROOT / "wordpress-loja" / "pm-home" / "media"
PUBLIC_IMAGES = ROOT / "public" / "images"


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    orphans = report.get("orphans") or []
    freed = 0
    deleted = 0
    missing = 0
    for row in orphans:
        rel = row["rel"]
        # media path: images/hero/... -> MEDIA/images/hero/...
        media_path = MEDIA / rel
        if media_path.is_file():
            freed += media_path.stat().st_size
            media_path.unlink()
            deleted += 1
            print("DEL media", rel)
        else:
            missing += 1
            print("MISS media", rel)
        # public mirror: images/hero/foo -> public/images/hero/foo
        if rel.startswith("images/"):
            pub = PUBLIC_IMAGES / rel[len("images/") :]
            if pub.is_file():
                freed += pub.stat().st_size
                pub.unlink()
                deleted += 1
                print("DEL public", pub.relative_to(ROOT).as_posix())
    print("deleted", deleted, "missing", missing, "freed_bytes", freed)


if __name__ == "__main__":
    main()
