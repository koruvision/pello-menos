# -*- coding: utf-8 -*-
"""Upload only checkout CSS/JS via mini zip, then bump snippet 6 to c19/brand14."""
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
ROOT = Path("wordpress-loja/pm-home")
FILES = ["checkout-brand.css", "checkout-shell-c19.js", "checkout-shell.js"]


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


def build_mini_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in FILES:
            text = (ROOT / name).read_text(encoding="utf-8").replace(CLONE, DEST)
            zf.writestr(name, text.encode("utf-8"))
    return buf.getvalue()


def main():
    blob = build_mini_zip()
    print("mini_zip", len(blob), "bytes")
    st, result = call(
        "POST",
        "/wp-json/pm-home/v1/bundle",
        raw=blob,
        content_type="application/zip",
        timeout=300,
    )
    print("bundle", st, result)
    if st != 200:
        raise SystemExit(1)

    st, sn = call("GET", "/wp-json/code-snippets/v1/snippets/6")
    code = sn.get("code") or ""
    next_code = code
    for a, b in [
        ("checkout-shell-c18.js?v=c18", "checkout-shell-c19.js?v=c19"),
        ("checkout-shell-c18.js", "checkout-shell-c19.js"),
        ("?v=c18", "?v=c19"),
        ("checkout-brand.css?v=brand13", "checkout-brand.css?v=brand14"),
        ("?v=brand13", "?v=brand14"),
    ]:
        next_code = next_code.replace(a, b)
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
    print("put", st2, "c19", "c19" in scode, "brand14", "brand14" in scode)

    html = urllib.request.urlopen(BASE + "/finalizar-pagamento/?pm=c19", timeout=60).read().decode(
        "utf-8", "replace"
    )
    print("assets", re.findall(r"checkout-(?:shell|brand)[^\"']*", html)[:6])

    css = urllib.request.urlopen(
        BASE + "/wp-content/uploads/pm-home/checkout-brand.css?v=brand14", timeout=30
    ).read().decode("utf-8", "replace")
    print(
        "css_ok",
        "sem faixa azul" in css,
        "e25ab8" in css,
        "btn-shine 3.6s" in css,
    )
    js = urllib.request.urlopen(
        BASE + "/wp-content/uploads/pm-home/checkout-shell-c19.js?v=c19", timeout=30
    ).read().decode("utf-8", "replace")
    print("js_ok", "resolveLineImage" in js, "48219" in js, DEST in js or "oficialteste" in js)


if __name__ == "__main__":
    main()
