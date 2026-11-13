# -*- coding: utf-8 -*-
"""Coloca SKUs de ensaio na Home da loja + fichas + bridge IDs corretos + publica."""
from __future__ import annotations

import base64
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
SKUS = json.loads((ROOT / "scripts" / "_loja_esquenta_test_skus.json").read_text(encoding="utf-8"))
CHEAP = json.loads((ROOT / "scripts" / "_loja_cheap_fixture.json").read_text(encoding="utf-8"))

PRODUCTS = [
    {
        "id": "produto-1-real",
        "woo": int(CHEAP["product_id"]),
        "name": "Produto R$ 1,99",
        "method": "cera",
        "price": "R$ 1,99",
        "cents": 199,
        "note": "sem Esquenta (excluído)",
    },
    {
        "id": "pm-teste-esquenta-laser",
        "woo": int(SKUS["pm-teste-esquenta-laser"]),
        "name": "PM Teste Esquenta Laser A",
        "method": "laser",
        "price": "R$ 5,00",
        "cents": 500,
        "note": "1 laser → Esquenta 60% = R$ 2,00",
    },
    {
        "id": "pm-teste-esquenta-laser-b",
        "woo": int(SKUS["pm-teste-esquenta-laser-b"]),
        "name": "PM Teste Esquenta Laser B",
        "method": "laser",
        "price": "R$ 5,00",
        "cents": 500,
        "note": "com A+C → 65%",
    },
    {
        "id": "pm-teste-esquenta-laser-c",
        "woo": int(SKUS["pm-teste-esquenta-laser-c"]),
        "name": "PM Teste Esquenta Laser C",
        "method": "laser",
        "price": "R$ 5,00",
        "cents": 500,
        "note": "com A+B → 65%",
    },
    {
        "id": "pm-teste-esquenta-cera",
        "woo": int(SKUS["pm-teste-esquenta-cera"]),
        "name": "PM Teste Esquenta Cera A",
        "method": "cera",
        "price": "R$ 5,00",
        "cents": 500,
        "note": "1 cera → 15% = R$ 4,25",
    },
    {
        "id": "pm-teste-esquenta-cera-b",
        "woo": int(SKUS["pm-teste-esquenta-cera-b"]),
        "name": "PM Teste Esquenta Cera B",
        "method": "cera",
        "price": "R$ 5,00",
        "cents": 500,
        "note": "com A+C → 20%",
    },
    {
        "id": "pm-teste-esquenta-cera-c",
        "woo": int(SKUS["pm-teste-esquenta-cera-c"]),
        "name": "PM Teste Esquenta Cera C",
        "method": "cera",
        "price": "R$ 5,00",
        "cents": 500,
        "note": "com A+B → 20%",
    },
]


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def call(method, path, payload=None, raw=None, content_type="application/json", timeout=300):
    cfg = env()
    data = raw if raw is not None else (None if payload is None else json.dumps(payload).encode())
    token = base64.b64encode(f"{cfg['PM_LOJA_USER']}:{cfg['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
        "User-Agent": "pm-home-ensaio/1.0",
        "Content-Type": content_type,
    }
    req = urllib.request.Request(cfg["PM_LOJA_URL"].rstrip("/") + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body[:1] in "[{" else body)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            return err.code, json.loads(body)
        except json.JSONDecodeError:
            return err.code, body[:500]


def ensure_woo_publish():
    for p in PRODUCTS:
        st, body = call(
            "PUT",
            f"/wp-json/wc/v3/products/{p['woo']}",
            {
                "status": "publish",
                "catalog_visibility": "hidden",
                "regular_price": f"{p['cents']/100:.2f}",
            },
        )
        print("woo", p["id"], p["woo"], st, body.get("status") if isinstance(body, dict) else body)


