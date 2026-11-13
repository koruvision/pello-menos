# -*- coding: utf-8 -*-
"""Rebuild PSI summary + markdown report from saved JSON runs (no new API calls)."""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "projeto-migracao" / ".secrets" / "psi-oficialteste"
REPORT = ROOT / "projeto-migracao" / "historico" / "17-psi-oficialteste-baseline.md"
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"

spec = importlib.util.spec_from_file_location("pm_psi_audit", ROOT / "scripts" / "pm_psi_audit.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)

print("out exists", OUT.exists(), "files", len(list(OUT.glob("*"))) if OUT.exists() else 0)

# Find latest stamp from assets-*.json
assets_files = sorted(OUT.glob("assets-*.json"))
pages_files = sorted(OUT.glob("pages-*.json"))
if not assets_files or not pages_files:
    raise SystemExit("missing assets/pages json — re-run audit")

stamp = assets_files[-1].name.replace("assets-", "").replace(".json", "")
print("stamp", stamp)

assets = json.loads(assets_files[-1].read_text(encoding="utf-8"))
page_probes = json.loads(pages_files[-1].read_text(encoding="utf-8"))

# Collect raw PSI runs: psi-{slug}-{strategy}-r{n}-{stamp}.json
pat = re.compile(
    r"^psi-(?P<slug>.+)-(?P<strategy>mobile|desktop)-r(?P<run>\d+)-(?P<stamp>.+)\.json$"
)
by_key: dict[tuple[str, str], list] = {}
by_key_stamp: dict[tuple[str, str], list] = {}
for path in sorted(OUT.glob("psi-*.json")):
    if path.name.startswith("psi-summary"):
        continue
    m = pat.match(path.name)
    if not m:
        continue
    slug = m.group("slug")
    strategy = m.group("strategy")
    raw = json.loads(path.read_text(encoding="utf-8"))
    summary = mod.summarize_psi(raw)
    by_key.setdefault((slug, strategy), []).append(summary)
    if m.group("stamp") == stamp:
        by_key_stamp.setdefault((slug, strategy), []).append(summary)

use = by_key_stamp if by_key_stamp else by_key
print("groups", len(use), "stamp_groups", len(by_key_stamp), "all_groups", len(by_key))

psi_results: dict = {}
for (slug, strategy), runs in use.items():
    psi_results.setdefault(slug, {})[strategy] = mod.median_summaries(runs)
    print(slug, strategy, "runs", len(runs), "score", psi_results[slug][strategy].get("performance_score"))

summary_path = OUT / f"psi-summary-{stamp}.json"
summary_path.write_text(json.dumps(psi_results, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", summary_path)

# meta paths order
paths = [(slug, path) for path, slug in mod.DEFAULT_PATHS]
meta = {
    "generated_at": stamp,
    "base": mod.read_env(ENV).get("PM_OFICIALTESTE_URL", "").rstrip("/"),
    "runs": 3,
    "paths": paths,
}
mod.write_report(REPORT, meta, psi_results, assets, page_probes)
print("wrote", REPORT)
print("report bytes", REPORT.stat().st_size)
