"""Clone woo-bridge entries for catalog IDs missing units (esfoliação, *-masc).

Uses the same slug resolution as export_wp_home.py so cart variation IDs
match products that already exist in WooCommerce.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_SRC = ROOT / "src" / "lib" / "woo-bridge.json"
BRIDGE_OUT = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
DATA_TS = ROOT / "src" / "lib" / "data.ts"
SLUGS_JSON = ROOT / "wordpress-loja" / "pm-home" / "woo-slugs.json"

ALIASES = {
    "plano-silver": "plano-de-assinatura-vip-silver-copia-2",
    "plano-gold": "plano-de-assinatura-vip-gold",
    "plano-clube-laser": "clube-do-laser",
    "plano-prepago": "pre-pago-pello-menos",
    "perna-laser": "perna-inteira-laser-2",
    "perna-cera": "perna-inteira-cera",
    "bracos-laser": "bracos-inteiros-laser-2",
    "nadegas-cera": "nadegas-completas-cera",
    "design-sobrancelha": "design-de-sobrancelha-cera",
    "rosto-inteiro-laser": "rosto-inteiro-laser-buqunzpsd-p",
    "virilha-faixa-laser": "virilha-c-faixa-laser-2",
    "virilha-cavada-faixa-laser": "virilha-cavada-c-faixa-laser-2",
    "axila-laser": "axilas-laser-2",
    "virilha-cera": "virilha-total-cera",
    "virilha-comum-laser": "virilha-laser-2",
    "coxa-laser": "coxas-laser",
    "sobrancelha-henna": "sobrancelha-henna-cera",
    "sobrancelha-henna-simples": "design-de-sobrancelha-henna-cera",
}

EXTRA = {
    "design-sobrancelha-realce": "design-de-sobrancelha-realce-cera",
    "areola-laser": "aureola-laser-2",
    "peito-cera-masc": "abdomen-cera-2",
    "peito-laser-masc": "abdomen-laser-2",
    "barba-laser-masc": "rosto-inteiro-laser-buqunzpsd-p",
    "bigode-laser-masc": "buco-laser-2",
    "torax-abdomen-laser-masc": "abdomen-laser-2",
    "mamilo-laser-masc": "aureola-laser-2",
    # Woo slug list has virilha-total-laser-2; bridge entry is virilha-laser / virilha-laser-2
    "virilha-total-laser-masc": "virilha-laser-2",
}

ESFOLIACAO = {
    "axilas": "axila-cera",
    "virilha": "virilha-total-cera",
    "virilha-faixa": "virilha-comum-faixa-cera",
    "perna": "perna-inteira-cera",
    "meia-perna": "meia-perna-cera",
    "faixa": "faixa-cera",
    "braco": "bracos-cera",
    "meio-braco": "antebraco-cera",
    "abdomen": "abdomen-cera-2",
    "nadegas": "nadegas-completas-cera",
    "meia-nadega": "meia-nadega-cera",
    "coxa": "coxa-cera",
    "costas": "costas-cera",
    "seios": "seios-cera",
}


def catalog_ids() -> list[str]:
    text = DATA_TS.read_text(encoding="utf-8")
    chunk = text.split("const catalogItems")[1].split("function defaultDescription")[0]
    return re.findall(r'\bid: "([^"]+)"', chunk)


def resolve_woo_slug(catalog_id: str, slugs: set[str]) -> str | None:
    if catalog_id == "body-splash" or catalog_id.startswith("cartao-presente"):
        return None
    slug = EXTRA.get(catalog_id, catalog_id)
    if slug.endswith("-masc"):
        slug = slug[: -len("-masc")]
    slug = ALIASES.get(slug, slug)
    if slug.startswith("esfoliacao-"):
        slug = ESFOLIACAO.get(slug[len("esfoliacao-") :], slug)
    for candidate in (slug, f"{slug}-2"):
        if candidate in slugs:
            return candidate
    return slug if slug else None


def index_by_slug(bridge: dict) -> dict[str, str]:
    by: dict[str, str] = {}
    for key, row in bridge.items():
        s = (row or {}).get("slug") or ""
        if s and s not in by:
            by[s] = key
        # also index by catalog key when slug differs
        if key not in by:
            by[key] = key
    return by


def find_source(bridge: dict, by_slug: dict[str, str], woo_slug: str | None) -> dict | None:
    if not woo_slug:
        return None
    # direct catalog key
    if woo_slug in bridge and (bridge[woo_slug].get("units") or bridge[woo_slug].get("productId")):
        return bridge[woo_slug]
    # slug field match
    key = by_slug.get(woo_slug)
    if key and key in bridge:
        return bridge[key]
    # strip -2
    if woo_slug.endswith("-2"):
        base = woo_slug[:-2]
        if base in bridge:
            return bridge[base]
        key = by_slug.get(base)
        if key and key in bridge:
            return bridge[key]
    # try without alias noise: match any entry whose slug equals woo_slug
    for row in bridge.values():
        if (row or {}).get("slug") == woo_slug:
            return row
    return None


def needs_clone(row: dict | None) -> bool:
    if not row:
        return True
    units = row.get("units") or {}
    product_id = row.get("productId")
    # empty units and no productId → unusable for cart
    if not product_id and not units:
        return True
    # product with units missing → still try clone if no variation map
    if product_id and not units:
        # simples (body-splash) ok; services need units
        return False
    return False


def main() -> None:
    bridge = json.loads(BRIDGE_SRC.read_text(encoding="utf-8"))
    slugs: set[str] = set()
    if SLUGS_JSON.is_file():
        slugs = set(json.loads(SLUGS_JSON.read_text(encoding="utf-8")))
    # also collect slugs from bridge
    for row in bridge.values():
        s = (row or {}).get("slug")
        if s:
            slugs.add(s)

    by_slug = index_by_slug(bridge)
    ids = catalog_ids()
    cloned = 0
    skipped = 0
    missing: list[str] = []

    for catalog_id in ids:
        existing = bridge.get(catalog_id)
        if existing and (existing.get("units") or {}):
            skipped += 1
            continue

        woo_slug = resolve_woo_slug(catalog_id, slugs)
        source = find_source(bridge, by_slug, woo_slug)
        # never clone from self when empty
        if source is existing:
            source = None
            for row in bridge.values():
                if row is existing:
                    continue
                if (row or {}).get("slug") == woo_slug and (row.get("units") or {}):
                    source = row
                    break
        if not source or not (source.get("units") or {}):
            if existing and existing.get("productId"):
                skipped += 1
            else:
                missing.append(f"{catalog_id} -> {woo_slug}")
            continue

        clone = deepcopy(source)
        if woo_slug:
            clone["slug"] = source.get("slug") or woo_slug
        bridge[catalog_id] = clone
        cloned += 1
        print("clone", catalog_id, "<-", woo_slug, "units", len(clone.get("units") or {}))

    text = json.dumps(bridge, ensure_ascii=False, indent=2) + "\n"
    BRIDGE_SRC.write_text(text, encoding="utf-8")
    BRIDGE_OUT.parent.mkdir(parents=True, exist_ok=True)
    BRIDGE_OUT.write_text(text, encoding="utf-8")
    print("done cloned", cloned, "kept", skipped, "missing", len(missing), "total", len(bridge))
    for row in missing[:30]:
        print("missing", row)
    if len(missing) > 30:
        print("missing …", len(missing) - 30, "more")


if __name__ == "__main__":
    main()
