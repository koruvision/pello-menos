# -*- coding: utf-8 -*-
"""
READ-ONLY product diff: loja.pellomenos.com.br vs oficialteste.

HARD RULES
- Only HTTP GET (never POST/PUT/PATCH/DELETE)
- Loja: public Store API only (no write credentials used)
- Oficialteste: authenticated GET with existing env (read products)
- Fields: name, slug, sku/prices when available, short description
"""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFIC_ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
OUT = ROOT / "projeto-migracao" / ".secrets" / "diff-loja-vs-oficialteste-products.json"

LOJA = "https://loja.pellomenos.com.br"
OFIC_FALLBACK = "https://pellomenosoficialteste.companygenesis.com.br"


def read_ofic():
    if not OFIC_ENV.is_file():
        return {"url": OFIC_FALLBACK, "user": "", "password": ""}
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


def http_get(url: str, auth: tuple[str, str] | None = None):
    headers = {
        "Accept": "application/json",
        "User-Agent": "pm-product-diff-readonly/1.1",
    }
    if auth:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        headers["Authorization"] = "Basic " + token
    req = urllib.request.Request(url, method="GET", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            data = json.loads(body) if body.strip()[:1] in "{[" else body
            hdrs = {k.lower(): v for k, v in r.headers.items()}
            return r.status, data, hdrs
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw[:400]
        return e.code, parsed, {}


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return " ".join(text.split())


def fetch_loja_store_api():
    """Public Store API — published catalog only. GET only."""
    page = 1
    per_page = 100
    items = []
    while page <= 200:
        url = (
            f"{LOJA}/wp-json/wc/store/v1/products"
            f"?page={page}&per_page={per_page}&orderby=id&order=asc"
        )
        status, data, headers = http_get(url)
        if status != 200:
            raise SystemExit(f"loja store API page {page}: HTTP {status} {data}")
        if not isinstance(data, list) or not data:
            break
        for p in data:
            prices = p.get("prices") or {}
            items.append(
                {
                    "id": p.get("id"),
                    "name": p.get("name") or "",
                    "slug": p.get("slug") or "",
                    "sku": (p.get("sku") or "").strip(),
                    "type": p.get("type"),
                    "status": "publish",
                    "price": prices.get("price") or prices.get("regular_price") or "",
                    "regular_price": prices.get("regular_price") or "",
                    "sale_price": prices.get("sale_price") or "",
                    "currency": prices.get("currency_code") or "",
                    "short_description": strip_html(p.get("short_description") or "")[:400],
                    "description": strip_html(p.get("description") or "")[:400],
                    "source": "wc/store/v1",
                }
            )
        print(f"loja(store): page {page} +{len(data)} (total {len(items)})")
        total_pages = int(headers.get("x-wp-totalpages") or "0") or None
        if total_pages is not None and page >= total_pages:
            break
        if len(data) < per_page:
            break
        page += 1
    return items


def fetch_ofic_wc_v3(cfg: dict):
    page = 1
    per_page = 100
    items = []
    auth = (cfg["user"], cfg["password"]) if cfg["user"] and cfg["password"] else None
    while page <= 200:
        url = (
            f"{cfg['url']}/wp-json/wc/v3/products"
            f"?page={page}&per_page={per_page}&status=any&orderby=id&order=asc"
        )
        status, data, headers = http_get(url, auth=auth)
        if status != 200:
            # fallback public store on oficialteste
            print(f"oficialteste wc/v3 failed ({status}); trying store API")
            return fetch_ofic_store(cfg["url"])
        if not isinstance(data, list) or not data:
            break
        for p in data:
            items.append(
                {
                    "id": p.get("id"),
                    "name": p.get("name") or "",
                    "slug": p.get("slug") or "",
                    "sku": (p.get("sku") or "").strip(),
                    "type": p.get("type"),
                    "status": p.get("status"),
                    "price": p.get("price") or "",
                    "regular_price": p.get("regular_price") or "",
                    "sale_price": p.get("sale_price") or "",
                    "short_description": strip_html(p.get("short_description") or "")[:400],
                    "description": strip_html(p.get("description") or "")[:400],
                    "source": "wc/v3",
                }
            )
        print(f"oficialteste(v3): page {page} +{len(data)} (total {len(items)})")
        total_pages = int(headers.get("x-wp-totalpages") or "0") or None
        if total_pages is not None and page >= total_pages:
            break
        if len(data) < per_page:
            break
        page += 1
    return items


def fetch_ofic_store(base: str):
    page = 1
    per_page = 100
    items = []
    while page <= 200:
        url = (
            f"{base}/wp-json/wc/store/v1/products"
            f"?page={page}&per_page={per_page}&orderby=id&order=asc"
        )
        status, data, headers = http_get(url)
        if status != 200:
            raise SystemExit(f"oficialteste store page {page}: HTTP {status} {data}")
        if not isinstance(data, list) or not data:
            break
        for p in data:
            prices = p.get("prices") or {}
            items.append(
                {
                    "id": p.get("id"),
                    "name": p.get("name") or "",
                    "slug": p.get("slug") or "",
                    "sku": (p.get("sku") or "").strip(),
                    "type": p.get("type"),
                    "status": "publish",
                    "price": prices.get("price") or "",
                    "regular_price": prices.get("regular_price") or "",
                    "sale_price": prices.get("sale_price") or "",
                    "short_description": strip_html(p.get("short_description") or "")[:400],
                    "description": strip_html(p.get("description") or "")[:400],
                    "source": "wc/store/v1",
                }
            )
        print(f"oficialteste(store): page {page} +{len(data)} (total {len(items)})")
        total_pages = int(headers.get("x-wp-totalpages") or "0") or None
        if total_pages is not None and page >= total_pages:
            break
        if len(data) < per_page:
            break
        page += 1
    return items


def index_products(products):
    by_sku, by_slug, by_name = {}, {}, {}
    for p in products:
        if p["sku"]:
            by_sku[p["sku"].lower()] = p
        if p["slug"]:
            by_slug[p["slug"].lower()] = p
        name = " ".join(p["name"].lower().split())
        if name:
            by_name[name] = p
    return by_sku, by_slug, by_name


def find_match(p, by_sku, by_slug, by_name):
    if p["sku"] and p["sku"].lower() in by_sku:
        return "sku", by_sku[p["sku"].lower()]
    if p["slug"] and p["slug"].lower() in by_slug:
        return "slug", by_slug[p["slug"].lower()]
    name = " ".join(p["name"].lower().split())
    if name in by_name:
        return "name", by_name[name]
    return None, None


def money(cents_or_str):
    s = str(cents_or_str or "").strip()
    if not s:
        return "-"
    # Store API often returns minor units as string of cents
    if s.isdigit() and len(s) >= 3:
        try:
            return f"R$ {int(s)/100:.2f}".replace(".", ",")
        except Exception:
            return s
    return s


def main():
    print("READ-ONLY loja:", LOJA, "(Store API pública — sem escrita)")
    ofic = read_ofic()
    print("READ-ONLY oficialteste:", ofic["url"])

    loja_products = fetch_loja_store_api()
    ofic_products = fetch_ofic_wc_v3(ofic)

    by_sku, by_slug, by_name = index_products(ofic_products)
    missing = []
    matched = 0
    for p in loja_products:
        how, hit = find_match(p, by_sku, by_slug, by_name)
        if hit is None:
            missing.append(p)
        else:
            matched += 1

    report = {
        "mode": "read-only",
        "loja_source": "wc/store/v1 (published only)",
        "nota_auth": (
            "App password '325g' retornou invalid_username na loja; "
            "comparação usou catálogo público. Rascunhos/privados da loja não entram."
        ),
        "loja_count": len(loja_products),
        "oficialteste_count": len(ofic_products),
        "matched_count": matched,
        "missing_on_oficialteste_count": len(missing),
        "missing_on_oficialteste": [
            {
                "id": p["id"],
                "name": p["name"],
                "slug": p["slug"],
                "sku": p["sku"],
                "type": p["type"],
                "price": p["price"],
                "regular_price": p["regular_price"],
                "short_description": p["short_description"][:200],
            }
            for p in missing
        ],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\n=== RESUMO (somente leitura) ===")
    print("loja (publicados):", report["loja_count"])
    print("oficialteste:", report["oficialteste_count"])
    print("com correspondente:", report["matched_count"])
    print("FALTANDO no oficialteste:", report["missing_on_oficialteste_count"])
    print("arquivo:", OUT)
    if missing:
        print("\n--- Na loja e AUSENTES no oficialteste ---")
        for p in missing:
            print(
                f"- [{p['id']}] {p['name']} | slug={p['slug']} | sku={p['sku'] or '-'} | "
                f"preço={money(p['price'])}"
            )


if __name__ == "__main__":
    main()
