# -*- coding: utf-8 -*-
"""Relatório somente-leitura: storeUnits × tokens AccesStage (não altera nada)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CODE_TO_SLUG = {
    "APE": "afonsopena",
    "BON": "bonsucesso",
    "CAX": "caxias",
    "CGR2": "campogrande",
    "DF-ASU": "asasul",
    "DF-ANO": "asanorte",
    "LEB2": "leblon2",
    "MAD": "madureira",
    "MEI": "meier",
    "SNP": "saenspena",
    "SJM": "saojoaomeriti",
    "SJO": "saojose",
    "TON": "copacabana1",
    "IPA": "ipanema",
    "NIG": "novaiguacu",
    "13M": "trezemaio",
    "REC": "recreio",
    "SP-AUG": "augusta",
    "SP-AVP": "paulista",
    "CEN": "goncalvesdias",
    "NIL": "nilopolis",
    "LMA": "largomachado",
    "SP-SJC": "saojosecampos",
    "PET": "petropolis",
    "IG02": "ilhagovernador2",
    "HUT": "humaita",
    "URG": "uruguai",
    "BAN": "bangu",
    "BOT": "botafogo",
    "COPA-2": "copacabana2",
    "EBA": "estradabandeirantes",
    "FLA": "flamengo",
    "FRE": "freguesia",
    "ICA": "icarai",
    "LBI": "largobicao",
    "NIG2": "novaiguacu2",
}


def main() -> None:
    text = (ROOT / "src/lib/data.ts").read_text(encoding="utf-8")
    units = []
    for m in re.finditer(
        r'unit\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"',
        text,
    ):
        units.append(
            {
                "code": m.group(1),
                "name": m.group(2),
                "city": m.group(3),
                "state": m.group(4),
            }
        )

    keys = json.loads(
        (ROOT / "projeto-migracao/.secrets/_accesstage_unit_keys_sanitized.json").read_text(
            encoding="utf-8"
        )
    )
    acces = {r["slug"] for r in keys["rows"] if r.get("has_api") and r.get("has_apikey")}

    inv_path = ROOT / "projeto-migracao/.secrets/_inventory_accesstage_units.json"
    cf7_unit = []
    if inv_path.is_file():
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        cf7_unit = [o["slug"] for o in inv.get("cf7", {}).get("loja", {}).get("unit") or []]

    print("CATALOGO_COUNT", len(units))
    print("TOKEN_COUNT", len(acces))
    print("CF7_UNIT_COUNT", len(cf7_unit))
    print("---RELACAO---")
    without = []
    with_tok = []
    for u in units:
        slug = CODE_TO_SLUG.get(u["code"])
        has = bool(slug and slug in acces)
        if u["code"] == "SJO" and ("saojose" in acces or "rjsaojose" in acces):
            has = True
            slug = "saojose"
        status = "COM_TOKEN" if has else "SEM_TOKEN"
        in_cf7 = "CF7_SIM" if slug in cf7_unit else "CF7_NAO"
        print(f"{u['code']}\t{u['name']}\t{u['state']}\t{slug or '-'}\t{status}\t{in_cf7}")
        (with_tok if has else without).append(u["code"])

    print("---SEM_TOKEN_NO_CATALOGO---")
    print(",".join(without) if without else "(nenhuma)")
    print("---SJM_NO_CATALOGO---")
    print("sim" if any(u["code"] == "SJM" for u in units) else "nao")
    print("---TOKEN_FORA_DO_CATALOGO---")
    mapped = set(CODE_TO_SLUG.values())
    # if SJM not in catalog, still count mapping for orphan detection using full map
    orphans = sorted(acces - mapped)
    for s in orphans:
        where = "cf7" if s in cf7_unit else "so_accesstage"
        print(f"{s}\t{where}")
    print("---CF7_SEM_TOKEN---")
    print(",".join(s for s in cf7_unit if s not in acces) or "(nenhuma)")


if __name__ == "__main__":
    main()
