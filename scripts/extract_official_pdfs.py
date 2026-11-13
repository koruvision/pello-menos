"""Extract text from official price PDFs."""
from pathlib import Path
from pypdf import PdfReader

root = Path(r"c:\Users\GC1\Desktop\pello-menos\tabelas")
files = list(root.rglob("*.pdf"))
out = Path(r"c:\Users\GC1\Desktop\pello-menos\scripts\_pdf_extract")
out.mkdir(exist_ok=True)
for f in files:
    safe = f.stem.encode("ascii", "ignore").decode()[:40] or "pdf"
    reader = PdfReader(str(f))
    texts = []
    for i, page in enumerate(reader.pages):
        texts.append(f"\n===== PAGE {i+1} =====\n")
        texts.append(page.extract_text() or "")
    dest = out / f"{safe}.txt"
    dest.write_text("".join(texts), encoding="utf-8")
    print("pages", len(reader.pages), "chars", dest.stat().st_size, "file", safe)
