# -*- coding: utf-8 -*-
"""Publica regras de parcelamento (R$ 180 total / R$ 50 parcela) na loja."""
from __future__ import annotations

import base64
import io
import json
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
SNIPPET = ROOT / "scripts" / "pm_home_snippet.php"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"

FILES = [
    "product.js",
    "checkout-shell.js",
    "checkout-shell-c24.js",
]


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


def call(c, method, path, payload=None, raw=None, content_type=None):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    data = raw
    headers = {
        "Authorization": "Basic " + tok,
        "User-Agent": "pm-installment-180",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        headers["Content-Type"] = content_type or "application/octet-stream"
    req = urllib.request.Request(c["url"] + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            body = r.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(body) if body else None
            except Exception:
                parsed = body
            return r.status, parsed
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body[:500]
        return err.code, parsed


def bump_product_js_cache():
    n = 0
    for path in PM.rglob("*"):
        if path.suffix.lower() not in {".html", ".js", ".php", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "product.js?v=units3" not in text:
            continue
        path.write_text(text.replace("product.js?v=units3", "product.js?v=units4"), encoding="utf-8")
        n += 1
    print("bumped product.js cache in", n, "files")


def publish_assets(c):
    dest = c["url"] + "/wp-content/uploads/pm-home"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            path = PM / rel
            raw = path.read_bytes()
            if rel.endswith(".js"):
                text = raw.decode("utf-8").replace(CLONE, dest)
                # sanity
                if rel.startswith("checkout-shell") and "MIN_INSTALLMENT_ORDER" not in text:
                    raise SystemExit(f"missing MIN_INSTALLMENT_ORDER in {rel}")
                if rel == "product.js" and "MIN_INSTALLMENT_ORDER_CENTS" not in text:
                    raise SystemExit("missing MIN_INSTALLMENT_ORDER_CENTS in product.js")
                raw = text.encode("utf-8")
            z.writestr(rel, raw)
            print("zip+", rel, path.stat().st_size)
    st, body = call(
        c,
        "POST",
        "/wp-json/pm-home/v1/bundle",
        raw=buf.getvalue(),
        content_type="application/zip",
    )
    print("bundle", st, body if isinstance(body, dict) else str(body)[:200])
    if st != 200:
        raise SystemExit(1)


def update_snippet(c):
    code = SNIPPET.read_text(encoding="utf-8")
    if "c40" not in code:
        raise SystemExit("local snippet missing c40")
    st, rows = call(c, "GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    if st != 200 or not isinstance(rows, list):
        raise SystemExit(f"snippets list {st}")
    sn = next((r for r in rows if r.get("name") == "pm-home (front do projeto)"), None)
    if not sn:
        raise SystemExit("pm-home snippet missing")
    st, current = call(c, "GET", f"/wp-json/code-snippets/v1/snippets/{sn['id']}")
    live = current.get("code") or "" if isinstance(current, dict) else ""
    routes_line = ""
    for line in live.splitlines():
        if line.startswith("define('PM_HOME_ROUTES'") or line.startswith('define("PM_HOME_ROUTES"'):
            routes_line = line
            break
    final_code = (routes_line + "\n\n" + code) if routes_line else code
    payload = {
        "name": "pm-home (front do projeto)",
        "code": final_code,
        "scope": (current.get("scope") if isinstance(current, dict) else None) or "global",
        "active": True,
    }
    st, saved = call(c, "PUT", f"/wp-json/code-snippets/v1/snippets/{sn['id']}", payload)
    print(
        "snippet",
        st,
        "c40" in ((saved.get("code") if isinstance(saved, dict) else "") or ""),
    )
    if st not in (200, 201):
        raise SystemExit(1)


def verify(c):
    base = c["url"]
    for path, needle in (
        ("/wp-content/uploads/pm-home/product.js?v=units4", "MIN_INSTALLMENT_ORDER_CENTS"),
        ("/wp-content/uploads/pm-home/checkout-shell-c24.js?v=c40", "maxInstallmentTimesForSelect"),
        ("/wp-content/uploads/pm-home/checkout-shell.js?v=inst180b", "maxInstallmentTimesForSelect"),
    ):
        req = urllib.request.Request(base + path, headers={"User-Agent": "pm", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode("utf-8", "replace")
            print(path, r.status, needle in text, "applyInstallmentRules" in text or "MIN_INSTALLMENT_ORDER_CENTS" in text)


def main():
    c = cfg()
    assert "loja.pellomenos.com.br" in c["url"]
    bump_product_js_cache()
    publish_assets(c)
    update_snippet(c)
    verify(c)
    print("LOJA_INSTALLMENT_180_OK")


if __name__ == "__main__":
    main()
