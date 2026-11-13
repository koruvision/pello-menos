# -*- coding: utf-8 -*-
"""Coloca SKUs de ensaio Esquenta em draft no OT."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
SKUS = json.loads((ROOT / "scripts" / "_ot_esquenta_test_skus.json").read_text(encoding="utf-8"))


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return e["PM_OFICIALTESTE_URL"].rstrip("/"), e["PM_OFICIALTESTE_USER"], e["PM_OFICIALTESTE_APP_PASSWORD"]


def main():
    url, user, password = cfg()
    tok = base64.b64encode(f"{user}:{password}".encode()).decode()
    for cid, pid in SKUS.items():
        req = urllib.request.Request(
            f"{url}/wp-json/wc/v3/products/{pid}",
            data=json.dumps({"status": "draft", "catalog_visibility": "hidden"}).encode(),
            method="PUT",
            headers={
                "Authorization": "Basic " + tok,
                "Content-Type": "application/json",
                "User-Agent": "pm-draft",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            print(cid, pid, r.status, "draft")


if __name__ == "__main__":
    main()
