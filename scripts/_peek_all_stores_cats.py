# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

data = Path("src/lib/data.ts").read_text(encoding="utf-8")
codes = re.findall(r'unit\(\s*"([^"]+)"', data)
all_ids = {c.lower().replace(" ", "-") for c in codes}
bridge = json.loads(Path("src/lib/woo-bridge.json").read_text(encoding="utf-8"))

checks = [
    ("body-splash", "produto/body-splash"),
    ("cartao-presente", "presente"),
    ("esfoliacao-axilas", "esfoliacao"),
    ("esfoliacao-faixa", "esfoliacao"),
    ("buco-linha", "linha"),
    ("faixa-linha", "linha"),
    ("queixo-linha", "linha"),
]

print("capacity rule in unitsForProduct: linha, esfoliacao, presente, produto, body-splash -> ALL", len(all_ids), "units")
print()
for pid, kind in checks:
    units = (bridge.get(pid) or {}).get("units") or {}
    keys = set(units.keys())
    if not keys:
        ui = "capacity only (all %d)" % len(all_ids)
        missing = []
    else:
        missing = sorted(all_ids - keys)
        ui = "capacity AND bridge = %d" % len(all_ids & keys)
    print("%s (%s): bridge=%d; UI %s; missing=%s" % (pid, kind, len(keys), ui, missing or "-"))
