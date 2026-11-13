# -*- coding: utf-8 -*-
"""Troca APENAS os links de SAC (wa.me/552125494265?text=...SAC...) pelo numero oficial
0800 282 1233 e ajusta o rotulo visivel "SAC WhatsApp (21) 2549-4265".

Os demais links de WhatsApp (duvidas/atendimento/widget) NAO sao tocados.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"

OLD_URL = "https://wa.me/552125494265?text=Ol%C3%A1!%20Gostaria%20de%20falar%20com%20o%20SAC%20Pello%20Menos."
NEW_URL = "https://api.whatsapp.com/send?phone=08002821233&text=Ol%C3%A1!%20Gostaria%20de%20falar%20com%20o%20SAC%20Pello%20Menos."
OLD_LABEL = "SAC WhatsApp (21) 2549-4265"
NEW_LABEL = "SAC WhatsApp 0800 282 1233"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    changed = []
    total_url = total_label = 0
    for f in sorted(PM.rglob("*.html")):
        s = f.read_text(encoding="utf-8", errors="strict")
        nu = s.count(OLD_URL)
        nl = s.count(OLD_LABEL)
        if not nu and not nl:
            continue
        new = s.replace(OLD_URL, NEW_URL).replace(OLD_LABEL, NEW_LABEL)
        changed.append({"file": str(f.relative_to(PM)), "url": nu, "label": nl})
        total_url += nu
        total_label += nl
        if args.write:
            f.write_text(new, encoding="utf-8")

    print("arquivos afetados:", len(changed))
    print("links SAC trocados:", total_url)
    print("rotulos trocados:", total_label)
    for c in changed[:8]:
        print("  ", c)

    # confere que nenhum link generico foi tocado
    gen = 0
    for f in sorted(PM.rglob("*.html")):
        gen += f.read_text(encoding="utf-8", errors="replace").count(
            "https://wa.me/552125494265?text=Ol%C3%A1!%20Quero%20tirar%20d%C3%BAvidas"
        )
    print("links genericos (intocados):", gen)

    (ROOT / "scripts" / "_sac_links_report.json").write_text(
        json.dumps({"changed": changed, "total_url": total_url, "total_label": total_label},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.write:
        print("(dry-run; use --write)")


if __name__ == "__main__":
    main()