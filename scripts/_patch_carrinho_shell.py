# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "wordpress-loja" / "pm-home"
OLD = (
    "mx-auto flex w-full max-w-xl flex-1 flex-col items-center justify-center "
    "px-container-margin py-16 text-center sm:py-20 md:py-24"
)
NEW = (
    "mx-auto flex w-full max-w-xl flex-col items-center justify-center "
    "px-container-margin py-24 text-center sm:py-28 md:py-32 "
    "min-h-[calc(100dvh-8rem)] sm:min-h-[calc(100dvh-7.5rem)] md:min-h-[calc(100dvh-7rem)]"
)

n = 0
for path in [ROOT / "carrinho.html", *ROOT.rglob("*.html")]:
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    orig = text
    if OLD in text:
        text = text.replace(OLD, NEW)
    text = text.replace("cart.js?v=cart12", "cart.js?v=cart13")
    if text != orig:
        path.write_text(text, encoding="utf-8")
        n += 1
        print("patched", path.relative_to(ROOT))
print("files", n)
