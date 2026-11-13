# -*- coding: utf-8 -*-
"""Relatório PDF 03–05/11/2026: GA4 (tagueamento) × verdade WooCommerce loja."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
JSON_OUT = ROOT / "projeto-migracao" / ".secrets" / "ga4-loja-3a5-nov-2026.json"

PURPLE = colors.HexColor("#700053")
WINE = colors.HexColor("#5a0a4a")
GOLD = colors.HexColor("#ffbb3a")
BG = colors.HexColor("#faf7f9")
TEXT = colors.HexColor("#1a1a1a")
MUTED = colors.HexColor("#5c5c5c")
WHITE = colors.white
ROW_ALT = colors.HexColor("#f3eef2")

START = date(2026, 11, 3)
END = date(2026, 11, 5)
AFTER = "2026-11-03T00:00:00"
BEFORE = "2026-11-06T00:00:00"
STATUS_ALL = "processing,completed,pending,on-hold,cancelled,failed,refunded"
PAID = ("processing", "completed")
DAYS = ("2026-11-03", "2026-11-04", "2026-11-05")

# Números do relatório GA4 colado (Páginas e telas por Data, 03–05/11/2026).
GA4 = {
    "2026-11-03": {
        "sessions": 349,
        "events_per_session": 17.36,
        "items_viewed": 158,
        "add_to_carts": 140,
        "checkouts": 51,
        "purchases": 10,
    },
    "2026-11-04": {
        "sessions": 154,
        "events_per_session": 3.23,
        "items_viewed": 222,
        "add_to_carts": 192,
        "checkouts": 65,
        "purchases": 19,
    },
    "2026-11-05": {
        "sessions": 45,
        "events_per_session": 4.11,
        "items_viewed": 84,
        "add_to_carts": 75,
        "checkouts": 24,
        "purchases": 2,
    },
}


def cfg() -> dict:
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


def get(c: dict, path: str):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        headers={
            "Authorization": "Basic " + tok,
            "User-Agent": "pm-ga4-loja-3a5-pdf",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode()), dict(r.headers)


def fetch_orders(c: dict) -> list[dict]:
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
                "status": STATUS_ALL,
            }
        )
        data, h = get(c, f"/wp-json/wc/v3/orders?{q}")
        print(f"orders page {page}: {len(data)}", flush=True)
        orders.extend(data)
        tp = int(h.get("X-WP-TotalPages") or h.get("x-wp-totalpages") or 0)
        if not data or (tp and page >= tp) or len(data) < 100:
            break
        page += 1
        if page > 50:
            break
    return orders


def fetch_customers_created(c: dict) -> list[dict]:
    """Clientes Woo criados no intervalo (filtro local por date_created)."""
    out: list[dict] = []
    page = 1
    start_dt = datetime(2026, 11, 3)
    end_dt = datetime(2026, 11, 6)
    while True:
        q = urllib.parse.urlencode(
            {
                "per_page": 100,
                "page": page,
                "orderby": "registered_date",
                "order": "desc",
                "role": "all",
            }
        )
        try:
            data, h = get(c, f"/wp-json/wc/v3/customers?{q}")
        except urllib.error.HTTPError as err:
            print("customers endpoint", err.code, flush=True)
            return fetch_users_registered(c)
        if not isinstance(data, list) or not data:
            break
        stop = False
        for u in data:
            raw = u.get("date_created") or u.get("date_created_gmt") or ""
            dt = parse_dt(raw)
            if not dt:
                continue
            if dt < start_dt:
                stop = True
                continue
            if dt >= end_dt:
                continue
            out.append(
                {
                    "id": u.get("id"),
                    "email": u.get("email"),
                    "first_name": u.get("first_name") or "",
                    "date": dt.strftime("%Y-%m-%d"),
                    "datetime": dt.strftime("%d/%m/%Y %H:%M"),
                }
            )
        print(f"customers page {page}: scanned {len(data)}, kept {len(out)}", flush=True)
        tp = int(h.get("X-WP-TotalPages") or h.get("x-wp-totalpages") or 0)
        if stop or (tp and page >= tp) or len(data) < 100:
            break
        page += 1
        if page > 80:
            break
    return out


def fetch_users_registered(c: dict) -> list[dict]:
    out: list[dict] = []
    page = 1
    start_dt = datetime(2026, 11, 3)
    end_dt = datetime(2026, 11, 6)
    while True:
        q = urllib.parse.urlencode(
            {
                "per_page": 100,
                "page": page,
                "orderby": "registered_date",
                "order": "desc",
                "context": "edit",
            }
        )
        try:
            data, h = get(c, f"/wp-json/wp/v2/users?{q}")
        except urllib.error.HTTPError as err:
            print("users fallback", err.code, flush=True)
            return out
        if not isinstance(data, list) or not data:
            break
        stop = False
        for u in data:
            raw = u.get("registered_date") or ""
            dt = parse_dt(raw)
            if not dt:
                continue
            if dt < start_dt:
                stop = True
                continue
            if dt >= end_dt:
                continue
            out.append(
                {
                    "id": u.get("id"),
                    "email": u.get("email") or "",
                    "first_name": (u.get("name") or ""),
                    "date": dt.strftime("%Y-%m-%d"),
                    "datetime": dt.strftime("%d/%m/%Y %H:%M"),
                }
            )
        tp = int(h.get("X-WP-TotalPages") or h.get("x-wp-totalpages") or 0)
        if stop or (tp and page >= tp) or len(data) < 100:
            break
        page += 1
        if page > 80:
            break
    return out


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00").split("+")[0])
    except Exception:
        return None


def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(n: float, d: float) -> float:
    return round(100.0 * n / d, 1) if d else 0.0


def slim(o: dict) -> dict:
    dt = parse_dt(o.get("date_created"))
    total = round(float(o.get("total") or 0), 2)
    coupons = []
    coupon_sum = 0.0
    for c in o.get("coupon_lines") or []:
        disc = round(float(c.get("discount") or 0), 2)
        coupon_sum += disc
        coupons.append(
            {
                "code": (c.get("code") or "").strip(),
                "discount": disc,
            }
        )
    # Woo às vezes deixa discount_total=0 e só preenche coupon_lines.
    discount = round(float(o.get("discount_total") or 0), 2)
    if discount <= 0 and coupon_sum > 0:
        discount = round(coupon_sum, 2)
    cid = o.get("customer_id")
    try:
        cid_i = int(cid or 0)
    except Exception:
        cid_i = 0
    return {
        "id": o.get("id"),
        "number": o.get("number") or str(o.get("id") or ""),
        "status": o.get("status") or "",
        "total": total,
        "discount_total": discount,
        "gross_before_discount": round(total + discount, 2),
        "coupons": coupons,
        "customer_id": cid_i,
        "guest": cid_i == 0,
        "email": ((o.get("billing") or {}).get("email") or "").lower(),
        "first_name": ((o.get("billing") or {}).get("first_name") or ""),
        "payment": (o.get("payment_method_title") or o.get("payment_method") or "—"),
        "date": dt.strftime("%Y-%m-%d") if dt else "unknown",
        "datetime": dt.strftime("%d/%m/%Y %H:%M") if dt else "—",
        "unit": next(
            (m.get("value") for m in (o.get("meta_data") or []) if m.get("key") == "Unidade"),
            "",
        ),
    }


def empty_day() -> dict:
    return {
        "orders_all": 0,
        "paid_orders": 0,
        "paid_net": 0.0,
        "paid_gross_before_discount": 0.0,
        "paid_discount": 0.0,
        "pending": 0,
        "cancelled": 0,
        "failed": 0,
        "refunded": 0,
        "refunded_net": 0.0,
        "guest_paid": 0,
        "logged_paid": 0,
        "coupon_uses": 0,
    }


def aggregate(orders: list[dict], customers: list[dict]) -> dict:
    by_day: dict[str, dict] = {d: empty_day() for d in DAYS}
    coupon_rank: dict[str, dict] = defaultdict(lambda: {"uses": 0, "discount": 0.0})
    paid_list: list[dict] = []
    all_slim: list[dict] = []

    for o in orders:
        s = slim(o)
        all_slim.append(s)
        day = s["date"] if s["date"] in by_day else None
        if not day:
            continue
        bucket = by_day[day]
        bucket["orders_all"] += 1
        st = s["status"]
        if st in PAID:
            bucket["paid_orders"] += 1
            bucket["paid_net"] += s["total"]
            bucket["paid_gross_before_discount"] += s["gross_before_discount"]
            bucket["paid_discount"] += s["discount_total"]
            if s["guest"]:
                bucket["guest_paid"] += 1
            else:
                bucket["logged_paid"] += 1
            if s["coupons"]:
                bucket["coupon_uses"] += 1
            for cpn in s["coupons"]:
                code = (cpn["code"] or "(sem código)").upper()
                coupon_rank[code]["uses"] += 1
                coupon_rank[code]["discount"] += cpn["discount"]
            paid_list.append(s)
        elif st in ("pending", "on-hold"):
            bucket["pending"] += 1
        elif st == "cancelled":
            bucket["cancelled"] += 1
        elif st == "failed":
            bucket["failed"] += 1
        elif st == "refunded":
            bucket["refunded"] += 1
            bucket["refunded_net"] += s["total"]

    for d, b in by_day.items():
        for k in (
            "paid_net",
            "paid_gross_before_discount",
            "paid_discount",
            "refunded_net",
        ):
            b[k] = round(b[k], 2)
        b["ticket_avg"] = round(b["paid_net"] / b["paid_orders"], 2) if b["paid_orders"] else 0.0

    totals = empty_day()
    for d in DAYS:
        for k, v in by_day[d].items():
            if k == "ticket_avg":
                continue
            totals[k] = totals.get(k, 0) + v
    for k in ("paid_net", "paid_gross_before_discount", "paid_discount", "refunded_net"):
        totals[k] = round(float(totals[k]), 2)
    totals["ticket_avg"] = (
        round(totals["paid_net"] / totals["paid_orders"], 2) if totals["paid_orders"] else 0.0
    )

    customers_by_day = {d: 0 for d in DAYS}
    for u in customers:
        if u["date"] in customers_by_day:
            customers_by_day[u["date"]] += 1

    coupons_sorted = sorted(
        (
            {"code": code, "uses": v["uses"], "discount": round(v["discount"], 2)}
            for code, v in coupon_rank.items()
        ),
        key=lambda x: (-x["discount"], -x["uses"], x["code"]),
    )

    return {
        "by_day": by_day,
        "totals": totals,
        "paid_orders": paid_list,
        "all_orders": all_slim,
        "coupons": coupons_sorted,
        "customers_by_day": customers_by_day,
        "customers_total": len(customers),
        "customers": customers,
    }


def ga4_totals() -> dict:
    t = {
        "sessions": 0,
        "items_viewed": 0,
        "add_to_carts": 0,
        "checkouts": 0,
        "purchases": 0,
    }
    for d in DAYS:
        g = GA4[d]
        for k in t:
            t[k] += g[k]
    t["conversion_pct"] = pct(t["purchases"], t["sessions"])
    t["view_to_cart_pct"] = pct(t["add_to_carts"], t["items_viewed"])
    t["cart_to_checkout_pct"] = pct(t["checkouts"], t["add_to_carts"])
    t["checkout_to_purchase_pct"] = pct(t["purchases"], t["checkouts"])
    return t


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "t", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=18,
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=4, leading=22,
        ),
        "subtitle": ParagraphStyle(
            "s", parent=base["Normal"], fontName="Helvetica", fontSize=11,
            textColor=GOLD, alignment=TA_CENTER, spaceAfter=2, leading=14,
        ),
        "meta": ParagraphStyle(
            "m", parent=base["Normal"], fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#f0e6ee"), alignment=TA_CENTER, leading=12,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12,
            textColor=PURPLE, spaceBefore=10, spaceAfter=6, leading=15,
        ),
        "body": ParagraphStyle(
            "b", parent=base["Normal"], fontName="Helvetica", fontSize=9,
            textColor=TEXT, leading=12,
        ),
        "note": ParagraphStyle(
            "n", parent=base["Normal"], fontName="Helvetica", fontSize=8,
            textColor=MUTED, leading=11,
        ),
        "kpi_label": ParagraphStyle(
            "kl", parent=base["Normal"], fontName="Helvetica", fontSize=7,
            textColor=MUTED, alignment=TA_CENTER, leading=9,
        ),
        "kpi_value": ParagraphStyle(
            "kv", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=11,
            textColor=PURPLE, alignment=TA_CENTER, leading=13,
        ),
        "cell": ParagraphStyle(
            "c", parent=base["Normal"], fontName="Helvetica", fontSize=7.5,
            textColor=TEXT, leading=9,
        ),
        "cell_r": ParagraphStyle(
            "cr", parent=base["Normal"], fontName="Helvetica", fontSize=7.5,
            textColor=TEXT, alignment=TA_RIGHT, leading=9,
        ),
        "th": ParagraphStyle(
            "th", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=7.5,
            textColor=WHITE, leading=9,
        ),
        "th_r": ParagraphStyle(
            "thr", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=7.5,
            textColor=WHITE, alignment=TA_RIGHT, leading=9,
        ),
    }


def add_footer(canvas, doc):
    canvas.saveState()
    w, _ = A4
    canvas.setFillColor(WINE)
    canvas.rect(0, 0, w, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, 12 * mm, w, 0.6 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(16 * mm, 5 * mm, "Pello Menos  ·  GA4 × Loja  ·  Confidencial")
    canvas.drawRightString(w - 16 * mm, 5 * mm, f"Página {doc.page}")
    canvas.restoreState()


def data_table(headers, rows, col_widths) -> Table:
    t = Table([headers] + rows, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 1, GOLD),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dcc9d7")),
    ]
    for i in range(1, len(rows) + 1):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(cmds))
    return t


def kpi_block(styles, labels_values, usable_w) -> Table:
    n = len(labels_values)
    w = usable_w / n
    row1 = [Paragraph(lab, styles["kpi_label"]) for lab, _ in labels_values]
    row2 = [Paragraph(val, styles["kpi_value"]) for _, val in labels_values]
    t = Table([row1, row2], colWidths=[w] * n)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BG),
                ("BOX", (0, 0), (-1, -1), 1, GOLD),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e4d6e0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


def day_label(d: str) -> str:
    return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")


def build_pdf(path: Path, payload: dict, generated_at: datetime) -> None:
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=18 * mm,
        title="GA4 × Loja — 03 a 05/11/2026",
        author="Pello Menos E-commerce",
    )
    story = []
    usable_w = A4[0] - 28 * mm
    woo = payload["woo"]
    ga4t = payload["ga4"]["totals"]
    totals = woo["totals"]

    cover_inner = [
        Paragraph("GA4 × Loja — Relatório cruzado", styles["title"]),
        Paragraph("03/11/2026 a 05/11/2026", styles["subtitle"]),
        Spacer(1, 2 * mm),
        Paragraph("loja.pellomenos.com.br", styles["meta"]),
        Paragraph(
            f"Gerado em {generated_at.strftime('%d/%m/%Y às %H:%M')} · America/Sao_Paulo",
            styles["meta"],
        ),
    ]
    cover = Table([[cover_inner]], colWidths=[usable_w])
    cover.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PURPLE),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("BOX", (0, 0), (-1, -1), 2, GOLD),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(cover)
    story.append(Spacer(1, 6 * mm))

    # Resumo executivo
    story.append(Paragraph("1. Resumo executivo", styles["h2"]))
    story.append(
        kpi_block(
            styles,
            [
                ("Pedidos pagos (Woo)", str(totals["paid_orders"])),
                ("Receita líquida", brl(totals["paid_net"])),
                ("Descontos", brl(totals["paid_discount"])),
                ("Ticket médio", brl(totals["ticket_avg"])),
                ("Contas criadas", str(woo["customers_total"])),
            ],
            usable_w,
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        kpi_block(
            styles,
            [
                ("Compras GA4", str(ga4t["purchases"])),
                ("Sessões GA4", str(ga4t["sessions"])),
                ("Conv. GA4", f"{ga4t['conversion_pct']}%"),
                ("Gap GA4−Woo", str(ga4t["purchases"] - totals["paid_orders"])),
                ("Estornos Woo", str(totals["refunded"])),
            ],
            usable_w,
        )
    )
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "Receita líquida = soma do <b>total</b> dos pedidos <b>processing + completed</b> "
            "(já com cupom). Bruto antes de desconto = total + discount_total. "
            "Compras GA4 vêm do relatório de tagueamento; pedidos Woo são a verdade do e-commerce.",
            styles["note"],
        )
    )

    # GA4 por dia
    story.append(Paragraph("2. GA4 — tagueamento por dia", styles["h2"]))
    headers = [
        Paragraph("Data", styles["th"]),
        Paragraph("Sessões", styles["th_r"]),
        Paragraph("Itens vistos", styles["th_r"]),
        Paragraph("Add carrinho", styles["th_r"]),
        Paragraph("Finalizações", styles["th_r"]),
        Paragraph("Compras", styles["th_r"]),
        Paragraph("Conv.", styles["th_r"]),
    ]
    rows = []
    for d in DAYS:
        g = GA4[d]
        rows.append(
            [
                Paragraph(day_label(d), styles["cell"]),
                Paragraph(str(g["sessions"]), styles["cell_r"]),
                Paragraph(str(g["items_viewed"]), styles["cell_r"]),
                Paragraph(str(g["add_to_carts"]), styles["cell_r"]),
                Paragraph(str(g["checkouts"]), styles["cell_r"]),
                Paragraph(str(g["purchases"]), styles["cell_r"]),
                Paragraph(f"{pct(g['purchases'], g['sessions'])}%", styles["cell_r"]),
            ]
        )
    rows.append(
        [
            Paragraph("<b>Total</b>", styles["cell"]),
            Paragraph(f"<b>{ga4t['sessions']}</b>", styles["cell_r"]),
            Paragraph(f"<b>{ga4t['items_viewed']}</b>", styles["cell_r"]),
            Paragraph(f"<b>{ga4t['add_to_carts']}</b>", styles["cell_r"]),
            Paragraph(f"<b>{ga4t['checkouts']}</b>", styles["cell_r"]),
            Paragraph(f"<b>{ga4t['purchases']}</b>", styles["cell_r"]),
            Paragraph(f"<b>{ga4t['conversion_pct']}%</b>", styles["cell_r"]),
        ]
    )
    story.append(
        data_table(
            headers,
            rows,
            [28 * mm, 22 * mm, 24 * mm, 24 * mm, 26 * mm, 22 * mm, usable_w - 146 * mm],
        )
    )
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            f"Funil GA4 (total): visto→carrinho {ga4t['view_to_cart_pct']}% · "
            f"carrinho→finalização {ga4t['cart_to_checkout_pct']}% · "
            f"finalização→compra {ga4t['checkout_to_purchase_pct']}% "
            f"(gargalo principal do tagueamento).",
            styles["note"],
        )
    )

    # Loja por dia
    story.append(Paragraph("3. Loja Woo — pedidos e receita por dia", styles["h2"]))
    headers = [
        Paragraph("Data", styles["th"]),
        Paragraph("Pagos", styles["th_r"]),
        Paragraph("Líquido", styles["th_r"]),
        Paragraph("Bruto*", styles["th_r"]),
        Paragraph("Desconto", styles["th_r"]),
        Paragraph("Pend/Canc/Fail", styles["th_r"]),
        Paragraph("Contas", styles["th_r"]),
    ]
    rows = []
    for d in DAYS:
        b = woo["by_day"][d]
        rows.append(
            [
                Paragraph(day_label(d), styles["cell"]),
                Paragraph(str(b["paid_orders"]), styles["cell_r"]),
                Paragraph(brl(b["paid_net"]), styles["cell_r"]),
                Paragraph(brl(b["paid_gross_before_discount"]), styles["cell_r"]),
                Paragraph(brl(b["paid_discount"]), styles["cell_r"]),
                Paragraph(
                    f"{b['pending']}/{b['cancelled']}/{b['failed']}",
                    styles["cell_r"],
                ),
                Paragraph(str(woo["customers_by_day"].get(d, 0)), styles["cell_r"]),
            ]
        )
    rows.append(
        [
            Paragraph("<b>Total</b>", styles["cell"]),
            Paragraph(f"<b>{totals['paid_orders']}</b>", styles["cell_r"]),
            Paragraph(f"<b>{brl(totals['paid_net'])}</b>", styles["cell_r"]),
            Paragraph(f"<b>{brl(totals['paid_gross_before_discount'])}</b>", styles["cell_r"]),
            Paragraph(f"<b>{brl(totals['paid_discount'])}</b>", styles["cell_r"]),
            Paragraph(
                f"<b>{totals['pending']}/{totals['cancelled']}/{totals['failed']}</b>",
                styles["cell_r"],
            ),
            Paragraph(f"<b>{woo['customers_total']}</b>", styles["cell_r"]),
        ]
    )
    story.append(
        data_table(
            headers,
            rows,
            [26 * mm, 18 * mm, 28 * mm, 28 * mm, 26 * mm, 32 * mm, usable_w - 158 * mm],
        )
    )
    story.append(
        Paragraph(
            "*Bruto = total do pedido + desconto de cupom (antes do desconto). "
            f"Estornos no período: {totals['refunded']} ({brl(totals['refunded_net'])}). "
            f"Guest vs logado (pagos): {totals['guest_paid']} / {totals['logged_paid']}.",
            styles["note"],
        )
    )

    # Cruzamento
    story.append(Paragraph("4. Cruzamento GA4 × Loja", styles["h2"]))
    headers = [
        Paragraph("Data", styles["th"]),
        Paragraph("Compras GA4", styles["th_r"]),
        Paragraph("Pedidos pagos Woo", styles["th_r"]),
        Paragraph("Diferença", styles["th_r"]),
        Paragraph("Receita Woo", styles["th_r"]),
        Paragraph("Finaliz. GA4", styles["th_r"]),
    ]
    rows = []
    for d in DAYS:
        g = GA4[d]
        b = woo["by_day"][d]
        diff = g["purchases"] - b["paid_orders"]
        rows.append(
            [
                Paragraph(day_label(d), styles["cell"]),
                Paragraph(str(g["purchases"]), styles["cell_r"]),
                Paragraph(str(b["paid_orders"]), styles["cell_r"]),
                Paragraph(str(diff), styles["cell_r"]),
                Paragraph(brl(b["paid_net"]), styles["cell_r"]),
                Paragraph(str(g["checkouts"]), styles["cell_r"]),
            ]
        )
    rows.append(
        [
            Paragraph("<b>Total</b>", styles["cell"]),
            Paragraph(f"<b>{ga4t['purchases']}</b>", styles["cell_r"]),
            Paragraph(f"<b>{totals['paid_orders']}</b>", styles["cell_r"]),
            Paragraph(
                f"<b>{ga4t['purchases'] - totals['paid_orders']}</b>",
                styles["cell_r"],
            ),
            Paragraph(f"<b>{brl(totals['paid_net'])}</b>", styles["cell_r"]),
            Paragraph(f"<b>{ga4t['checkouts']}</b>", styles["cell_r"]),
        ]
    )
    story.append(
        data_table(
            headers,
            rows,
            [28 * mm, 28 * mm, 34 * mm, 24 * mm, 32 * mm, usable_w - 146 * mm],
        )
    )
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "Diferença positiva (GA4 &gt; Woo) pode indicar evento de compra disparado "
            "sem pedido criado, teste, ou atraso de status. Diferença negativa indica "
            "pedido pago sem purchase no GA4 (tag ausente/bloqueada). "
            "Finalizações GA4 bem acima de pedidos pagos reforçam abandono / falha no "
            "checkout (Accesstage, validação, overlay) — tema tratado em 06/11.",
            styles["note"],
        )
    )

    # Cupons
    story.append(Paragraph("5. Cupons e descontos (pedidos pagos)", styles["h2"]))
    if woo["coupons"]:
        headers = [
            Paragraph("Cupom", styles["th"]),
            Paragraph("Usos", styles["th_r"]),
            Paragraph("Desconto", styles["th_r"]),
        ]
        rows = []
        for cpn in woo["coupons"][:25]:
            rows.append(
                [
                    Paragraph(cpn["code"], styles["cell"]),
                    Paragraph(str(cpn["uses"]), styles["cell_r"]),
                    Paragraph(brl(cpn["discount"]), styles["cell_r"]),
                ]
            )
        rows.append(
            [
                Paragraph("<b>Total descontos nos pagos</b>", styles["cell"]),
                Paragraph(f"<b>{totals['coupon_uses']}</b>", styles["cell_r"]),
                Paragraph(f"<b>{brl(totals['paid_discount'])}</b>", styles["cell_r"]),
            ]
        )
        story.append(data_table(headers, rows, [usable_w - 70 * mm, 28 * mm, 42 * mm]))
    else:
        story.append(Paragraph("Nenhum cupom aplicado nos pedidos pagos do período.", styles["body"]))

    # Contas
    story.append(Paragraph("6. Contas criadas", styles["h2"]))
    headers = [
        Paragraph("Data", styles["th"]),
        Paragraph("Novas contas", styles["th_r"]),
        Paragraph("Pedidos pagos guest", styles["th_r"]),
        Paragraph("Pedidos pagos logados", styles["th_r"]),
    ]
    rows = []
    for d in DAYS:
        b = woo["by_day"][d]
        rows.append(
            [
                Paragraph(day_label(d), styles["cell"]),
                Paragraph(str(woo["customers_by_day"].get(d, 0)), styles["cell_r"]),
                Paragraph(str(b["guest_paid"]), styles["cell_r"]),
                Paragraph(str(b["logged_paid"]), styles["cell_r"]),
            ]
        )
    rows.append(
        [
            Paragraph("<b>Total</b>", styles["cell"]),
            Paragraph(f"<b>{woo['customers_total']}</b>", styles["cell_r"]),
            Paragraph(f"<b>{totals['guest_paid']}</b>", styles["cell_r"]),
            Paragraph(f"<b>{totals['logged_paid']}</b>", styles["cell_r"]),
        ]
    )
    story.append(
        data_table(headers, rows, [40 * mm, 40 * mm, 50 * mm, usable_w - 130 * mm])
    )

    # Lista pedidos pagos
    story.append(Paragraph("7. Lista — pedidos pagos", styles["h2"]))
    headers = [
        Paragraph("#", styles["th"]),
        Paragraph("Data/hora", styles["th"]),
        Paragraph("Cliente", styles["th"]),
        Paragraph("Cupom", styles["th"]),
        Paragraph("Desc.", styles["th_r"]),
        Paragraph("Total", styles["th_r"]),
    ]
    rows = []
    for o in woo["paid_orders"]:
        name = (o["first_name"] or o["email"] or "—")[:28]
        cpn = ", ".join(c["code"] for c in o["coupons"]) or "—"
        rows.append(
            [
                Paragraph(str(o["number"]), styles["cell"]),
                Paragraph(o["datetime"], styles["cell"]),
                Paragraph(name, styles["cell"]),
                Paragraph(cpn[:22], styles["cell"]),
                Paragraph(brl(o["discount_total"]), styles["cell_r"]),
                Paragraph(brl(o["total"]), styles["cell_r"]),
            ]
        )
    if not rows:
        rows.append(
            [
                Paragraph("—", styles["cell"]),
                Paragraph("Sem pedidos pagos", styles["cell"]),
                Paragraph("—", styles["cell"]),
                Paragraph("—", styles["cell"]),
                Paragraph(brl(0), styles["cell_r"]),
                Paragraph(brl(0), styles["cell_r"]),
            ]
        )
    story.append(
        data_table(
            headers,
            rows,
            [20 * mm, 28 * mm, usable_w - 120 * mm, 28 * mm, 22 * mm, 22 * mm],
        )
    )

    # Notas
    story.append(Paragraph("8. Notas e fontes", styles["h2"]))
    for n in [
        "GA4: relatório Páginas e telas por Data, propriedade Pello Menos LOJA, 03–05/11/2026 (números fornecidos).",
        f"Loja: WooCommerce REST {payload['source']} — orders after={AFTER} before={BEFORE}.",
        "Pago = status processing ou completed. Estornos listados à parte.",
        "03/11: alto volume de eventos/sessão no GA4 (17,36) com conversão baixa — investigar tráfego/tag.",
        "04/11: melhor conversão GA4 (12,34%) e maior fatia das compras do período.",
        "05/11: volume menor; dados GA4 podem estar parcialmente processados no dia da captura.",
        "Checkout: correções de overlay/UF/nome publicadas em 06/11 (histórico 43) — fora deste intervalo.",
    ]:
        story.append(Paragraph(f"• {n}", styles["note"]))

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)


def main() -> None:
    generated_at = datetime.now()
    c = cfg()
    print(f"Fetching orders {AFTER} -> {BEFORE} from {c['url']}", flush=True)
    raw = fetch_orders(c)
    print("Fetching customers…", flush=True)
    customers = fetch_customers_created(c)
    print("customers in range", len(customers), flush=True)

    woo = aggregate(raw, customers)
    ga4_tot = ga4_totals()

    # checksum
    checksum = round(sum(o["total"] for o in woo["paid_orders"]), 2)
    assert checksum == woo["totals"]["paid_net"], (checksum, woo["totals"]["paid_net"])

    # sample peek
    sample_ids = [o["id"] for o in woo["paid_orders"][:3]]
    samples = []
    for oid in sample_ids:
        try:
            data, _ = get(c, f"/wp-json/wc/v3/orders/{oid}")
            samples.append(
                {
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "total": data.get("total"),
                    "discount_total": data.get("discount_total"),
                    "date_created": data.get("date_created"),
                }
            )
        except Exception as err:
            samples.append({"id": oid, "error": str(err)})

    payload = {
        "as_of": generated_at.isoformat(timespec="seconds"),
        "period": {"start": START.isoformat(), "end": END.isoformat(), "after": AFTER, "before": BEFORE},
        "source": c["url"],
        "ga4": {"by_day": GA4, "totals": ga4_tot},
        "woo": {
            "by_day": woo["by_day"],
            "totals": woo["totals"],
            "coupons": woo["coupons"],
            "customers_total": woo["customers_total"],
            "customers_by_day": woo["customers_by_day"],
            "customers": woo["customers"],
            "paid_orders": woo["paid_orders"],
            "orders_all_count": len(woo["all_orders"]),
        },
        "cross": {
            "ga4_purchases": ga4_tot["purchases"],
            "woo_paid_orders": woo["totals"]["paid_orders"],
            "gap": ga4_tot["purchases"] - woo["totals"]["paid_orders"],
        },
        "checksum_paid_net": checksum,
        "samples": samples,
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("json", JSON_OUT)

    pdf_path = Path.home() / "Desktop" / "Relatorio-GA4-x-Loja-03a05-Nov-2026.pdf"
    build_pdf(pdf_path, payload, generated_at)

    print()
    print("=== RESUMO 03–05/11 ===")
    print("GA4 compras:", ga4_tot["purchases"], "sessões:", ga4_tot["sessions"])
    print("Woo pagos:", woo["totals"]["paid_orders"], brl(woo["totals"]["paid_net"]))
    print("descontos:", brl(woo["totals"]["paid_discount"]))
    print("bruto antes desc:", brl(woo["totals"]["paid_gross_before_discount"]))
    print("contas:", woo["customers_total"])
    print("gap GA4-Woo:", ga4_tot["purchases"] - woo["totals"]["paid_orders"])
    print("pdf:", pdf_path)
    print("ok checksum", checksum)


if __name__ == "__main__":
    main()
