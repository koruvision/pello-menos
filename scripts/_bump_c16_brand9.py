# -*- coding: utf-8 -*-
import base64
import json
import re
import subprocess
import sys
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
    with urllib.request.urlopen(req, timeout=90) as r:
        body = r.read().decode() or "{}"
        return r.status, json.loads(body) if body.strip().startswith(("{", "[")) else body


def main():
    rc = subprocess.call(
        [sys.executable, "-u", "scripts/pm_publicar_destino.py", "--env", str(ENV), "bundle"]
    )
    print("bundle", rc)
    if rc != 0:
        raise SystemExit(rc)
    st, sn = call("GET", "/wp-json/code-snippets/v1/snippets/6")
    code = sn.get("code") or ""
    next_code = code
    for a, b in [
        ("checkout-shell-c15.js?v=c15", "checkout-shell-c16.js?v=c16"),
        ("checkout-shell-c15.js", "checkout-shell-c16.js"),
        ("?v=c15", "?v=c16"),
        ("checkout-brand.css?v=brand8", "checkout-brand.css?v=brand9"),
        ("?v=brand8", "?v=brand9"),
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
    print("put", st2, "c16", "c16" in scode, "brand9", "brand9" in scode)
    html = urllib.request.urlopen(BASE + "/finalizar-pagamento/?pm=c16", timeout=60).read().decode(
        "utf-8", "replace"
    )
    print("assets", re.findall(r"checkout-(?:shell|brand)[^\"']*", html)[:6])


if __name__ == "__main__":
    main()
