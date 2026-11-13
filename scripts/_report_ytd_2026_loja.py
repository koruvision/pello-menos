# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
SALES_2025 = ROOT / "projeto-migracao" / ".secrets" / "sales-2025-loja.json"


def main() -> None:
    vals = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    url = vals["PM_LOJA_URL"].rstrip("/")
    tok = base64.b64encode(
        f"{vals['PM_LOJA_USER']}:{vals['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()

    def get(path: str):
        req = urllib.request.Request(
            url + path,
            headers={
                "Authorization": "Basic " + tok,
                "User-Agent": "pm-ytd",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode()), dict(r.headers)

    orders = []
    page = 1
    while True:
        q = urllib.parse.urlencode(
            {
                "after": "2026-01-01T00:00:00",
                "before": "2027-01-01T00:00:00",
                "per_page": 100,
                "page": page,
                "orderby": "date",
                "order": "asc",
                "status": "processing,completed,refunded",
            }
        )
        data, h = get(f"/wp-json/wc/v3/orders?{q}")
        print("page", page, len(data), flush=True)
        orders.extend(data)
        tp = int(h.get("X-WP-TotalPages") or h.get("x-wp-totalpages") or 0)
        if not data or (tp and page >= tp) or len(data) < 100:
            break
        page += 1
        if page > 300:
            break

    gross = sum(float(o.get("total") or 0) for o in orders)
    base = json.loads(SALES_2025.read_text(encoding="utf-8"))
    target = float(base["target_2026_double_brl"])
    remain = target - gross
    days = (date(2027, 1, 1) - date.today()).days
    print("orders_2026", len(orders))
    print("gross_2026", round(gross, 2))
    print("target", round(target, 2))
    print("remain", round(remain, 2))
    print("days_left", days)
    print("daily_needed", round(remain / days, 2) if days else None)
    print("pct_of_target", round(100 * gross / target, 2) if target else None)


if __name__ == "__main__":
    main()
