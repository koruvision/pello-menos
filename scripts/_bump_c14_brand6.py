# -*- coding: utf-8 -*-
import base64
import json
import re
import subprocess
import sys
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
            parsed = raw[:500]
        return e.code, parsed


def main():
    rc = subprocess.call(
        [
            sys.executable,
            "-u",
            "scripts/pm_publicar_destino.py",
            "--env",
            str(ENV),
            "bundle",
        ]
    )
    print("bundle", rc)
    if rc != 0:
        raise SystemExit(rc)
    st, sn = call("GET", "/wp-json/code-snippets/v1/snippets/6")
    code = (sn.get("code") if isinstance(sn, dict) else "") or ""
    next_code = code
    for a, b in [
        ("checkout-shell-c13.js?v=c13", "checkout-shell-c14.js?v=c14"),
        ("checkout-shell-c12.js?v=c12", "checkout-shell-c14.js?v=c14"),
        ("checkout-brand.css?v=brand5", "checkout-brand.css?v=brand6"),
        ("checkout-brand.css?v=brand4", "checkout-brand.css?v=brand6"),
    ]:
        next_code = next_code.replace(a, b)
    next_code = next_code.replace("checkout-shell-c13.js", "checkout-shell-c14.js")
    next_code = next_code.replace("?v=c13", "?v=c14")
    next_code = next_code.replace("?v=brand5", "?v=brand6")
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
    print("put", st2, "c14", "c14" in (scode or ""), "brand6", "brand6" in (scode or ""))
    html = urllib.request.urlopen(BASE + "/finalizar-pagamento/?pm=c14", timeout=60).read().decode(
        "utf-8", "replace"
    )
    print("scripts", re.findall(r"checkout-shell[^\"']*", html)[:3])
    print("brand", re.findall(r"checkout-brand[^\"']*", html)[:3])


if __name__ == "__main__":
    main()
