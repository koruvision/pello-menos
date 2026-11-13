# -*- coding: utf-8 -*-
"""Publica snippet cache seletivo + checkout-loading/shell (GSAP on-demand)."""
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
SNIPPET_SRC = ROOT / "scripts" / "pm_home_snippet.php"
SNIPPET_NAME = "pm-home (front do projeto)"


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def main():
    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    tok = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()

    def call(method, path, payload=None, raw=None, content_type="application/json", timeout=180):
        data = raw
        if payload is not None:
            data = json.dumps(payload).encode()
        req = urllib.request.Request(
            base + path,
            data=data,
            method=method,
            headers={
                "Authorization": "Basic " + tok,
                "Content-Type": content_type,
                "Accept": "application/json",
                "User-Agent": "pm-cache-gsap",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
                return r.status, (json.loads(body) if body.strip()[:1] in "{[" else body)
        except urllib.error.HTTPError as err:
            return err.code, err.read().decode("utf-8", "replace")

    code = SNIPPET_SRC.read_text(encoding="utf-8")
    if code.startswith("<?php"):
        code = code[5:].lstrip()
    if "max-age=300, s-maxage=600" not in code:
        raise SystemExit("snippet missing catalog TTL")
    if "pm-gsap" in code and "wp_enqueue_script('pm-gsap'" in code:
        raise SystemExit("snippet still enqueues pm-gsap on boot")
    if "checkout-loading.js?v=load6" not in code or "checkout-shell-c24.js?v=c46" not in code:
        raise SystemExit("snippet missing load6/c46 bumps")

    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    sn = next((x for x in rows if x.get("name") == SNIPPET_NAME), None) if isinstance(rows, list) else None
    if not sn:
        raise SystemExit("pm-home snippet missing")
    st, current = call("GET", f"/wp-json/code-snippets/v1/snippets/{sn['id']}")
    live = current.get("code") or "" if isinstance(current, dict) else ""
    routes_line = ""
    for line in live.splitlines():
        if line.startswith("define('PM_HOME_ROUTES'") or line.startswith('define("PM_HOME_ROUTES"'):
            routes_line = line
            break
    final_code = (routes_line + "\n\n" + code) if routes_line else code
    st, saved = call(
        "PUT",
        f"/wp-json/code-snippets/v1/snippets/{sn['id']}",
        {
            "name": sn.get("name") or SNIPPET_NAME,
            "code": final_code,
            "scope": (current.get("scope") if isinstance(current, dict) else None) or "global",
            "active": True,
        },
    )
    saved_code = (saved.get("code") or "") if isinstance(saved, dict) else ""
    print(
        "snippet",
        st,
        sn["id"],
        "ttl300",
        "max-age=300, s-maxage=600" in saved_code,
        "load6",
        "load6" in saved_code,
        "no_boot_gsap",
        "wp_enqueue_script('pm-gsap'" not in saved_code,
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("checkout-loading.js", (PM / "checkout-loading.js").read_bytes())
        z.writestr("checkout-shell-c24.js", (PM / "checkout-shell-c24.js").read_bytes())
    st, resp = call(
        "POST",
        "/wp-json/pm-home/v1/bundle",
        raw=buf.getvalue(),
        content_type="application/zip",
    )
    print("bundle", st, str(resp)[:160])

    # cache probe
    for path in ("/", "/carrinho/", "/minha-conta/", "/produto/axila-cera/"):
        req = urllib.request.Request(
            base + path + ("?pm=cachev2" if "?" not in path else ""),
            headers={"User-Agent": "pm", "Cache-Control": "no-cache"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            cc = r.headers.get("Cache-Control")
            print("cache", path, r.status, cc)

    # loading asset
    req = urllib.request.Request(
        base + "/wp-content/uploads/pm-home/checkout-loading.js?v=load6",
        headers={"User-Agent": "pm", "Cache-Control": "no-cache"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
        print("load6", r.status, b"ensureGsap" in body, b"GSAP_URL" in body)


if __name__ == "__main__":
    main()
