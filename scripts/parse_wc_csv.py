"""Parse WooCommerce CSV into a compact JSON map for catalog sync."""
from __future__ import annotations

import csv
import json
import re
from html import unescape
from pathlib import Path

CSV = Path(r"C:\Users\GC1\Downloads\wc-product-export-14-9-2026-1789413349154.csv")
OUT = Path(__file__).resolve().parents[1] / "scripts" / "wc_catalog.json"

NAME_TO_ID = {
    "Buço - Cera": "buco-cera",
    "Antebraço - Cera": "antebraco-cera",
    "Abdômen - Cera": "abdomen-cera",
    "Axila - Cera": "axila-cera",
    "Costas - Cera": "costas-cera",
    "Coxa - Cera": "coxa-cera",
    "Faixa - Cera": "faixa-cera",
    "Interglúteos - Cera": "intergluteos-cera",
    "Nariz - Cera": "nariz-cera",
    "Meia Nádega - Cera": "meia-nadega-cera",
    "Nádegas Completas - Cera": "nadegas-cera",
    "Perna Inteira - Cera": "perna-cera",
    "Meia Perna - Cera": "meia-perna-cera",
    "Queixo - Cera": "queixo-cera",
    "Seios - Cera": "seios-cera",
    "Virilha Modelada - Cera": "virilha-modelada-cera",
    "Virilha Total - Cera": "virilha-cera",
    "Virilha Comum - Cera": "virilha-comum-cera",
    "Virilha Comum + Faixa - Cera": "virilha-comum-faixa-cera",
    "Virilha Cavada - Cera": "virilha-cavada-cera",
    "Virilha Cavada + Faixa - Cera": "virilha-cavada-faixa-cera",
    "Lábios Genitais - Cera": "labios-genitais-cera",
    "Sobrancelha - Cera": "sobrancelha-cera",
    "Sobrancelha + Realce - Cera": "sobrancelha-realce-cera",
    "Design de Sobrancelha + Henna Feminino": "sobrancelha-henna",
    "Design de Sobrancelha - Cera": "design-sobrancelha",
    "Design de Sobrancelha + Realce - Cera": "design-sobrancelha-realce",
    "Sobrancelha Simples + Henna": "sobrancelha-henna-simples",
    "Realce": "realce",
    "Henna": "henna",
    "Braços - Cera": "bracos-cera",
    "Clube do Laser": "plano-clube-laser",
    "Plano de Assinatura VIP - Silver": "plano-silver",
    "Plano de Assinatura VIP - Gold": "plano-gold",
    "Pré-pago Pello Menos": "plano-prepago",
    "Axilas Laser": "axilas-laser",
    "Rosto Inteiro Laser (BU+QU+NZ+PSD P)": "rosto-inteiro-laser",
    "Pescoço Laser": "pescoco-laser",
    "Orelhas Laser": "orelhas-laser",
    "Nariz Laser": "nariz-laser",
    "Meia Nádega Laser": "meia-nadega-laser",
    "Nádegas Laser": "nadegas-laser",
    "PSD G Laser": "psd-g-laser",
    "PSD M Laser": "psd-m-laser",
    "PSD P Laser": "psd-p-laser",
    "Costas Laser": "costas-laser",
    "Antebraço Laser": "antebraco-laser",
    "Braços Inteiros Laser": "bracos-laser",
    "Abdômen Laser": "abdomen-laser",
    "Aréola Laser": "areola-laser",
    "Interglúteos Laser": "intergluteos-laser",
    "Virilha Total Laser": "virilha-laser",
    "Virilha Cavada c/ Faixa Laser": "virilha-cavada-faixa-laser",
    "Virilha Cavada Laser": "virilha-cavada-laser",
    "Virilha c/ Faixa Laser": "virilha-faixa-laser",
    "Virilha Comum Laser": "virilha-comum-laser",
    "Meia Perna Laser": "meia-perna-laser",
    "Perna Inteira Laser": "perna-laser",
    "Coxas Laser": "coxas-laser",
    "Buço Laser": "buco-laser",
    "Queixo Laser": "queixo-laser",
    "Buço - Linha": "buco-linha",
    "Queixo - Linha": "queixo-linha",
    "Faixa - Linha": "faixa-linha",
}


def strip_html(raw: str) -> str:
    text = unescape(raw or "")
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n", text)
    text = re.sub(r"(?i)</h[1-6]>", "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "• ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\r", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def first_useful_sentence(short_plain: str, yoast: str) -> str:
    if yoast and len(yoast.strip()) > 20:
        yoast_clean = yoast.strip()
        if not yoast_clean.lower().startswith("a partir"):
            return yoast_clean
    lines = [ln.strip(" *") for ln in short_plain.split("\n") if ln.strip()]
    skip = (
        "depilação a cera",
        "depilação com cera",
        "imagem do serviço",
        "valor do serviço",
        "a partir de",
        "pacote completo",
    )
    for line in lines:
        low = line.lower()
        if any(s in low for s in skip) and len(line) < 80:
            continue
        if line.startswith("*"):
            continue
        if len(line) >= 40:
            return line
    for line in lines:
        if len(line) >= 30 and not line.lower().startswith("a partir"):
            return line
    return yoast.strip() or (lines[0] if lines else "")


def parse_price(value: str) -> int | None:
    if not value:
        return None
    cleaned = value.strip().replace(".", "").replace(",", ".")
    try:
        return int(round(float(cleaned) * 100))
    except ValueError:
        return None


def main() -> None:
    with CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    parents = [r for r in rows if r.get("Tipo") in ("simple", "variable")]
    variations = [r for r in rows if r.get("Tipo") == "variation"]
    by_parent: dict[str, list[dict]] = {}
    for v in variations:
        pid = (v.get("Ascendente") or "").replace("id:", "").strip()
        by_parent.setdefault(pid, []).append(v)

    products = []
    unmatched = []
    for p in parents:
        name = (p.get("Nome") or "").strip()
        pid = NAME_TO_ID.get(name)
        if not pid:
            unmatched.append(name)
            continue
        yoast = (p.get("Metadado: _yoast_wpseo_metadesc") or "").strip()
        short = first_useful_sentence(strip_html(p.get("Descrição curta") or ""), yoast)
        img = (p.get("Imagens") or "").split(",")[0].strip()
        vars_ = by_parent.get(p.get("ID") or "", [])
        copa = None
        copa2 = None
        any_price = None
        for v in vars_:
            unit = v.get("Valores do atributo 1") or ""
            price = parse_price(v.get("Preço") or "")
            if price is None:
                continue
            if any_price is None:
                any_price = price
            if "Copacabana I" in unit:
                copa = price
            elif "Copacabana II" in unit and copa2 is None:
                copa2 = price
        parent_price = parse_price(p.get("Preço") or "")
        original = copa or copa2 or parent_price or any_price
        products.append(
            {
                "id": pid,
                "wcName": name,
                "originalCents": original,
                "description": short,
                "imageUrl": img,
                "category": p.get("Categorias") or "",
            }
        )

    OUT.write_text(
        json.dumps({"products": products, "unmatched": unmatched}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("wrote", OUT, "count", len(products), "unmatched", unmatched)


if __name__ == "__main__":
    main()
