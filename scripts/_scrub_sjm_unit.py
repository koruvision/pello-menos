# -*- coding: utf-8 -*-
"""Remove unidade SJM / São João de Meriti de bridge, cart-related e HTML pm-home."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"


def strip_units_obj(obj: object) -> int:
    removed = 0
    if isinstance(obj, dict):
        if "units" in obj and isinstance(obj["units"], dict):
            drop = [k for k in obj["units"] if str(k).lower() == "sjm"]
            for k in drop:
                del obj["units"][k]
                removed += 1
        for v in obj.values():
            removed += strip_units_obj(v)
    elif isinstance(obj, list):
        for v in obj:
            removed += strip_units_obj(v)
    return removed


def scrub_json(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    n = strip_units_obj(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return n


OPTION_SJM = re.compile(
    r'<option\b[^>]*\bvalue=["\']sjm["\'][^>]*>.*?</option>',
    re.I | re.S,
)
JSON_SJM = re.compile(r',[ \t]*"sjm"\s*:\s*\{(?:[^{}]|\{[^{}]*\})*\}', re.I)
JSON_SJM_FIRST = re.compile(r'"sjm"\s*:\s*\{(?:[^{}]|\{[^{}]*\})*\}\s*,?', re.I)


def scrub_html_text(text: str) -> tuple[str, int]:
    out, n1 = OPTION_SJM.subn("", text)
    out2, n2 = JSON_SJM.subn("", out)
    out3, n3 = JSON_SJM_FIRST.subn("", out2)
    out = out3
    n = n1 + n2 + n3
    out = re.sub(r",\s*,", ",", out)
    out = re.sub(r"\{\s*,", "{", out)
    out = re.sub(r",\s*\}", "}", out)
    return out, n


def main() -> None:
    total = 0
    for path in (
        ROOT / "src" / "lib" / "woo-bridge.json",
        PM / "woo-bridge.json",
        PM / "cart-related.json",
    ):
        if not path.is_file():
            print("skip", path)
            continue
        n = scrub_json(path)
        total += n
        print(path.relative_to(ROOT).as_posix(), "removed", n)

    html_files = 0
    html_ops = 0
    left = []
    for path in PM.rglob("*.html"):
        raw = path.read_text(encoding="utf-8")
        if "sjm" not in raw.lower() and "meriti" not in raw.lower():
            continue
        new, n = scrub_html_text(raw)
        if new != raw:
            path.write_text(new, encoding="utf-8")
            html_files += 1
            html_ops += n
        if "sjm" in new.lower() or "meriti" in new.lower():
            left.append(path.relative_to(ROOT).as_posix())

    print("html touched", html_files, "ops", html_ops)
    print("json unit keys removed", total)
    print("still mentioning sjm/meriti", len(left))
    for p in left[:20]:
        print(" leftover", p)


if __name__ == "__main__":
    main()
