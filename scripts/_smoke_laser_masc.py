# -*- coding: utf-8 -*-
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = (ROOT / "src/lib/data.ts").read_text(encoding="utf-8")
BRIDGE = json.loads((ROOT / "src/lib/woo-bridge.json").read_text(encoding="utf-8"))
REPORT = ROOT / "projeto-migracao" / "historico" / "14-origem-precos-catalogo.md"

EXPECT = {
    "axilas-laser-masc": (24500, 23275),
    "abdomen-laser-masc": (27250, 25888),
    "barba-laser-masc": (26750, 25413),
    "perna-laser-masc": (108000, 102600),
    "peito-laser-masc": (35500, 33725),
}


def main() -> int:
    ok = True
    for pid, (reg, sale) in EXPECT.items():
        m = re.search(rf'id:\s*"{re.escape(pid)}"[^}}]*?originalCents:\s*(\d+)', DATA, re.S)
        seed = int(m.group(1)) if m else None
        row = BRIDGE.get(pid, {})
        br = (row.get("rj") or {}).get("regularCents")
        bs = (row.get("rj") or {}).get("saleCents")
        calc = int(reg * 0.95 + 0.5)  # JS Math.round
        status = "OK" if seed == reg and br == reg and bs == sale and bs == calc else "FAIL"
        if status != "OK":
            ok = False
        print(f"{status} {pid}: seed={seed} bridge={br}/{bs} expect={reg}/{sale}")

    if not REPORT.exists():
        print("FAIL report missing")
        ok = False
    else:
        text = REPORT.read_text(encoding="utf-8")
        for needle in ("## Feminino", "## Masculino", "### Laser", "laser-masc-tabela-2026-10", "rafael-cera-esfol-planos"):
            if needle not in text:
                print("FAIL report missing", needle)
                ok = False
            else:
                print("OK report has", needle)

    print("SMOKE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