def patch_bridge_and_related():
    bridge_path = PM / "woo-bridge.json"
    bridge = json.loads(bridge_path.read_text(encoding="utf-8"))
    related_path = PM / "cart-related.json"
    related = json.loads(related_path.read_text(encoding="utf-8"))
    products = related.setdefault("products", {})

    for p in PRODUCTS:
        entry = bridge.get(p["id"]) or {
            "slug": p["id"] if p["id"] != "produto-1-real" else "produto-r-1",
            "longText": p["name"],
            "rj": {"regularCents": p["cents"], "saleCents": p["cents"]},
            "spdf": {"regularCents": p["cents"], "saleCents": p["cents"]},
            "units": {},
        }
        entry["productId"] = p["woo"]
        entry["slug"] = entry.get("slug") or p["id"]
        entry["rj"] = {"regularCents": p["cents"], "saleCents": p["cents"]}
        entry["spdf"] = {"regularCents": p["cents"], "saleCents": p["cents"]}
        entry["units"] = {}
        if p["id"].startswith("pm-teste"):
            entry["testEsquenta"] = True
        bridge[p["id"]] = entry

        products[p["id"]] = {
            "id": p["id"],
            "name": p["name"],
            "method": p["method"],
            "audience": "feminino",
            "originalCents": p["cents"],
            "priceCents": p["cents"],
            "skipDiscount": p["id"] == "produto-1-real",
            "image": "/images/products/cartao-presente-80.jpg"
            if p["id"] == "produto-1-real"
            else "/images/products/axila-cera.webp",
            "wooProductId": p["woo"],
            "wooId": str(p["woo"]),
            "productId": str(p["woo"]),
            "duration": "Ensaio",
            "category": "corpo",
        }

    bridge_path.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    related_path.write_text(json.dumps(related, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("bridge+related OK")


def make_product_html():
    template = (PM / "products" / "produto-1-real.html").read_text(encoding="utf-8")
    routes = json.loads((PM / "routes.json").read_text(encoding="utf-8"))

    for p in PRODUCTS:
        html = template
        # IDs / catalog
        html = html.replace('data-product-id="49394"', f'data-product-id="{p["woo"]}"')
        html = html.replace('data-product-id="48409"', f'data-product-id="{p["woo"]}"')
        html = re.sub(r'data-catalog-id="[^"]+"', f'data-catalog-id="{p["id"]}"', html)
        html = re.sub(r'data-method="[^"]+"', f'data-method="{p["method"]}"', html)
        html = re.sub(r'href="/produto/produto-1-real/"', f'href="/produto/{p["id"]}/"', html)
        html = re.sub(r'href="/produto/produto-r-1/"', f'href="/produto/{p["id"]}/"', html)
        # titles / names
        html = re.sub(r"Produto R\$ 1,99", p["name"], html)
        html = re.sub(r"Produto R\$ 1(?!,99)", p["name"], html)
        html = re.sub(r"R\$\s*1,99", p["price"], html)
        html = re.sub(r">Teste\*", f'>{p["note"][:40]}*', html, count=1)
        # SKU line if present
        html = re.sub(r"PM-0001", f'PM-T{p["woo"]}', html)
        html = re.sub(r"PEL-PRODUTO1REAL", p["id"].upper().replace("-", "")[:24], html)

        out = PM / "products" / f"{p['id']}.html"
        out.write_text(html, encoding="utf-8")
        routes[p["id"]] = f"products/{p['id']}.html"
        if p["id"] == "produto-1-real":
            routes["produto-r-1"] = f"products/{p['id']}.html"
        print("ficha", out.name, "woo", p["woo"])

    (PM / "routes.json").write_text(json.dumps(routes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("routes OK")


def inject_home_strip():
    home_path = PM / "home.html"
    text = home_path.read_text(encoding="utf-8")
    # remove previous ensaio strip if re-run
    text = re.sub(
        r'<section id="ensaio-testes"[\s\S]*?</section>',
        "",
        text,
        count=1,
    )

    marker = "Cera em destaque"
    i = text.find(marker)
    if i < 0:
        raise SystemExit("Cera em destaque not found")
    # insert before the section that contains the marker
    sec = text.rfind("<section", 0, i)
    if sec < 0:
        raise SystemExit("section start not found")

    # template card from first article after marker
    art1 = text.find('<article data-carousel-card="true"', i)
    art2 = text.find('<article data-carousel-card="true"', art1 + 10)
    card_tpl = text[art1:art2]

    cards = []
    for p in PRODUCTS:
        card = card_tpl
        card = re.sub(r'href="/produto/[^"]+"', f'href="/produto/{p["id"]}/"', card)
        card = re.sub(r"(<h3[^>]*>)([\s\S]*?)(</h3>)", rf"\1{p['name']}\3", card, count=1)
        card = re.sub(r'alt="[^"]*"', f'alt="{p["name"]}"', card, count=1)
        card = re.sub(r"R\$\s*[0-9\.]+,[0-9]{2}", p["price"], card)
        card = re.sub(
            r"(clock[^<]*</svg>\s*)([^<]+)",
            rf"\1Ensaio · {p['method']}",
            card,
            count=1,
            flags=re.I,
        )
        cards.append(card)

    section = (
        '<section id="ensaio-testes" data-home-panel="extra" class="js-reveal border-b border-outline/30 bg-secondary-container/30 py-10 md:py-14">'
        '<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">'
        '<div class="mb-4 max-w-2xl">'
        '<p class="text-xs font-semibold uppercase tracking-[0.2em] text-primary">Ensaio interno</p>'
        '<h2 class="mt-1 font-display text-2xl text-on-background md:text-3xl">Produtos de teste (carrinho)</h2>'
        '<p class="mt-1 text-on-surface-variant">Laser/Cera R$ 5 + produto R$ 1,99. Abra a ficha, escolha unidade e adicione.</p>'
        "</div>"
        '<div class="relative mx-auto max-w-7xl px-12 sm:px-14 md:px-16">'
        '<div class="pointer-events-none absolute inset-y-0 left-0 z-10 w-10 bg-gradient-to-r from-secondary-container/30 to-transparent sm:w-12"></div>'
        '<div class="pointer-events-none absolute inset-y-0 right-0 z-10 w-10 bg-gradient-to-l from-secondary-container/30 to-transparent sm:w-12"></div>'
        '<div class="flex snap-x snap-mandatory gap-4 overflow-x-auto pb-2 scroll-px-4" data-carousel-track="ensaio">'
        + "".join(cards)
        + "</div></div></div></section>"
    )

    text2 = text[:sec] + section + text[sec:]
    home_path.write_text(text2, encoding="utf-8")
    print("home strip OK", "ensaio-testes" in text2, "cards", len(cards))


def open_maintenance_off():
    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    if st != 200 or not isinstance(rows, list):
        raise SystemExit(f"snippets {st}")
    for row in rows:
        if row.get("name") == "pm-ecommerce-maintenance":
            sn = call("GET", f"/wp-json/code-snippets/v1/snippets/{row['id']}")[1]
            payload = {
                "name": sn.get("name"),
                "code": sn.get("code"),
                "scope": sn.get("scope") or "global",
                "active": False,
            }
            st2, saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{row['id']}", payload)
            print("maintenance off", st2, saved.get("active") if isinstance(saved, dict) else saved)
            return
    print("maintenance snippet not found")


def publish():
    files = [
        "home.html",
        "routes.json",
        "woo-bridge.json",
        "cart-related.json",
    ] + [f"products/{p['id']}.html" for p in PRODUCTS]
    dest_base = env()["PM_LOJA_URL"].rstrip("/") + "/wp-content/uploads/pm-home"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            path = PM / rel
            text = path.read_text(encoding="utf-8")
            text = text.replace(
                "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home",
                dest_base,
            )
            z.writestr(rel, text.encode("utf-8"))
            print("zip+", rel)
    st, body = call(
        "POST",
        "/wp-json/pm-home/v1/bundle",
        raw=buf.getvalue(),
        content_type="application/zip",
        timeout=600,
    )
    print("bundle", st, body if isinstance(body, dict) else str(body)[:300])
    if st != 200:
        raise SystemExit("publish failed")


def verify():
    base = env()["PM_LOJA_URL"].rstrip("/")
    html = urllib.request.urlopen(base + "/wp-content/uploads/pm-home/home.html?v=ensaio1", timeout=60).read().decode(
        "utf-8", "replace"
    )
    print(
        "live home ensaio",
        "ensaio-testes" in html,
        "laser A",
        "pm-teste-esquenta-laser" in html,
        "1,99",
        "produto-1-real" in html,
    )
    bridge = json.loads(
        urllib.request.urlopen(base + "/wp-content/uploads/pm-home/woo-bridge.json?v=ensaio1", timeout=60).read().decode()
    )
    for p in PRODUCTS:
        print("bridge", p["id"], bridge.get(p["id"], {}).get("productId"))


def main():
    ensure_woo_publish()
    patch_bridge_and_related()
    make_product_html()
    inject_home_strip()
    open_maintenance_off()
    publish()
    verify()
    print("HOME_ENSAIO_OK")


if __name__ == "__main__":
    main()
