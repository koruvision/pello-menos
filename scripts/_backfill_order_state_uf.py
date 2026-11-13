# -*- coding: utf-8 -*-
"""Backfill billing/shipping state → UF 2 letras (ex. #49500 Rio de Janeiro → RJ)."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/loja.env")
OUT = Path("scripts/_backfill_order_state_uf_result.json")
ORDER_IDS = [49500]

UF_MAP = {
    "acre": "AC",
    "alagoas": "AL",
    "amapa": "AP",
    "amapá": "AP",
    "amazonas": "AM",
    "bahia": "BA",
    "ceara": "CE",
    "ceará": "CE",
    "distrito federal": "DF",
    "espirito santo": "ES",
    "espírito santo": "ES",
    "goias": "GO",
    "goiás": "GO",
    "maranhao": "MA",
    "maranhão": "MA",
    "mato grosso": "MT",
    "mato grosso do sul": "MS",
    "minas gerais": "MG",
    "para": "PA",
    "pará": "PA",
    "paraiba": "PB",
    "paraíba": "PB",
    "parana": "PR",
    "paraná": "PR",
    "pernambuco": "PE",
    "piaui": "PI",
    "piauí": "PI",
    "rio de janeiro": "RJ",
    "rio grande do norte": "RN",
    "rio grande do sul": "RS",
    "rondonia": "RO",
    "rondônia": "RO",
    "roraima": "RR",
    "santa catarina": "SC",
    "sao paulo": "SP",
    "são paulo": "SP",
    "sergipe": "SE",
    "tocantins": "TO",
}


def load_env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def call(method, path, payload=None):
    e = load_env()
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    base = e["PM_LOJA_URL"].rstrip("/")
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        base + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-backfill-uf",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode()
        return json.loads(body) if body else {}


def to_uf(raw: str) -> str | None:
    s = (raw or "").strip()
    if not s:
        return None
    if len(s) == 2:
        return s.upper()
    return UF_MAP.get(s.lower())


def fix_order(oid: int) -> dict:
    before = call("GET", f"/wp-json/wc/v3/orders/{oid}")
    billing = dict(before.get("billing") or {})
    shipping = dict(before.get("shipping") or {})
    b_state = billing.get("state") or ""
    s_state = shipping.get("state") or ""
    nb = to_uf(b_state)
    ns = to_uf(s_state)
    patch = {}
    if nb and nb != b_state:
        billing["state"] = nb
        patch["billing"] = billing
    if ns and ns != s_state:
        shipping["state"] = ns
        patch["shipping"] = shipping
    # Nome = e-mail: limpar first_name (não inventar)
    fn = (billing.get("first_name") or "").strip()
    if "@" in fn:
        billing["first_name"] = ""
        patch["billing"] = billing
    if not patch:
        return {
            "id": oid,
            "changed": False,
            "billing_state": b_state,
            "shipping_state": s_state,
            "first_name": fn,
        }
    after = call("PUT", f"/wp-json/wc/v3/orders/{oid}", patch)
    return {
        "id": oid,
        "changed": True,
        "before": {"billing_state": b_state, "shipping_state": s_state, "first_name": fn},
        "after": {
            "billing_state": (after.get("billing") or {}).get("state"),
            "shipping_state": (after.get("shipping") or {}).get("state"),
            "first_name": (after.get("billing") or {}).get("first_name"),
        },
    }


def main():
    rows = [fix_order(i) for i in ORDER_IDS]
    # Also scan recent orders with long state (last 40)
    recent = call("GET", "/wp-json/wc/v3/orders?per_page=40&orderby=date&order=desc")
    extra = []
    for o in recent or []:
        oid = int(o["id"])
        if oid in ORDER_IDS:
            continue
        st = ((o.get("billing") or {}).get("state") or "").strip()
        fn = ((o.get("billing") or {}).get("first_name") or "").strip()
        if len(st) > 2 or "@" in fn:
            extra.append(fix_order(oid))
    summary = {"orders": rows, "extra": extra, "ok": all(r.get("after", {}).get("billing_state") == "RJ" or not r.get("changed") or len(str(r.get("after", {}).get("billing_state") or "")) == 2 for r in rows)}
    # verify 49500
    v = call("GET", "/wp-json/wc/v3/orders/49500")
    summary["verify_49500"] = {
        "state": (v.get("billing") or {}).get("state"),
        "first_name": (v.get("billing") or {}).get("first_name"),
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
