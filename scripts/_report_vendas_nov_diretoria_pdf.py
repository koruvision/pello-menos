# -*- coding: utf-8 -*-
"""READ-ONLY: relatório PDF de vendas loja (01/11 → hoje) para diretoria."""
from __future__ import annotations

import base64
import json
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
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
JSON_OUT = ROOT / "projeto-migracao" / ".secrets" / "sales-nov-diretoria.json"

PURPLE = colors.HexColor("#700053")
WINE = colors.HexColor("#5a0a4a")
GOLD = colors.HexColor("#ffbb3a")
BG = colors.HexColor("#faf7f9")
TEXT = colors.HexColor("#1a1a1a")
MUTED = colors.HexColor("#5c5c5c")
WHITE = colors.white
ROW_ALT = colors.HexColor("#f3eef2")

# No Woo, "processing" e "completed" = pagamento recebido.
# Na loja quase todos ficam em processing; completed sozinho zera o relatório.
STATUS_MAIN = ("processing", "completed")
STATUS_ALL = "processing,completed,pending,on-hold,cancelled,failed,refunded"


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
            "User-Agent": "pm-vendas-diretoria-pdf",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode()), dict(r.headers)


def fetch_range(c: dict, after: str, before: str) -> list[dict]:
    orders: list[dict] = []
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
                "status": STATUS_ALL,
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


def fetch_abandonment(c: dict, after: str, before: str) -> dict:
    q = urllib.parse.urlencode({"after": after, "before": before})
    data, _ = get(c, f"/wp-json/pm-wcar/v1/abandonment-report?{q}")
    abandoned = data.get("abandoned") or {}
    recovered = data.get("recovered") or {}
    normal = data.get("normal") or {}
    return {
        "abandoned_carts": int(abandoned.get("carts") or 0),
        "abandoned_gross": round(float(abandoned.get("gross") or 0), 2),
        "recovered_carts": int(recovered.get("carts") or 0),
        "recovered_gross": round(float(recovered.get("gross") or 0), 2),
        "normal_carts": int(normal.get("carts") or 0),
        "normal_gross": round(float(normal.get("gross") or 0), 2),
        "by_status": data.get("by_status") or {},
        "source": data.get("source") or "",
    }


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00").split("+")[0])
    except Exception:
        return None


def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def status_label(s: str) -> str:
    # Para a diretoria: processing/completed = pagamento recebido (sem jargão Woo).
    if s in ("processing", "completed"):
        return "Pago"
    return {
        "refunded": "Estornado",
        "pending": "Pendente",
        "on-hold": "Em espera",
        "cancelled": "Cancelado",
        "failed": "Falhou",
    }.get(s or "", s or "—")


def bucket_orders(slim: list[dict]) -> dict[str, list[dict]]:
    buckets = {
        "paid": [],
        "pending": [],
        "cancelled": [],
        "failed": [],
        "refunded": [],
        "other": [],
    }
    for o in slim:
        st = o["status"]
        if st in STATUS_MAIN:
            buckets["paid"].append(o)
        elif st in ("pending", "on-hold"):
            buckets["pending"].append(o)
        elif st == "cancelled":
            buckets["cancelled"].append(o)
        elif st == "failed":
            buckets["failed"].append(o)
        elif st == "refunded":
            buckets["refunded"].append(o)
        else:
            buckets["other"].append(o)
    return buckets


def group_totals(rows: list[dict]) -> dict:
    return {
        "orders": len(rows),
        "gross": round(sum(float(o["total"]) for o in rows), 2),
    }


def build_funnel(buckets: dict[str, list[dict]], abandon: dict) -> dict:
    paid = group_totals(buckets["paid"])
    pending = group_totals(buckets["pending"])
    cancelled = group_totals(buckets["cancelled"])
    failed = group_totals(buckets["failed"])
    refunded = group_totals(buckets["refunded"])
    other = group_totals(buckets["other"])
    orders_created = (
        paid["orders"]
        + pending["orders"]
        + cancelled["orders"]
        + failed["orders"]
        + refunded["orders"]
        + other["orders"]
    )
    unpaid_attempts = pending["orders"] + cancelled["orders"] + failed["orders"] + other["orders"]
    purchase_attempts = orders_created + int(abandon["abandoned_carts"])
    return {
        "paid": paid,
        "pending": pending,
        "cancelled": cancelled,
        "failed": failed,
        "refunded": refunded,
        "other": other,
        "orders_created": orders_created,
        "unpaid_order_attempts": unpaid_attempts,
        "purchase_attempts": purchase_attempts,
        "abandoned_carts": int(abandon["abandoned_carts"]),
        "abandoned_gross": float(abandon["abandoned_gross"]),
        "conversion_vs_attempts_pct": round(
            100 * paid["orders"] / purchase_attempts, 1
        )
        if purchase_attempts
        else 0.0,
        "conversion_vs_orders_pct": round(100 * paid["orders"] / orders_created, 1)
        if orders_created
        else 0.0,
    }


