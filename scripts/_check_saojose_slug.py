# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "scripts/_hostinger_ot_dumps/shopwise-child__functions.php").read_text(
    encoding="utf-8"
)
inv = json.loads(
    (ROOT / "projeto-migracao/.secrets/_inventory_accesstage_units.json").read_text(
        encoding="utf-8"
    )
)


def parse(var: str) -> dict[str, str]:
    m = re.search(rf"\${var}\s*=\s*array\s*\((.*?)\)\s*;", text, flags=re.S | re.I)
    if not m:
        return {}
    out = {}
    for km in re.finditer(
        r"['\"]([a-z0-9_-]+)['\"]\s*=>\s*['\"]([^'\"]+)['\"]", m.group(1), flags=re.I
    ):
        out[km.group(1).lower()] = km.group(2)
    return out


api = parse("api")
apikey = parse("apikey")
for s in ("saojose", "rjsaojose"):
    a, k = api.get(s, ""), apikey.get(s, "")
    print(
        s,
        "api",
        bool(a),
        a[-4:] if a else None,
        "apikey",
        bool(k),
        k[-4:] if k else None,
    )
print("api same", api.get("saojose") == api.get("rjsaojose"))
print("apikey same", apikey.get("saojose") == apikey.get("rjsaojose"))
for o in inv["cf7"]["loja"]["unit"]:
    if "sao" in o["slug"] or "José" in o["label"] or "Jose" in o["label"]:
        print("cf7", o["slug"], o["label"])
for r in inv["catalog_crosswalk"]:
    if r["code"] == "SJO":
        print("inventory SJO", r)
