# -*- coding: utf-8 -*-
"""Compare storeUnits capacity vs woo-bridge unit keys for sample SKUs."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")
bridge = json.loads((ROOT / "src" / "lib" / "woo-bridge.json").read_text(encoding="utf-8"))

pat = re.compile(
    r'unit\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"[^"]+"\s*,\s*"[^"]+"\s*,\s*"[^"]*"\s*,\s*'
    r"(true|false)\s*,\s*(true|false)\s*,\s*(true|false)\s*,\s*(true|false)",
)
units = []
for m in pat.finditer(DATA):
    code, name, cf, lf, cm, lm = m.groups()
    uid = code.lower().replace(" ", "-")
    units.append(
        {
            "id": uid,
            "code": code,
            "name": name,
            "cera_fem": cf == "true",
            "laser_fem": lf == "true",
            "cera_masc": cm == "true",
            "laser_masc": lm == "true",
        }
    )


def ids(flag: str):
    return {u["id"] for u in units if u[flag]}


checks = [
    ("axila-cera", "cera_fem"),
    ("axilas-laser", "laser_fem"),
    ("plano-clube-laser", "laser_fem"),
    ("axila-cera-masc", "cera_masc"),
    ("axilas-laser-masc", "laser_masc"),
    ("produto-1-real", "cera_fem"),
]

for pid, flag in checks:
    row = bridge.get(pid) or {}
    bkeys = set((row.get("units") or {}).keys())
    expected = ids(flag)
    missing = sorted(expected - bkeys)
    extra = sorted(bkeys - expected)
    print(f"\n{pid} capacity={len(expected)} bridge={len(bkeys)}")
    if not bkeys:
        print("  (bridge units empty → UI falls back to capacity list)")
    if missing:
        print("  missing in bridge:", ", ".join(missing))
    if extra:
        print("  extra in bridge:", ", ".join(extra))
    if bkeys and not missing and not extra:
        print("  OK exact match")

# abdomen-laser-masc longText audience leak
row = bridge.get("abdomen-laser-masc") or {}
lt = row.get("longText") or ""
print("\nabdomen-laser-masc longText has 'feminino':", "feminino" in lt.lower())
print("product-copy is preferred for UI when present; bridge leak noted only.")
