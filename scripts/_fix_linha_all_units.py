# -*- coding: utf-8 -*-
"""Ensure linha SKUs expose all 37 store units in the UI.

If Woo already has Afonso Pena / Treze de Maio variations, map them.
Otherwise clear the units map so the ficha falls back to capacity (all stores).
"""
from __future__ import annotations

import base64
import json
import re
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
BRIDGE_WP = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"

LINHA_IDS = ["buco-linha", "queixo-linha", "faixa-linha"]


def read_env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def http_json(url: str, auth: str):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": "Basic " + auth,
            "User-Agent": "pm-fix-linha/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def norm(s: str) -> str:
    s = (s or "").lower()
    s = (
        s.replace("á", "a")
        .replace("à", "a")
        .replace("â", "a")
        .replace("ã", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )
    return re.sub(r"[^a-z0-9]+", " ", s)


def map_option_to_unit(option: str) -> str | None:
    n = norm(option)
    rules = [
        ("afonso pena", "ape"),
        ("treze de maio", "13m"),
        ("13 de maio", "13m"),
        ("saens pena", "snp"),
        ("saens peña", "snp"),
        ("uruguai", "urg"),
        ("augusta", "sp-aug"),
        ("paulista", "sp-avp"),
        ("sao jose", "sp-sjc"),
        ("asa sul", "df-asu"),
        ("asa norte", "df-ano"),
    ]
    for needle, uid in rules:
        if needle in n:
            return uid
    return None


def main():
    env = read_env()
    base = env["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{env['PM_OFICIALTESTE_USER']}:{env['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()

    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    data = Path(ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")
    all_unit_ids = {
        c.lower().replace(" ", "-") for c in re.findall(r'unit\(\s*"([^"]+)"', data)
    }
    print("all units", len(all_unit_ids))

    for pid in LINHA_IDS:
        row = bridge.get(pid)
        if not row:
            print("SKIP missing bridge", pid)
            continue
        product_id = row.get("productId")
        print("\n===", pid, "productId", product_id, "units now", len(row.get("units") or {}))
        if not product_id:
            print("no productId; clearing units for capacity fallback")
            row["units"] = {}
            continue

        vars_url = f"{base}/wp-json/wc/v3/products/{product_id}/variations?per_page=100"
        try:
            variations = http_json(vars_url, auth)
        except Exception as e:
            print("variations fetch failed", type(e).__name__, e)
            # Prefer showing all stores in UI over hiding two.
            row["units"] = {}
            print("cleared units -> capacity all stores")
            continue

        found = {}
        for v in variations:
            attrs = v.get("attributes") or []
            option = ""
            for a in attrs:
                option = a.get("option") or a.get("name") or option
            uid = map_option_to_unit(option)
            # also keep existing bridge keys by matching option text loosely
            if not uid:
                on = norm(option)
                for existing_id, link in (row.get("units") or {}).items():
                    if norm(link.get("option") or "") == on:
                        uid = existing_id
                        break
            if not uid:
                # try heuristic from option
                if "tijuca" in norm(option) and "afonso" in norm(option):
                    uid = "ape"
                elif "treze" in norm(option) or "13 de maio" in norm(option):
                    uid = "13m"
            if uid:
                found[uid] = {
                    "variationId": int(v["id"]),
                    "option": option,
                }

        # merge with existing bridge units (prefer Woo live ids when found)
        merged = dict(row.get("units") or {})
        merged.update(found)
        missing = sorted(all_unit_ids - set(merged.keys()))
        print("after merge", len(merged), "missing", missing)

        if missing:
            # User asked all stores in selector. Empty map = capacity fallback (all 37).
            # Checkout for units without Woo variation may need staff follow-up.
            row["units"] = {}
            print("cleared units map so UI lists all", len(all_unit_ids), "stores")
        else:
            row["units"] = merged
            print("OK full map", len(merged))

    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(BRIDGE, BRIDGE_WP)
    print("\nwrote", BRIDGE)
    print("copied", BRIDGE_WP)


if __name__ == "__main__":
    main()