def pay_label(o: dict) -> str:
    title = (o.get("payment_method_title") or "").strip()
    method = (o.get("payment_method") or "").strip()
    return title or method or "—"


def slim_order(o: dict) -> dict:
    dt = parse_dt(o.get("date_created"))
    return {
        "id": o.get("id"),
        "number": o.get("number") or str(o.get("id") or ""),
        "status": o.get("status") or "",
        "total": round(float(o.get("total") or 0), 2),
        "date": dt.strftime("%Y-%m-%d") if dt else "unknown",
        "datetime": dt.strftime("%d/%m/%Y %H:%M") if dt else "—",
        "payment": pay_label(o),
    }


def summarize(main: list[dict], refunded: list[dict], start: date, end: date) -> dict:
    by_day: dict[str, dict] = defaultdict(lambda: {"orders": 0, "gross": 0.0})
    gross = 0.0
    for o in main:
        t = float(o["total"])
        gross += t
        by_day[o["date"]]["orders"] += 1
        by_day[o["date"]]["gross"] += t

    days_span = max(1, (end - start).days + 1)
    days_with = len([d for d, v in by_day.items() if v["orders"] > 0 and d != "unknown"])
    n = len(main)
    return {
        "orders": n,
        "gross": round(gross, 2),
        "ticket_avg": round(gross / n, 2) if n else 0.0,
        "daily_avg": round(gross / days_span, 2),
        "days_span": days_span,
        "days_with_sales": days_with,
        "by_day": {
            k: {"orders": v["orders"], "gross": round(v["gross"], 2)}
            for k, v in sorted(by_day.items())
        },
        "refunded_orders": len(refunded),
        "refunded_gross": round(sum(float(o["total"]) for o in refunded), 2),
    }


def desktop_pdf_path(start: date, end: date) -> Path:
    name = (
        f"Relatorio-Vendas-PelloMenos-"
        f"{start.day:02d}a{end.day:02d}-Nov-{start.year}.pdf"
    )
    return Path.home() / "Desktop" / name


def build_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "pmTitle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=WHITE,
            alignment=TA_CENTER,
            spaceAfter=4,
            leading=24,
        ),
        "subtitle": ParagraphStyle(
            "pmSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11,
            textColor=GOLD,
            alignment=TA_CENTER,
            spaceAfter=2,
            leading=14,
        ),
        "meta": ParagraphStyle(
            "pmMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#f0e6ee"),
            alignment=TA_CENTER,
            leading=12,
        ),
        "h2": ParagraphStyle(
            "pmH2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=PURPLE,
            spaceBefore=10,
            spaceAfter=8,
            leading=16,
        ),
        "body": ParagraphStyle(
            "pmBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=TEXT,
            leading=12,
        ),
        "note": ParagraphStyle(
            "pmNote",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            leading=11,
        ),
        "kpi_label": ParagraphStyle(
            "pmKpiLabel",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
            leading=10,
        ),
        "kpi_value": ParagraphStyle(
            "pmKpiValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=PURPLE,
            alignment=TA_CENTER,
            leading=14,
        ),
        "cell": ParagraphStyle(
            "pmCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=TEXT,
            leading=10,
        ),
        "cell_r": ParagraphStyle(
            "pmCellR",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=TEXT,
            alignment=TA_RIGHT,
            leading=10,
        ),
        "th": ParagraphStyle(
            "pmTh",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=WHITE,
            leading=10,
        ),
        "th_r": ParagraphStyle(
            "pmThR",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=WHITE,
            alignment=TA_RIGHT,
            leading=10,
        ),
    }
    return styles


