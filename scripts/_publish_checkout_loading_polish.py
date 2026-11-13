# -*- coding: utf-8 -*-
"""Publica overlay de pagamento (JS/CSS + snippet) no OficialTeste e na loja."""
from __future__ import annotations

import base64
import io
import json
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
PUB = ROOT / "scripts" / "pm_publicar_destino.py"
FILES = ("checkout-loading.js", "checkout-brand.css")


def load_env(name: str) -> dict:
    vals = {}
    path = ROOT / "projeto-migracao" / ".secrets" / name
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def cfg_for(env_name: str) -> dict:
    e = load_env(env_name)
    if env_name.startswith("loja"):
        return {
            "url": e["PM_LOJA_URL"].rstrip("/"),
            "user": e["PM_LOJA_USER"],
            "password": e["PM_LOJA_APP_PASSWORD"],
            "env": "projeto-migracao/.secrets/loja.env",
            "prefix": "PM_LOJA",
            "permit": True,
        }
    return {
        "url": e["PM_OFICIALTESTE_URL"].rstrip("/"),
        "user": e["PM_OFICIALTESTE_USER"],
        "password": e["PM_OFICIALTESTE_APP_PASSWORD"],
        "env": "projeto-migracao/.secrets/oficialteste.env",
        "prefix": "PM_OFICIALTESTE",
        "permit": False,
    }


def call(c, method, path, payload=None, raw=None, content_type="application/json", timeout=300):
    data = raw if raw is not None else (
        None if payload is None else json.dumps(payload).encode("utf-8")
    )
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + tok,
            "User-Agent": "pm-ck-loading-polish",
            "Content-Type": content_type,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body[:1] in "[{" else body)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        return err.code, (json.loads(body) if body[:1] in "[{" else body[:500])


def publish_assets(c):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            z.write(PM / name, name)
            print("zip+", c["url"], name)
    st, body = call(
        c,
        "POST",
        "/wp-json/pm-home/v1/bundle",
        raw=buf.getvalue(),
        content_type="application/zip",
        timeout=600,
    )
    print("bundle", c["url"], st, body)


def publish_snippet(c):
    cmd = [
        sys.executable,
        str(PUB),
        "--env",
        str(ROOT / c["env"]),
        "--prefix",
        c["prefix"],
        "snippet",
        "--routes",
        "home,masculino,produto,carrinho,conta,shell,loja",
    ]
    if c["permit"]:
        # Flag global — precisa vir antes do subcomando.
        cmd.insert(cmd.index("snippet"), "--permitir-loja")
    print("snippet", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(ROOT))


def verify(c):
    for path in (
        "/wp-content/uploads/pm-home/checkout-loading.js?v=load5",
        "/wp-content/uploads/pm-home/checkout-brand.css?v=brand21",
    ):
        st, body = call(c, "GET", path)
        text = body if isinstance(body, str) else json.dumps(body)
        print(
            path,
            st,
            "pay-icon" not in text and "pm-ck-loading__pay-icon" not in text,
            "pm-ck-spin" in text or "pm-ck-loading__spinner" in text or "opacity: 1" in text,
            "rect x=\"2\"" in text or "calc(14rem - 10px)" in text,
        )
    st, html = call(c, "GET", "/finalizar-pagamento/?pm=ckload5")
    text = html if isinstance(html, str) else ""
    print(
        "page",
        c["url"],
        st,
        "load5" in text,
        "brand21" in text,
    )


def main():
    targets = ["oficialteste.env", "loja.env"]
    for name in targets:
        c = cfg_for(name)
        print("===", c["url"], "===")
        publish_assets(c)
        publish_snippet(c)
        verify(c)


if __name__ == "__main__":
    main()
