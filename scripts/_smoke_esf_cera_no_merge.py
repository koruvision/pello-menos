# -*- coding: utf-8 -*-
"""Smoke: esfoliação + cera da mesma área NÃO fundem quando pm_catalog_id é enviado."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"

PAIRS = [
    ("esfoliacao-axilas", "axila-cera"),
    ("esfoliacao-coxa", "coxa-cera"),
    ("esfoliacao-nadegas", "nadegas-cera"),
    ("esfoliacao-faixa", "faixa-cera"),
    ("esfoliacao-abdomen", "abdomen-cera"),
    ("esfoliacao-virilha", "virilha-cera"),
]
UNITS = ("ipa", "bot")
OUT = ROOT / "scripts" / "_smoke_esf_cera_no_merge_result.json"


def base_url() -> str:
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e["PM_LOJA_URL"].rstrip("/")


def catalog_id(line: dict) -> str:
    for d in line.get("item_data") or []:
        if str(d.get("key") or "").lower() == "pm_catalog_id":
            return str(d.get("value") or d.get("display") or "").strip()
    return ""


def session(base: str):
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    state = {"nonce": None, "token": None}

    def call(method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-esf-cera-smoke",
        }
        if state["nonce"]:
            h["Nonce"] = state["nonce"]
        if state["token"]:
            h["Cart-Token"] = state["token"]
        req = urllib.request.Request(base + path, data=data, method=method, headers=h)
        try:
            with opener.open(req, timeout=90) as resp:
                body = resp.read().decode("utf-8", "replace")
                state["nonce"] = resp.headers.get("Nonce") or state["nonce"]
                state["token"] = resp.headers.get("Cart-Token") or state["token"]
                return resp.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body[:400]}
            state["nonce"] = err.headers.get("Nonce") or state["nonce"]
            state["token"] = err.headers.get("Cart-Token") or state["token"]
            return err.code, parsed

    return call


def clear(call):
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    for it in list(cart.get("items") or []):
        call("POST", "/wp-json/wc/store/v1/cart/remove-item", {"key": it["key"]})
    for c in list(cart.get("coupons") or []):
        code = c.get("code") if isinstance(c, dict) else c
        if code:
            call("POST", "/wp-json/wc/store/v1/cart/remove-coupon", {"code": code})


def resolve_cera_key(bridge: dict, esf: str, preferred: str) -> str:
    if preferred in bridge:
        return preferred
    slug = str((bridge.get(esf) or {}).get("slug") or "")
    if slug in bridge:
        return slug
    pid = (bridge.get(esf) or {}).get("productId")
    for k, row in bridge.items():
        if row.get("productId") == pid and not str(k).startswith("esfoliacao-"):
            return k
    raise KeyError(f"cera for {esf}")


def main():
    base = base_url()
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    call = session(base)
    results = []
    failed = 0

    for unit in UNITS:
        for esf, cera_pref in PAIRS:
            cera = resolve_cera_key(bridge, esf, cera_pref)
            esf_var = bridge[esf]["units"][unit]["variationId"]
            cera_var = bridge[cera]["units"][unit]["variationId"]
            case = {"unit": unit, "esf": esf, "cera": cera, "esf_var": esf_var, "cera_var": cera_var}
            if int(esf_var) != int(cera_var):
                case["skip"] = "different_variation"
                results.append(case)
                continue

            clear(call)
            st1, cart = call(
                "POST",
                "/wp-json/wc/store/v1/cart/add-item",
                {"id": int(esf_var), "quantity": 1, "pm_catalog_id": esf},
            )
            st2, cart = call(
                "POST",
                "/wp-json/wc/store/v1/cart/add-item",
                {"id": int(cera_var), "quantity": 1, "pm_catalog_id": cera},
            )
            items = cart.get("items") or []
            cats = sorted(catalog_id(it) for it in items)
            ok = (
                st1 < 400
                and st2 < 400
                and len(items) == 2
                and cats == sorted([esf, cera])
                and all((it.get("quantity") or 0) == 1 for it in items)
            )
            case.update({"ok": ok, "n": len(items), "cats": cats, "status": [st1, st2]})
            if not ok:
                failed += 1
            results.append(case)
            print(("OK" if ok else "FAIL"), unit, esf, "+", cera, "n=", len(items), cats)

            # qty update on esf line must keep cera
            esf_line = next((it for it in items if catalog_id(it) == esf), None)
            if esf_line and ok:
                st3, cart2 = call(
                    "POST",
                    "/wp-json/wc/store/v1/cart/update-item",
                    {"key": esf_line["key"], "quantity": 2, "pm_catalog_id": esf},
                )
                items2 = cart2.get("items") or []
                cats2 = sorted(catalog_id(it) for it in items2)
                qty_ok = (
                    st3 < 400
                    and len(items2) == 2
                    and cats2 == sorted([esf, cera])
                    and any(catalog_id(it) == esf and (it.get("quantity") or 0) == 2 for it in items2)
                    and any(catalog_id(it) == cera and (it.get("quantity") or 0) == 1 for it in items2)
                )
                results.append({"unit": unit, "case": "qty_update", "esf": esf, "ok": qty_ok, "n": len(items2)})
                print(("OK" if qty_ok else "FAIL"), "qty_update", unit, esf)
                if not qty_ok:
                    failed += 1

    # Negativo: sem catalog id → merge (documenta bug antigo)
    clear(call)
    esf, cera = "esfoliacao-coxa", "coxa-cera"
    vid = bridge[esf]["units"]["ipa"]["variationId"]
    call("POST", "/wp-json/wc/store/v1/cart/add-item", {"id": int(vid), "quantity": 1})
    st, cart = call("POST", "/wp-json/wc/store/v1/cart/add-item", {"id": int(vid), "quantity": 1})
    items = cart.get("items") or []
    merged = len(items) == 1 and (items[0].get("quantity") or 0) == 2
    results.append({"case": "negative_no_catalog", "ok": merged, "n": len(items), "qty": (items[0].get("quantity") if items else None)})
    print(("OK" if merged else "FAIL"), "negative_no_catalog merge", "n=", len(items))
    if not merged:
        failed += 1

    OUT.write_text(json.dumps({"failed": failed, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT, "failed", failed)
    if failed:
        raise SystemExit(1)
    print("SMOKE_ESF_CERA_NO_MERGE_OK")


if __name__ == "__main__":
    main()
