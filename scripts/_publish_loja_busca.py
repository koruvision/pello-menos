# -*- coding: utf-8 -*-
"""Publica busca SERP + home.js + snippet na loja oficial."""
import io
import json
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PM = ROOT / "wordpress-loja" / "pm-home"
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def call(method, path, payload=None, raw=None, content_type="application/json", timeout=600):
    cfg = env()
    import base64

    token = base64.b64encode(
        f"{cfg['PM_LOJA_USER']}:{cfg['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()
    data = raw if raw is not None else (
        None if payload is None else json.dumps(payload).encode("utf-8")
    )
    req = urllib.request.Request(
        cfg["PM_LOJA_URL"].rstrip("/") + path,
        data=data,
        method=method,
        headers={
            "User-Agent": "pm-loja-busca/1.0",
            "Authorization": "Basic " + token,
            "Content-Type": content_type,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            return resp.status, (json.loads(body) if body[:1] in "[{" else body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        return error.code, (json.loads(body) if body[:1] in "[{" else body[:800])


def publish_files():
    cfg = env()
    dest_base = cfg["PM_LOJA_URL"].rstrip("/") + "/wp-content/uploads/pm-home"
    clone_base = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"
    files = [
        "busca.html",
        "busca.js",
    ]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            path = PM / rel
            if not path.is_file():
                raise SystemExit(f"missing {rel}")
            text = path.read_text(encoding="utf-8")
            text = text.replace(clone_base, dest_base)
            z.writestr(rel, text.encode("utf-8"))
            print("zip+", rel, path.stat().st_size)
    st, body = call(
        "POST",
        "/wp-json/pm-home/v1/bundle",
        raw=buf.getvalue(),
        content_type="application/zip",
        timeout=600,
    )
    print("bundle", st, body if isinstance(body, dict) else str(body)[:400])
    if st != 200:
        raise SystemExit("bundle failed")


def smoke():
    cfg = env()
    base = cfg["PM_LOJA_URL"].rstrip("/")

    def get(url):
        req = urllib.request.Request(url, headers={"User-Agent": "pm-busca-smoke"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode("utf-8", "replace"), dict(resp.headers)

    st, html, _ = get(base + "/wp-content/uploads/pm-home/busca.html?v=layout2")
    print(
        "asset busca",
        st,
        "sidebar",
        "data-pm-search-sidebar" in html,
        "select audience",
        'data-pm-search-audience' in html and "<select" in html,
    )
    st, page, _ = get(base + "/busca?q=axila")
    print(
        "route",
        st,
        "sidebar",
        "data-pm-search-sidebar" in page,
        "selects",
        page.count("<select"),
        "Feminino option",
        ">Feminino<" in page,
    )
    if "data-pm-search-sidebar" not in page:
        raise SystemExit("layout missing")


def main():
    if "loja.pellomenos.com.br" not in env()["PM_LOJA_URL"]:
        raise SystemExit("expected loja env")
    publish_files()
    smoke()
    print("BUSCA_LAYOUT_OK")


if __name__ == "__main__":
    main()
