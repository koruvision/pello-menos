# -*- coding: utf-8 -*-
"""Cria/renomeia os 3 Body Splash no Woo oficialteste e atualiza woo-bridge.json.

- Renomeia o SKU 48219 para Body Splash - Livre (slug body-splash-livre)
- Cria Marcante e Autêntica (simple, R$ 1,00 no oficialteste)
- Atualiza src/lib/woo-bridge.json e a cópia em wordpress-loja/pm-home/
"""
from __future__ import annotations

import base64
import json
import shutil
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
BRIDGE_WP = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"

EXISTING_ID = 48219
SPLASHES = [
    {
        "id": "body-splash-livre",
        "name": "Body Splash - Livre",
        "slug": "body-splash-livre",
        "reuse_id": EXISTING_ID,
    },
    {
        "id": "body-splash-marcante",
        "name": "Body Splash - Marcante",
        "slug": "body-splash-marcante",
        "reuse_id": None,
    },
    {
        "id": "body-splash-autentica",
        "name": "Body Splash - Autêntica",
        "slug": "body-splash-autentica",
        "reuse_id": None,
    },
]
LONG = (
    "Body Splash oficial Pello Menos para o cuidado em casa após a depilação. "
    "Produto para retirada na loja — não há entrega."
)


def read_env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return {
        "url": values["PM_OFICIALTESTE_URL"].rstrip("/"),
        "user": values["PM_OFICIALTESTE_USER"],
        "password": values["PM_OFICIALTESTE_APP_PASSWORD"],
    }


def api(method: str, url: str, auth: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-body-splash/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8", "replace")
            return resp.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body[:800]
        return error.code, parsed


def find_by_slug(base: str, auth: str, slug: str):
    st, rows = api(
        "GET",
        f"{base}/wp-json/wc/v3/products?slug={slug}&per_page=5",
        auth,
    )
    if st != 200 or not isinstance(rows, list):
        return None
    return rows[0] if rows else None


def ensure_product(base: str, auth: str, spec: dict) -> int:
    if spec["reuse_id"]:
        pid = spec["reuse_id"]
        st, current = api("GET", f"{base}/wp-json/wc/v3/products/{pid}", auth)
        if st != 200:
            raise SystemExit(f"GET {pid} falhou: {st} {current}")
        payload = {
            "name": spec["name"],
            "slug": spec["slug"],
            "type": "simple",
            "status": "publish",
            "catalog_visibility": "visible",
            "regular_price": "1.00",
            "sale_price": "",
            "manage_stock": False,
            "stock_status": "instock",
            "description": LONG,
            "short_description": spec["name"],
        }
        st, saved = api("PUT", f"{base}/wp-json/wc/v3/products/{pid}", auth, payload)
        if st not in (200, 201):
            raise SystemExit(f"PUT {pid} falhou: {st} {saved}")
        print("renamed", pid, saved.get("slug"), saved.get("name"))
        return int(saved["id"])

    existing = find_by_slug(base, auth, spec["slug"])
    if existing:
        pid = int(existing["id"])
        st, saved = api(
            "PUT",
            f"{base}/wp-json/wc/v3/products/{pid}",
            auth,
            {
                "name": spec["name"],
                "status": "publish",
                "regular_price": "1.00",
                "description": LONG,
                "short_description": spec["name"],
            },
        )
        if st not in (200, 201):
            raise SystemExit(f"PUT existing {pid} falhou: {st} {saved}")
        print("updated", pid, saved.get("slug"), saved.get("name"))
        return pid

    st, saved = api(
        "POST",
        f"{base}/wp-json/wc/v3/products",
        auth,
        {
            "name": spec["name"],
            "slug": spec["slug"],
            "type": "simple",
            "status": "publish",
            "catalog_visibility": "visible",
            "regular_price": "1.00",
            "manage_stock": False,
            "stock_status": "instock",
            "description": LONG,
            "short_description": spec["name"],
        },
    )
    if st not in (200, 201) or not isinstance(saved, dict):
        raise SystemExit(f"POST {spec['slug']} falhou: {st} {saved}")
    print("created", saved.get("id"), saved.get("slug"), saved.get("name"))
    return int(saved["id"])


def bridge_row(slug: str, product_id: int, name: str) -> dict:
    return {
        "slug": slug,
        "productId": product_id,
        "longText": f"{name} para o cuidado em casa após a depilação. Retirada na loja — não há entrega.",
        "rj": {"regularCents": 100, "saleCents": 100},
        "spdf": {"regularCents": 100, "saleCents": 100},
        "units": {},
    }


def main():
    cfg = read_env()
    auth = base64.b64encode(f"{cfg['user']}:{cfg['password']}".encode()).decode()
    base = cfg["url"]
    print("destino:", base)

    ids = {}
    for spec in SPLASHES:
        ids[spec["id"]] = ensure_product(base, auth, spec)

    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    bridge.pop("body-splash", None)
    for spec in SPLASHES:
        bridge[spec["id"]] = bridge_row(spec["slug"], ids[spec["id"]], spec["name"])
    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(BRIDGE, BRIDGE_WP)
    print("bridge ok")
    for key, pid in ids.items():
        print(f"  {key} -> {pid}")

    # Atualiza cart.js wooId do Livre (continua 48219) e fallbacks do checkout-shell
    cart = ROOT / "wordpress-loja" / "pm-home" / "cart.js"
    text = cart.read_text(encoding="utf-8")
    text = text.replace(f'wooId: "{EXISTING_ID}"', f'wooId: "{ids["body-splash-livre"]}"')
    cart.write_text(text, encoding="utf-8")

    for shell_name in ("checkout-shell.js", "checkout-shell-c21.js", "checkout-shell-c20.js", "checkout-shell-c19.js"):
        path = ROOT / "wordpress-loja" / "pm-home" / shell_name
        if not path.exists():
            continue
        js = path.read_text(encoding="utf-8")
        img = 'base + "media/images/products/body-splash.png"'
        for key, pid in ids.items():
            needle = f'"{pid}": {img}'
            if needle not in js:
                # inject after body-splash key if present
                marker = '"body-splash": ' + img
                if marker in js and f'"{key}":' not in js:
                    js = js.replace(
                        marker,
                        marker + f',\n    "{key}": {img},\n    "{pid}": {img}',
                        1,
                    )
        path.write_text(js, encoding="utf-8")
        print("shell patched", shell_name)

    report = ROOT / "projeto-migracao" / ".secrets" / "body-splash-trio.json"
    report.write_text(json.dumps(ids, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("report", report)


if __name__ == "__main__":
    main()