def add_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(WINE)
    canvas.rect(0, 0, w, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, 12 * mm, w, 0.6 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(18 * mm, 5 * mm, "Pello Menos  ·  Confidencial — uso interno")
    canvas.drawRightString(w - 18 * mm, 5 * mm, f"Página {doc.page}")
    canvas.restoreState()


def kpi_table(styles, summary: dict) -> Table:
    cells = [
        [
            Paragraph("Pedidos", styles["kpi_label"]),
            Paragraph("Receita bruta", styles["kpi_label"]),
            Paragraph("Ticket médio", styles["kpi_label"]),
            Paragraph("Média / dia", styles["kpi_label"]),
            Paragraph("Dias c/ venda", styles["kpi_label"]),
        ],
        [
            Paragraph(str(summary["orders"]), styles["kpi_value"]),
            Paragraph(brl(summary["gross"]), styles["kpi_value"]),
            Paragraph(brl(summary["ticket_avg"]), styles["kpi_value"]),
            Paragraph(brl(summary["daily_avg"]), styles["kpi_value"]),
            Paragraph(
                f"{summary['days_with_sales']} / {summary['days_span']}",
                styles["kpi_value"],
            ),
        ],
    ]
    t = Table(cells, colWidths=[34 * mm, 38 * mm, 34 * mm, 34 * mm, 30 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BG),
                ("BOX", (0, 0), (-1, -1), 1, GOLD),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e4d6e0")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


def abandon_kpi_table(styles, abandon: dict) -> Table:
    cells = [
        [
            Paragraph("Carrinhos abandonados", styles["kpi_label"]),
            Paragraph("Valor abandonado", styles["kpi_label"]),
            Paragraph("Recuperados", styles["kpi_label"]),
            Paragraph("Valor recuperado", styles["kpi_label"]),
        ],
        [
            Paragraph(str(abandon["abandoned_carts"]), styles["kpi_value"]),
            Paragraph(brl(abandon["abandoned_gross"]), styles["kpi_value"]),
            Paragraph(str(abandon["recovered_carts"]), styles["kpi_value"]),
            Paragraph(brl(abandon["recovered_gross"]), styles["kpi_value"]),
        ],
    ]
    t = Table(cells, colWidths=[45 * mm, 45 * mm, 40 * mm, 40 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BG),
                ("BOX", (0, 0), (-1, -1), 1, GOLD),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e4d6e0")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


def funnel_kpi_table(styles, funnel: dict) -> Table:
    cells = [
        [
            Paragraph("Vendas pagas", styles["kpi_label"]),
            Paragraph("Tentativas de compra", styles["kpi_label"]),
            Paragraph("Pedidos criados", styles["kpi_label"]),
            Paragraph("Conversão", styles["kpi_label"]),
        ],
        [
            Paragraph(str(funnel["paid"]["orders"]), styles["kpi_value"]),
            Paragraph(str(funnel["purchase_attempts"]), styles["kpi_value"]),
            Paragraph(str(funnel["orders_created"]), styles["kpi_value"]),
            Paragraph(f"{funnel['conversion_vs_attempts_pct']}%", styles["kpi_value"]),
        ],
    ]
    t = Table(cells, colWidths=[42 * mm, 48 * mm, 42 * mm, 38 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BG),
                ("BOX", (0, 0), (-1, -1), 1, GOLD),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e4d6e0")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


def outcome_table(styles, funnel: dict, usable_w: float) -> Table:
    headers = [
        Paragraph("Situação", styles["th"]),
        Paragraph("Qtd", styles["th"]),
        Paragraph("Valor", styles["th_r"]),
    ]
    rows_src = [
        ("Vendas com pagamento recebido", funnel["paid"]["orders"], funnel["paid"]["gross"]),
        ("Pendentes / em espera", funnel["pending"]["orders"], funnel["pending"]["gross"]),
        ("Cancelados", funnel["cancelled"]["orders"], funnel["cancelled"]["gross"]),
        ("Falhou no pagamento", funnel["failed"]["orders"], funnel["failed"]["gross"]),
        ("Estornados", funnel["refunded"]["orders"], funnel["refunded"]["gross"]),
        (
            "Carrinhos abandonados (sem pedido)",
            funnel["abandoned_carts"],
            funnel["abandoned_gross"],
        ),
    ]
    if funnel["other"]["orders"]:
        rows_src.append(
            ("Outros status", funnel["other"]["orders"], funnel["other"]["gross"])
        )
    rows = [
        [
            Paragraph(label, styles["cell"]),
            Paragraph(str(qty), styles["cell"]),
            Paragraph(brl(gross), styles["cell_r"]),
        ]
        for label, qty, gross in rows_src
    ]
    return data_table(headers, rows, [usable_w - 70 * mm, 28 * mm, 42 * mm])


def orders_list_table(styles, orders: list[dict], usable_w: float) -> Table:
    headers = [
        Paragraph("#", styles["th"]),
        Paragraph("Data/hora", styles["th"]),
        Paragraph("Status", styles["th"]),
        Paragraph("Pagamento", styles["th"]),
        Paragraph("Total", styles["th_r"]),
    ]
    rows = []
    for o in orders:
        rows.append(
            [
                Paragraph(str(o["number"]), styles["cell"]),
                Paragraph(o["datetime"], styles["cell"]),
                Paragraph(status_label(o["status"]), styles["cell"]),
                Paragraph(o["payment"][:42], styles["cell"]),
                Paragraph(brl(o["total"]), styles["cell_r"]),
            ]
        )
    if not rows:
        rows.append(
            [
                Paragraph("—", styles["cell"]),
                Paragraph("Nenhum neste grupo", styles["cell"]),
                Paragraph("—", styles["cell"]),
                Paragraph("—", styles["cell"]),
                Paragraph(brl(0), styles["cell_r"]),
            ]
        )
    return data_table(
        headers,
        rows,
        [22 * mm, 32 * mm, 28 * mm, usable_w - 110 * mm, 28 * mm],
    )


def data_table(headers: list, rows: list, col_widths: list) -> Table:
    t = Table([headers] + rows, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 1, GOLD),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#dcc9d7")),
    ]
    for i in range(1, len(rows) + 1):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(style_cmds))
    return t


def build_pdf(
    pdf_path: Path,
    start: date,
    end: date,
    generated_at: datetime,
    summary: dict,
    buckets: dict[str, list[dict]],
    abandon: dict,
    funnel: dict,
) -> None:
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm,
        title="Relatório de Vendas — Pello Menos",
        author="Pello Menos E-commerce",
    )
    story = []
    usable_w = A4[0] - 32 * mm

    # Capa / cabeçalho (sem logo)
    period_txt = f"{start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}"
    cover_inner = [
        Paragraph("Relatório de Vendas — E-commerce", styles["title"]),
        Paragraph(period_txt, styles["subtitle"]),
        Spacer(1, 2 * mm),
        Paragraph("loja.pellomenos.com.br", styles["meta"]),
        Paragraph(
            f"Gerado em {generated_at.strftime('%d/%m/%Y às %H:%M')} (America/Sao_Paulo)",
            styles["meta"],
        ),
    ]
    cover = Table([[cover_inner]], colWidths=[usable_w])
    cover.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PURPLE),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("BOX", (0, 0), (-1, -1), 2, GOLD),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(cover)
    story.append(Spacer(1, 8 * mm))

    # Resumo vendas pagas
    story.append(Paragraph("Resumo executivo — vendas pagas", styles["h2"]))
    story.append(kpi_table(styles, summary))
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            "Os KPIs acima consideram apenas pedidos com "
            "<b>pagamento recebido</b>. Demais tentativas aparecem no funil abaixo.",
            styles["note"],
        )
    )

    # Funil: vendas vs tentativas
    story.append(Paragraph("Funil: vendas × tentativas", styles["h2"]))
    story.append(funnel_kpi_table(styles, funnel))
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "<b>Tentativas de compra</b> = todos os pedidos criados no período "
            f"(<b>{funnel['orders_created']}</b>) + carrinhos abandonados "
            f"(<b>{funnel['abandoned_carts']}</b>). "
            f"<b>Conversão</b> = vendas pagas ÷ tentativas "
            f"({funnel['conversion_vs_attempts_pct']}%). "
            f"Só entre pedidos criados, a conversão é {funnel['conversion_vs_orders_pct']}%.",
            styles["note"],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Detalhamento por situação", styles["h2"]))
    story.append(outcome_table(styles, funnel, usable_w))

    # Carrinho abandonado
    story.append(Paragraph("Carrinho abandonado", styles["h2"]))
    story.append(abandon_kpi_table(styles, abandon))
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "Fonte: plugin Cart Abandonment Recovery (CartFlows). "
            "<b>Abandonados</b> = e-mail no checkout sem pedido pago. "
            "<b>Recuperados</b> = compra após abandono. "
            f"Ainda em aberto (normal): <b>{abandon['normal_carts']}</b> "
            f"({brl(abandon['normal_gross'])}).",
            styles["note"],
        )
    )

    # Por dia
    story.append(Paragraph("Vendas por dia", styles["h2"]))
    day_headers = [
        Paragraph("Data", styles["th"]),
        Paragraph("Pedidos", styles["th"]),
        Paragraph("Receita", styles["th_r"]),
    ]
    day_rows = []
    for day, info in summary["by_day"].items():
        if day == "unknown":
            label = "—"
        else:
            label = datetime.strptime(day, "%Y-%m-%d").strftime("%d/%m/%Y")
        day_rows.append(
            [
                Paragraph(label, styles["cell"]),
                Paragraph(str(info["orders"]), styles["cell"]),
                Paragraph(brl(info["gross"]), styles["cell_r"]),
            ]
        )
    day_rows.append(
        [
            Paragraph("<b>Total</b>", styles["cell"]),
            Paragraph(f"<b>{summary['orders']}</b>", styles["cell"]),
            Paragraph(f"<b>{brl(summary['gross'])}</b>", styles["cell_r"]),
        ]
    )
    story.append(
        data_table(day_headers, day_rows, [55 * mm, 40 * mm, usable_w - 95 * mm])
    )

    # Listas por grupo
    story.append(Paragraph("Lista — vendas pagas", styles["h2"]))
    story.append(orders_list_table(styles, buckets["paid"], usable_w))

    story.append(Paragraph("Lista — cancelados", styles["h2"]))
    story.append(orders_list_table(styles, buckets["cancelled"], usable_w))

    story.append(Paragraph("Lista — falhou no pagamento", styles["h2"]))
    story.append(orders_list_table(styles, buckets["failed"], usable_w))

    story.append(Paragraph("Lista — pendentes / em espera", styles["h2"]))
    story.append(orders_list_table(styles, buckets["pending"], usable_w))

    story.append(Paragraph("Lista — estornos", styles["h2"]))
    story.append(orders_list_table(styles, buckets["refunded"], usable_w))

    if buckets["other"]:
        story.append(Paragraph("Lista — outros status", styles["h2"]))
        story.append(orders_list_table(styles, buckets["other"], usable_w))

    # Notas
    story.append(Paragraph("Notas", styles["h2"]))
    notes = [
        f"Fonte pedidos: WooCommerce REST API (wc/v3/orders) em {cfg()['url']}.",
        "Fonte abandonos: plugin Cart Abandonment Recovery (CartFlows).",
        f"Período: {start.isoformat()} 00:00:00 até {end.isoformat()} 23:59:59 (horário do servidor da loja).",
        "Receita do resumo executivo = somente pagamento recebido (não inclui cancelados, falhas, pendentes nem estornos).",
        "Tentativas de compra = pedidos criados (qualquer status) + carrinhos abandonados no período.",
        "Valores em BRL conforme total na loja (já com descontos/cupons).",
    ]
    for n in notes:
        story.append(Paragraph(f"• {n}", styles["note"]))

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)


