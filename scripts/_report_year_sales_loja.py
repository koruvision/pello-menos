# -*- coding: utf-8 -*-
"""READ-ONLY: vendas Woo loja ano completo + média diária para dobrar em 2026."""
from __future__ import annotations

import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"

YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
AFTER = f"{YEAR}-01-01T00:00:00"
BEFORE = f"{YEAR + 1}-01-01T00:00:00"
OUT = ROOT / "projeto-migracao" / ".secrets" / f"sales-{YEAR}-loja.json"

# Pedidos que entram no funil; receita considera só os pagos.
ALL_STATUSES = (
    "pending",
    "processing",
    "on-hold",
    "completed",
    "refunded",
    "cancelled",
    "failed",
)
PAID_STATUSES = {"processing", "completed", "refunded"}


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


def get_json(cfg: dict, path: str, timeout: int = 180):
    token = base64.b64encode(f"{cfg['user']}:{cfg['password']}".encode()).decode()
    req = urllib.request.Request(
        cfg["url"] + path,
        headers={
            "Authorization": "Basic " + token,
            "User-Agent": "Mozilla/5.0 (compatible; pm-year-sales/1.0)",
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
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00").split("+")[0])
    except Exception:
        return None


def money(o: dict) -> float:
    try:
        return float(o.get("total") or 0)
    except Exception:
        return 0.0


def refund_total(o: dict) -> float:
    total = 0.0
    for r in o.get("refunds") or []:
        try:
            # Woo lista refunds com total negativo às vezes
            total += abs(float(r.get("total") or 0))
        except Exception:
            pass
    return total


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
                "status": ",".join(ALL_STATUSES),
            }
        )
        st, data, headers = get_json(cfg, f"/wp-json/wc/v3/orders?{q}")
        if st != 200:
            sys.exit(f"orders page {page}: HTTP {st} {data}")
        if not isinstance(data, list):
            sys.exit(f"unexpected payload page {page}: {type(data)}")
        print(f"page {page}: {len(data)} orders", flush=True)
        orders.extend(data)
        total_pages = int(headers.get("X-WP-TotalPages") or headers.get("x-wp-totalpages") or "0")
        if page == 1:
            print("total pages hint", total_pages or "?", "total header", headers.get("X-WP-Total") or headers.get("x-wp-total"), flush=True)
        if not data or (total_pages and page >= total_pages) or len(data) < 100:
            break
        page += 1
        if page > 500:
            sys.exit("safety: too many pages")
    return orders


def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main() -> None:
    cfg = read_env(ENV)
    assert "loja.pellomenos" in cfg["url"]
    orders = fetch_all(cfg)
    print("fetched", len(orders), flush=True)

    by_status: Counter = Counter()
    by_month: dict[str, float] = defaultdict(float)
    by_day: dict[str, float] = defaultdict(float)
    paid_gross = 0.0
    paid_net = 0.0
    paid_count = 0
    refunded_count = 0
    refund_sum = 0.0

    for o in orders:
        status = str(o.get("status") or "")
        by_status[status] += 1
        dt = parse_dt(o.get("date_created"))
        if not dt:
            continue
        month = dt.strftime("%Y-%m")
        day = dt.strftime("%Y-%m-%d")
        total = money(o)
        if status in PAID_STATUSES:
            paid_count += 1
            paid_gross += total
            ref = refund_total(o) if status == "refunded" else 0.0
            # completed/processing: use order total; refunded: total already may be 0 or residual
            if status == "refunded":
                refunded_count += 1
                refund_sum += max(ref, total)
                # net: if total still >0 keep it; else 0
                paid_net += total
            else:
                paid_net += total
            by_month[month] += total
            by_day[day] += total

    days_with_sales = len(by_day)
    calendar_days_2025 = (date(YEAR + 1, 1, 1) - date(YEAR, 1, 1)).days  # 365
    avg_day_2025 = paid_gross / calendar_days_2025 if calendar_days_2025 else 0
    avg_day_active = paid_gross / days_with_sales if days_with_sales else 0

    target_2026 = paid_gross * 2
    days_2026 = (date(2027, 1, 1) - date(2026, 1, 1)).days  # 365
    # from today (user_info said Nov 3 2026 earlier but now Nov 3 night - still 2026)
    today = date.today()
    if today.year == 2026:
        remaining = (date(2027, 1, 1) - today).days
        # ytd 2026 if we had it — without fetch, only full-year and remaining-year targets
    else:
        remaining = days_2026

    daily_full_year = target_2026 / days_2026
    daily_remaining = target_2026 / remaining if remaining else daily_full_year

    report = {
        "source": "wc/v3/orders",
        "store": cfg["url"],
        "period": {"after": AFTER, "before": BEFORE, "year": YEAR},
        "orders_total": len(orders),
        "by_status": dict(by_status),
        "paid_statuses": sorted(PAID_STATUSES),
        "paid_orders": paid_count,
        "refunded_orders": refunded_count,
        "paid_gross_brl": round(paid_gross, 2),
        "paid_net_brl": round(paid_net, 2),
        "refund_sum_listed_brl": round(refund_sum, 2),
        "days_with_sales": days_with_sales,
        "calendar_days_year": calendar_days_2025,
        "avg_daily_calendar_2025_brl": round(avg_day_2025, 2),
        "avg_daily_active_days_2025_brl": round(avg_day_active, 2),
        "by_month_paid_brl": {k: round(v, 2) for k, v in sorted(by_month.items())},
        "target_2026_double_brl": round(target_2026, 2),
        "days_2026": days_2026,
        "min_daily_2026_full_year_brl": round(daily_full_year, 2),
        "as_of": today.isoformat(),
        "days_remaining_2026_inclusive_end": remaining,
        "min_daily_2026_from_today_if_zero_ytd_brl": round(daily_remaining, 2),
        "note": "Meta 2026 = 2× receita paga 2025 (processing+completed+refunded totals). "
        "min_daily_full_year = meta/365. "
        "min_daily_from_today assume YTD 2026 = 0 (conservador); se já vendeu em 2026, falta menos.",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("=== VENDAS LOJA", YEAR, "===")
    print("pedidos (todos status):", len(orders))
    print("por status:", dict(by_status))
    print("pedidos pagos (processing/completed/refunded):", paid_count)
    print("receita bruta paga:", brl(paid_gross))
    print("média/dia calendário", YEAR, ":", brl(avg_day_2025), f"({calendar_days_2025} dias)")
    print("média/dia com venda:", brl(avg_day_active), f"({days_with_sales} dias)")
    print()
    print("=== META 2026 = 2×", YEAR, "===")
    print("meta ano:", brl(target_2026))
    print("mínimo/dia (ano cheio 365):", brl(daily_full_year))
    print(f"mínimo/dia de {today.isoformat()} até 31/12/2026 (se YTD=0):", brl(daily_remaining), f"({remaining} dias)")
    print()
    print("por mês:")
    for m, v in sorted(by_month.items()):
        print(f"  {m}: {brl(v)}")
    print("saved", OUT)


if __name__ == "__main__":
    main()
