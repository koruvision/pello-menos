from pathlib import Path
import re
import shutil
from datetime import datetime

ROOT = Path(r"c:\Users\GC1\Desktop\pello-menos")
SRC = Path(r"C:\Users\GC1\.cursor\projects\c-Users-GC1-Desktop-pello-menos\assets")
DST = ROOT / "public" / "images" / "products"
DST_M = DST / "male"
CUTOFF = datetime(2026, 9, 14, 20, 59, 0).timestamp()
text = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")
block = text.split("const catalogItems")[1].split("function defaultDescription")[0]
items = re.findall(r'catalogImage\("([^"]+)"(?:, "(masculino)")?\)', block)
wanted = {img: (aud == "masculino") for img, aud in items}

for folder in (DST, DST_M):
    folder.mkdir(parents=True, exist_ok=True)
    for p in list(folder.glob("*.png")) + list(folder.glob("*.jpg")):
        p.unlink()

copied = []
missing_src = []
for img, is_male in wanted.items():
    src = SRC / f"{img}.png"
    dest = (DST_M if is_male else DST) / f"{img}.png"
    if src.exists() and src.stat().st_mtime >= CUTOFF:
        shutil.copy2(src, dest)
        copied.append(img)
    else:
        missing_src.append(img)
print("skus", len(wanted))
print("copied", len(copied))
print("missing", len(missing_src))
print("\n".join(missing_src))
