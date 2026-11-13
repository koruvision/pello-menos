# -*- coding: utf-8 -*-
"""Fetch shopwise-child/functions.php and extract Accesstage sections."""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "hostinger-ot.env"
OT = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
DUMP = ROOT / "scripts" / "_hostinger_ot_dumps"
OUT = ROOT / "scripts" / "_hostinger_accesstage_excerpt.md"
BASE = "https://developers.hostinger.com"


def env():
    e = {}
    for path in (ENV, OT):
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def api(token, path, query=None):
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": "pm-hostinger-read/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body else {})


def extract_text(body):
    if isinstance(body, dict):
        for k in ("content", "data", "file_content", "body", "value"):
            v = body.get(k)
            if isinstance(v, str):
                return v
            if isinstance(v, dict) and "content" in v:
                return str(v["content"])
        return json.dumps(body)
    return str(body)


def main():
    e = env()
    token = e["PM_HOSTINGER_API_TOKEN"]
    user = e["PM_HOSTINGER_ACCOUNT"]
    domain = e.get("PM_HOSTINGER_DOMAIN") or "pellomenosoficialteste.companygenesis.com.br"
    DUMP.mkdir(parents=True, exist_ok=True)

    file_path = "wp-content/themes/shopwise-child/functions.php"
    st, body = api(
        token,
        f"/api/hosting/v1/accounts/{user}/domains/{domain}/files/content",
        {"path": file_path},
    )
    text = extract_text(body) if st == 200 else ""
    print("status", st, "bytes", len(text))
    if st != 200:
        print(body)
        return

    (DUMP / "shopwise-child__functions.php").write_text(text, encoding="utf-8")

    # Also list child theme fully
    st2, listing = api(
        token,
        f"/api/hosting/v1/accounts/{user}/domains/{domain}/files",
        {
            "directory": "wp-content/themes/shopwise-child",
            "max_depth": 3,
            "max_items": 500,
        },
    )
    print("child listing", st2, listing.get("total_items") if isinstance(listing, dict) else listing)
    items = (listing.get("items") if isinstance(listing, dict) else []) or []
    for it in items:
        print(" ", it.get("type"), it.get("path") or it.get("name"))

    # Extract Accesstage-related function blocks
    lines = text.splitlines()
    markers = []
    for i, line in enumerate(lines):
        low = line.lower()
        if any(
            k in low
            for k in (
                "accesstage",
                "totalamount",
                "wpcf7_before_send_mail",
                "wpcf7_mail_sent",
                "cart-number",
                "securitycode",
                "removeitemcartpl",
                "redirectsuccess",
                "pedido accesstage",
            )
        ):
            markers.append(i)

    blocks = []
    for i in markers:
        start = max(0, i - 15)
        # walk back to nearest function/add_action
        for j in range(i, max(-1, i - 80), -1):
            if re.search(r"^\s*(function\s+|add_action\s*\(|add_filter\s*\()", lines[j]):
                start = j
                break
        end = min(len(lines), i + 40)
        for j in range(i, min(len(lines), i + 120)):
            if j > i + 5 and re.search(r"^\s*(function\s+|add_action\s*\(|add_filter\s*\()", lines[j]):
                end = j
                break
        blocks.append((start, end))

    # merge overlapping
    merged = []
    for s, e in sorted(blocks):
        if not merged or s > merged[-1][1] + 2:
            merged.append([s, e])
        else:
            merged[-1][1] = max(merged[-1][1], e)

    parts = ["# Accesstage excerpt — shopwise-child/functions.php\n"]
    for s, e in merged:
        parts.append(f"\n## lines {s+1}-{e}\n```php\n")
        parts.append("\n".join(lines[s:e]))
        parts.append("\n```\n")
    OUT.write_text("".join(parts), encoding="utf-8")
    print("wrote", OUT, "blocks", len(merged))

    # quick totalamount analysis
    for i, line in enumerate(lines):
        if "totalamount" in line.lower() or "total_amount" in line.lower() or "get_total" in line.lower():
            print(f"L{i+1}: {line.strip()}")


if __name__ == "__main__":
    main()
