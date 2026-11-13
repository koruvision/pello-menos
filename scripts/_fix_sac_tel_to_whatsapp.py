# -*- coding: utf-8 -*-
"""Troca links SAC tel:0800 por WhatsApp (21) 2549-4265 em pm-home HTML."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"

WA = (
    "https://wa.me/552125494265"
    "?text=Ol%C3%A1!%20Gostaria%20de%20falar%20com%20o%20SAC%20Pello%20Menos."
)
OLD_HREF = 'href="tel:08002821233"'
NEW_HREF = f'href="{WA}" target="_blank" rel="noreferrer"'
OLD_LABEL = "SAC 0800 282 1233"
NEW_LABEL = "SAC WhatsApp (21) 2549-4265"

changed = 0
tel_hits = 0
label_hits = 0
for f in PM.rglob("*.html"):
    text = f.read_text(encoding="utf-8")
    n_tel = text.count("tel:08002821233")
    n_lab = text.count(OLD_LABEL)
    if not n_tel and not n_lab:
        continue
    out = text.replace(OLD_HREF, NEW_HREF)
    # fallback se href já tiver attrs diferentes
    out = out.replace("tel:08002821233", WA)
    out = out.replace(OLD_LABEL, NEW_LABEL)
    if out != text:
        f.write_text(out, encoding="utf-8")
        changed += 1
        tel_hits += n_tel
        label_hits += n_lab

print(f"changed={changed} tel_hits={tel_hits} label_hits={label_hits}")

leftover = []
for f in PM.rglob("*.html"):
    t = f.read_text(encoding="utf-8")
    if "tel:0800" in t or "SAC 0800" in t:
        leftover.append(str(f.relative_to(ROOT)))
print("leftover", len(leftover))
for p in leftover[:20]:
    print(" ", p)
