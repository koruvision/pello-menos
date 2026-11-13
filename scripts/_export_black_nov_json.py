# -*- coding: utf-8 -*-
"""Gera wordpress-loja/pm-home/black-nov-campaign.json (espelho de src/lib/black-nov-campaign.ts)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TS = ROOT / "src" / "lib" / "black-nov-campaign.ts"
OUT = ROOT / "wordpress-loja" / "pm-home" / "black-nov-campaign.json"


def extract_string_array(name: str, text: str) -> list[str]:
    m = re.search(rf"export const {name}: string\[\] = \[([\s\S]*?)\];", text)
    if not m:
        raise SystemExit(f"array {name} não encontrado")
    return re.findall(r'"([^"]+)"', m.group(1))


def main() -> None:
    text = TS.read_text(encoding="utf-8")
    # Datas / números básicos via regex simples no objeto BLACK_NOV
    def field(key: str) -> str:
        m = re.search(rf'{key}:\s*"([^"]+)"', text)
        if not m:
            raise SystemExit(f"campo {key} ausente")
        return m.group(1)

    year_m = re.search(r"year:\s*(\d+)", text)
    payload = {
        "year": int(year_m.group(1)) if year_m else 2026,
        "timezone": "America/Sao_Paulo",
        "esquentaStart": field("esquentaStart"),
        "esquentaEnd": field("esquentaEnd"),
        "blackWeekStart": field("blackWeekStart"),
        "blackWeekEnd": field("blackWeekEnd"),
        "laser": {
            "esquenta": {"any": 0.6, "multi": 0.65},
            "black_week": {"any": 0.7, "multi": 0.75},
        },
        "ceraEsf": {
            "esquenta": {"any": 0.15, "multi": 0.2},
            "black_week_esfoliacao": 0.15,
            "black_week_cera": {"P": 0.4, "M": 0.3, "G": 0.25},
        },
        "multiThreshold": 3,
        "excludeIdPrefixes": ["body-splash", "cartao-presente", "plano-", "produto-1-real"],
        "excludeMethods": ["produto", "presente", "plano", "linha"],
        "ceraTierP": extract_string_array("CERA_TIER_P", text),
        "ceraTierM": extract_string_array("CERA_TIER_M", text),
        "ceraTierG": extract_string_array("CERA_TIER_G", text),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT, "P", len(payload["ceraTierP"]), "M", len(payload["ceraTierM"]), "G", len(payload["ceraTierG"]))


if __name__ == "__main__":
    main()
