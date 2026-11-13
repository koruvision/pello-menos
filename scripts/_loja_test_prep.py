# -*- coding: utf-8 -*-
"""Prep/restore loja for production test battery."""
from __future__ import annotations

import argparse
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
SKUS = json.loads((ROOT / "scripts" / "_loja_esquenta_test_skus.json").read_text(encoding="utf-8"))
RECAPTCHA_OFF_NAME = "Checkout sem reCAPTCHA"
RECAPTCHA_OFF_CODE = r"""
// Hard-disable CF7 reCAPTCHA / spam during test battery
add_filter('wpcf7_recaptcha_available', '__return_false', 999);
add_filter('wpcf7_recaptcha_verify_response', '__return_true', 999);
add_filter('wpcf7_spam', '__return_false', 999);
add_filter('wpcf7_skip_spam_check', '__return_true', 999);
remove_action('wpcf7_init', 'wpcf7_recaptcha_register_service', 10);
add_action('wpcf7_init', function () {
    if (function_exists('wpcf7_recaptcha_register_service')) {
        remove_action('wpcf7_init', 'wpcf7_recaptcha_register_service', 10);
    }
}, 1);
add_filter('wpcf7_form_hidden_fields', function ($fields) {
    unset($fields['_wpcf7_recaptcha_response']);
    return $fields;
}, 999);
add_filter('wpcf7_posted_data', function ($posted) {
    if (is_array($posted)) {
        $posted['g-recaptcha-response'] = 'pm-test-bypass';
        $posted['_wpcf7_recaptcha_response'] = 'pm-test-bypass';
    }
    return $posted;
}, 999);
"""


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def call(method, path, payload=None):
    cfg = env()
    base = cfg["PM_LOJA_URL"].rstrip("/")
    token = base64.b64encode(
        f"{cfg['PM_LOJA_USER']}:{cfg['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
        "User-Agent": "pm-loja-prep/1.0",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body.strip()[:1] in "{[" else body
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8", "replace")
        try:
            return err.code, json.loads(raw)
        except json.JSONDecodeError:
            return err.code, raw[:500]


def list_snippets():
    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    if st != 200 or not isinstance(rows, list):
        raise SystemExit(f"snippets list {st} {rows}")
    return rows


def find_snippet(rows, name):
    for row in rows:
        if row.get("name") == name:
            return row
    return None


def set_snippet_active(sid, active, name=None, code=None, scope="global"):
    st, sn = call("GET", f"/wp-json/code-snippets/v1/snippets/{sid}")
    if st != 200 or not isinstance(sn, dict):
        raise SystemExit(f"get snippet {sid} {st}")
    payload = {
        "name": name or sn.get("name"),
        "code": code if code is not None else sn.get("code"),
        "scope": scope or sn.get("scope") or "global",
        "active": bool(active),
    }
    st, saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{sid}", payload)
    print("snippet", sid, payload["name"], "active", saved.get("active") if isinstance(saved, dict) else saved, st)
    return saved


def ensure_skus_publish():
    for sku, pid in SKUS.items():
        st, body = call(
            "PUT",
            f"/wp-json/wc/v3/products/{pid}",
            {"status": "publish", "catalog_visibility": "hidden", "regular_price": "5.00"},
        )
        print("sku", sku, pid, st, body.get("status") if isinstance(body, dict) else body)


def set_plugin(slug, status):
    st, body = call("PUT", f"/wp-json/wp/v2/plugins/{slug}", {"status": status})
    print("plugin", slug, status, st, body.get("status") if isinstance(body, dict) else body)


def open_loja():
    rows = list_snippets()
    for row in rows:
        print("id", row.get("id"), "active", row.get("active"), row.get("name"))

    maint = find_snippet(rows, "pm-ecommerce-maintenance")
    if maint:
        set_snippet_active(maint["id"], False)

    sync = find_snippet(rows, "pm-accesstage-order-total-sync")
    bn = find_snippet(rows, "pm-black-nov-pricing")
    print("sync", sync and {"id": sync.get("id"), "active": sync.get("active")})
    print("blacknov", bn and {"id": bn.get("id"), "active": bn.get("active")})
    if not sync or not sync.get("active"):
        raise SystemExit("accesstage sync missing/inactive")
    if not bn or not bn.get("active"):
        raise SystemExit("black-nov missing/inactive")

    rec = find_snippet(rows, RECAPTCHA_OFF_NAME)
    if rec:
        set_snippet_active(rec["id"], True, name=RECAPTCHA_OFF_NAME, code=RECAPTCHA_OFF_CODE)
    else:
        st, saved = call(
            "POST",
            "/wp-json/code-snippets/v1/snippets",
            {
                "name": RECAPTCHA_OFF_NAME,
                "code": RECAPTCHA_OFF_CODE,
                "scope": "global",
                "active": True,
            },
        )
        print("create recaptcha-off", st, saved.get("id") if isinstance(saved, dict) else saved)

    # Plugin oficial CF7 reCAPTCHA bloqueava submit mesmo com snippet fraco
    set_plugin("wpcf7-recaptcha/wpcf7-recaptcha", "inactive")

    ensure_skus_publish()
    print("LOJA_OPEN_OK")


def restore_loja():
    rows = list_snippets()
    # Loja em produção: NÃO religar manutenção após ensaio.
    # (Antes o restore reativava #6 e a loja ficava 503 — E-commerce em Manutenção.)
    maint = find_snippet(rows, "pm-ecommerce-maintenance")
    if maint:
        set_snippet_active(maint["id"], False)
    rec = find_snippet(rows, RECAPTCHA_OFF_NAME)
    if rec:
        set_snippet_active(rec["id"], False)
    # Mantém pm-accesstage-normalize-test se for só o patch leve (label→slug + parcelas).
    # Desativa se ainda tiver endpoint de ensaio / cartão embutido.
    norm = find_snippet(rows, "pm-accesstage-normalize-test")
    if norm:
        st, full = call("GET", f"/wp-json/code-snippets/v1/snippets/{norm['id']}")
        code = (full.get("code") if isinstance(full, dict) else "") or ""
        if "test-order" in code or "test-charge" in code or "2238" in code:
            set_snippet_active(norm["id"], False)
            print("normalize_test deactivated (ensaio)")
        else:
            print("normalize_test kept (prod patch)")
    set_plugin("wpcf7-recaptcha/wpcf7-recaptcha", "active")
    # cupons de ensaio → draft
    for cid in (49539, 49540, 49523):
        st, body = call("PUT", f"/wp-json/wc/v3/coupons/{cid}", {"status": "draft"})
        print("coupon_draft", cid, st, body.get("status") if isinstance(body, dict) else body)
    print("LOJA_RESTORE_OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("open", "restore"), required=True)
    args = ap.parse_args()
    if args.mode == "open":
        open_loja()
    else:
        restore_loja()


if __name__ == "__main__":
    main()
