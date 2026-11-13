# -*- coding: utf-8 -*-
"""Update snippet 6 to checkout-shell-c13 + brand4."""
import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/oficialteste.env")
BASE = "https://pellomenosoficialteste.companygenesis.com.br"


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
    st, sn = call("GET", "/wp-json/code-snippets/v1/snippets/6")
    code = (sn.get("code") if isinstance(sn, dict) else "") or ""
    print("get", st, "len", len(code))
    next_code = code
    for a, b in [
        ("checkout-shell-c12.js?v=c12", "checkout-shell-c13.js?v=c13"),
        ("checkout-shell-c11.js?v=c11", "checkout-shell-c13.js?v=c13"),
        ("checkout-brand.css?v=brand3", "checkout-brand.css?v=brand4"),
        ("checkout-brand.css?v=brand2", "checkout-brand.css?v=brand4"),
        ("checkout-brand.css?v=brand1", "checkout-brand.css?v=brand4"),
    ]:
        next_code = next_code.replace(a, b)
    next_code = next_code.replace("checkout-shell-c12.js", "checkout-shell-c13.js")
    next_code = next_code.replace("?v=c12", "?v=c13")
    next_code = next_code.replace("?v=brand3", "?v=brand4")
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
    scode = saved.get("code") if isinstance(saved, dict) else ""
    print(
        "put",
        st2,
        "c13",
        "c13" in (scode or ""),
        "brand4",
        "brand4" in (scode or ""),
    )
    html = urllib.request.urlopen(BASE + "/finalizar-pagamento/?pm=brand4", timeout=60).read().decode(
        "utf-8", "replace"
    )
    print("scripts", re.findall(r"checkout-shell[^\"']*", html)[:4])
    print("brand", re.findall(r"checkout-brand[^\"']*", html)[:4])


if __name__ == "__main__":
    main()
