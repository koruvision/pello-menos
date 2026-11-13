# -*- coding: utf-8 -*-
"""Corrige mojibake do pm-home com ftfy e grava UTF-8 sem BOM."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import ftfy

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
OUT = ROOT / "scripts" / "_fix_mojibake_utf8_result.json"
TEXT_SUFFIXES = {".html", ".js", ".css", ".json", ".txt", ".svg", ".md"}


def score(text: str) -> int:
    return text.count("Ã") + text.count("â€") + text.count("Â\xa0") + text.count("Â ")


def main():
    dry = "--dry" in sys.argv
    changed = []
    unchanged = 0
    for path in sorted(PM.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        before = score(text)
        if before == 0 and "\ufeff" not in path.read_text(encoding="utf-8", errors="ignore")[:1]:
            # still may have BOM only
            raw = path.read_bytes()
            if raw.startswith(b"\xef\xbb\xbf") and before == 0:
                if not dry:
                    path.write_bytes(raw[3:])
                changed.append({"file": str(path.relative_to(PM)).replace("\\", "/"), "codec": "strip-bom", "before": 0, "after": 0})
            else:
                unchanged += 1
            continue
        fixed = ftfy.fix_text(text)
        after = score(fixed)
        if fixed == text and after >= before:
            unchanged += 1
            continue
        if not dry:
            path.write_bytes(fixed.encode("utf-8"))
        changed.append(
            {
                "file": str(path.relative_to(PM)).replace("\\", "/"),
                "codec": "ftfy",
                "before": before,
                "after": after,
            }
        )

    report = {"dry": dry, "changed": len(changed), "unchanged": unchanged, "files": changed}
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    sample = (PM / "products" / "axila-cera.html").read_text(encoding="utf-8-sig")
    print(
        "changed",
        len(changed),
        "dry",
        dry,
        "sample",
        {
            "Inicio": "Início" in sample,
            "bad": "InÃ­cio" in sample,
            "Servicos": "Serviços" in sample,
            "regiao": "região" in sample,
            "score": score(sample),
        },
    )
    print("wrote", OUT)


if __name__ == "__main__":
    main()
