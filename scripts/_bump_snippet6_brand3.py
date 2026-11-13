# -*- coding: utf-8 -*-
"""Update snippet 6 (pm-home) to c12/brand3; keep snippet 8 inactive."""
import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/oficialteste.env")
BASE = "https://pellomenosoficialteste.companygenesis.com.br"
LOCAL = Path("scripts/pm_home_snippet.php")


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def call(method, path, payload=None):
    cfg = env()
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        cfg["PM_OFICIALTESTE_URL"].rstrip("/") + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode() or "{}"
            return r.status, json.loads(body) if body.strip().startswith(("{", "[")) else body
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw[:800]
        return e.code, parsed


def put_code(sid, name, scope, code, active=True):
    return call(
        "PUT",
        f"/wp-json/code-snippets/v1/snippets/{sid}",
        {"name": name, "code": code, "scope": scope or "global", "active": active},
    )


def main():
    # Deactivate 8 again
    st8, sn8 = call("GET", "/wp-json/code-snippets/v1/snippets/8")
    if isinstance(sn8, dict):
        st_off, saved8 = put_code(
            8,
            sn8.get("name") or "pm-home checkout shell c10",
            sn8.get("scope"),
            sn8.get("code") or "",
            active=False,
        )
        print("deactivate 8", st_off, saved8.get("active") if isinstance(saved8, dict) else saved8)

    st6, sn6 = call("GET", "/wp-json/code-snippets/v1/snippets/6")
    code = (sn6.get("code") if isinstance(sn6, dict) else "") or ""
    print("snippet6 len", len(code), "c11", "c11" in code, "brand1", "brand1" in code, "brand2", "brand2" in code)

    m = re.search(r"define\('PM_HOME_ROUTES',\s*'([^']*)'\)", code)
    routes = m.group(1) if m else "home,masculino,produto,carrinho,conta,shell,loja"
    local = LOCAL.read_text(encoding="utf-8")
    full = f"define('PM_HOME_ROUTES', '{routes}');\n\n" + local
    st_full, saved = put_code(6, sn6.get("name") or "pm-home (front do projeto)", sn6.get("scope"), full, True)
    print("full PUT 6", st_full)

    if st_full not in (200, 201) or not isinstance(saved, dict):
        next_code = code
        for a, b in [
            ("checkout-shell-c11.js?v=c11", "checkout-shell-c12.js?v=c12"),
            ("checkout-shell-c10.js?v=c10", "checkout-shell-c12.js?v=c12"),
            ("checkout-brand.css?v=brand2", "checkout-brand.css?v=brand3"),
            ("checkout-brand.css?v=brand1", "checkout-brand.css?v=brand3"),
        ]:
            next_code = next_code.replace(a, b)
        # Also replace enqueue function body patterns if present without query bump
        next_code = next_code.replace("checkout-shell-c11.js", "checkout-shell-c12.js")
        next_code = next_code.replace("?v=c11", "?v=c12")
        next_code = next_code.replace("?v=brand1", "?v=brand3")
        next_code = next_code.replace("?v=brand2", "?v=brand3")

        old_hide = (
            "header.header_wrap,footer.footer_dark,.section.bg_default"
            "{display:none!important}.main_content{margin-top:176px}"
            "#pm-shell-header,#pm-shell-footer{position:relative;z-index:80}"
        )
        new_hide = (
            "header.header_wrap,footer.footer_dark,.section.bg_default,"
            ".breadcrumb_section,.page-title-light,.page-title{display:none!important}"
            "html,body,.main_content,.section,.container,#content,.content-area,"
            ".bg_default,.bg_light{background:#fff!important;background-image:none!important}"
            ".main_content{margin-top:176px}"
            "#pm-shell-header,#pm-shell-footer{position:relative;z-index:80}"
        )
        if old_hide in next_code:
            next_code = next_code.replace(old_hide, new_hide)
            print("replaced hide css")
        else:
            print("old hide not found; sample hide region:")
            idx = next_code.find("header.header_wrap")
            print(repr(next_code[idx : idx + 280]) if idx >= 0 else "no header.header_wrap")

        st2, saved = put_code(
            6,
            sn6.get("name") or "pm-home (front do projeto)",
            sn6.get("scope"),
            next_code,
            True,
        )
        print("surgical PUT 6", st2)

    if not isinstance(saved, dict):
        raise SystemExit(f"failed: {saved}")
    scode = saved.get("code") or ""
    print(
        "saved",
        "c12",
        "checkout-shell-c12" in scode,
        "brand3",
        "brand3" in scode,
        "active",
        saved.get("active"),
    )

    html = urllib.request.urlopen(BASE + "/finalizar-pagamento/?pm=brand3b", timeout=60).read().decode(
        "utf-8", "replace"
    )
    print("page scripts", re.findall(r"checkout-shell[^\"']*", html)[:6])
    print("page brand", re.findall(r"checkout-brand[^\"']*", html)[:6])


if __name__ == "__main__":
    main()
