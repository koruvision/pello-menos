# -*- coding: utf-8 -*-
"""Point oficialteste snippet to checkout-shell-c12 + brand3."""
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


def main():
    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets")
    print("list", st)
    sid = None
    if isinstance(rows, list):
        for r in rows:
            print(r.get("id"), r.get("name"), "active", r.get("active"))
            code = r.get("code") or ""
            if "checkout-shell" in code or "pm_home_enqueue_shell" in code:
                sid = r["id"]
    if sid is None and isinstance(rows, list):
        for r in rows:
            if (r.get("name") or "") == "pm-home":
                sid = r["id"]
                break
    print("using", sid)
    st6, sn = call("GET", f"/wp-json/code-snippets/v1/snippets/{sid}")
    code = (sn.get("code") if isinstance(sn, dict) else "") or ""
    print("get", st6, "len", len(code), "c11", "c11" in code, "brand2", "brand2" in code)

    m = re.search(r"define\('PM_HOME_ROUTES',\s*'([^']*)'\)", code)
    routes = m.group(1) if m else "home,masculino,produto,carrinho,conta,shell,loja"
    local = LOCAL.read_text(encoding="utf-8")
    new_code = f"define('PM_HOME_ROUTES', '{routes}');\n\n" + local
    payload = {
        "name": sn.get("name") or "pm-home",
        "code": new_code,
        "scope": sn.get("scope") or "global",
        "active": True,
    }
    st_put, saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{sid}", payload)
    print("full PUT", st_put)
    if st_put not in (200, 201) or not isinstance(saved, dict):
        next_code = code
        for a, b in [
            ("checkout-shell-c11.js?v=c11", "checkout-shell-c12.js?v=c12"),
            ("checkout-shell-c10.js?v=c10", "checkout-shell-c12.js?v=c12"),
            ("checkout-brand.css?v=brand2", "checkout-brand.css?v=brand3"),
            ("checkout-brand.css?v=brand1", "checkout-brand.css?v=brand3"),
        ]:
            next_code = next_code.replace(a, b)
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
        st2, saved = call(
            "PUT",
            f"/wp-json/code-snippets/v1/snippets/{sid}",
            {
                "name": sn.get("name") or "pm-home",
                "code": next_code,
                "scope": sn.get("scope") or "global",
                "active": True,
            },
        )
        print("surgical PUT", st2)

    if not isinstance(saved, dict):
        raise SystemExit(f"snippet update failed: {saved}")
    scode = saved.get("code") or ""
    print(
        "saved active",
        saved.get("active"),
        "c12",
        "checkout-shell-c12" in scode,
        "brand3",
        "brand3" in scode,
        "len",
        len(scode),
    )

    for path in [
        "/wp-content/uploads/pm-home/checkout-brand.css?v=brand3",
        "/wp-content/uploads/pm-home/checkout-shell-c12.js?v=c12",
    ]:
        with urllib.request.urlopen(BASE + path, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
            mark = "decodeEntities" if path.endswith(".js?v=c12") else "pm-ck-bg"
            print(path, r.status, len(body), mark, mark in body)

    html = urllib.request.urlopen(BASE + "/finalizar-pagamento/?pm=brand3", timeout=60).read().decode(
        "utf-8", "replace"
    )
    print("page scripts", re.findall(r"checkout-shell[^\"']*", html)[:5])
    print("page brand", re.findall(r"checkout-brand[^\"']*", html)[:5])


if __name__ == "__main__":
    main()
