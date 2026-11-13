# -*- coding: utf-8 -*-
"""Pedidos/dia e pico/hora dos últimos N dias (loja Woo)."""
from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
OUT = ROOT / "scripts" / "_report_demand_recent_loja.json"
DAYS = 30
STATUSES = "completed,processing"


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def main():
    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    after = (datetime.now(timezone.utc) - timedelta(days=DAYS)).strftime("%Y-%m-%dT00:00:00")
    page = 1
    orders = []
    while True:
        q = urllib.parse.urlencode(
            {
                "status": STATUSES,
                "after": after,
                "per_page": 100,
                "page": page,
                "orderby": "date",
                "order": "asc",
            }
        )
        req = urllib.request.Request(
            base + f"/wp-json/wc/v3/orders?{q}",
            headers={"Authorization": "Basic " + auth, "Accept": "application/json", "User-Agent": "pm"},
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            batch = json.loads(r.read().decode())
            total_pages = int(r.headers.get("X-WP-TotalPages") or "1")
        if not isinstance(batch, list) or not batch:
            break
        orders.extend(batch)
        print("page", page, "/", total_pages, "got", len(batch), "acc", len(orders))
        if page >= total_pages:
            break
        page += 1

    by_day: Counter[str] = Counter()
    by_hour: Counter[str] = Counter()
    for o in orders:
        dc = o.get("date_created") or ""
        if not dc:
            continue
        # 2026-11-05T16:39:10
        day = dc[:10]
        hour = dc[:13]  # YYYY-MM-DDTHH
        by_day[day] += 1
        by_hour[hour] += 1

    days_sorted = sorted(by_day.keys())
    n_days = max(1, len(days_sorted))
    total = len(orders)
    avg_day = total / n_days if n_days else 0
    peak_day = by_day.most_common(1)[0] if by_day else ("", 0)
    peak_hour = by_hour.most_common(1)[0] if by_hour else ("", 0)
    peak_per_min = (peak_hour[1] / 60.0) if peak_hour[1] else 0.0

    # proxy concurrent GET (doc 25 premissa B: 50 GETs/pedido, ~30s)
    peak_orders_h = peak_hour[1]
    proxy_concurrent_b = (peak_orders_h * 50 / 3600.0) * 30.0
    # usuários/minuto proxy (GETs/min no pico)
    gets_per_min_peak = (peak_orders_h * 50) / 60.0

    report = {
        "days": DAYS,
        "after": after,
        "statuses": STATUSES,
        "orders": total,
        "days_with_orders": n_days,
        "avg_orders_per_day": round(avg_day, 2),
        "peak_day": {"day": peak_day[0], "orders": peak_day[1]},
        "peak_hour": {"hour": peak_hour[0], "orders": peak_hour[1]},
        "peak_orders_per_minute": round(peak_per_min, 3),
        "proxy": {
            "assumption": "50 GETs/pedido, dwell 30s (doc 25 B)",
            "peak_gets_per_minute": round(gets_per_min_peak, 2),
            "est_concurrent_get": round(proxy_concurrent_b, 2),
        },
        "by_day": dict(sorted(by_day.items())),
        "top_hours": [{"hour": h, "orders": c} for h, c in by_hour.most_common(10)],
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k not in ("by_day", "top_hours")}, indent=2))
    print("top_hours", report["top_hours"][:5])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
