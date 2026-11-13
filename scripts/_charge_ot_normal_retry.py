# -*- coding: utf-8 -*-
"""Retry only normal R$1.99 charge (FORCE=off)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# reuse matrix runner pieces
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _charge_ot_matrix_min import (  # noqa: E402
    CASES,
    load_card,
    put_force,
    run_case,
    set_product_status,
    LASER_ID,
)

from playwright.sync_api import sync_playwright

BASE_CASE = next(c for c in CASES if c["id"] == "normal")


def main():
    card = load_card()
    put_force("off")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        result = run_case(page, card, BASE_CASE)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        browser.close()
    put_force("esquenta")
    out = Path(__file__).resolve().parents[1] / "scripts" / "_charge_ot_normal_retry_result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if not result.get("ok"):
        raise SystemExit("normal retry failed")
    print("NORMAL_RETRY_OK")


if __name__ == "__main__":
    main()
