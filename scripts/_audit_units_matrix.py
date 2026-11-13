# -*- coding: utf-8 -*-
"""Read-only: print storeUnits capacity matrix for chat delivery."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"

# Parse unit("CODE", "Name", ... offersCera, offersLaser, offersCeraMasculino, offersLaserMasculino)
pat = re.compile(
    r'unit\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]*)"\s*,\s*'
    r"(true|false)\s*,\s*(true|false)\s*,\s*(true|false)\s*,\s*(true|false)",
    re.M,
)
rows = []
for m in pat.finditer(DATA):
    code, name, city, state, addr, cf, lf, cm, lm = m.groups()
    rows.append(
        {
            "code": code,
            "id": code.lower().replace(" ", "-"),
            "name": name,
            "city": city,
            "state": state,
            "cera_fem": cf == "true",
            "laser_fem": lf == "true",
            "cera_masc": cm == "true",
            "laser_masc": lm == "true",
        }
    )

assert len(rows) == 37, f"expected 37 units, got {len(rows)}"

# Bridge intersection sample: count units keys for representative SKUs
import json

bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
samples = {
    "axila-cera": "cera_fem",
    "axilas-laser": "laser_fem",
    "axila-cera-masc": "cera_masc",
    "axilas-laser-masc": "laser_masc",
    "plano-clube-laser": "laser_fem",
    "produto-1-real": "cera_fem",
}
print("=== BRIDGE SAMPLE UNIT COUNTS ===")
for pid, flag in samples.items():
    row = bridge.get(pid) or {}
    units = row.get("units") or {}
    print(f"{pid}: bridge_units={len(units)} (capacity flag={flag})")

print("\n=== MATRIX BY UNIT (UI capacity) ===")
print("Sempre disponíveis em todas: linha, esfoliação (fem), gift, retail/body-splash.")
print("produto-1-real: segue capacidade de cera feminina (todas as 37).\n")

groups = {
    "so_cera_fem": [],
    "cera_laser_fem": [],
    "cera_fem_masc_sem_laser": [],
    "cera_laser_fem_cera_masc": [],
    "full": [],
}

for u in rows:
    flags = []
    if u["cera_fem"]:
        flags.append("Cera feminina (+ planos cera fem + teste R$1)")
    if u["laser_fem"]:
        flags.append("Laser feminino (+ Clube Laser)")
    if u["cera_masc"]:
        flags.append("Cera/esfoliação/planos masculinos")
    if u["laser_masc"]:
        flags.append("Laser masculino")

    line = f"- {u['code']} — {u['name']} ({u['city']}/{u['state']}): " + "; ".join(flags)
    print(line)

    if u["laser_masc"]:
        groups["full"].append(u["code"])
    elif u["cera_masc"] and u["laser_fem"]:
        groups["cera_laser_fem_cera_masc"].append(u["code"])
    elif u["cera_masc"] and not u["laser_fem"]:
        groups["cera_fem_masc_sem_laser"].append(u["code"])
    elif u["laser_fem"]:
        groups["cera_laser_fem"].append(u["code"])
    else:
        groups["so_cera_fem"].append(u["code"])

print("\n=== COUNTS ===")
print("só cera fem:", len(groups["so_cera_fem"]), groups["so_cera_fem"])
print("cera+laser fem:", len(groups["cera_laser_fem"]), groups["cera_laser_fem"])
print("cera fem+masc sem laser:", len(groups["cera_fem_masc_sem_laser"]), groups["cera_fem_masc_sem_laser"])
print("cera+laser fem + cera masc (sem laser masc):", len(groups["cera_laser_fem_cera_masc"]), groups["cera_laser_fem_cera_masc"])
print("full:", len(groups["full"]), groups["full"])
print("laser_fem total", sum(1 for u in rows if u["laser_fem"]))
print("cera_masc total", sum(1 for u in rows if u["cera_masc"]))
print("laser_masc total", sum(1 for u in rows if u["laser_masc"]))
