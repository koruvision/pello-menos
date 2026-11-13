# -*- coding: utf-8 -*-
"""
READ-ONLY full catalog listing + comparison.
Loja = public Store API. Oficialteste = WC v3 (auth) + Store fallback.
Never writes to loja.
"""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFIC_ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
OUT_JSON = ROOT / "projeto-migracao" / ".secrets" / "catalog-loja-vs-oficialteste-full.json"
OUT_MD = ROOT / "projeto-migracao" / ".secrets" / "catalog-loja-vs-oficialteste-full.md"

LOJA = "https://loja.pellomenos.com.br"


def ofic_cfg():
    values = {}
    for line in OFIC_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return {
        "url": values["PM_OFICIALTESTE_URL"].rstrip("/"),
        "user": values["PM_OFICIALTESTE_USER"],
        "password": values["PM_OFICIALTESTE_APP_PASSWORD"],
    }


def http_get(url: str, auth=None):
    headers = {"Accept": "application/json", "User-Agent": "pm-catalog-readonly/2.0"}
    if auth:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        headers["Authorization"] = "Basic " + token
    req = urllib.request.Request(url, method="GET", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            data = json.loads(body) if body.strip()[:1] in "{[" else body
            return r.status, data, {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw[:400]
        return e.code, parsed, {}


def strip_html(text: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", text or "").split())


def classify(name: str, slug: str) -> dict:
    blob = f"{name} {slug}".lower()
    audience = "masculino" if (
        "masculin" in blob or slug.endswith("-masc") or "-masc-" in slug or slug.endswith("masc")
    ) else "feminino"
    # method / kind
    kind = "outro"
    if "gift" in blob or "presente" in blob or "cartao" in blob or "cartão" in blob:
        kind = "gift"
    elif "splash" in blob:
        kind = "produto-retail"
    elif "plano" in blob or "assinatura" in blob or "silver" in blob or "gold" in blob or "pré-pago" in blob or "prepago" in blob or "clube" in blob:
        kind = "plano"
    elif "laser" in blob:
        kind = "laser"
    elif "cera" in blob:
        kind = "cera"
    elif "linha" in blob:
        kind = "linha"
    elif "esfolia" in blob:
        kind = "esfoliacao"
    elif "tintura" in blob or "plus" in blob or "calcinha" in blob:
        kind = "complemento"
    return {"audience": audience, "kind": kind}


def money_store(prices: dict) -> str:
    raw = prices.get("price") or prices.get("regular_price") or ""
    if not raw:
        return "-"
    s = str(raw)
    if s.isdigit():
        return f"{int(s)/100:.2f}"
    return s


def fetch_store(base: str, label: str):
    page, items = 1, []
    while page <= 200:
        url = f"{base}/wp-json/wc/store/v1/products?page={page}&per_page=100&orderby=id&order=asc"
        st, data, headers = http_get(url)
        if st != 200:
            raise SystemExit(f"{label} store {page}: {st} {data}")
        if not isinstance(data, list) or not data:
            break
        for p in data:
            name = p.get("name") or ""
            slug = p.get("slug") or ""
            meta = classify(name, slug)
            prices = p.get("prices") or {}
            items.append(
                {
                    "id": p.get("id"),
                    "name": name,
                    "slug": slug,
                    "sku": (p.get("sku") or "").strip(),
                    "type": p.get("type"),
                    "status": "publish",
                    "price": money_store(prices),
                    "short_description": strip_html(p.get("short_description") or "")[:240],
                    **meta,
                    "source": "store",
                }
            )
        print(f"{label} store page {page} +{len(data)} total={len(items)}")
        tp = int(headers.get("x-wp-totalpages") or 0) or None
        if tp and page >= tp:
            break
        if len(data) < 100:
            break
        page += 1
    return items


def fetch_v3(cfg: dict, label: str):
    page, items = 1, []
    auth = (cfg["user"], cfg["password"])
    while page <= 200:
        url = (
            f"{cfg['url']}/wp-json/wc/v3/products"
            f"?page={page}&per_page=100&status=any&orderby=id&order=asc"
        )
        st, data, headers = http_get(url, auth=auth)
        if st != 200:
            print(f"{label} v3 failed {st}, fallback store")
            return fetch_store(cfg["url"], label)
        if not isinstance(data, list) or not data:
            break
        for p in data:
            name = p.get("name") or ""
            slug = p.get("slug") or ""
            meta = classify(name, slug)
            items.append(
                {
                    "id": p.get("id"),
                    "name": name,
                    "slug": slug,
                    "sku": (p.get("sku") or "").strip(),
                    "type": p.get("type"),
                    "status": p.get("status"),
                    "price": p.get("price") or p.get("regular_price") or "",
                    "short_description": strip_html(p.get("short_description") or "")[:240],
                    **meta,
                    "source": "v3",
                }
            )
        print(f"{label} v3 page {page} +{len(data)} total={len(items)}")
        tp = int(headers.get("x-wp-totalpages") or 0) or None
        if tp and page >= tp:
            break
        if len(data) < 100:
            break
        page += 1
    return items


def index(products):
    by_slug, by_sku, by_name = {}, {}, {}
    for p in products:
        if p["slug"]:
            by_slug[p["slug"].lower()] = p
        if p["sku"]:
            by_sku[p["sku"].lower()] = p
        by_name[" ".join(p["name"].lower().split())] = p
    return by_slug, by_sku, by_name


def match(p, by_slug, by_sku, by_name):
    if p["sku"] and p["sku"].lower() in by_sku:
        return "sku", by_sku[p["sku"].lower()]
    if p["slug"] and p["slug"].lower() in by_slug:
        return "slug", by_slug[p["slug"].lower()]
    key = " ".join(p["name"].lower().split())
    if key in by_name:
        return "name", by_name[key]
    return None, None


def group_key(p):
    return f"{p['kind']}|{p['audience']}"


def render_list(products):
    lines = []
    groups = defaultdict(list)
    for p in products:
        groups[group_key(p)].append(p)
    order = [
        "cera|feminino",
        "cera|masculino",
        "laser|feminino",
        "laser|masculino",
        "linha|feminino",
        "linha|masculino",
        "esfoliacao|feminino",
        "esfoliacao|masculino",
        "plano|feminino",
        "plano|masculino",
        "gift|feminino",
        "gift|masculino",
        "produto-retail|feminino",
        "produto-retail|masculino",
        "complemento|feminino",
        "complemento|masculino",
        "outro|feminino",
        "outro|masculino",
    ]
    seen = set()
    for key in order + sorted(groups.keys()):
        if key in seen or key not in groups:
            continue
        seen.add(key)
        kind, audience = key.split("|", 1)
        rows = sorted(groups[key], key=lambda x: (x["name"].lower(), x["id"] or 0))
        lines.append(f"\n### {kind.upper()} — {audience} ({len(rows)})\n")
        for p in rows:
            lines.append(
                f"- `{p['id']}` **{p['name']}** | slug=`{p['slug']}` | sku=`{p['sku'] or '-'}` | "
                f"status=`{p['status']}` | tipo=`{p['type']}` | preço=`{p['price'] or '-'}`"
            )
    return "\n".join(lines)


def counts_by_group(products):
    c = defaultdict(int)
    for p in products:
        c[group_key(p)] += 1
    return dict(sorted(c.items()))


def main():
    print("READ-ONLY loja", LOJA)
    ofic = ofic_cfg()
    print("READ-ONLY oficialteste", ofic["url"])

    loja = fetch_store(LOJA, "loja")
    ofic_items = fetch_v3(ofic, "oficialteste")

    by_slug, by_sku, by_name = index(ofic_items)
    missing, matched = [], []
    for p in loja:
        how, hit = match(p, by_slug, by_sku, by_name)
        if hit:
            matched.append({"loja": p, "ofic": hit, "by": how})
        else:
            missing.append(p)

    # reverse: on ofic not on loja (published store)
    by_slug_l, by_sku_l, by_name_l = index(loja)
    only_ofic = []
    for p in ofic_items:
        how, hit = match(p, by_slug_l, by_sku_l, by_name_l)
        if not hit:
            only_ofic.append(p)

    report = {
        "mode": "read-only",
        "loja_count": len(loja),
        "oficialteste_count": len(ofic_items),
        "matched": len(matched),
        "missing_on_oficialteste": len(missing),
        "only_on_oficialteste": len(only_ofic),
        "loja_by_group": counts_by_group(loja),
        "oficialteste_by_group": counts_by_group(ofic_items),
        "loja_products": loja,
        "oficialteste_products": ofic_items,
        "missing_products": missing,
        "only_oficialteste_products": only_ofic,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = []
    md.append("# Catálogo loja vs oficialteste (somente leitura)\n")
    md.append(
        f"- Loja publicados (Store API): **{len(loja)}**\n"
        f"- Oficialteste (WC, status any): **{len(ofic_items)}**\n"
        f"- Com correspondente: **{len(matched)}**\n"
        f"- Na loja e faltando no oficialteste: **{len(missing)}**\n"
        f"- Só no oficialteste: **{len(only_ofic)}**\n"
    )
    md.append("\n## Contagem por tipo × público\n")
    md.append("### Loja\n")
    for k, v in counts_by_group(loja).items():
        md.append(f"- `{k}`: {v}")
    md.append("\n### Oficialteste\n")
    for k, v in counts_by_group(ofic_items).items():
        md.append(f"- `{k}`: {v}")

    md.append("\n## Lista completa — LOJA\n")
    md.append(render_list(loja))
    md.append("\n## Lista completa — OFICIALTESTE\n")
    md.append(render_list(ofic_items))

    if missing:
        md.append("\n## Faltando no oficialteste (existem na loja)\n")
        for p in missing:
            md.append(
                f"- **{p['name']}** | {p['kind']}/{p['audience']} | slug=`{p['slug']}` | sku=`{p['sku'] or '-'}`"
            )
    else:
        md.append("\n## Faltando no oficialteste\n\nNenhum (todos os publicados da loja têm correspondente).\n")

    if only_ofic:
        md.append("\n## Só no oficialteste (não achados na loja publicada)\n")
        for p in only_ofic:
            md.append(
                f"- **{p['name']}** | {p['kind']}/{p['audience']} | slug=`{p['slug']}` | "
                f"status=`{p['status']}` | sku=`{p['sku'] or '-'}`"
            )

    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n=== CONTAGEM LOJA ===")
    for k, v in counts_by_group(loja).items():
        print(f"  {k}: {v}")
    print("=== CONTAGEM OFICIALTESTE ===")
    for k, v in counts_by_group(ofic_items).items():
        print(f"  {k}: {v}")
    print("missing", len(missing), "only_ofic", len(only_ofic))
    print("wrote", OUT_MD)


if __name__ == "__main__":
    main()
