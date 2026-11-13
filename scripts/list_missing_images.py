from pathlib import Path
import re
from datetime import datetime

ROOT = Path(r"c:\Users\GC1\Desktop\pello-menos")
SRC = Path(r"C:\Users\GC1\.cursor\projects\c-Users-GC1-Desktop-pello-menos\assets")
DST = ROOT / "public" / "images" / "products"
CUTOFF = datetime(2026, 9, 14, 20, 59, 0).timestamp()
text = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")
block = text.split("const catalogItems")[1].split("function defaultDescription")[0]
items = re.findall(r'catalogImage\("([^"]+)"(?:, "(masculino)")?\)', block)
wanted = {img: (aud == "masculino") for img, aud in items}
print("skus", len(wanted))
src_files = {p.stem: p for p in SRC.glob("*.png")}
print("assets png", len(src_files))
fresh = [s for s, p in src_files.items() if p.stat().st_mtime >= CUTOFF]
print("fresh since cutoff", len(fresh))
missing = [img for img in wanted if img not in src_files or src_files[img].stat().st_mtime < CUTOFF]
print("missing or stale", len(missing))
print("---MISSING---")
print("\n".join(missing))
pub = (
    list(DST.glob("*.png"))
    + list((DST / "male").glob("*.png"))
    + list(DST.glob("*.jpg"))
    + list((DST / "male").glob("*.jpg"))
)
print("---PUBLIC---")
print("public count", len(pub))
