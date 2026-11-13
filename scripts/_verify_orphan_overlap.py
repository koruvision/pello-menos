# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / "scripts/_orphan_media_report.json").read_text(encoding="utf-8"))
orph = {r["rel"] for r in report["orphans"]}
refs: set[str] = set()
pat = re.compile(
    r"(?:media/)?(images/(?:hero|categories|promo)/[^\s\"'?#]+)",
    re.I,
)
pm = ROOT / "wordpress-loja" / "pm-home"
for path in pm.rglob("*"):
    if path.suffix.lower() not in {".html", ".js", ".css", ".json"}:
        continue
    try:
        path.relative_to(pm / "media")
        continue
    except ValueError:
        pass
    text = path.read_text(encoding="utf-8", errors="ignore")
    for m in pat.findall(text):
        refs.add(m.split("?", 1)[0].replace("\\", "/"))

overlap = sorted(orph & refs)
print("live hero/cat/promo refs", len(refs))
print("orphan overlap", len(overlap))
for x in overlap:
    print("WARN", x)
print("orphan_count", len(orph))
# files that exist and are referenced
media = pm / "media"
alive = [r for r in sorted(refs) if (media / r).is_file()]
print("alive_count", len(alive))
print("alive_sample", alive[:20])
