# -*- coding: utf-8 -*-
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
t = (ROOT / "src/lib/data.ts").read_text(encoding="utf-8")
copy = json.loads((ROOT / "src/lib/product-copy.json").read_text(encoding="utf-8"))
bridge = json.loads((ROOT / "src/lib/woo-bridge.json").read_text(encoding="utf-8"))

ok = True
for k in ("antebraco-cera-masc", "meia-nadega-cera-masc"):
    has = f'id: "{k}"' in t
    print(("OK" if has else "FAIL"), "seed", k)
    ok = ok and has
    ok = ok and (k in bridge)
    print(("OK" if k in bridge else "FAIL"), "bridge", k)

for k in ("esfoliacao-faixa-02", "esfoliacao-faixa-02-masc"):
    for label, present in (
        ("data", f'id: "{k}"' in t),
        ("copy", k in copy),
        ("bridge", k in bridge),
    ):
        status = "OK" if not present else "FAIL"
        if present:
            ok = False
        print(status, "absent", label, k)

print("SMOKE", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