def main() -> None:
    today = date.today()
    start = date(2026, 11, 1)
    end = today if today >= start else start
    # API before is exclusive-ish; use next day 00:00
    after = f"{start.isoformat()}T00:00:00"
    before = f"{(end + timedelta(days=1)).isoformat()}T00:00:00"
    generated_at = datetime.now()

    c = cfg()
    print(f"Fetching {after} → {before} from {c['url']}", flush=True)
    raw = fetch_range(c, after, before)
    print("Fetching abandonment report…", flush=True)
    abandon = fetch_abandonment(c, after, before)

    slim = [slim_order(o) for o in raw]
    buckets = bucket_orders(slim)
    main = buckets["paid"]
    refunded = buckets["refunded"]
    summary = summarize(main, refunded, start, end)
    funnel = build_funnel(buckets, abandon)

    # Sanity: sum of main totals == summary gross
    checksum = round(sum(o["total"] for o in main), 2)
    assert checksum == summary["gross"], (checksum, summary["gross"])

    payload = {
        "as_of": generated_at.isoformat(timespec="seconds"),
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "source": c["url"],
        "summary": summary,
        "funnel": funnel,
        "abandonment": abandon,
        "orders_by_bucket": {k: v for k, v in buckets.items()},
        "checksum_gross": checksum,
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("json", JSON_OUT)

    pdf_path = desktop_pdf_path(start, end)
    build_pdf(pdf_path, start, end, generated_at, summary, buckets, abandon, funnel)

    print()
    print("=== RESUMO ===")
    print("período:", start.isoformat(), "→", end.isoformat())
    print("vendas pagas:", summary["orders"], brl(summary["gross"]))
    print("tentativas:", funnel["purchase_attempts"])
    print("pedidos criados:", funnel["orders_created"])
    print("cancelados:", funnel["cancelled"]["orders"], brl(funnel["cancelled"]["gross"]))
    print("falhou:", funnel["failed"]["orders"], brl(funnel["failed"]["gross"]))
    print("pendentes:", funnel["pending"]["orders"], brl(funnel["pending"]["gross"]))
    print("estornos:", funnel["refunded"]["orders"], brl(funnel["refunded"]["gross"]))
    print(
        "abandonados:",
        abandon["abandoned_carts"],
        brl(abandon["abandoned_gross"]),
    )
    print("conversão:", f"{funnel['conversion_vs_attempts_pct']}%")
    print("pdf:", pdf_path)
    print("ok checksum", checksum)


if __name__ == "__main__":
    main()
