# -*- coding: utf-8 -*-
"""Cria/atualiza cupom seguro na loja: ao aplicar, buço feminino linha fica a R$ 1,00.

O desconto real e feito pelo hook no snippet (pm-home), gated pela meta
_pm_linha_1real do cupom. So vale para buco-linha.
"""
from __future__ import annotations

import base64
import json
import secrets
import string
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
OUT = ROOT / "projeto-migracao" / ".secrets" / "linha-1real-coupon.json"
# So buço feminino linha (nao queixo/faixa).
LINHA_SKUS = ("buco-linha",)
# ERP interno aceita no maximo 20 chars em coupon_lines[].code.
KEEP_CODE = "PM1LTEST01"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return {
        "url": e["PM_LOJA_URL"].rstrip("/"),
        "user": e["PM_LOJA_USER"],
        "password": e["PM_LOJA_APP_PASSWORD"],
    }


def call(c, method, path, payload=None):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": "Basic " + tok,
        "Accept": "application/json",
        "User-Agent": "pm-linha-1real-coupon",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(c["url"] + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body[:500]}
        return err.code, parsed


def gen_code(n: int = 12) -> str:
    """PM1L + ate 12 = 16 chars (limite ERP = 20)."""
    n = max(1, min(int(n), 12))
    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.replace("0", "").replace("O", "").replace("1", "").replace("I", "")
    return "PM1L" + "".join(secrets.choice(alphabet) for _ in range(n))


def find_products(c) -> list[dict]:
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    found = []
    for catalog_id in LINHA_SKUS:
        info = bridge.get(catalog_id) or {}
        pid = int(info.get("productId") or 0)
        if not pid:
            raise SystemExit(f"bridge sem productId: {catalog_id}")
        st, p = call(c, "GET", f"/wp-json/wc/v3/products/{pid}")
        if st != 200 or not isinstance(p, dict):
            raise SystemExit(f"produto Woo {pid} ({catalog_id}): {st} {p}")
        price = float(p.get("price") or p.get("regular_price") or 0)
        found.append(
            {
                "catalog_id": catalog_id,
                "id": int(p["id"]),
                "slug": p.get("slug"),
                "name": p.get("name"),
                "price": price,
                "regular_price": p.get("regular_price"),
            }
        )
        print("product", catalog_id, p["id"], "price", price, "slug", p.get("slug"))
    return found


def main() -> None:
    c = cfg()
    assert "loja.pellomenos.com.br" in c["url"]
    products = find_products(c)
    product_ids = [p["id"] for p in products]

    # Preferir cupom existente com o codigo KEEP_CODE (ou meta _pm_linha_1real).
    existing_id = None
    existing_code = None
    st, rows = call(
        c,
        "GET",
        "/wp-json/wc/v3/coupons?" + urllib.parse.urlencode({"search": "PM1L", "per_page": 50}),
    )
    keep = KEEP_CODE.upper()
    assert len(keep) <= 20, f"KEEP_CODE > 20: {keep}"
    for old in rows if isinstance(rows, list) else []:
        meta = {m.get("key"): m.get("value") for m in (old.get("meta_data") or [])}
        code_u = str(old.get("code") or "").upper()
        code_len = len(code_u)
        is_linha = meta.get("_pm_linha_1real") == "1" or code_u.startswith("PM1L")
        if code_u == keep:
            existing_id = int(old["id"])
            existing_code = old.get("code")
            continue
        # Remove longo legado ou outros cupons linha 1real.
        if is_linha and (code_len > 20 or code_u != keep):
            call(c, "DELETE", f"/wp-json/wc/v3/coupons/{old['id']}?force=true")
            print("removed old", old.get("id"), old.get("code"), "len", code_len)

    payload = {
        "discount_type": "fixed_product",
        "amount": "0.01",
        "individual_use": True,
        "exclude_sale_items": False,
        "product_ids": product_ids,
        "description": "TESTE interno PM: so buco-linha a R$1 via hook. NAO divulgar. code<=20 (ERP).",
        "meta_data": [
            {"key": "_pm_linha_1real", "value": "1"},
            {"key": "_pm_linha_1real_target", "value": "1.00"},
        ],
    }

    if existing_id:
        st, coupon = call(c, "PUT", f"/wp-json/wc/v3/coupons/{existing_id}", payload)
        code = existing_code or KEEP_CODE
        print("coupon update", st, existing_id)
    else:
        code = KEEP_CODE if KEEP_CODE else gen_code(12)
        if len(code) > 20:
            raise SystemExit(f"code > 20: {code}")
        payload["code"] = code
        st, coupon = call(c, "POST", "/wp-json/wc/v3/coupons", payload)
        print("coupon create", st, coupon.get("id") if isinstance(coupon, dict) else coupon)

    if st not in (200, 201) or not isinstance(coupon, dict):
        raise SystemExit(coupon)

    out = {
        "code": code,
        "coupon_id": coupon.get("id"),
        "products": products,
        "target": 1.0,
        "how": "Aplicar no carrinho (Store API). Hook forca preco R$1 so em buco-linha.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("CODE", code)
    print("products", product_ids)
    print("wrote", OUT.relative_to(ROOT).as_posix())
    print("COUPON_OK")


if __name__ == "__main__":
    main()
