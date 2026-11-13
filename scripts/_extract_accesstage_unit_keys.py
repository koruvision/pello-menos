# -*- coding: utf-8 -*-
"""Extract sanitized AccesStage unit slugs from shopwise-child functions.php dumps."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DUMP = ROOT / "scripts" / "_hostinger_ot_dumps" / "shopwise-child__functions.php"
OUT = ROOT / "projeto-migracao" / ".secrets" / "_accesstage_unit_keys_sanitized.json"


def parse_php_assoc_array(src: str, var_name: str) -> dict[str, str]:
    """Return {slug: kind} where kind is hex32|uuid|other — never store raw secrets in output values beyond kind+len."""
    m = re.search(
        rf"\${re.escape(var_name)}\s*=\s*array\s*\((.*?)\)\s*;",
        src,
        flags=re.S | re.I,
    )
    if not m:
        return {}
    body = m.group(1)
    out: dict[str, str] = {}
    for km in re.finditer(
        r"['\"]([a-z0-9_-]+)['\"]\s*=>\s*['\"]([^'\"]+)['\"]",
        body,
        flags=re.I,
    ):
        slug, val = km.group(1).lower(), km.group(2)
        if re.fullmatch(r"[0-9a-f]{32}", val, flags=re.I):
            kind = "hex32"
        elif re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            val,
            flags=re.I,
        ):
            kind = "uuid"
        else:
            kind = f"other:{len(val)}"
        out[slug] = kind
    return out


def main() -> None:
    text = DUMP.read_text(encoding="utf-8", errors="replace")
    api = parse_php_assoc_array(text, "api")
    apikey = parse_php_assoc_array(text, "apikey")
    # Some copies use $API / $apiKey variants
    if not api:
        api = parse_php_assoc_array(text, "API")
    if not apikey:
        for name in ("apikey", "apiKey", "APIKey", "api_key"):
            apikey = parse_php_assoc_array(text, name)
            if apikey:
                break

    all_slugs = sorted(set(api) | set(apikey))
    rows = []
    for slug in all_slugs:
        rows.append(
            {
                "slug": slug,
                "has_api": slug in api,
                "has_apikey": slug in apikey,
                "api_kind": api.get(slug),
                "apikey_kind": apikey.get(slug),
            }
        )

    report = {
        "source": str(DUMP.relative_to(ROOT)).replace("\\", "/"),
        "bytes": len(text),
        "api_count": len(api),
        "apikey_count": len(apikey),
        "slug_count": len(all_slugs),
        "api_only": sorted(set(api) - set(apikey)),
        "apikey_only": sorted(set(apikey) - set(api)),
        "both": sorted(set(api) & set(apikey)),
        "rows": rows,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("api", len(api), "apikey", len(apikey), "union", len(all_slugs))
    print("api_only", report["api_only"])
    print("apikey_only", report["apikey_only"])
    print("slugs:", ", ".join(all_slugs))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
