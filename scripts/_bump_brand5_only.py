# -*- coding: utf-8 -*-
"""Bump snippet 6 brand CSS query to brand5; upload CSS via bundle first."""
import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/oficialteste.env")
BASE = "https://pellomenosoficialteste.companygenesis.com.br"
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


def call(method, path, payload=None, raw=None, content_type=None):
    cfg = env()
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    data = raw if raw is not None else (None if payload is None else json.dumps(payload).encode())
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
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
        with urllib.request.urlopen(req, timeout=180) as r:
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
    # Prefer full bundle for consistency
    import subprocess
    import sys

    rc = subprocess.call(
        [
            sys.executable,
            "-u",
            "scripts/pm_publicar_destino.py",
            "--env",
            "projeto-migracao/.secrets/oficialteste.env",
            "bundle",
        ]
    )
    print("bundle exit", rc)
    if rc != 0:
        raise SystemExit(rc)

    st, sn = call("GET", "/wp-json/code-snippets/v1/snippets/6")
    code = (sn.get("code") if isinstance(sn, dict) else "") or ""
    next_code = code.replace("checkout-brand.css?v=brand4", "checkout-brand.css?v=brand5")
    next_code = next_code.replace("?v=brand4", "?v=brand5")
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
    print("put", st2, "brand5", "brand5" in (scode or ""))
    html = urllib.request.urlopen(BASE + "/finalizar-pagamento/?pm=brand5", timeout=60).read().decode(
        "utf-8", "replace"
    )
    print("brand links", re.findall(r"checkout-brand[^\"']*", html)[:4])
    css = urllib.request.urlopen(BASE + "/wp-content/uploads/pm-home/checkout-brand.css?v=brand5", timeout=30).read().decode(
        "utf-8", "replace"
    )
    print("order:2 present", "order: 2" in css or "order:2" in css)


if __name__ == "__main__":
    main()
