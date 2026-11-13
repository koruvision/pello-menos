# -*- coding: utf-8 -*-
"""Correlate Accesstage order id suffixes with store units."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "_audit_accesstage.json"


def main():
    rows = json.loads(DATA.read_text(encoding="utf-8"))["orders"]
    by_suffix4 = defaultdict(set)
    by_suffix5 = defaultdict(set)
    by_unit_suffix = defaultdict(list)
    for r in rows:
        acc = str(r.get("pedido_accesstage") or "")
        unit = str(r.get("unit_meta") or r.get("line_unit") or "?")
        if not acc.isdigit():
            print("non-digit", acc, unit)
            continue
        s4 = acc[-4:]
        s5 = acc[-5:]
        by_suffix4[s4].add(unit)
        by_suffix5[s5].add(unit)
        by_unit_suffix[unit].append({"acc": acc, "s4": s4, "s5": s5, "total": r.get("total")})

    print("=== suffix4 -> units ===")
    for s, units in sorted(by_suffix4.items(), key=lambda x: (-len(x[1]), x[0])):
        print(f"  …{s}  n_orders={sum(1 for r in rows if str(r.get('pedido_accesstage','')).endswith(s))}  units={sorted(units)}")

    print("\n=== suffix5 -> units ===")
    for s, units in sorted(by_suffix5.items(), key=lambda x: (-len(x[1]), x[0])):
        print(f"  …{s}  units={sorted(units)}")

    print("\n=== per unit suffixes ===")
    for unit, items in sorted(by_unit_suffix.items()):
        sufs = sorted({i["s4"] for i in items})
        print(f"  {unit}: suffixes4={sufs} counts={len(items)} sample={items[0]['acc']}")

    # Does same unit always same suffix?
    print("\n=== consistency: unit always same s4? ===")
    for unit, items in sorted(by_unit_suffix.items()):
        sufs = {i["s4"] for i in items}
        ok = len(sufs) == 1
        print(("OK" if ok else "MIX"), unit, sufs)


if __name__ == "__main__":
    main()
