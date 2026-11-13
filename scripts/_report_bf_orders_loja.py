# -*- coding: utf-8 -*-
"""READ-ONLY: pedidos Woo loja Nov/2024 agregados dia/hora (Black Friday report)."""
from __future__ import annotations

import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"

# Inclui status que geram carga no checkout; exclui trash/auto-draft.
STATUSES = ("pending", "processing", "on-hold", "completed", "refunded", "cancelled", "failed")

# Uso: python scripts/_report_bf_orders_loja.py [2024|2025]
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
AFTER = f"{YEAR}-11-01T00:00:00"
BEFORE = f"{YEAR}-12-01T00:00:00"
OUT = ROOT / "projeto-migracao" / ".secrets" / f"bf-{YEAR}-orders-loja.json"
# Sexta Black Friday BR: 2024-11-29, 2025-11-28
BF_FRIDAY = {2024: "2024-11-29", 2025: "2025-11-28"}.get(YEAR, f"{YEAR}-11-29")


def read_env(path: Path) -> dict:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": values["PM_LOJA_URL"].rstrip("/"),
        "user": values["PM_LOJA_USER"],
        "password": values["PM_LOJA_APP_PASSWORD"],
    }


def get_json(cfg: dict, path: str, timeout: int = 120):
    token = base64.b64encode(f"{cfg['user']}:{cfg['password']}".encode()).decode()
    req = urllib.request.Request(
        cfg["url"] + path,
        headers={
            "Authorization": "Basic " + token,
            "User-Agent": "Mozilla/5.0 (compatible; pm-bf-orders/1.0)",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body else None, dict(r.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body[:500]
        return e.code, parsed, {}


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    # Woo returns "2024-11-29T14:22:11" (site tz) — treat as naive local wall clock.
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00").split("+")[0])
    except Exception:
        return None


def fetch_all(cfg: dict) -> list[dict]:
    orders: list[dict] = []
    page = 1
    while True:
        q = urllib.parse.urlencode(
            {
                "after": AFTER,
                "before": BEFORE,
                "per_page": 100,
                "page": page,
                "orderby": "date",
                "order": "asc",
                "status": ",".join(STATUSES),
            }
        )
        st, data, headers = get_json(cfg, f"/wp-json/wc/v3/orders?{q}")
        if st != 200:
            sys.exit(f"orders page {page}: HTTP {st} {data}")
        if not isinstance(data, list):
            sys.exit(f"unexpected payload page {page}: {type(data)}")
        print(f"page {page}: {len(data)} orders")
        orders.extend(data)
        total_pages = int(headers.get("X-WP-TotalPages") or headers.get("x-wp-totalpages") or "0")
        if not data or (total_pages and page >= total_pages) or len(data) < 100:
            break
        page += 1
        if page > 200:
            sys.exit("safety: too many pages")
    return orders


def aggregate(orders: list[dict]) -> dict:
    by_day: dict[str, list] = defaultdict(list)
    by_hour: dict[str, int] = Counter()
    by_status: Counter = Counter()
    paid_totals: list[float] = []
    slim = []

    for o in orders:
        status = o.get("status") or ""
        by_status[status] += 1
        dt = parse_dt(o.get("date_created"))
        day = dt.strftime("%Y-%m-%d") if dt else "unknown"
        hour_key = dt.strftime("%Y-%m-%d %H:00") if dt else "unknown"
        by_day[day].append(o)
        by_hour[hour_key] += 1
        total = None
        try:
            total = float(o.get("total") or 0)
        except Exception:
            total = None
        if status in ("processing", "completed", "on-hold") and total is not None:
            paid_totals.append(total)
        slim.append(
            {
                "id": o.get("id"),
                "status": status,
                "total": o.get("total"),
                "date_created": o.get("date_created"),
                "payment_method": o.get("payment_method"),
            }
        )

    day_counts = {d: len(rows) for d, rows in sorted(by_day.items())}
    day_paid = {}
    for d, rows in sorted(by_day.items()):
        day_paid[d] = sum(
            1 for r in rows if (r.get("status") or "") in ("processing", "completed", "on-hold")
        )

    # Windows
    nov_all = list(day_counts.keys())
    bf_day = BF_FRIDAY
    week1 = [d for d in nov_all if d <= f"{YEAR}-11-07"]
    bf_week = [d for d in nov_all if f"{YEAR}-11-25" <= d <= f"{YEAR}-11-30"]

    def avg(days: list[str]) -> float | None:
        if not days:
            return None
        return sum(day_counts.get(d, 0) for d in days) / len(days)

    top_hours = sorted(by_hour.items(), key=lambda x: -x[1])[:20]
    peak_hour = top_hours[0] if top_hours else (None, 0)

    report = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "year": YEAR,
        "source": "wc/v3/orders",
        "window": {"after": AFTER, "before": BEFORE, "statuses": list(STATUSES)},
        "totals": {
            "orders": len(orders),
            "by_status": dict(by_status),
            "paidish_count": len(paid_totals),
            "paidish_gmv": round(sum(paid_totals), 2) if paid_totals else 0,
            "paidish_aov": round(sum(paid_totals) / len(paid_totals), 2) if paid_totals else None,
        },
        "by_day": day_counts,
        "by_day_paidish": day_paid,
        "avg_orders_per_day_nov": round(sum(day_counts.values()) / max(len(day_counts), 1), 2),
        "avg_orders_per_day_week1": round(avg(week1) or 0, 2),
        "avg_orders_per_day_bf_week": round(avg(bf_week) or 0, 2),
        "bf_friday": {"date": bf_day, "orders": day_counts.get(bf_day, 0)},
        "peak_hour": {"key": peak_hour[0], "orders": peak_hour[1]},
        "top_hours": [{"hour": h, "orders": n} for h, n in top_hours],
        "factor_bf_week_vs_week1": (
            round((avg(bf_week) or 0) / (avg(week1) or 1), 2) if week1 and bf_week else None
        ),
        "orders_slim": slim,
    }
    return report


def main() -> None:
    cfg = read_env(ENV)
    print("destino:", cfg["url"], "year", YEAR)
    orders = fetch_all(cfg)
    print("total orders", len(orders))
    report = aggregate(orders)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)
    print("by_status", report["totals"]["by_status"])
    print("avg/day nov", report["avg_orders_per_day_nov"])
    print("avg/day week1", report["avg_orders_per_day_week1"])
    print("avg/day bf week", report["avg_orders_per_day_bf_week"])
    print("BF Friday", report["bf_friday"])
    print("peak hour", report["peak_hour"])
    print("factor", report["factor_bf_week_vs_week1"])


if __name__ == "__main__":
    main()
