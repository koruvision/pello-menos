"""Emit catalogItems TypeScript from wc_catalog.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WC = json.loads((ROOT / "scripts" / "wc_catalog.json").read_text(encoding="utf-8"))
by_id = {p["id"]: p for p in WC["products"]}

META = {
    "abdomen-cera": ("15 min • Avulso", "corpo", None, False, "Abdômen após cera"),
    "axila-cera": ("15 min • Avulso", "axilas", "Cera", True, "Axila lisa após cera"),
    "antebraco-cera": ("15 min • Avulso", "bracos", None, False, "Antebraço após cera"),
    "bracos-cera": ("20 min • Avulso", "bracos", None, False, "Braços lisos após cera"),
    "buco-cera": ("10 min • Avulso", "rosto", None, True, "Buço após cera"),
    "costas-cera": ("25 min • Avulso", "corpo", None, False, "Costas após cera"),
    "coxa-cera": ("20 min • Avulso", "pernas", None, False, "Coxa após cera"),
    "faixa-cera": ("10 min • Avulso", "corpo", None, False, "Faixa de cera no corpo"),
    "intergluteos-cera": ("15 min • Avulso", "corpo", None, False, "Cera na região dos interglúteos"),
    "nariz-cera": ("10 min • Avulso", "rosto", None, False, "Nariz após cera"),
    "nadegas-cera": ("20 min • Avulso", "corpo", None, False, "Nádegas após cera"),
    "meia-nadega-cera": ("15 min • Avulso", "corpo", "Cera", False, "Meia nádega após cera"),
    "perna-cera": ("40 min • Avulso", "pernas", "5% OFF", True, "Perna inteira após cera"),
    "meia-perna-cera": ("20 min • Avulso", "pernas", None, False, "Meia perna após cera"),
    "queixo-cera": ("10 min • Avulso", "rosto", "Cera", False, "Queixo após cera"),
    "seios-cera": ("10 min • Avulso", "corpo", None, False, "Seios após cera"),
    "virilha-comum-cera": ("15 min • Avulso", "virilha", "Cera", False, "Virilha comum após cera"),
    "virilha-comum-faixa-cera": ("20 min • Avulso", "virilha", None, False, "Virilha comum com faixa após cera"),
    "virilha-cavada-cera": ("20 min • Avulso", "virilha", None, False, "Virilha cavada após cera"),
    "virilha-cavada-faixa-cera": ("25 min • Avulso", "virilha", None, False, "Virilha cavada com faixa após cera"),
    "virilha-modelada-cera": ("25 min • Avulso", "virilha", None, False, "Virilha modelada após cera"),
    "virilha-cera": ("25 min • Avulso", "virilha", None, True, "Virilha total após cera"),
    "labios-genitais-cera": ("15 min • Avulso", "virilha", None, False, "Cera nos lábios genitais"),
    "sobrancelha-cera": ("15 min • Avulso", "sobrancelha", None, False, "Sobrancelha com cera"),
    "sobrancelha-realce-cera": ("25 min • Avulso", "sobrancelha", None, False, "Sobrancelha com realce"),
    "sobrancelha-henna-simples": ("25 min • Avulso", "sobrancelha", None, False, "Sobrancelha simples com henna"),
    "design-sobrancelha": ("20 min • Avulso", "sobrancelha", "Olhar", True, "Design de sobrancelha"),
    "design-sobrancelha-realce": ("30 min • Avulso", "sobrancelha", None, False, "Design de sobrancelha com realce"),
    "sobrancelha-henna": ("30 min • Avulso", "sobrancelha", "Combo", False, "Design de sobrancelha com henna"),
    "realce": ("15 min • Avulso", "sobrancelha", None, False, "Realce de sobrancelha"),
    "henna": ("20 min • Avulso", "sobrancelha", None, False, "Henna nas sobrancelhas"),
    "buco-linha": ("10 min • Avulso", "rosto", "Linha", False, "Buço após linha"),
    "queixo-linha": ("10 min • Avulso", "rosto", "Linha", False, "Queixo após linha"),
    "faixa-linha": ("10 min • Avulso", "rosto", "Linha", False, "Faixa após linha"),
    "axilas-laser": ("15 min • até 10 sessões", "axilas", "5% OFF", True, "Axilas após laser"),
    "areola-laser": ("10 min • até 10 sessões", "corpo", None, False, "Aréola após laser"),
    "buco-laser": ("10 min • até 10 sessões", "rosto", None, False, "Buço após laser"),
    "virilha-laser": ("20 min • até 10 sessões", "virilha", "Mais vendido", True, "Virilha total após laser"),
    "virilha-comum-laser": ("15 min • até 10 sessões", "virilha", None, False, "Virilha comum após laser"),
    "virilha-cavada-laser": ("20 min • até 10 sessões", "virilha", None, False, "Virilha cavada após laser"),
    "virilha-cavada-faixa-laser": ("20 min • até 10 sessões", "virilha", None, False, "Virilha cavada com faixa após laser"),
    "virilha-faixa-laser": ("15 min • até 10 sessões", "virilha", None, False, "Virilha com faixa após laser"),
    "perna-laser": ("40 min • até 10 sessões", "pernas", "Verão", False, "Perna inteira após laser"),
    "meia-perna-laser": ("20 min • até 10 sessões", "pernas", "Verão", True, "Meia perna após laser"),
    "coxas-laser": ("25 min • até 10 sessões", "pernas", None, False, "Coxas após laser"),
    "bracos-laser": ("20 min • até 10 sessões", "bracos", "Novo", True, "Braços após laser"),
    "antebraco-laser": ("15 min • até 10 sessões", "bracos", None, False, "Antebraço após laser"),
    "abdomen-laser": ("20 min • até 10 sessões", "corpo", "Corpo", False, "Abdômen após laser"),
    "costas-laser": ("25 min • até 10 sessões", "corpo", None, False, "Costas após laser"),
    "queixo-laser": ("10 min • até 10 sessões", "rosto", None, False, "Queixo após laser"),
    "pescoco-laser": ("10 min • até 10 sessões", "rosto", None, False, "Pescoço após laser"),
    "nariz-laser": ("10 min • até 10 sessões", "rosto", None, False, "Nariz após laser"),
    "orelhas-laser": ("10 min • até 10 sessões", "rosto", None, False, "Orelhas após laser"),
    "rosto-inteiro-laser": ("20 min • até 10 sessões", "rosto", "Combo", True, "Rosto inteiro após laser"),
    "intergluteos-laser": ("15 min • até 10 sessões", "corpo", None, False, "Interglúteos após laser"),
    "meia-nadega-laser": ("15 min • até 10 sessões", "corpo", None, False, "Meia nádega após laser"),
    "nadegas-laser": ("20 min • até 10 sessões", "corpo", None, False, "Nádegas após laser"),
    "psd-p-laser": ("10 min • até 10 sessões", "corpo", None, False, "Área sem definição P após laser"),
    "psd-m-laser": ("15 min • até 10 sessões", "corpo", None, False, "Área sem definição M após laser"),
    "psd-g-laser": ("20 min • até 10 sessões", "corpo", None, False, "Área sem definição G após laser"),
}

CERA_ORDER = [
    "abdomen-cera", "axila-cera", "antebraco-cera", "bracos-cera", "buco-cera",
    "costas-cera", "coxa-cera", "faixa-cera", "intergluteos-cera", "nariz-cera",
    "nadegas-cera", "meia-nadega-cera", "perna-cera", "meia-perna-cera", "queixo-cera",
    "seios-cera", "virilha-comum-cera", "virilha-comum-faixa-cera", "virilha-cavada-cera",
    "virilha-cavada-faixa-cera", "virilha-modelada-cera", "virilha-cera", "labios-genitais-cera",
    "sobrancelha-cera", "sobrancelha-realce-cera", "sobrancelha-henna-simples",
    "design-sobrancelha", "design-sobrancelha-realce", "sobrancelha-henna", "realce", "henna",
]
LINHA_ORDER = ["buco-linha", "queixo-linha", "faixa-linha"]
LASER_ORDER = [
    "axilas-laser", "areola-laser", "buco-laser", "virilha-laser", "virilha-comum-laser",
    "virilha-cavada-laser", "virilha-cavada-faixa-laser", "virilha-faixa-laser", "perna-laser",
    "meia-perna-laser", "coxas-laser", "bracos-laser", "antebraco-laser", "abdomen-laser",
    "costas-laser", "queixo-laser", "pescoco-laser", "nariz-laser", "orelhas-laser",
    "rosto-inteiro-laser", "intergluteos-laser", "meia-nadega-laser", "nadegas-laser",
    "psd-p-laser", "psd-m-laser", "psd-g-laser",
]

EXPLICIT_METHOD = {
    "realce": "cera",
    "henna": "cera",
    "buco-linha": "linha",
    "queixo-linha": "linha",
    "faixa-linha": "linha",
}


def ts_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def clean_desc(text: str) -> str:
    text = (text or "").replace("\u00a0", " ").strip()
    text = text.replace("Saiba mais aqui!", "").replace("Saiba Mais.", "").strip()
    text = " ".join(text.split())
    if text and not text.endswith((".", "!", "?")):
        text += "."
    return text


def emit_item(pid: str) -> str:
    wc = by_id[pid]
    duration, category, badge, highlight, alt = META[pid]
    name = wc["wcName"].replace(" - ", " – ")
    desc = clean_desc(wc["description"])
    extras = []
    method = EXPLICIT_METHOD.get(pid)
    if method:
        extras.append(f'method: "{method}"')
    if badge:
        extras.append(f'badge: {ts_str(badge)}')
    if highlight:
        extras.append("highlight: true")
    extra = (", " + ", ".join(extras)) if extras else ""
    return (
        f'  {{ id: "{pid}", name: {ts_str(name)}, duration: {ts_str(duration)}, '
        f'originalCents: {wc["originalCents"]}, category: "{category}", '
        f'image: catalogImage("{pid}"), imageAlt: {ts_str(alt)}, '
        f'description: {ts_str(desc)}{extra} }},'
    )


ESFOLIACAO = [
    ("esfoliacao-faixa", "Esfoliação de faixa", "10 min • Avulso", 1400, "corpo", None, False, "Esfoliação de faixa"),
    ("esfoliacao-meio-braco", "Esfoliação de meio braço", "15 min • Avulso", 2595, "bracos", None, False, "Esfoliação de meio braço"),
    ("esfoliacao-braco", "Esfoliação de braço", "20 min • Avulso", 3595, "bracos", None, False, "Esfoliação de braço"),
    ("esfoliacao-meia-perna", "Esfoliação de meia perna", "20 min • Avulso", 2595, "pernas", None, False, "Esfoliação de meia perna"),
    ("esfoliacao-abdomen", "Esfoliação de abdômen", "15 min • Avulso", 2995, "corpo", None, False, "Esfoliação de abdômen"),
    ("esfoliacao-axilas", "Esfoliação de axilas", "15 min • Avulso", 1750, "axilas", "Pele", False, "Esfoliação de axilas"),
    ("esfoliacao-nadegas", "Esfoliação de nádegas", "15 min • Avulso", 2595, "corpo", None, False, "Esfoliação de nádegas"),
    ("esfoliacao-meia-nadega", "Esfoliação de meia nádega", "10 min • Avulso", 1300, "corpo", None, False, "Esfoliação de meia nádega"),
    ("esfoliacao-coxa", "Esfoliação de coxa", "20 min • Avulso", 2595, "pernas", None, False, "Esfoliação de coxa"),
    ("esfoliacao-costas", "Esfoliação de costas", "20 min • Avulso", 2900, "corpo", None, False, "Esfoliação de costas"),
    ("esfoliacao-perna", "Esfoliação de perna inteira", "25 min • Avulso", 4350, "pernas", "Pele", True, "Esfoliação de perna inteira"),
    ("esfoliacao-virilha", "Esfoliação de virilha", "15 min • Avulso", 2000, "virilha", None, False, "Esfoliação de virilha"),
    ("esfoliacao-virilha-faixa", "Esfoliação de virilha + faixa", "20 min • Avulso", 2699, "virilha", None, False, "Esfoliação de virilha com faixa"),
    ("esfoliacao-seios", "Esfoliação de seios", "10 min • Avulso", 1450, "corpo", None, False, "Esfoliação de seios"),
]

MASC_CERA = [
    ("peito-cera-masc", "Peito – Cera", "20 min • Avulso", 5990, "torax", "Cera", True, "Homem após cera no peito Pello Menos"),
    ("abdomen-cera-masc", "Abdômen – Cera", "15 min • Avulso", 5990, "torax", None, False, "Homem após cera no abdômen Pello Menos"),
    ("axila-cera-masc", "Axila – Cera", "15 min • Avulso", 3500, "axilas", "Cera", True, "Homem após cera nas axilas Pello Menos"),
    ("antebraco-cera-masc", "Antebraço – Cera", "15 min • Avulso", 5190, "bracos", None, False, "Homem após cera no antebraço Pello Menos"),
    ("bracos-cera-masc", "Braços – Cera", "20 min • Avulso", 7190, "bracos", None, False, "Homem após cera nos braços Pello Menos"),
    ("costas-cera-masc", "Costas – Cera", "25 min • Avulso", 5800, "corpo", None, True, "Homem após cera nas costas Pello Menos"),
    ("coxa-cera-masc", "Coxa – Cera", "20 min • Avulso", 5190, "pernas", None, False, "Homem após cera na coxa Pello Menos"),
    ("faixa-cera-masc", "Faixa – Cera", "10 min • Avulso", 2800, "corpo", None, False, "Homem após cera na faixa Pello Menos"),
    ("intergluteos-cera-masc", "Interglúteos – Cera", "15 min • Avulso", 3390, "corpo", None, False, "Homem após cera nos interglúteos Pello Menos"),
    ("nariz-cera-masc", "Nariz – Cera", "10 min • Avulso", 3000, "rosto", None, False, "Homem após cera no nariz Pello Menos"),
    ("nadegas-cera-masc", "Nádegas – Cera", "20 min • Avulso", 5190, "corpo", None, False, "Homem após cera nas nádegas Pello Menos"),
    ("meia-nadega-cera-masc", "Meia nádega – Cera", "15 min • Avulso", 2600, "corpo", "Cera", False, "Homem após cera na meia nádega Pello Menos"),
    ("perna-cera-masc", "Perna Inteira – Cera", "40 min • Avulso", 8700, "pernas", "5% OFF", True, "Homem após cera na perna inteira Pello Menos"),
    ("meia-perna-cera-masc", "Meia Perna – Cera", "20 min • Avulso", 5190, "pernas", None, False, "Homem após cera na meia perna Pello Menos"),
    ("queixo-cera-masc", "Queixo – Cera", "10 min • Avulso", 2800, "rosto", "Cera", False, "Homem após cera no queixo Pello Menos"),
    ("virilha-comum-cera-masc", "Virilha comum – Cera", "15 min • Avulso", 3999, "virilha", "Cera", False, "Homem após cera na virilha comum Pello Menos"),
    ("virilha-cera-masc", "Virilha Total – Cera", "25 min • Avulso", 8890, "virilha", None, True, "Homem após cera na virilha total Pello Menos"),
]

MASC_ESF = [
    ("esfoliacao-faixa-masc", "Esfoliação de faixa", "10 min • Avulso", 1400, "corpo", None, False),
    ("esfoliacao-meio-braco-masc", "Esfoliação de meio braço", "15 min • Avulso", 2595, "bracos", None, False),
    ("esfoliacao-braco-masc", "Esfoliação de braço", "20 min • Avulso", 3595, "bracos", None, False),
    ("esfoliacao-meia-perna-masc", "Esfoliação de meia perna", "20 min • Avulso", 2595, "pernas", None, False),
    ("esfoliacao-abdomen-masc", "Esfoliação de abdômen", "15 min • Avulso", 2995, "torax", None, False),
    ("esfoliacao-axilas-masc", "Esfoliação de axilas", "15 min • Avulso", 1750, "axilas", "Pele", False),
    ("esfoliacao-nadegas-masc", "Esfoliação de nádegas", "15 min • Avulso", 2595, "corpo", None, False),
    ("esfoliacao-meia-nadega-masc", "Esfoliação de meia nádega", "10 min • Avulso", 1300, "corpo", None, False),
    ("esfoliacao-coxa-masc", "Esfoliação de coxa", "20 min • Avulso", 2595, "pernas", None, False),
    ("esfoliacao-costas-masc", "Esfoliação de costas", "20 min • Avulso", 2900, "corpo", None, False),
    ("esfoliacao-perna-masc", "Esfoliação de perna inteira", "25 min • Avulso", 4350, "pernas", "Pele", True),
    ("esfoliacao-virilha-masc", "Esfoliação de virilha", "15 min • Avulso", 2000, "virilha", None, False),
    ("esfoliacao-virilha-faixa-masc", "Esfoliação de virilha + faixa", "20 min • Avulso", 2699, "virilha", None, False),
]

MASC_LASER = [
    ("axilas-laser-masc", "Axilas Laser", "15 min • até 10 sessões", 89990, "axilas", "5% OFF", True, "Homem em campanha de laser nas axilas Pello Menos"),
    ("peito-laser-masc", "Peito Laser", "25 min • até 10 sessões", 149500, "torax", "Masculino", True, "Homem em campanha de laser no peito Pello Menos"),
    ("costas-laser-masc", "Costas Laser", "30 min • até 10 sessões", 149500, "corpo", "Masculino", True, "Homem em campanha de laser nas costas Pello Menos"),
    ("abdomen-laser-masc", "Abdômen Laser", "20 min • até 10 sessões", 102000, "torax", None, False, "Homem em campanha de laser no abdômen Pello Menos"),
    ("barba-laser-masc", "Barba Laser", "15 min • até 10 sessões", 99000, "rosto", "Rosto", True, "Homem em campanha de laser na barba Pello Menos"),
    ("nuca-laser-masc", "Nuca Laser", "10 min • até 10 sessões", 70300, "rosto", None, False, "Homem em campanha de laser na nuca Pello Menos"),
    ("pescoco-laser-masc", "Pescoço Laser", "10 min • até 10 sessões", 70300, "rosto", None, False, "Homem em campanha de laser no pescoço Pello Menos"),
    ("orelhas-laser-masc", "Orelhas Laser", "10 min • até 10 sessões", 43990, "rosto", None, False, "Homem em campanha de laser nas orelhas Pello Menos"),
    ("nariz-laser-masc", "Nariz Laser", "10 min • até 10 sessões", 34000, "rosto", None, False, "Homem em campanha de laser no nariz Pello Menos"),
    ("bracos-laser-masc", "Braços Inteiros Laser", "20 min • até 10 sessões", 144000, "bracos", None, False, "Homem em campanha de laser nos braços Pello Menos"),
    ("antebraco-laser-masc", "Antebraço Laser", "15 min • até 10 sessões", 108000, "bracos", None, False, "Homem em campanha de laser no antebraço Pello Menos"),
    ("perna-laser-masc", "Perna Inteira Laser", "40 min • até 10 sessões", 423500, "pernas", "Verão", False, "Homem em campanha de laser nas pernas Pello Menos"),
    ("meia-perna-laser-masc", "Meia Perna Laser", "20 min • até 10 sessões", 203000, "pernas", None, False, "Homem em campanha de laser na meia perna Pello Menos"),
    ("virilha-laser-masc", "Virilha Laser", "20 min • até 10 sessões", 209000, "virilha", None, False, "Homem em campanha de laser na virilha Pello Menos"),
]


def emit_simple(pid, name, duration, cents, category, badge, highlight, alt, audience=None, method=None, desc=None):
    extras = []
    if method:
        extras.append(f'method: "{method}"')
    if audience:
        extras.append(f'audience: "{audience}"')
    if badge:
        extras.append(f'badge: {ts_str(badge)}')
    if highlight:
        extras.append("highlight: true")
    extra = (", " + ", ".join(extras)) if extras else ""
    desc_part = f", description: {ts_str(desc)}" if desc else ""
    audience_arg = ', "masculino"' if audience == "masculino" else ""
    img = f'catalogImage("{pid}"{audience_arg})'
    return (
        f'  {{ id: "{pid}", name: {ts_str(name)}, duration: {ts_str(duration)}, '
        f'originalCents: {cents}, category: "{category}", image: {img}, '
        f'imageAlt: {ts_str(alt)}{desc_part}{extra} }},'
    )


lines = ["const catalogItems: ProductSeed[] = [", "  // Cera / laser / linha feminino — nomes, preços Copacabana I e descrições do CSV da loja"]
for pid in CERA_ORDER:
    lines.append(emit_item(pid))
lines += ["", "  // Linha feminino"]
for pid in LINHA_ORDER:
    lines.append(emit_item(pid))
lines += ["", "  // Esfoliação feminino — tabela atual, fora do CSV"]
for row in ESFOLIACAO:
    pid, name, duration, cents, cat, badge, hl, alt = row
    lines.append(emit_simple(pid, name, duration, cents, cat, badge, hl, alt, method="esfoliacao"))
lines += ["", "  // Laser feminino"]
for pid in LASER_ORDER:
    lines.append(emit_item(pid))

lines.append(
    """
  // Produto oficial, planos e presente
  { id: "body-splash", name: "Body Splash Pello Menos", duration: "Uso diário", originalCents: 6900, badge: "Oficial", category: "produtos", method: "produto", image: catalogImage("body-splash"), imageAlt: "Body Splash oficial Pello Menos" },
  {
    id: "cartao-presente",
    name: "Cartão Presente",
    duration: "Vale presente",
    originalCents: 20000,
    skipDiscount: true,
    badge: "Presente",
    highlight: true,
    category: "produtos",
    method: "presente",
    image: catalogImage("cartao-presente"),
    imageAlt: "Cartão Presente Pello Menos",
    description:
      "Cartão Presente Pello Menos para presentear com serviços de depilação. Informe a unidade onde o presente será usado.",
  },
  {
    id: "plano-silver",
    name: "Plano de Assinatura VIP – Silver",
    duration: "1ª parcela • mensal",
    originalCents: 10990,
    skipDiscount: true,
    badge: "Silver",
    highlight: true,
    category: "produtos",
    method: "plano",
    image: catalogImage("plano-silver"),
    imageAlt: "Plano de assinatura VIP Silver Cera Pello Menos",
    description:
      "Como assinante Vip Silver você depila 3 áreas a cera (axila + 1/2 perna + qualquer virilha) por um valor fixo mensal, com 10% em serviços extras. A compra no e-commerce é a primeira parcela: depois cadastre a recorrência na loja escolhida.",
  },
  {
    id: "plano-gold",
    name: "Plano de Assinatura VIP – Gold",
    duration: "1ª parcela • mensal",
    originalCents: 11490,
    skipDiscount: true,
    badge: "Gold",
    highlight: true,
    category: "produtos",
    method: "plano",
    image: catalogImage("plano-gold"),
    imageAlt: "Plano de assinatura VIP Gold Cera Pello Menos",
    description:
      "No Vip Gold você escolhe os serviços de cera da sessão mensal. Exceto sobrancelha; perna inteira conta como 2 serviços. A compra no e-commerce é a primeira parcela: depois cadastre a recorrência na loja escolhida.",
  },
  {
    id: "plano-clube-laser",
    name: "Clube do Laser",
    duration: "1ª parcela • mensal",
    originalCents: 24990,
    skipDiscount: true,
    badge: "Laser",
    highlight: true,
    category: "produtos",
    method: "plano",
    image: catalogImage("plano-clube-laser"),
    imageAlt: "Clube de Laser Pello Menos",
    description:
      "Assinatura mensal de laser por R$ 249,90, com fidelidade mínima de 5 meses. Até 8 áreas no mês, sem hora marcada. A compra no e-commerce é a primeira parcela: depois cadastre a recorrência do clube na loja escolhida.",
  },
  {
    id: "plano-prepago",
    name: "Pré-pago Pello Menos",
    duration: "Compra única • 3 sessões",
    originalCents: 34470,
    skipDiscount: true,
    badge: "Pré-pago",
    highlight: true,
    category: "produtos",
    method: "plano",
    image: catalogImage("plano-prepago"),
    imageAlt: "Plano Pré-pago Pello Menos",
    description:
      "Pacote pré-pago de cera em compra única: 3 sessões, com até 3 serviços por visita. Perna inteira conta como 2 serviços; sobrancelha não entra. Informe a unidade no pedido e use na loja escolhida.",
  },
"""
)

lines.append("  // Cera masculino — áreas da tabela RJ-SP para homem; preço cartão + 5% OFF no site")
for row in MASC_CERA:
    lines.append(emit_simple(*row, audience="masculino", method="cera"))
lines.append("")
lines.append("  // Esfoliação masculino — áreas equivalentes da tabela, sem seios")
for pid, name, duration, cents, cat, badge, hl in MASC_ESF:
    lines.append(
        emit_simple(
            pid, name, duration, cents, cat, badge, hl,
            f"{name} masculina Pello Menos",
            audience="masculino",
            method="esfoliacao",
        )
    )
lines.append("")
lines.append("  // Laser masculino — original da tabela/loja para a área equivalente")
for row in MASC_LASER:
    lines.append(emit_simple(*row, audience="masculino", method="laser"))
lines.append("];")

out = ROOT / "scripts" / "_catalog_fragment.ts"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wrote", out, "lines", len(lines))
print("csv products", len(CERA_ORDER) + len(LINHA_ORDER) + len(LASER_ORDER))
