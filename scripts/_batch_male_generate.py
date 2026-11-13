# -*- coding: utf-8 -*-
"""Emit next batch of GenerateImage payloads (stdout JSON)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from _home_image_specs import prompt_for  # noqa: E402

REF = (
    r"C:\Users\GC1\.cursor\projects\c-Users-GC1-Desktop-pello-menos\assets"
    r"\c__Users_GC1_AppData_Roaming_Cursor_User_workspaceStorage_5fbd0f4a155bce6742dfd1809ecf2a22_images_image-5dd49f35-80a2-4c81-8953-e120dabca8f5.jpg"
)
ASSETS = Path(
    r"C:\Users\GC1\.cursor\projects\c-Users-GC1-Desktop-pello-menos\assets"
)
patterns = ["cera", "laser", "esfolia", "sobrancelha", "design", "barba", "bigode"]
ids = sorted(
    p.stem
    for p in (ROOT / "public/images/products/male").glob("*.png")
    if any(x in p.stem for x in patterns)
)


def pending() -> list[str]:
    out: list[str] = []
    for pid in ids:
        if (ASSETS / f"{pid}-gen.jpg").is_file():
            continue
        if pid == "axila-cera-masc" and (ASSETS / "axila-cera-masc-gen.jpg").is_file():
            continue
        out.append(pid)
    return out


def payload(pid: str) -> dict:
    desc = (
        prompt_for(pid)
        + " Match reference moodboard composition, background color, and dashed oval style."
    )
    return {
        "id": pid,
        "description": desc,
        "filename": f"{pid}-gen.jpg",
        "reference_image_paths": [REF],
        "aspect_ratio": "1:1",
    }


def main() -> None:
    todo = pending()
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    batch = [payload(pid) for pid in todo[:batch_size]]
    print(json.dumps({"pending": len(todo), "batch": batch}, ensure_ascii=False))


if __name__ == "__main__":
    main()
