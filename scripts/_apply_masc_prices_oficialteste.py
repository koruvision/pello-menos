# -*- coding: utf-8 -*-
"""
1) Audit 64 loja (read-only Store API) vs woo-bridge feminine quotes
2) Apply Rafael masculine ecommerce prices to data.ts + woo-bridge *-masc
3) Write report of applied vs missing
"""
from __future__ import annotations

import json
import re
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "lib" / "data.ts"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
BRIDGE_WP = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
REPORT = ROOT / "projeto-migracao" / ".secrets" / "masc-prices-applied-report.md"
AUDIT = ROOT / "projeto-migracao" / ".secrets" / "audit-64-fem-prices.json"
LOJA = "https://loja.pellomenos.com.br"

# Tabela Rafael — preço e-commerce final (centavos). skipDiscount.
MASC_PRICES: dict[str, int] = {
    # Cera
    "peito-cera-masc": 4990,  # TÓRAX
    "abdomen-cera-masc": 5790,
    "axila-cera-masc": 3890,
    "bracos-cera-masc": 7400,
    "costas-cera-masc": 5990,
    "coxa-cera-masc": 6190,
    "faixa-cera-masc": 3400,
    "intergluteos-cera-masc": 4850,
    "nadegas-cera-masc": 5250,
    "nariz-cera-masc": 3290,
    "meia-perna-cera-masc": 6190,
    "perna-cera-masc": 11500,
    "queixo-cera-masc": 3290,
    "virilha-cera-masc": 8890,
    "virilha-comum-cera-masc": 5890,
    # Esfoliação
    "esfoliacao-faixa-masc": 1700,
    "esfoliacao-braco-masc": 3700,
    "esfoliacao-meia-perna-masc": 3095,
    "esfoliacao-abdomen-masc": 2895,
    "esfoliacao-axilas-masc": 1945,
    "esfoliacao-nadegas-masc": 2625,
    "esfoliacao-coxa-masc": 3095,
    "esfoliacao-costas-masc": 2995,
    "esfoliacao-perna-masc": 5750,
    "esfoliacao-virilha-masc": 2945,
    # Planos (twins)
    "plano-silver-masc": 12490,
    "plano-gold-masc": 12990,
}

MISSING_FROM_TABLE = [
    ("BARBA", "56,90", "cera"),
    ("BARBA MODELADORA", "74,90", "cera"),
    ("BIGODE", "38,50", "cera"),
    ("ORELHA", "32,90", "cera"),
    ("PESCOÇO", "32,90", "cera"),
    ("MAMILOS", "32,90", "cera"),
    ("SOBRANCELHA", "52,90", "cera"),
    ("DESIGN DE SOBRANCELHA", "69,90", "cera"),
    ("TÓRAX + ABDÔMEN", "89,90", "cera"),
    ("SACO ESCROTAL", "58,90", "cera"),
]


