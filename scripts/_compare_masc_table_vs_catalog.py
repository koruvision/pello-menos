# -*- coding: utf-8 -*-
"""Compare Rafael masc cera/esfol/planos table vs existing Next catalog."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")

# Table from Rafael email (ecommerce final, reais)
TABLE_CERA = {
    "ABDOMEN": 57.90,
    "INTERGLÚTEOS": 48.50,
    "AXILA": 38.90,
    "BARBA": 56.90,
    "BARBA (MODELADORA)": 74.90,
    "BRAÇO": 74.00,
    "BIGODE": 38.50,
    "COSTAS": 59.90,
    "COXA": 61.90,
    "FAIXA": 34.00,
    "NADEGAS": 52.50,
    "NARIZ": 32.90,
    "ORELHA": 32.90,
    "1/2 PERNA": 61.90,
    "PERNA INTEIRA": 115.00,
    "PESCOÇO": 32.90,
    "QUEIXO": 32.90,
    "MAMILOS": 32.90,
    "SOBRANCELHA": 52.90,
    "DESIGN DE SOBRANCELHA": 69.90,
    "TÓRAX": 49.90,
    "TÓRAX + ABDÔMEN": 89.90,
    "VIRILHA TOTAL": 88.90,
    "VIRILHA": 58.90,
    "SACO ESCROTAL": 58.90,
}
TABLE_PLAN = {"PLANO VIP SILVER": 124.90, "PLANO VIP GOLD": 129.90}
TABLE_ESFOL = {
    "FAIXA": 17.00,
    "BRAÇO": 37.00,
    "MEIA PERNA": 30.95,
    "ABDOMEN": 28.95,
    "AXILA": 19.45,
    "NADEGAS": 26.25,
    "COXA": 30.95,
    "COSTAS": 29.95,
    "PERNA INTEIRA": 57.50,
    "VIRILHA": 29.45,
}

# Expected mapping table label -> catalog id (what we apply/create)
MAP_CERA = {
    "ABDOMEN": "abdomen-cera-masc",
    "INTERGLÚTEOS": "intergluteos-cera-masc",
    "AXILA": "axila-cera-masc",
    "BARBA": "barba-cera-masc",
    "BARBA (MODELADORA)": "barba-modeladora-cera-masc",
    "BRAÇO": "bracos-cera-masc",
    "BIGODE": "bigode-cera-masc",
    "COSTAS": "costas-cera-masc",
    "COXA": "coxa-cera-masc",
    "FAIXA": "faixa-cera-masc",
    "NADEGAS": "nadegas-cera-masc",
    "NARIZ": "nariz-cera-masc",
    "ORELHA": "orelha-cera-masc",
    "1/2 PERNA": "meia-perna-cera-masc",
    "PERNA INTEIRA": "perna-cera-masc",
    "PESCOÇO": "pescoco-cera-masc",
    "QUEIXO": "queixo-cera-masc",
    "MAMILOS": "mamilos-cera-masc",
    "SOBRANCELHA": "sobrancelha-cera-masc",
    "DESIGN DE SOBRANCELHA": "design-sobrancelha-masc",
    "TÓRAX": "peito-cera-masc",
    "TÓRAX + ABDÔMEN": "torax-abdomen-cera-masc",
    "VIRILHA TOTAL": "virilha-cera-masc",
    "VIRILHA": "virilha-comum-cera-masc",
    "SACO ESCROTAL": "saco-escrotal-cera-masc",
}
MAP_ESFOL = {
    "FAIXA": "esfoliacao-faixa-masc",
    "BRAÇO": "esfoliacao-braco-masc",
    "MEIA PERNA": "esfoliacao-meia-perna-masc",
    "ABDOMEN": "esfoliacao-abdomen-masc",
    "AXILA": "esfoliacao-axilas-masc",
    "NADEGAS": "esfoliacao-nadegas-masc",
    "COXA": "esfoliacao-coxa-masc",
    "COSTAS": "esfoliacao-costas-masc",
    "PERNA INTEIRA": "esfoliacao-perna-masc",
    "VIRILHA": "esfoliacao-virilha-masc",
}
MAP_PLAN = {
    "PLANO VIP SILVER": "plano-silver-masc",
    "PLANO VIP GOLD": "plano-gold-masc",
}


def catalog_masc_seeds():
    chunk = DATA.split("const catalogItems")[1].split("function expandCatalog")[0]
    items = []
    for m in re.finditer(r"\{ id: \"([^\"]+)\"([^}]*)\}", chunk, re.S):
        pid, rest = m.group(1), m.group(2)
        if "audience: \"masculino\"" not in rest and not pid.endswith("-masc"):
            continue
        cents_m = re.search(r"originalCents:\s*(\d+)", rest)
        name_m = re.search(r'name:\s*"([^"]+)"', rest)
        items.append(
            {
                "id": pid,
                "cents": int(cents_m.group(1)) if cents_m else None,
                "name": name_m.group(1) if name_m else "",
            }
        )
    # twin overrides
    for pid, cents in (
        ("plano-silver-masc", 12490),
        ("plano-gold-masc", 12990),
    ):
        if not any(i["id"] == pid for i in items):
            items.append({"id": pid, "cents": cents, "name": pid, "twin": True})
    return items


def kind(pid: str) -> str:
    if "laser" in pid:
        return "laser"
    if "esfoliacao" in pid:
        return "esfol"
    if "plano" in pid:
        return "plano"
    if any(x in pid for x in ("cera", "sobrancelha", "design", "barba", "bigode", "orelha", "pescoco", "mamil", "saco", "peito", "torax")):
        # peito/torax without laser already filtered
        if "laser" in pid:
            return "laser"
        return "cera"
    if pid.endswith("-masc") and "splash" not in pid and "presente" not in pid and "cartao" not in pid:
        return "cera" if "cera" in pid or "design" in pid else "outro"
    return "outro"


def main():
    items = catalog_masc_seeds()
    table_ids = set(MAP_CERA.values()) | set(MAP_ESFOL.values()) | set(MAP_PLAN.values())

    cera = [i for i in items if kind(i["id"]) == "cera" or (
        i["id"].endswith("-masc")
        and "laser" not in i["id"]
        and "esfoliacao" not in i["id"]
        and "plano" not in i["id"]
        and "splash" not in i["id"]
        and "presente" not in i["id"]
        and "cartao" not in i["id"]
        and "body" not in i["id"]
    )]
    esfol = [i for i in items if "esfoliacao" in i["id"]]
    planos = [i for i in items if "plano" in i["id"]]
    laser = [i for i in items if "laser" in i["id"]]
    retail = [i for i in items if any(x in i["id"] for x in ("splash", "presente", "cartao", "body"))]

    print("## Na tabela Rafael mas AUSENTE no catálogo")
    for label, pid in {**MAP_CERA, **{f"ESFOL {k}": v for k, v in MAP_ESFOL.items()}, **MAP_PLAN}.items():
        if not any(i["id"] == pid for i in items) and pid not in (
            # planos are twins — check override / SHARED
            "plano-silver-masc",
            "plano-gold-masc",
        ):
            print(f"  FALTA {label} -> {pid}")
    # planos always twin
    if "SHARED_CHROME_TWIN_OVERRIDES" in DATA and "plano-silver-masc" in DATA:
        print("  (planos silver/gold-masc: twin OK)")

    print("\n## No catálogo cera/esfol/plano masc e NÃO na tabela Rafael")
    for i in sorted(cera + esfol + planos, key=lambda x: x["id"]):
        if i["id"] not in table_ids:
            print(f"  EXTRA {i['id']}\t{i['cents']}\t{i['name']}")

    print("\n## Contagens masc (fora do escopo da tabela e-mail)")
    print(f"  laser masc: {len(laser)}")
    print(f"  retail/gift twins: {len(retail)}")
    print(f"  cera masc total: {len(cera)}")
    print(f"  esfol masc total: {len(esfol)}")


if __name__ == "__main__":
    main()
