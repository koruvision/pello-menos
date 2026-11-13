# -*- coding: utf-8 -*-
"""READ-ONLY: vendas loja só novembro (2025 vs 2026) + mínimo/dia para dobrar."""
from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
OUT = ROOT / "projeto-migracao" / ".secrets" / "sales-nov-loja.json"


def cfg():
    vals = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": vals["PM_LOJA_URL"].rstrip("/"),
        "user": vals["PM_LOJA_USER"],
        "password": vals["PM_LOJA_APP_PASSWORD"],
    }


def get(c, path):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        headers={
            "Authorization": "Basic " + tok,
            "User-Agent": "pm-nov",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode()), dict(r.headers)


def fetch_month(c, year: int, month: int = 11) -> list[dict]:
    after = f"{year}-{month:02d}-01T00:00:00"
    if month == 12:
        before = f"{year + 1}-01-01T00:00:00"
    else:
        before = f"{year}-{month + 1:02d}-01T00:00:00"
    orders = []
    page = 1
    while True:
        q = urllib.parse.urlencode(
            {
                "after": after,
                "before": before,
                "per_page": 100,
                "page": page,
                "orderby": "date",
                "order": "asc",
                "status": "processing,completed,refunded",
            }
        )
        data, h = get(c, f"/wp-json/wc/v3/orders?{q}")
        print(f"{year}-{month:02d} page {page}: {len(data)}", flush=True)
        orders.extend(data)
        tp = int(h.get("X-WP-TotalPages") or h.get("x-wp-totalpages") or 0)
        if not data or (tp and page >= tp) or len(data) < 100:
            break
        page += 1
        if page > 200:
            break
    return orders


def parse_day(o):
    s = o.get("date_created") or ""
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00").split("+")[0]).strftime("%Y-%m-%d")
    except Exception:
        return "unknown"


def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def summarize(orders: list[dict]):
    by_day = defaultdict(float)
    total = 0.0
    for o in orders:
        t = float(o.get("total") or 0)
        total += t
        by_day[parse_day(o)] += t
    return {
        "orders": len(orders),
        "gross": round(total, 2),
        "by_day": {k: round(v, 2) for k, v in sorted(by_day.items())},
        "days_with_sales": len(by_day),
    }


def main():
    c = cfg()
    o25 = fetch_month(c, 2025, 11)
    o26 = fetch_month(c, 2026, 11)
    s25 = summarize(o25)
    s26 = summarize(o26)

    days_nov = monthrange(2025, 11)[1]  # 30
    days_nov_26 = monthrange(2026, 11)[1]  # 30
    target = s25["gross"] * 2
    daily_full = target / days_nov_26

    today = date.today()
    if today.year == 2026 and today.month == 11:
        # remaining days including today through Nov 30
        remaining = (date(2026, 11, 30) - today).days + 1
    else:
        remaining = days_nov_26

    remain_brl = target - s26["gross"]
    daily_remain = remain_brl / remaining if remaining else 0

    avg25 = s25["gross"] / days_nov
    avg26_so_far_days = max(1, (today - date(2026, 11, 1)).days + 1) if today.month == 11 and today.year == 2026 else days_nov_26
    avg26 = s26["gross"] / avg26_so_far_days

    report = {
        "nov_2025": s25,
        "nov_2026_ytd": s26,
        "days_in_nov": days_nov_26,
        "avg_daily_nov_2025": round(avg25, 2),
        "avg_daily_nov_2026_so_far": round(avg26, 2),
        "target_double_nov_2025": round(target, 2),
        "min_daily_full_nov_2026": round(daily_full, 2),
        "as_of": today.isoformat(),
        "days_remaining_incl_today": remaining,
        "remaining_to_target_brl": round(remain_brl, 2),
        "min_daily_from_today_brl": round(daily_remain, 2),
        "pct_of_target": round(100 * s26["gross"] / target, 2) if target else 0,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("=== NOVEMBRO 2025 ===")
    print("pedidos:", s25["orders"])
    print("receita:", brl(s25["gross"]))
    print("média/dia (30 dias):", brl(avg25))
    print()
    print("=== NOVEMBRO 2026 (até agora) ===")
    print("pedidos:", s26["orders"])
    print("receita:", brl(s26["gross"]))
    print("média/dia até agora:", brl(avg26), f"({avg26_so_far_days} dias corridos)")
    print()
    print("=== DOBRAR NOV/2025 EM NOV/2026 ===")
    print("meta:", brl(target))
    print("mínimo/dia no mês cheio (30 dias):", brl(daily_full))
    print("já feito:", brl(s26["gross"]), f"({report['pct_of_target']}%)")
    print("falta:", brl(remain_brl))
    print(f"mínimo/dia de {today.isoformat()} a 30/11 ({remaining} dias):", brl(daily_remain))
    print("saved", OUT)


if __name__ == "__main__":
    main()