def http_get_json(url: str):
    req = urllib.request.Request(
        url, method="GET", headers={"User-Agent": "pm-masc-prices/1.0", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8", "replace")), {
            k.lower(): v for k, v in r.headers.items()
        }


def fetch_loja_products():
    page, items = 1, []
    while page <= 50:
        data, headers = http_get_json(
            f"{LOJA}/wp-json/wc/store/v1/products?page={page}&per_page=100&orderby=id&order=asc"
        )
        if not data:
            break
        items.extend(data)
        tp = int(headers.get("x-wp-totalpages") or 0) or None
        if tp and page >= tp:
            break
        if len(data) < 100:
            break
        page += 1
    return items


def store_sale_cents(p) -> int | None:
    prices = p.get("prices") or {}
    raw = prices.get("price") or prices.get("sale_price") or prices.get("regular_price")
    if raw is None or raw == "":
        return None
    s = str(raw)
    if s.isdigit():
        return int(s)
    try:
        return int(round(float(s.replace(",", ".")) * 100))
    except Exception:
        return None


def audit_64(bridge: dict):
    loja = fetch_loja_products()
    rows = []
    mismatch = []
    for p in loja:
        slug = (p.get("slug") or "").lower()
        sale = store_sale_cents(p)
        # find bridge by slug match on feminine keys (not -masc)
        hit = None
        for key, row in bridge.items():
            if key.endswith("-masc"):
                continue
            if (row.get("slug") or "").lower() == slug:
                hit = (key, row)
                break
        bridge_sale = None
        if hit:
            bridge_sale = (hit[1].get("rj") or {}).get("saleCents")
        ok = sale is not None and bridge_sale is not None and sale == bridge_sale
        # Store API price may be minor units; also compare regular
        row = {
            "loja_id": p.get("id"),
            "name": p.get("name"),
            "slug": slug,
            "loja_sale_cents": sale,
            "bridge_key": hit[0] if hit else None,
            "bridge_rj_sale": bridge_sale,
            "match": ok,
        }
        rows.append(row)
        if not ok:
            mismatch.append(row)
    report = {
        "loja_count": len(loja),
        "matched_bridge_slug": sum(1 for r in rows if r["bridge_key"]),
        "price_exact_match": sum(1 for r in rows if r["match"]),
        "mismatch_count": len(mismatch),
        "mismatches": mismatch[:40],
        "note": (
            "Store API sale vs bridge rj.saleCents. Divergências comuns: Store mostra "
            "preço da variação default; bridge usa tabela RJ seed."
        ),
    }
    AUDIT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "audit64 loja",
        report["loja_count"],
        "bridge_slug",
        report["matched_bridge_slug"],
        "price_match",
        report["price_exact_match"],
        "mismatch",
        report["mismatch_count"],
    )
    return report


def patch_data_ts(text: str) -> str:
    # Update each masc catalog line: originalCents + ensure skipDiscount: true
    for pid, cents in MASC_PRICES.items():
        if pid.startswith("plano-"):
            continue  # handled via twin overrides
        # Match object starting with id: "pid"
        pattern = rf'(\{{ id: "{re.escape(pid)}",[^\}}]*?originalCents: )\d+'
        new_text, n = re.subn(pattern, rf"\g<1>{cents}", text, count=1)
        if n != 1:
            raise SystemExit(f"data.ts: could not patch originalCents for {pid}")
        text = new_text
        # Ensure skipDiscount: true after originalCents if missing
        # Find the object again and inject skipDiscount if absent before category/method
        obj_pat = rf'(\{{ id: "{re.escape(pid)}",[^\}}]*?originalCents: {cents})(,\s*)(?!skipDiscount)'
        if re.search(rf'id: "{re.escape(pid)}"[^\}}]*skipDiscount', text):
            # already has skipDiscount somewhere in object — force true
            text = re.sub(
                rf'(\{{ id: "{re.escape(pid)}",[^\}}]*?skipDiscount:\s*)(?:true|false)',
                rf"\g<1>true",
                text,
                count=1,
            )
        else:
            text2, n2 = re.subn(
                obj_pat,
                rf"\g<1>, skipDiscount: true\g<2>",
                text,
                count=1,
            )
            if n2 != 1:
                raise SystemExit(f"data.ts: could not add skipDiscount for {pid}")
            text = text2

    # Twin price overrides for planos
    override_block = """
const SHARED_CHROME_TWIN_OVERRIDES: Partial<Record<string, Partial<ProductSeed>>> = {
  "plano-silver-masc": { originalCents: 12490, skipDiscount: true },
  "plano-gold-masc": { originalCents: 12990, skipDiscount: true },
};
"""
    if "SHARED_CHROME_TWIN_OVERRIDES" not in text:
        text = text.replace(
            "function expandCatalogWithAudienceTwins(items: ProductSeed[]): ProductSeed[] {",
            override_block
            + "\nfunction expandCatalogWithAudienceTwins(items: ProductSeed[]): ProductSeed[] {",
        )
    else:
        # refresh override values
        text = re.sub(
            r'const SHARED_CHROME_TWIN_OVERRIDES: Partial<Record<string, Partial<ProductSeed>>> = \{[\s\S]*?\n\};',
            override_block.strip(),
            text,
            count=1,
        )

    # Update expand to merge overrides
    old_expand = """    out.push({
      ...base,
      id: `${baseId}-masc`,
      audience: "masculino",
    });"""
    new_expand = """    const twinId = `${baseId}-masc`;
    out.push({
      ...base,
      id: twinId,
      audience: "masculino",
      ...(SHARED_CHROME_TWIN_OVERRIDES[twinId] ?? {}),
    });"""
    if new_expand not in text:
        if old_expand not in text:
            raise SystemExit("expandCatalog push block not found")
        text = text.replace(old_expand, new_expand)

    # Comment update for cera masc block
    text = text.replace(
        "// Cera masculino — áreas da tabela RJ-SP para homem; preço cartão + 5% OFF no site",
        "// Cera masculino — tabela Rafael e-commerce (já com desconto; skipDiscount)",
    )
    text = text.replace(
        "// Esfoliação masculino — preço cartão da tabela oficial (sem meio braço, meia nádega, virilha+faixa e seios)",
        "// Esfoliação masculino — tabela Rafael e-commerce (já com desconto; skipDiscount)",
    )
    return text


