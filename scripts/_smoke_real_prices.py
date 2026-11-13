# -*- coding: utf-8 -*-
"""Smoke: TEST_CHARGE off; produto-1-real stays R$1; sample catalog prices real."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")

m = re.search(r"export const TEST_CHARGE_CENTS = (\d+)", DATA)
assert m and m.group(1) == "0", f"TEST_CHARGE_CENTS expected 0, got {m.group(1) if m else None}"

# Seed produto-1-real
m1 = re.search(
    r'id: "produto-1-real"[\s\S]*?originalCents: (\d+)[\s\S]*?skipDiscount: true',
    DATA,
)
assert m1 and m1.group(1) == "100", "produto-1-real must stay 100 + skipDiscount"

samples = {
    "axilas-laser": None,
    "axila-cera-masc": None,
    "axilas-laser-masc": None,
    "antebraco-cera-masc": None,
}
for pid in samples:
    mm = re.search(rf'id: "{pid}"[^}}]*originalCents: (\d+)', DATA)
    assert mm, f"missing {pid}"
    cents = int(mm.group(1))
    assert cents != 100 or pid == "produto-1-real", f"{pid} still looks like test price: {cents}"
    samples[pid] = cents

print("OK TEST_CHARGE=0")
print("OK produto-1-real=100 skipDiscount")
for k, v in samples.items():
    print(f"OK {k}={v}")
