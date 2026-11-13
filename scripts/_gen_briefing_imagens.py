# -*- coding: utf-8 -*-
"""Generate designer briefing text: products + loja reference image URLs."""
from __future__ import annotations

import csv
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")
CSV = ROOT / "projeto-migracao" / "historico" / "14-origem-precos-catalogo.csv"
BRIDGE = json.loads((ROOT / "src" / "lib" / "woo-bridge.json").read_text(encoding="utf-8"))
OUT = ROOT / "projeto-migracao" / "historico" / "15-briefing-imagens-ecommerce.md"
LOJA = "https://loja.pellomenos.com.br"


def fetch_loja_images() -> dict[str, str]:
    """slug -> image src from Store API."""
    by_slug: dict[str, str] = {}
    page = 1
    while page <= 50:
        url = f"{LOJA}/wp-json/wc/store/v1/products?page={page}&per_page=100&orderby=id&order=asc"
        req = urllib.request.Request(url, headers={"User-Agent": "pm-briefing/1", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
            headers = {k.lower(): v for k, v in r.headers.items()}
        if not data:
            break
        for p in data:
            slug = (p.get("slug") or "").lower()
            imgs = p.get("images") or []
            src = ""
            if imgs:
                src = imgs[0].get("src") or imgs[0].get("thumbnail") or ""
            if slug and src:
                by_slug[slug] = src
        tp = int(headers.get("x-wp-totalpages") or 0) or None
        if tp and page >= tp:
            break
        if len(data) < 100:
            break
        page += 1
    return by_slug


def catalog_ids_from_csv():
    rows = list(
        csv.DictReader(CSV.open(encoding="utf-8-sig"), delimiter=";")
    )
    skip = {"Cartão presente", "Produtos (retail)"}
    skip_ids = {"produto-1-real", "henna", "realce"}
    # include henna/realce/tintura as they're in cera category visually - user said all services
    # Actually include everything in cera/laser/linha/esfol/planos except test product
    skip_ids = {"produto-1-real"}
    out = []
    for r in rows:
        if r["categoria"] in skip:
            continue
        if r["id"] in skip_ids:
            continue
        out.append(r)
    return out


def loja_ref_for(catalog_id: str, audience: str, by_slug: dict[str, str]) -> str:
    if audience != "feminino":
        return ""  # masculino não existe na loja
    row = BRIDGE.get(catalog_id) or {}
    slug = (row.get("slug") or "").lower()
    if slug and slug in by_slug:
        return by_slug[slug]
    # try catalog id as slug
    if catalog_id in by_slug:
        return by_slug[catalog_id]
    if f"{catalog_id}-2" in by_slug:
        return by_slug[f"{catalog_id}-2"]
    return ""


def shirt_hint(pid: str) -> str:
    """Masculine wardrobe hint for designer."""
    bare = (
        "peito",
        "abdomen",
        "torax",
        "costas",
        "mamilo",
        "mamilos",
        "intergluteos",
        "nadegas",
        "meia-nadega",
        "virilha",
        "saco",
        "coxa",
        "perna",
        "meia-perna",
        "faixa",
    )
    face = ("barba", "bigode", "queixo", "nariz", "orelha", "pescoco", "rosto", "sobrancelha", "design")
    arms = ("braco", "antebraco", "axila")
    base = pid.replace("-cera-masc", "").replace("-laser-masc", "").replace("-masc", "")
    if any(x in base for x in face):
        return "Com camisa (ou gola/camiseta discreta); foco no rosto/área; cueca N/A"
    if any(x in base for x in arms):
        return "Sem camisa ou manga curta/regata conforme área; cueca box branca se aparecer tronco"
    if any(x in base for x in bare):
        return "Sem camisa; cueca box branca"
    if "esfoliacao" in pid:
        return "Mesmo guarda-roupa da área correspondente em cera"
    if "plano" in pid:
        return "Arte de plano (não foto de área); seguir identidade da marca"
    return "Avaliar área: tronco descoberto + box branca OU camisa se for rosto/acessório"


def main():
    print("fetching loja images...")
    by_slug = fetch_loja_images()
    print("loja slugs with images", len(by_slug))
    rows = catalog_ids_from_csv()

    lines = []
    lines.append("# BRIEFING DE IMAGENS — E-commerce Pello Menos")
    lines.append("")
    lines.append("**Para:** designer (refazer todas as fotos de serviço do e-commerce)")
    lines.append("**Data:** 27/10/2026")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Objetivo")
    lines.append("")
    lines.append(
        "Refazer **todas** as imagens de produto/serviço do e-commerce (feminino e masculino), "
        "com qualidade de campanha, no padrão visual definido abaixo. "
        "**Não** reutilizar as imagens atuais do site como entrega final — elas servem só de contexto "
        "quando houver referência da loja. A única referência visual **obrigatória** de estilo feminino "
        "é **Axila – Cera** (`axila-cera`)."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Especificações técnicas (todas as fotos de serviço)")
    lines.append("")
    lines.append("| Item | Especificação |")
    lines.append("|------|----------------|")
    lines.append("| Formato de entrega | **WebP** (qualidade alta, sem artefato) |")
    lines.append("| Proporção | **4:5** (retrato — card do site) |")
    lines.append("| Tamanho recomendado | **1080 × 1350 px** (export final); mínimo aceitável **864 × 1152 px** |")
    lines.append("| Nome do arquivo | Igual ao ID do produto + `.webp` (ex.: `axila-cera.webp`, `peito-cera-masc.webp`) |")
    lines.append("| Pasta lógica | Feminino: `products/`; Masculino: `products/male/` |")
    lines.append("| Fundo / luz | Limpo, clínico-suave, pele bem iluminada; área do serviço clara e legível |")
    lines.append("| Texto na imagem | Evitar texto; se precisar, mínimo e legível |")
    lines.append("")
    lines.append("Planos / clube: podem ser artes 4:5 no mesmo tamanho, sem foto de corpo se a campanha for gráfica.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Padrão visual")
    lines.append("")
    lines.append("### Feminino — referência obrigatória")
    lines.append("")
    lines.append(
        "- **Modelo de estilo:** produto **Axila – Cera** (`axila-cera`)."
    )
    lines.append(
        "- Tom: foto de campanha, área marcada/visível, estética spa/clínica, enquadramento 4:5."
    )
    lines.append(
        "- Todas as demais fotos femininas devem parecer da **mesma sessão / mesmo tratamento visual** "
        "(cor, luz, crop, pele, ausência de poluição visual)."
    )
    axila_loja = loja_ref_for("axila-cera", "feminino", by_slug)
    if axila_loja:
        lines.append(f"- Imagem de referência na loja (axila-cera): {axila_loja}")
    lines.append("")
    lines.append("### Masculino — referência de guarda-roupa")
    lines.append("")
    lines.append("- **Cueca:** boxer / box **branca** sempre que a região inferior ou tronco aparecer.")
    lines.append("- **Com camisa:** áreas de rosto / barba / bigode / pescoço / orelha / nariz / queixo / sobrancelha (camisa ou gola discreta).")
    lines.append(
        "- **Sem camisa:** peito, abdômen, tórax, costas, axila/braço quando a área exigir, virilha, nádegas, pernas, coxa, etc."
    )
    lines.append(
        "- Não há equivalente masculino na loja oficial — coluna de referência da loja fica **vazia**; "
        "seguir só este briefing + coerência com o set masculino."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Lista produto a produto")
    lines.append("")
    lines.append(
        "Coluna **Imagem de referência (loja)**: URL da loja `loja.pellomenos.com.br` quando existir. "
        "Se vazio = não há referência na loja (típico do masculino e de alguns itens)."
    )
    lines.append("")

    order = [
        ("feminino", "Cera"),
        ("feminino", "Laser"),
        ("feminino", "Linha"),
        ("feminino", "Esfoliação"),
        ("feminino", "Planos"),
        ("masculino", "Cera"),
        ("masculino", "Laser"),
        ("masculino", "Esfoliação"),
        ("masculino", "Planos"),
    ]

    for publico, cat in order:
        group = [r for r in rows if r["publico"] == publico and r["categoria"] == cat]
        if not group:
            continue
        lines.append(f"### {publico.capitalize()} — {cat}")
        lines.append("")
        n = 0
        for r in sorted(group, key=lambda x: x["id"]):
            n += 1
            ref = loja_ref_for(r["id"], r["publico"], by_slug)
            ref_txt = ref if ref else "—(sem referência na loja)"
            file_out = f"{r['id']}.webp"
            extra = ""
            if r["publico"] == "masculino" and cat not in ("Planos",):
                extra = f"\n- Guarda-roupa: {shirt_hint(r['id'])}"
            lines.append(f"#### {n}. {r['nome']}")
            lines.append(f"- ID / arquivo: `{file_out}`")
            lines.append(f"- Categoria: {publico} · {cat}")
            lines.append(f"- Formato: WebP · 1080×1350 (4:5)")
            lines.append(f"- Imagem de referência (loja): {ref_txt}")
            if r["id"] == "axila-cera":
                lines.append("- **PADRÃO VISUAL FEMININO — usar esta como modelo de estilo para todas as femininas**")
            lines.append(extra)
            lines.append("")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Entrega")
    lines.append("")
    lines.append("1. Um arquivo WebP por ID listado.")
    lines.append("2. Mesmo nome de arquivo do ID.")
    lines.append("3. Pasta `feminino/` e `masculino/` (ou `products/` e `products/male/`).")
    lines.append("4. Versão master (PSD/TIFF) opcional, mas a entrega de site é WebP.")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT)
    # also print full text for chat? user asked chat - write file AND we'll read it back
    print("CHARS", len("\n".join(lines)))


if __name__ == "__main__":
    main()
