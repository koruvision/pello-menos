# -*- coding: utf-8 -*-
"""Smoke: getProductById-equivalent seed + quoteFor-equivalent bridge for key masc SKUs."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = json.loads((ROOT / "src/lib/woo-bridge.json").read_text(encoding="utf-8"))
DATA = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")

# Mimic quoteFor: prefer bridge[id], else bridge[base], then seed.
EXPECT = {
    "axila-cera-masc": 3890,
    "perna-cera-masc": 11500,
    "plano-silver-masc": 12490,
    "esfoliacao-axilas-masc": 1945,
    "abdomen-cera-masc": 5790,
}


def product_bridge(pid: str):
    if pid in BRIDGE:
        return BRIDGE[pid]
    if pid.endswith("-masc"):
        return BRIDGE.get(pid[:-5])
    return None


def seed_cents(pid: str) -> int | None:
    # twin override
    m = re.search(
        rf'"{re.escape(pid)}":\s*\{{[^}}]*originalCents:\s*(\d+)',
        DATA,
    )
    if m:
        return int(m.group(1))
    m = re.search(rf'id:\s*"{re.escape(pid)}"[^}}]*?originalCents:\s*(\d+)', DATA, re.S)
    return int(m.group(1)) if m else None


def quote_sale(pid: str) -> int | None:
    row = product_bridge(pid)
    if not row:
        return None
    side = row.get("rj") or row.get("spdf")
    if not side:
        return None
    return side.get("saleCents")


def main() -> int:
    ok = True
    for pid, exp in EXPECT.items():
        seed = seed_cents(pid)
        sale = quote_sale(pid)
        status = "OK" if seed == exp and sale == exp else "FAIL"
        if status != "OK":
            ok = False
        print(f"{status} {pid}: seed={seed} quote.rj.sale={sale} expect={exp}")
    print("SMOKE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
