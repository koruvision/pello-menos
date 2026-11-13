# -*- coding: utf-8 -*-
"""Publica account.php + lost-password.html + snippet pm-home (rota lost-password)."""
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
                "User-Agent": "pm-lost-password",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
                return r.status, (json.loads(body) if body.strip()[:1] in "{[" else body)
        except urllib.error.HTTPError as err:
            return err.code, err.read().decode("utf-8", "replace")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("account.php", (PM / "account.php").read_bytes())
        z.writestr("lost-password.html", (PM / "lost-password.html").read_bytes())
    st, resp = call(
        "POST",
        "/wp-json/pm-home/v1/bundle",
        raw=buf.getvalue(),
        content_type="application/zip",
    )
    print("bundle", st, str(resp)[:200])

    code = SNIPPET_SRC.read_text(encoding="utf-8")
    if code.startswith("<?php"):
        code = code[5:].lstrip()
    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    if st != 200 or not isinstance(rows, list):
        raise SystemExit(f"snippets {st} {rows}")
    sn = next((x for x in rows if x.get("name") == SNIPPET_NAME), None)
    if not sn:
        sn = next((x for x in rows if "pm-home" in (x.get("name") or "")), None)
    if not sn:
        raise SystemExit("pm-home snippet not found: " + str([x.get("name") for x in rows[:20]]))
    st, current = call("GET", f"/wp-json/code-snippets/v1/snippets/{sn['id']}")
    live = current.get("code") or "" if isinstance(current, dict) else ""
    routes_line = ""
    for line in live.splitlines():
        if line.startswith("define('PM_HOME_ROUTES'") or line.startswith('define("PM_HOME_ROUTES"'):
            routes_line = line
            break
    final_code = (routes_line + "\n\n" + code) if routes_line else code
    payload = {
        "name": sn.get("name") or SNIPPET_NAME,
        "code": final_code,
        "scope": (current.get("scope") if isinstance(current, dict) else None) or "global",
        "active": True,
    }
    st, saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{sn['id']}", payload, timeout=180)
    saved_code = (saved.get("code") or "") if isinstance(saved, dict) else ""
    print(
        "snippet",
        st,
        sn["id"],
        isinstance(saved, dict) and saved.get("active"),
        "lost_fn",
        "pm_home_lost_password_body" in saved_code,
        "routes",
        bool(routes_line),
    )

    checks = [
        ("/wp-content/uploads/pm-home/lost-password.html", b"<!--PM_LOST_BODY-->"),
        ("/wp-content/uploads/pm-home/account.php", b"'completed', 'refunded'"),
        ("/minha-conta/lost-password/", b"pm-account-card"),
        ("/minha-conta/lost-password/?reset-link-sent=true", b"E-mail enviado"),
    ]
    for path, needle in checks:
        req = urllib.request.Request(
            base + path,
            headers={"User-Agent": "pm", "Cache-Control": "no-cache"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            text = body.decode("utf-8", "replace")
            bad_old = "Vitrine de Serviços" in text or "breadcrumb_section" in text
            print(
                path[:60],
                r.status,
                "needle",
                needle in body or needle.decode() in text,
                "old_theme",
                bad_old,
            )


if __name__ == "__main__":
    main()
