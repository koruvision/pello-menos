# -*- coding: utf-8 -*-
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = json.loads((ROOT / "src/lib/woo-bridge.json").read_text(encoding="utf-8"))
DATA = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")

EXPECT = {
    "barba-cera-masc": 5690,
    "barba-modeladora-cera-masc": 7490,
    "bigode-cera-masc": 3850,
    "orelha-cera-masc": 3290,
    "pescoco-cera-masc": 3290,
    "mamilos-cera-masc": 3290,
    "sobrancelha-cera-masc": 5290,
    "design-sobrancelha-masc": 6990,
    "torax-abdomen-cera-masc": 8990,
    "saco-escrotal-cera-masc": 5890,
}


def main() -> int:
    ok = True
    for pid, exp in EXPECT.items():
        if f'id: "{pid}"' not in DATA:
            print("FAIL seed missing", pid)
            ok = False
            continue
        m = re.search(rf'id:\s*"{re.escape(pid)}"[^}}]*?originalCents:\s*(\d+)', DATA, re.S)
        seed = int(m.group(1)) if m else None
        row = BRIDGE.get(pid)
        sale = (row or {}).get("rj", {}).get("saleCents")
        units = len((row or {}).get("units") or {})
        pid_woo = (row or {}).get("productId")
        status = "OK" if seed == exp and sale == exp and units == 13 and pid_woo else "FAIL"
        if status != "OK":
            ok = False
        print(f"{status} {pid}: seed={seed} bridge={sale} woo={pid_woo} units={units}")
    print("SMOKE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
