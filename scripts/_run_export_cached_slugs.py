# -*- coding: utf-8 -*-
"""export_wp_home using cached woo-slugs.json (skip live Woo listing)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import export_wp_home as exp

CACHE = ROOT / "wordpress-loja" / "pm-home" / "woo-slugs.json"


def woo_slugs_cached():
    if CACHE.is_file():
        slugs = set(json.loads(CACHE.read_text(encoding="utf-8")))
        print("woo slugs cached", len(slugs), flush=True)
        return slugs
    print("woo slugs cache missing; falling back", flush=True)
    return exp.woo_slugs()


exp.woo_slugs = woo_slugs_cached
exp.main()
