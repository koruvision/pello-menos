# -*- coding: utf-8 -*-
"""Upload checkout-brand.css mini zip and bump snippet to brand15."""
import base64
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/oficialteste.env")
BASE = "https://pellomenosoficialteste.companygenesis.com.br"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"
DEST = BASE + "/wp-content/uploads/pm-home"
CSS = Path("wordpress-loja/pm-home/checkout-brand.css")


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def call(method, path, payload=None, raw=None, content_type=None, timeout=180):
    cfg = env()
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    data = raw if raw is not None else (None if payload is None else json.dumps(payload).encode())
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; pm-publicar/1.0)",
    }
    if content_type:
        headers["Content-Type"] = content_type
    elif payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        cfg["PM_OFICIALTESTE_URL"].rstrip("/") + path,
        data=data,
        method=method,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode() or "{}"
            return r.status, json.loads(body) if body.strip().startswith(("{", "[")) else body
    except urllib.error.HTTPError as e:
        raw_body = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw_body)
        except Exception:
            parsed = raw_body[:800]
        return e.code, parsed


def main():
    buf = io.BytesIO()
    text = CSS.read_text(encoding="utf-8").replace(CLONE, DEST)
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("checkout-brand.css", text.encode("utf-8"))
    blob = buf.getvalue()
    print("mini_zip", len(blob))
    st, result = call(
        "POST", "/wp-json/pm-home/v1/bundle", raw=blob, content_type="application/zip", timeout=300
    )
    print("bundle", st, result)
    if st != 200:
        raise SystemExit(1)

    st, sn = call("GET", "/wp-json/code-snippets/v1/snippets/6")
    code = sn.get("code") or ""
    next_code = code.replace("checkout-brand.css?v=brand14", "checkout-brand.css?v=brand15").replace(
        "?v=brand14", "?v=brand15"
    )
    st2, saved = call(
        "PUT",
        "/wp-json/code-snippets/v1/snippets/6",
        {
            "name": sn.get("name") or "pm-home (front do projeto)",
            "code": next_code,
            "scope": sn.get("scope") or "global",
            "active": True,
        },
    )
    scode = (saved.get("code") if isinstance(saved, dict) else "") or ""
    print("put", st2, "brand15", "brand15" in scode)

    html = urllib.request.urlopen(BASE + "/finalizar-pagamento/?pm=b15", timeout=60).read().decode(
        "utf-8", "replace"
    )
    print("assets", re.findall(r"checkout-brand[^\"']*", html)[:4])
    css = urllib.request.urlopen(
        BASE + "/wp-content/uploads/pm-home/checkout-brand.css?v=brand15", timeout=30
    ).read().decode("utf-8", "replace")
    print("css_ok", "btn-glow" in css, "f0b56a" in css, "skewX(-18deg)" in css)


if __name__ == "__main__":
    main()
