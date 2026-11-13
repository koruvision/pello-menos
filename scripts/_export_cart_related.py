# -*- coding: utf-8 -*-
"""Build cart-related.json for pm-home/cart.js from src/lib/data.ts."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")
OUT = ROOT / "wordpress-loja" / "pm-home" / "cart-related.json"
BRIDGE = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
CAMPAIGN = ROOT / "wordpress-loja" / "pm-home" / "black-nov-campaign.json"
DISCOUNT = 0.05


def campaign_phase(cfg: dict) -> str:
    """Espelha black-nov-campaign.js phaseAt (sem FORCE)."""
    import time

    now = time.time()
    try:
        a = __import__("datetime").datetime.fromisoformat(
            str(cfg.get("esquentaStart") or "").replace("Z", "+00:00")
        ).timestamp()
        b = __import__("datetime").datetime.fromisoformat(
            str(cfg.get("esquentaEnd") or "").replace("Z", "+00:00")
        ).timestamp()
        c = __import__("datetime").datetime.fromisoformat(
            str(cfg.get("blackWeekStart") or "").replace("Z", "+00:00")
        ).timestamp()
        d = __import__("datetime").datetime.fromisoformat(
            str(cfg.get("blackWeekEnd") or "").replace("Z", "+00:00")
        ).timestamp()
    except Exception:
        return "off"
    if a and b and a <= now <= b:
        return "esquenta"
    if c and d and c <= now <= d:
        return "black_week"
    return "off"


def campaign_any_rate(cfg: dict, pid: str, method: str, phase: str) -> float | None:
    """Taxa 'any' (1 item) — a mesma da Home/PDP. Multi só no carrinho."""
    if phase == "off" or not cfg:
        return None
    prefixes = cfg.get("excludeIdPrefixes") or []
    methods = cfg.get("excludeMethods") or []
    if any(pid == p or pid.startswith(p) for p in prefixes):
        return None
    m = (method or "").lower()
    if m and m in methods:
        return None
    if m == "laser" or "-laser" in pid or pid.endswith("laser"):
        table = (cfg.get("laser") or {}).get(phase) or {}
        return float(table.get("any") or 0) or None
    is_esf = m == "esfoliacao" or pid.startswith("esfoliacao")
    is_cera = m in ("cera", "esfoliacao") or "-cera" in pid or "esfoliacao" in pid or pid in (
        "realce",
        "henna",
    ) or "tintura-pelos" in pid
    if not is_cera:
        return None
    if phase == "esquenta":
        table = (cfg.get("ceraEsf") or {}).get("esquenta") or {}
        return float(table.get("any") or 0) or None
    if is_esf:
        return float((cfg.get("ceraEsf") or {}).get("black_week_esfoliacao") or 0.15)
    # Black Week cera: tiers
    for tier, key in (("P", "ceraTierP"), ("M", "ceraTierM"), ("G", "ceraTierG")):
        if pid in (cfg.get(key) or []):
            return float(((cfg.get("ceraEsf") or {}).get("black_week_cera") or {}).get(tier) or 0.25)
    return float(((cfg.get("ceraEsf") or {}).get("black_week_cera") or {}).get("G") or 0.25)


def vitrine_price_cents(original: int, method: str, pid: str, skip: bool, cfg: dict) -> int:
    """Preço de vitrine: campanha (any) se ativa; senão 5% (ou skip)."""
    phase = campaign_phase(cfg) if cfg else "off"
    rate = campaign_any_rate(cfg, pid, method, phase) if cfg else None
    base = original
    if rate is not None:
        # skipDiscount masc cera/esf: seed já vem −5%; reconstrói tabela ÷0.95
        if skip and method in ("cera", "esfoliacao"):
            base = int(round(original / 0.95))
        return int(round(base * (1 - rate)))
    if skip:
        return int(original)
    return int(round(original * (1 - DISCOUNT)))

m = re.search(r"const CROSS_SELL[^=]*=\s*\{([\s\S]*?)\n\};", DATA)
cross: dict[str, list[str]] = {}
if m:
    for key, arr in re.findall(r'"([^"]+)":\s*\[([^\]]*)\]', m.group(1)):
        cross[key] = re.findall(r'"([^"]+)"', arr)

# Single-line catalog rows (dominant style in data.ts)
products: dict[str, dict] = {}
# O lookahead aceita linhas de comentário entre um produto e o próximo
# (ex.: "// Cera / laser / linha feminino" antes de abdomen-cera); sem isso o
# produto anterior engolia a linha seguinte e ela ficava fora do JSON.
for match in re.finditer(
    r'\{\s*id:\s*"([^"]+)"\s*,\s*name:\s*"((?:\\.|[^"\\])*)"([\s\S]*?)'
    r'(?=\},\s*(?://[^\n]*\n\s*)*\{|\},\s*(?://[^\n]*\n\s*)*\])',
    DATA,
):
    pid = match.group(1)
    name = match.group(2)
    body = match.group(3)
    if "originalCents" not in body and "priceCents" not in body:
        continue
    img_m = re.search(
        r'image:\s*(?:catalogImage\("([^"]+)"(?:,\s*"([^"]+)")?\)|"([^"]+)")',
        body,
    )
    price_m = re.search(r"originalCents:\s*(\d+)", body) or re.search(
        r"priceCents:\s*(\d+)", body
    )
    skip = "skipDiscount: true" in body
    dur_m = re.search(r'duration:\s*"((?:\\.|[^"\\])*)"', body)
    cat_m = re.search(r'category:\s*"([^"]+)"', body)
    method_m = re.search(r'method:\s*"([^"]+)"', body)
    aud_m = re.search(r'audience:\s*"([^"]+)"', body)
    if not price_m:
        continue
    original = int(price_m.group(1))
    # Imagem do card = exatamente a imagem da ficha: reproduz catalogImage() de data.ts
    # (`/images/products/<id>.webp`, ou `/images/products/male/<id>.webp` no masculino).
    if img_m and img_m.group(3):
        image = img_m.group(3)
    elif img_m:
        cid = img_m.group(1)
        aud = img_m.group(2) or "feminino"
        image = (
            f"/images/products/male/{cid}.webp"
            if aud == "masculino"
            else f"/images/products/{cid}.webp"
        )
    else:
        image = f"/images/products/{pid}.webp"
    if not (ROOT / "public" / image.lstrip("/")).is_file():
        raise SystemExit(f"imagem não encontrada em public/: {pid} -> {image}")
    method = method_m.group(1) if method_m else (
        "laser" if "laser" in pid else "cera" if "cera" in pid else "outro"
    )
    products[pid] = {
        "id": pid,
        "name": name,
        "image": image,
        "originalCents": int(original),
        # priceCents preenchido depois com campanha/5% (não usar saleCents do bridge —
        # isso misturava preço Woo antigo e gerava risco de base errada no fallback).
        "priceCents": int(original),
        "skipDiscount": bool(skip),
        "duration": dur_m.group(1) if dur_m else "",
        "audience": aud_m.group(1)
        if aud_m
        else ("masculino" if pid.endswith("-masc") else "feminino"),
        "method": method,
        "category": cat_m.group(1) if cat_m else "",
    }

campaign_cfg: dict = {}
if CAMPAIGN.exists():
    try:
        campaign_cfg = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    except Exception:
        campaign_cfg = {}
phase = campaign_phase(campaign_cfg) if campaign_cfg else "off"
print("campaign_phase", phase)

bridge = {}
if BRIDGE.exists():
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
for pid, row in products.items():
    entry = bridge.get(pid) or {}
    if entry.get("productId"):
        row["productId"] = str(entry["productId"])
        # Compat: wooId no cart era productId; o push precisa da variation por unidade.
        row["wooId"] = str(entry["productId"])
    units = entry.get("units") or {}
    if isinstance(units, dict) and units:
        row["units"] = {
            str(uid).lower(): {
                "variationId": str(meta.get("variationId") or ""),
                "option": meta.get("option") or "",
            }
            for uid, meta in units.items()
            if isinstance(meta, dict)
        }
    sale = (entry.get("rj") or {}).get("saleCents")
    # originalCents = tabela; priceCents = vitrine (Esquenta/Black any, ou 5%).
    # NUNCA sobrescrever com saleCents genérico do bridge (causava laser a R$94,90 etc.).
    row["priceCents"] = vitrine_price_cents(
        int(row["originalCents"]),
        str(row.get("method") or ""),
        pid,
        bool(row.get("skipDiscount")),
        campaign_cfg,
    )
    if pid == "produto-1-real" and isinstance(sale, int) and sale > 0:
        row["priceCents"] = sale


# Sanidade: todo produto do catálogo (exceto depoimentos r1–r6/m1–m6) precisa estar no JSON.
all_ids = re.findall(r'^\s*\{\s*id:\s*"([^"]+)"\s*,\s*name:', DATA, re.M)
missing = [
    pid for pid in all_ids
    if pid not in products and not re.fullmatch(r"[rm]\d+", pid)
]
if missing:
    raise SystemExit(f"produtos fora do cart-related.json: {missing}")

OUT.write_text(
    json.dumps({"crossSell": cross, "products": products}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("wrote", OUT.name, "products", len(products), "cross", len(cross))
