from pathlib import Path
import re

text = Path("src/lib/data.ts").read_text(encoding="utf-8")
block = text.split("const catalogItems")[1].split("function defaultDescription")[0]
items = re.findall(
    r'id: "([^"]+)".*?originalCents: (\d+).*?method: "([^"]+)"(?:, audience: "(masculino)")?',
    block,
    re.S,
)
print("parsed", len(items))
units = re.findall(r'^\s+unit\("([^"]+)"', text, re.M)
print("units", len(units), units)

def cents(n):
    return int(round(float(n) * 100)) if isinstance(n, float) else n

male_laser = {
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
fem_laser = {
    "axilas-laser": 89990,
    "coxas-laser": 219990,
    "perna-laser": 423500,
    "meia-perna-laser": 203000,
    "intergluteos-laser": 47000,
    "areola-laser": 38090,
    "abdomen-laser": 102000,
    "bracos-laser": 144000,
    "antebraco-laser": 108000,
    "costas-laser": 149500,
    "nadegas-laser": 123090,
    "meia-nadega-laser": 70300,
    "pescoco-laser": 70300,
    "orelhas-laser": 43990,
    "virilha-comum-laser": 132000,
    "virilha-faixa-laser": 156000,
    "virilha-cavada-laser": 179000,
    "virilha-cavada-faixa-laser": 203500,
    "virilha-laser": 209000,
    "buco-laser": 42590,
    "queixo-laser": 73300,
    "nariz-laser": 34000,
    "rosto-inteiro-laser": 144500,
    "psd-p-laser": 43000,
    "psd-m-laser": 49500,
    "psd-g-laser": 76900,
}
male_esf = {
    "esfoliacao-faixa-masc": 1850,
    "esfoliacao-braco-masc": 3850,
    "esfoliacao-meia-perna-masc": 3295,
    "esfoliacao-abdomen-masc": 3095,
    "esfoliacao-axilas-masc": 2095,
    "esfoliacao-nadegas-masc": 2795,
    "esfoliacao-coxa-masc": 3245,
    "esfoliacao-costas-masc": 3145,
    "esfoliacao-perna-masc": 5945,
    "esfoliacao-virilha-masc": 3095,
}
fem_esf = {
    "esfoliacao-faixa": 1200,
    "esfoliacao-meio-braco": 2390,
    "esfoliacao-braco": 3390,
    "esfoliacao-meia-perna": 2325,
    "esfoliacao-abdomen": 2750,
    "esfoliacao-axilas": 1590,
    "esfoliacao-meia-nadega": 1195,
    "esfoliacao-nadegas": 2390,
    "esfoliacao-coxa": 2325,
    "esfoliacao-costas": 2600,
    "esfoliacao-perna": 3995,
    "esfoliacao-virilha": 1825,
    "esfoliacao-virilha-faixa": 2425,
    "esfoliacao-seios": 1250,
}

by_id = {i[0]: int(i[1]) for i in items}
mismatch = []
missing = []
for group in (male_laser, fem_laser, male_esf, fem_esf):
    for pid, price in group.items():
        if pid not in by_id:
            missing.append(pid)
        elif by_id[pid] != price:
            mismatch.append((pid, by_id[pid], price))
print("missing", missing)
print("mismatch", mismatch)
print("male laser count", sum(1 for i in items if i[2]=="laser" and i[3]=="masculino"))
print("fem laser count", sum(1 for i in items if i[2]=="laser" and not i[3]))
print("male esf", sum(1 for i in items if i[2]=="esfoliacao" and i[3]=="masculino"))
print("fem esf", sum(1 for i in items if i[2]=="esfoliacao" and not i[3]))
print("forbidden male", [i[0] for i in items if i[0] in {
    "nuca-laser-masc","esfoliacao-meio-braco-masc","esfoliacao-meia-nadega-masc","esfoliacao-virilha-faixa-masc"
}])
