# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "wordpress-loja" / "pm-home"
OLD_HREF = "https://wa.me/?text="
NEW_HREF = "https://wa.me/552125494265?text="
OLD_LABEL = "Whatsapp Sac Pello Menos"
NEW_LABEL = "WhatsApp (21) 2549-4265"
# encoded versions that appear in static HTML
OLD_ENC = "https://wa.me/?text=Ol%C3%A1!%20Gostaria%20de%20falar%20com%20o%20SAC%20Pello%20Menos."
NEW_ENC = (
    "https://wa.me/552125494265?text=Ol%C3%A1!%20Gostaria%20de%20falar%20com%20o%20SAC%20Pello%20Menos."
)

n_files = 0
n_href = n_label = n_wa = 0
for path in list(ROOT.rglob("*.html")) + list(ROOT.rglob("*.js")):
    text = path.read_text(encoding="utf-8")
    orig = text
    c1 = text.count(OLD_HREF)
    if c1:
        text = text.replace(OLD_HREF, NEW_HREF)
        n_href += c1
    c2 = text.count(OLD_ENC)
    if c2:
        text = text.replace(OLD_ENC, NEW_ENC)
        n_href += c2
    c3 = text.count(OLD_LABEL)
    if c3:
        text = text.replace(OLD_LABEL, NEW_LABEL)
        n_label += c3
    c4 = text.count("whatsapp-float.js?v=wa5")
    if c4:
        text = text.replace("whatsapp-float.js?v=wa5", "whatsapp-float.js?v=wa6")
        n_wa += c4
    if text != orig:
        path.write_text(text, encoding="utf-8")
        n_files += 1

print("files", n_files, "href", n_href, "label", n_label, "wa bump", n_wa)
