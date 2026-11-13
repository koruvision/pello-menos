# -*- coding: utf-8 -*-
"""Publica página Compra não realizada + shell c38 + snippet pm-home na loja."""
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
FILES = [
    "compra-nao-realizada.html",
    "checkout-shell-c24.js",
]


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def call(method, path, payload=None, raw=None, content_type="application/json", timeout=300):
    cfg = env()
    data = raw if raw is not None else (None if payload is None else json.dumps(payload).encode())
    token = base64.b64encode(f"{cfg['PM_LOJA_USER']}:{cfg['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    req = urllib.request.Request(
        cfg["PM_LOJA_URL"].rstrip("/") + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + token,
            "Accept": "application/json",
            "User-Agent": "pm-fail-page/1.0",
            "Content-Type": content_type,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body[:1] in "[{" else body)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            return err.code, json.loads(body)
        except json.JSONDecodeError:
            return err.code, body[:600]


def publish_files():
    cfg = env()
    dest = cfg["PM_LOJA_URL"].rstrip("/") + "/wp-content/uploads/pm-home"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            text = (PM / rel).read_text(encoding="utf-8")
            text = text.replace(
                "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home",
                dest,
            )
            z.writestr(rel, text.encode("utf-8"))
            print("zip+", rel)
    st, body = call("POST", "/wp-json/pm-home/v1/bundle", raw=buf.getvalue(), content_type="application/zip")
    print("bundle", st, body if isinstance(body, dict) else str(body)[:200])
    if st != 200:
        raise SystemExit(1)


def update_snippet():
    code = SNIPPET.read_text(encoding="utf-8")
    # keep current routes constant if already set in live snippet
    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    if st != 200 or not isinstance(rows, list):
        raise SystemExit(f"snippets {st}")
    sn = next((r for r in rows if r.get("name") == "pm-home (front do projeto)"), None)
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
    if "compra-nao-realizada" not in final_code:
        raise SystemExit("snippet source missing fail route")
    if "c38" not in final_code:
        raise SystemExit("snippet source missing c38")
    payload = {
        "name": "pm-home (front do projeto)",
        "code": final_code,
        "scope": (current.get("scope") if isinstance(current, dict) else None) or "global",
        "active": True,
    }
    st, saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{sn['id']}", payload)
    print(
        "snippet",
        st,
        saved.get("id") if isinstance(saved, dict) else saved,
        "active",
        saved.get("active") if isinstance(saved, dict) else None,
        "has_fail_route",
        "compra-nao-realizada" in (saved.get("code") or "") if isinstance(saved, dict) else False,
    )


def verify():
    base = env()["PM_LOJA_URL"].rstrip("/")
    for path in (
        "/compra-nao-realizada/",
        "/finalizar-pagamento/undefined",
        "/wp-content/uploads/pm-home/checkout-shell-c24.js?v=c38",
    ):
        try:
            req = urllib.request.Request(base + path, headers={"User-Agent": "pm"})
            with urllib.request.urlopen(req, timeout=60) as r:
                t = r.read().decode("utf-8", "replace")
                print(
                    path,
                    r.status,
                    "Compra não realizada" in t or "bindPaymentFailRedirect" in t or "__pmPaymentFailBound" in t,
                )
        except urllib.error.HTTPError as err:
            print(path, "HTTP", err.code)


def main():
    publish_files()
    update_snippet()
    verify()
    print("FAIL_PAGE_OK")


if __name__ == "__main__":
    main()
