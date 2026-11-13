# -*- coding: utf-8 -*-
"""Prune woo-bridge.json unit maps to match store capacity flags."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "lib" / "woo-bridge.json"
WP = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"

# Mirrors storeUnits flags in src/lib/data.ts
CERA_MASC = {
    "rec",
    "sp-aug",
    "sp-avp",
    "urg",
    "ban",
    "bot",
    "copa-2",
    "eba",
    "fla",
    "fre",
    "ica",
    "lbi",
    "nig2",
}
LASER_FEM = {
    "rec",
    "cen",
    "sgo",
    "nil",
    "lma",
    "sp-sjc",
    "pet",
    "ig02",
    "hut",
    "urg",
    "ban",
    "bot",
    "copa-2",
    "eba",
    "fla",
    "fre",
    "ica",
    "lbi",
    "nig2",
}
LASER_MASC = {
    "urg",
    "ban",
    "bot",
    "copa-2",
    "eba",
    "fla",
    "fre",
    "ica",
    "lbi",
    "nig2",
}


def allowed_for(product_id: str):
    base = product_id[:-5] if product_id.endswith("-masc") else product_id
    is_masc = product_id.endswith("-masc") or "-masc" in product_id
    # All units (empty map = UI shows all)
    if base in {
        "body-splash",
        "cartao-presente",
        "cartao-presente-160",
        "cartao-presente-215",
        "cartao-presente-290",
        "produto-1-real",
    } or base.startswith("cartao-presente"):
        return None
    if base == "plano-clube-laser":
        return LASER_FEM
    if base.startswith("plano-"):
        return CERA_MASC if is_masc else None  # None = keep all (cera fem everywhere)
    if "laser" in base or base.endswith("-laser"):
        return LASER_MASC if is_masc else LASER_FEM
    if "esfoliacao" in base or "linha" in base or "henna" in base or "sobrancelha" in base:
        return None
    if "cera" in base:
        return CERA_MASC if is_masc else None
    return None


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    removed = 0
    touched = 0
    for pid, row in data.items():
        units = row.get("units") or {}
        if not units:
            continue
        allow = allowed_for(pid)
        if allow is None:
            continue
        before = len(units)
        row["units"] = {k: v for k, v in units.items() if k in allow}
        after = len(row["units"])
        if after != before:
            touched += 1
            removed += before - after
    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(SRC, WP)
    print("touched", touched, "removed_entries", removed)
    print("copied", WP)


if __name__ == "__main__":
    main()
