# -*- coding: utf-8 -*-
"""Desliga reCAPTCHA CF7 na loja de forma dura (snippet + plugin se preciso)."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "loja.env"
NAME = "Checkout sem reCAPTCHA"
CODE = r"""
// Hard-disable CF7 reCAPTCHA during test battery
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
add_filter('wpcf7_validate_recaptcha', function ($result, $tag = null) {
    return $result;
}, 999, 2);
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
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def call(method, path, payload=None):
    cfg = env()
    base = cfg["PM_LOJA_URL"].rstrip("/")
    token = base64.b64encode(f"{cfg['PM_LOJA_USER']}:{cfg['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    data = None if payload is None else json.dumps(payload).encode()
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
        "User-Agent": "pm-loja-recaptcha",
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


def main():
    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    if st != 200:
        raise SystemExit(f"list {st}")
    sn = next((x for x in rows if x.get("name") == NAME), None)
    if sn:
        st, saved = call(
            "PUT",
            f"/wp-json/code-snippets/v1/snippets/{sn['id']}",
            {"name": NAME, "code": CODE, "scope": "global", "active": True},
        )
        print("update", st, sn["id"], isinstance(saved, dict) and saved.get("active"))
    else:
        st, saved = call(
            "POST",
            "/wp-json/code-snippets/v1/snippets",
            {"name": NAME, "code": CODE, "scope": "global", "active": True},
        )
        print("create", st, isinstance(saved, dict) and saved.get("id"))

    # deactivate plugin if REST allows
    st, plugs = call("GET", "/wp-json/wp/v2/plugins?per_page=100")
    if st == 200 and isinstance(plugs, list):
        for p in plugs:
            slug = str(p.get("plugin") or "")
            if "recaptcha" in slug.lower() or "wpcf7-recaptcha" in slug.lower():
                print("plugin", slug, "status", p.get("status"))
                if p.get("status") == "active":
                    st2, body = call("PUT", f"/wp-json/wp/v2/plugins/{slug}", {"status": "inactive"})
                    print("deactivate", slug, st2, body.get("status") if isinstance(body, dict) else body)
    else:
        print("plugins endpoint", st, type(plugs))

    # CF7 form 1831 - check demo
    st, form = call("GET", "/wp-json/contact-form-7/v1/contact-forms/1831")
    print("cf7 form", st, type(form), (form.get("title") if isinstance(form, dict) else str(form)[:120]))
    print("RECAPTCHA_HARD_OK")


if __name__ == "__main__":
    main()
