# -*- coding: utf-8 -*-
"""
Apply masculine laser prices: originalCents = tabela cheia (até 10 sessões);
bridge regular = tabela; sale legado = round(tabela * 0.95) (Esquenta recalcula 60%/65%).
Also generate origem-precos report.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "lib" / "data.ts"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
BRIDGE_WP = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
REPORT = ROOT / "projeto-migracao" / "historico" / "14-origem-precos-catalogo.md"

ECOMMERCE = 0.05

# Tabela oficial laser masculino — até 10 sessões (cents)
LASER_MASC: dict[str, int] = {
    "abdomen-laser-masc": 109000,
    "axilas-laser-masc": 98000,
    "bracos-laser-masc": 146000,
    "antebraco-laser-masc": 115500,
    "costas-laser-masc": 158000,
    "coxa-laser-masc": 228000,
    "nadegas-laser-masc": 131000,
    "meia-nadega-laser-masc": 78000,
    "meia-perna-laser-masc": 211500,
    "perna-laser-masc": 432000,
    "mamilo-laser-masc": 46000,
    "peito-laser-masc": 142000,
    "torax-abdomen-laser-masc": 236500,
    "pescoco-laser-masc": 78000,
    "intergluteos-laser-masc": 55000,
    "virilha-laser-masc": 139900,
    "virilha-total-laser-masc": 217000,
    "barba-laser-masc": 107000,
    "bigode-laser-masc": 50500,
    "nariz-laser-masc": 41500,
    "orelhas-laser-masc": 52000,
    "queixo-laser-masc": 81000,
    "rosto-inteiro-laser-masc": 159500,
    "psd-p-laser-masc": 50500,
    "psd-m-laser-masc": 58000,
    "psd-g-laser-masc": 85000,
}

# Heroes masculino (formatHeroCampaignPrice base = tabela)
HERO_MASC: dict[str, int] = {
    "axilasLaserMascHero": 98000,
    "peitoHero": 142000,
    "costasHero": 158000,
    "barbaHero": 107000,
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


def sale_cents(regular: int) -> int:
    # Match JS Math.round (half away from zero / half-up for positive).
    return int(regular * (1 - ECOMMERCE) + 0.5)


def patch_data_ts(text: str) -> str:
    for old_cmt, new_cmt in (
        (
            "// Laser masculino — 10 sessões: originalCents = coluna pós-75%; site aplica 5% OFF (ECOMMERCE_DISCOUNT)",
            "// Laser masculino — 10 sessões: originalCents = tabela cheia; Esquenta/Black aplica % sobre a tabela",
        ),
        (
            "// Laser masculino — preço de 10 sessões da tabela oficial (sem 50% de loja; 5% OFF só no e-commerce)",
            "// Laser masculino — 10 sessões: originalCents = tabela cheia; Esquenta/Black aplica % sobre a tabela",
        ),
    ):
        if old_cmt in text:
            text = text.replace(old_cmt, new_cmt)
            break
    for pid, cents in LASER_MASC.items():
        pattern = rf'(id:\s*"{re.escape(pid)}"[^}}]*?originalCents:\s*)\d+'
        new_text, n = re.subn(pattern, rf"\g<1>{cents}", text, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"could not patch originalCents for {pid} (matches={n})")
        text = new_text
    for const_name, cents in HERO_MASC.items():
        pattern = rf"(const {re.escape(const_name)} = formatHeroCampaignPrice\()\d+"
        new_text, n = re.subn(pattern, rf"\g<1>{cents}", text, count=1)
        if n != 1:
            raise SystemExit(f"could not patch hero {const_name} (matches={n})")
        text = new_text
    return text


def patch_bridge(bridge: dict) -> int:
    n = 0
    for pid, regular in LASER_MASC.items():
        row = bridge.get(pid)
        if not row:
            print("WARN missing bridge", pid)
            continue
        sale = sale_cents(regular)
        for side in ("rj", "spdf"):
            if side not in row or not isinstance(row[side], dict):
                row[side] = {}
            row[side]["regularCents"] = regular
            row[side]["saleCents"] = sale
        n += 1
    return n


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


def source_for(pid: str, audience: str, method: str) -> str:
    if pid in LEGADO:
        return "legado-catalogo"
    if pid in LASER_MASC or (pid.endswith("-laser-masc")):
        return "laser-masc-tabela-2026-10"
    if pid in RAFAEL_MASC:
        return "rafael-cera-esfol-planos"
    base = pid[:-5] if pid.endswith("-masc") else pid
    if base in TWIN_CHROME_BASE or method in ("presente", "produto"):
        if audience == "masculino" and pid.endswith("-masc"):
            return "twin-chrome"
        if method in ("presente", "produto"):
            return "twin-chrome"
    return "loja-store"


def parse_catalog(text: str) -> list[dict]:
    chunk = text.split("const catalogItems")[1].split("function expandCatalog")[0]
    items = []
    # Supports one-line `{ id: "..." , ... }` and multiline `{ \n id: "..." \n ... }`
    for m in re.finditer(
        r"\{\s*id:\s*\"([^\"]+)\"(.*?)(?=\n\s*\{|\n\];)",
        chunk,
        re.S,
    ):
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

    # twin overrides from SHARED_CHROME
    overrides = {
        "plano-silver-masc": 12490,
        "plano-gold-masc": 12990,
    }
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
        if twin_id in by_id:
            continue
        if base not in by_id:
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


def brl(cents: int) -> str:
    return f"R$ {cents/100:.2f}".replace(".", ",")


def display_price(item: dict) -> tuple[int, int | None]:
    o = item["originalCents"]
    if item["skipDiscount"]:
        return o, None
    return sale_cents(o), o


def write_report(items: list[dict]):
    lines = [
        "# Origem dos preços do catálogo (e-commerce)",
        "",
        "**Data:** 26/10/2026",
        "",
        "## Legenda das fontes",
        "",
        "| Código | Significado |",
        "|--------|-------------|",
        "| `loja-store` | Espelhado da loja (`loja.pellomenos.com.br` / bridge Woo feminino legado) |",
        "| `rafael-cera-esfol-planos` | E-mail Supervisão → Rafael (já e-commerce; `skipDiscount`) |",
        "| `laser-masc-tabela-2026-10` | Tabela laser masc cheia; Esquenta/Black % sobre a tabela |",
        "| `legado-catalogo` | Seed Next pré-existente (fora do e-mail Rafael) |",
        "| `twin-chrome` | Twin `*-masc` de gift/splash/planos compartilhados |",
        "",
        "Fora da campanha: preço exibido = `skipDiscount` ? original : `round(original × 0,95)`. "
        "Na Esquenta laser: `round(original × 0,40)` (60% OFF) / multi 65%. "
        "Checkout de teste ainda usa `TEST_CHARGE_CENTS` = R$ 1,00.",
        "",
    ]

    method_order = ["cera", "laser", "linha", "esfoliacao", "plano", "presente", "produto"]
    method_labels = {
        "cera": "Cera",
        "laser": "Laser (pacote 10 sessões)",
        "linha": "Linha",
        "esfoliacao": "Esfoliação",
        "plano": "Planos",
        "presente": "Cartão presente",
        "produto": "Produtos (retail)",
    }

    for audience, title in (("feminino", "Feminino"), ("masculino", "Masculino")):
        lines.append(f"## {title}")
        lines.append("")
        subset = [i for i in items if i["audience"] == audience]
        for method in method_order:
            group = [i for i in subset if i["method"] == method]
            if not group:
                continue
            lines.append(f"### {method_labels.get(method, method)}")
            lines.append("")
            lines.append("| ID | Nome | Original | Exibido no site | Fonte |")
            lines.append("|----|------|----------|-----------------|-------|")
            for i in sorted(group, key=lambda x: x["id"]):
                sale, old = display_price(i)
                shown = brl(sale)
                if old is not None:
                    shown = f"{brl(sale)} (de {brl(old)})"
                src = source_for(i["id"], i["audience"], i["method"])
                lines.append(
                    f"| `{i['id']}` | {i['name']} | {brl(i['originalCents'])} | {shown} | `{src}` |"
                )
            lines.append("")

    lines += [
        "## Nota laser masculino",
        "",
        "Base = tabela oficial (até 10 sessões). "
        "Na Esquenta: 60% OFF (1 área) / 65% (≥3). Ex.: Axila R$ 980 → R$ 392.",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("report", REPORT)


def main():
    text = DATA.read_text(encoding="utf-8")
    DATA.write_text(patch_data_ts(text), encoding="utf-8")
    print("patched data.ts laser masc", len(LASER_MASC))

    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    n = patch_bridge(bridge)
    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(BRIDGE, BRIDGE_WP)
    print("patched bridge", n, "keys; copied WP")

    items = parse_catalog(DATA.read_text(encoding="utf-8"))
    write_report(items)
    print("DONE")


if __name__ == "__main__":
    main()
