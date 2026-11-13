# -*- coding: utf-8 -*-
"""Nov/2026 a partir do lançamento da promo (03/11 08:00) vs dobrar Nov/2025."""
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
OUT = ROOT / "projeto-migracao" / ".secrets" / "sales-nov-promo-launch.json"

# Lançamento Esquenta no e-commerce
PROMO_START = datetime(2026, 11, 3, 8, 0, 0)
NOV_END = datetime(2026, 11, 30, 23, 59, 59)


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
            "User-Agent": "pm-nov-promo",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode()), dict(r.headers)


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00").split("+")[0])
    except Exception:
        return None


def fetch_range(c, after: str, before: str) -> list[dict]:
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
        print(f"page {page}: {len(data)}", flush=True)
        orders.extend(data)
        tp = int(h.get("X-WP-TotalPages") or h.get("x-wp-totalpages") or 0)
        if not data or (tp and page >= tp) or len(data) < 100:
            break
        page += 1
        if page > 200:
            break
    return orders


def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main() -> None:
    c = cfg()

    # Nov 2025 full month (base para dobrar)
    o25 = fetch_range(c, "2025-11-01T00:00:00", "2025-12-01T00:00:00")
    gross25 = sum(float(o.get("total") or 0) for o in o25)

    # Nov 2026 from promo launch 03/11 08:00 through end of month API window
    # Fetch from 03/11 00:00 then filter >= 08:00 locally (Woo after is inclusive-ish)
    o26_raw = fetch_range(c, "2026-11-03T00:00:00", "2026-12-01T00:00:00")
    o26 = []
    by_day = defaultdict(float)
    before_8h = []
    for o in o26_raw:
        dt = parse_dt(o.get("date_created"))
        if not dt:
            continue
        total = float(o.get("total") or 0)
        if dt < PROMO_START:
            before_8h.append((dt.isoformat(sep=" "), total, o.get("id")))
            continue
        if dt > NOV_END:
            continue
        o26.append(o)
        by_day[dt.strftime("%Y-%m-%d")] += total

    gross26 = sum(float(o.get("total") or 0) for o in o26)
    target = gross25 * 2

    today = date.today()
    now = datetime.now()
    # dias de calendário com promo ativa no mês: 03..30 = 28 dias
    promo_calendar_days = (date(2026, 11, 30) - date(2026, 11, 3)).days + 1  # 28
    # dias restantes incl. hoje até 30/11
    if today.year == 2026 and today.month == 11:
        days_left = (date(2026, 11, 30) - today).days + 1
    else:
        days_left = promo_calendar_days

    # horas desde o lançamento até agora (para média "desde 8h")
    hours_elapsed = max((now - PROMO_START).total_seconds() / 3600.0, 1 / 60)
    # dias equivalentes desde 8h do dia 3
    days_elapsed_equiv = hours_elapsed / 24.0

    remain = target - gross26
    daily_full_promo_window = target / promo_calendar_days
    daily_from_today = remain / days_left if days_left else 0
    avg_since_launch = gross26 / days_elapsed_equiv

    report = {
        "promo_start": PROMO_START.isoformat(sep=" "),
        "nov_2025_orders": len(o25),
        "nov_2025_gross": round(gross25, 2),
        "nov_2026_from_launch_orders": len(o26),
        "nov_2026_from_launch_gross": round(gross26, 2),
        "excluded_before_8h_on_03": [
            {"when": w, "total": t, "id": i} for w, t, i in before_8h
        ],
        "excluded_before_8h_count": len(before_8h),
        "excluded_before_8h_gross": round(sum(t for _, t, _ in before_8h), 2),
        "by_day_from_launch": {k: round(v, 2) for k, v in sorted(by_day.items())},
        "target_double_nov_2025": round(target, 2),
        "promo_calendar_days_03_to_30": promo_calendar_days,
        "min_daily_across_promo_window": round(daily_full_promo_window, 2),
        "as_of": now.isoformat(sep=" ", timespec="minutes"),
        "hours_since_launch": round(hours_elapsed, 2),
        "days_equiv_since_launch": round(days_elapsed_equiv, 3),
        "avg_daily_pace_since_launch": round(avg_since_launch, 2),
        "days_left_incl_today": days_left,
        "remaining_brl": round(remain, 2),
        "min_daily_from_today": round(daily_from_today, 2),
        "pct_of_target": round(100 * gross26 / target, 2) if target else 0,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("=== BASE: NOV/2025 (mês cheio) ===")
    print("pedidos:", len(o25), "| receita:", brl(gross25))
    print()
    print("=== NOV/2026 desde promo 03/11 08:00 ===")
    print("excluídos antes das 8h no dia 3:", len(before_8h), brl(sum(t for _, t, _ in before_8h)))
    for w, t, i in before_8h:
        print(f"  - #{i} {w} {brl(t)}")
    print("pedidos desde 8h:", len(o26), "| receita:", brl(gross26))
    print("por dia:")
    for d, v in sorted(by_day.items()):
        print(f"  {d}: {brl(v)}")
    print("ritmo desde o lançamento:", brl(avg_since_launch), f"/dia equiv. ({hours_elapsed:.1f}h)")
    print()
    print("=== DOBRAR NOV/2025 NA JANELA DA PROMO (03→30) ===")
    print("meta:", brl(target))
    print(f"mínimo/dia nos {promo_calendar_days} dias (03–30):", brl(daily_full_promo_window))
    print(f"já feito desde 8h: {brl(gross26)} ({report['pct_of_target']}%)")
    print("falta:", brl(remain))
    print(f"mínimo/dia de hoje a 30/11 ({days_left} dias):", brl(daily_from_today))
    print("saved", OUT)


if __name__ == "__main__":
    main()
