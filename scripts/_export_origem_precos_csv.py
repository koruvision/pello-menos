# -*- coding: utf-8 -*-
"""Export origem-precos catalog to CSV with human-readable source labels."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "lib" / "data.ts"
OUT_CSV = ROOT / "projeto-migracao" / "historico" / "14-origem-precos-catalogo.csv"
OUT_MD = ROOT / "projeto-migracao" / "historico" / "14-origem-precos-catalogo.md"

ECOMMERCE = 0.05

LASER_MASC = {
    "abdomen-laser-masc",
    "axilas-laser-masc",
    "bracos-laser-masc",
    "antebraco-laser-masc",
    "costas-laser-masc",
    "coxa-laser-masc",
    "nadegas-laser-masc",
    "meia-nadega-laser-masc",
    "meia-perna-laser-masc",
    "perna-laser-masc",
    "mamilo-laser-masc",
    "peito-laser-masc",
    "torax-abdomen-laser-masc",
    "pescoco-laser-masc",
    "intergluteos-laser-masc",
    "virilha-laser-masc",
    "virilha-total-laser-masc",
    "barba-laser-masc",
    "bigode-laser-masc",
    "nariz-laser-masc",
    "orelhas-laser-masc",
    "queixo-laser-masc",
    "rosto-inteiro-laser-masc",
    "psd-p-laser-masc",
    "psd-m-laser-masc",
    "psd-g-laser-masc",
}

RAFAEL_MASC = {
    "peito-cera-masc",
    "abdomen-cera-masc",
    "axila-cera-masc",
    "bracos-cera-masc",
    "costas-cera-masc",
    "coxa-cera-masc",
    "faixa-cera-masc",
    "intergluteos-cera-masc",
    "nadegas-cera-masc",
    "nariz-cera-masc",
    "meia-perna-cera-masc",
    "perna-cera-masc",
    "queixo-cera-masc",
    "virilha-cera-masc",
    "virilha-comum-cera-masc",
    "barba-cera-masc",
    "barba-modeladora-cera-masc",
    "bigode-cera-masc",
    "orelha-cera-masc",
    "pescoco-cera-masc",
    "mamilos-cera-masc",
    "sobrancelha-cera-masc",
    "design-sobrancelha-masc",
    "torax-abdomen-cera-masc",
    "saco-escrotal-cera-masc",
    "esfoliacao-faixa-masc",
    "esfoliacao-braco-masc",
    "esfoliacao-meia-perna-masc",
    "esfoliacao-abdomen-masc",
    "esfoliacao-axilas-masc",
    "esfoliacao-nadegas-masc",
    "esfoliacao-coxa-masc",
    "esfoliacao-costas-masc",
    "esfoliacao-perna-masc",
    "esfoliacao-virilha-masc",
    "plano-silver-masc",
    "plano-gold-masc",
}

LEGADO = {"antebraco-cera-masc", "meia-nadega-cera-masc"}
TWIN_CHROME_BASE = {
    "body-splash",
    "cartao-presente",
    "cartao-presente-160",
    "cartao-presente-215",
    "cartao-presente-290",
}

SOURCE_LABEL = {
    "loja-store": "loja original",
    "rafael-cera-esfol-planos": "e-mail supervisão",
    "laser-masc-tabela-2026-10": "tabela Account Manager",
    "legado-catalogo": "sem fonte",
    "twin-chrome": "fonte extra",
}


def sale_cents(regular: int) -> int:
    return int(regular * (1 - ECOMMERCE) + 0.5)


def brl(cents: int) -> str:
    return f"{cents/100:.2f}".replace(".", ",")


def infer_method(pid: str, rest: str) -> str:
    m = re.search(r'method:\s*"([^"]+)"', rest)
    if m:
        return m.group(1)
    if "laser" in pid:
        return "laser"
    if "esfoliacao" in pid:
        return "esfoliacao"
    if "linha" in pid:
        return "linha"
    if "plano" in pid:
        return "plano"
    if any(x in pid for x in ("presente", "cartao")):
        return "presente"
    if "splash" in pid or "body" in pid:
        return "produto"
    return "cera"


def source_code(pid: str, audience: str, method: str) -> str:
    if pid in LEGADO:
        return "legado-catalogo"
    if pid in LASER_MASC or pid.endswith("-laser-masc"):
        return "laser-masc-tabela-2026-10"
    if pid in RAFAEL_MASC:
        return "rafael-cera-esfol-planos"
    base = pid[:-5] if pid.endswith("-masc") else pid
    if base in TWIN_CHROME_BASE or method in ("presente", "produto"):
        return "twin-chrome"
    return "loja-store"


def parse_catalog(text: str) -> list[dict]:
    chunk = text.split("const catalogItems")[1].split("function expandCatalog")[0]
    items = []
    for m in re.finditer(r"\{\s*id:\s*\"([^\"]+)\"(.*?)(?=\n\s*\{|\n\];)", chunk, re.S):
        pid, rest = m.group(1), m.group(2)
        cents_m = re.search(r"originalCents:\s*(\d+)", rest)
        name_m = re.search(r'name:\s*"([^"]+)"', rest)
        skip = "skipDiscount: true" in rest
        aud_m = re.search(r'audience:\s*"([^"]+)"', rest)
        audience = aud_m.group(1) if aud_m else "feminino"
        method = infer_method(pid, rest)
        original = int(cents_m.group(1)) if cents_m else 0
        items.append(
            {
                "id": pid,
                "name": name_m.group(1) if name_m else pid,
                "originalCents": original,
                "skipDiscount": skip,
                "audience": audience,
                "method": method,
            }
        )

    overrides = {"plano-silver-masc": 12490, "plano-gold-masc": 12990}
    twin_bases = [
        "body-splash",
        "cartao-presente",
        "cartao-presente-160",
        "cartao-presente-215",
        "cartao-presente-290",
        "plano-silver",
        "plano-gold",
        "plano-prepago",
    ]
    by_id = {i["id"]: i for i in items}
    for base in twin_bases:
        twin_id = f"{base}-masc"
        if twin_id in by_id or base not in by_id:
            continue
        src = by_id[base]
        cents = overrides.get(twin_id, src["originalCents"])
        skip = twin_id in overrides or src["skipDiscount"]
        items.append(
            {
                "id": twin_id,
                "name": src["name"] + " (masc)",
                "originalCents": cents,
                "skipDiscount": skip,
                "audience": "masculino",
                "method": src["method"],
            }
        )
    return items


METHOD_LABEL = {
    "cera": "Cera",
    "laser": "Laser",
    "linha": "Linha",
    "esfoliacao": "Esfoliação",
    "plano": "Planos",
    "presente": "Cartão presente",
    "produto": "Produtos (retail)",
}


def display_price(item: dict) -> tuple[str, str]:
    o = item["originalCents"]
    if item["skipDiscount"]:
        return brl(o), brl(o)
    return brl(o), brl(sale_cents(o))


def write_csv(items: list[dict]):
    rows = []
    for i in items:
        code = source_code(i["id"], i["audience"], i["method"])
        orig, shown = display_price(i)
        rows.append(
            {
                "publico": i["audience"],
                "categoria": METHOD_LABEL.get(i["method"], i["method"]),
                "id": i["id"],
                "nome": i["name"],
                "preco_original": orig,
                "preco_exibido_site": shown,
                "fonte": SOURCE_LABEL[code],
            }
        )
    rows.sort(key=lambda r: (r["publico"], r["categoria"], r["id"]))
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "publico",
                "categoria",
                "id",
                "nome",
                "preco_original",
                "preco_exibido_site",
                "fonte",
            ],
            delimiter=";",
        )
        w.writeheader()
        w.writerows(rows)
    print("csv", OUT_CSV, "rows", len(rows))


def write_md(items: list[dict]):
    lines = [
        "# Origem dos preços do catálogo (e-commerce)",
        "",
        "**Data:** 26/10/2026",
        "",
        "## Legenda das fontes",
        "",
        "| Fonte | Significado |",
        "|-------|-------------|",
        "| loja original | Espelhado da loja (`loja.pellomenos.com.br`) |",
        "| e-mail supervisão | E-mail Supervisão → Rafael (cera/esfol/planos masc; já e-commerce) |",
        "| tabela Account Manager | Tabela laser masculino (pós-75% × 5% OFF site) |",
        "| fonte extra | Cartão presente / body splash e clones chrome (fontes pontuais / WhatsApp) |",
        "| sem fonte | Seed legado no catálogo (sem tabela/e-mail desta leva) |",
        "",
        "CSV: `14-origem-precos-catalogo.csv` (separador `;`).",
        "",
        "Preço exibido = sem desconto extra se já veio e-commerce; senão `round(original × 0,95)`.",
        "",
    ]
    method_order = ["cera", "laser", "linha", "esfoliacao", "plano", "presente", "produto"]
    for audience, title in (("feminino", "Feminino"), ("masculino", "Masculino")):
        lines.append(f"## {title}")
        lines.append("")
        subset = [i for i in items if i["audience"] == audience]
        for method in method_order:
            group = [i for i in subset if i["method"] == method]
            if not group:
                continue
            lines.append(f"### {METHOD_LABEL.get(method, method)}")
            lines.append("")
            lines.append("| ID | Nome | Original | Exibido no site | Fonte |")
            lines.append("|----|------|----------|-----------------|-------|")
            for i in sorted(group, key=lambda x: x["id"]):
                orig, shown = display_price(i)
                code = source_code(i["id"], i["audience"], i["method"])
                label = SOURCE_LABEL[code]
                shown_cell = f"R$ {shown}"
                if not i["skipDiscount"]:
                    shown_cell = f"R$ {shown} (de R$ {orig})"
                else:
                    shown_cell = f"R$ {shown}"
                lines.append(
                    f"| `{i['id']}` | {i['name']} | R$ {orig} | {shown_cell} | {label} |"
                )
            lines.append("")
    lines += [
        "## Nota laser masculino",
        "",
        "Base = coluna “desconto” da tabela Account Manager (após 75% sobre o bruto). "
        "O site aplica mais 5%. Ex.: Axila bruto R$ 980 → pós-75% R$ 245 → e-commerce R$ 232,75.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("md", OUT_MD)


def main():
    items = parse_catalog(DATA.read_text(encoding="utf-8"))
    write_csv(items)
    write_md(items)


if __name__ == "__main__":
    main()
