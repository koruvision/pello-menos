"""Convert GenerateImage outputs in assets/ to public/images/products/{id}.png"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("PIL not installed", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "scripts" / "product_image_batch.json"


def main() -> None:
    if not JOBS.exists():
        print(f"Missing {JOBS}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(JOBS.read_text(encoding="utf-8"))
    out_dir = Path(data["outDir"])
    assets = Path(data["assetsDir"])
    ok: list[str] = []
    fail: list[str] = []
    for job in data["jobs"]:
        pid = job["id"]
        src_name = job["filename"]
        src = assets / src_name
        if not src.exists():
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                alt = assets / (Path(src_name).stem + ext)
                if alt.exists():
                    src = alt
                    break
        dest = out_dir / f"{pid}.png"
        if not src.exists():
            fail.append(f"{pid}: source missing ({src_name})")
            continue
        try:
            with Image.open(src) as im:
                im = im.convert("RGBA") if im.mode in ("P", "LA") else im.convert("RGB")
                if im.mode == "RGBA":
                    bg = Image.new("RGB", im.size, (255, 255, 255))
                    bg.paste(im, mask=im.split()[3])
                    im = bg
                im.save(dest, "PNG", optimize=True)
            ok.append(str(dest))
        except OSError as e:
            fail.append(f"{pid}: {e}")
    print(json.dumps({"written": len(ok), "paths": ok, "failures": fail}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