def patch_bridge(bridge: dict) -> int:
    touched = 0
    for pid, cents in MASC_PRICES.items():
        row = bridge.get(pid)
        if not row:
            # create minimal clone from feminine if needed for planos
            if pid.endswith("-masc"):
                base = pid[:-5]
                if base in bridge:
                    row = json.loads(json.dumps(bridge[base]))
                    bridge[pid] = row
                else:
                    print("WARN no bridge for", pid)
                    continue
            else:
                print("WARN no bridge for", pid)
                continue
        for side in ("rj", "spdf"):
            if side not in row or not isinstance(row[side], dict):
                row[side] = {}
            row[side]["regularCents"] = cents
            row[side]["saleCents"] = cents
        touched += 1
    return touched


def write_report(audit: dict):
    lines = [
        "# Preços masculinos aplicados (oficialteste / catálogo Next)",
        "",
        "## Auditoria 64 (loja Store API vs bridge feminino RJ)",
        f"- Produtos loja: {audit['loja_count']}",
        f"- Com slug no bridge: {audit['matched_bridge_slug']}",
        f"- Preço Store == bridge rj.saleCents: {audit['price_exact_match']}",
        f"- Divergências: {audit['mismatch_count']} (ver `{AUDIT.name}`)",
        "",
        "## Aplicado (tabela Rafael → seed + bridge `*-masc`)",
        "",
    ]
    for pid, cents in sorted(MASC_PRICES.items()):
        lines.append(f"- `{pid}` → R$ {cents/100:.2f}".replace(".", ","))
    lines += [
        "",
        "## Falta criar (tabela masculina sem SKU no catálogo)",
        "",
    ]
    for name, price, kind in MISSING_FROM_TABLE:
        lines.append(f"- **{name}** ({kind}) — R$ {price}")
    lines += [
        "",
        "## Notas",
        "",
        "- Valores da tabela = preço e-commerce final (`skipDiscount: true`).",
        "- `TEST_CHARGE_CENTS` continua R$ 1,00 no checkout de teste; ficha usa bridge atualizado.",
        "- Laser masculino e gift cards: fora desta leva (sem tabela / sem Woo gift na loja).",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("report", REPORT)


def main():
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    audit = audit_64(bridge)

    text = DATA.read_text(encoding="utf-8")
    DATA.write_text(patch_data_ts(text), encoding="utf-8")
    print("patched data.ts")

    n = patch_bridge(bridge)
    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(BRIDGE, BRIDGE_WP)
    print("patched woo-bridge", n, "keys; copied to WP")

    write_report(audit)
    print("DONE")


if __name__ == "__main__":
    main()
