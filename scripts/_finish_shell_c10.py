# -*- coding: utf-8 -*-
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
        with urllib.request.urlopen(req, timeout=60) as r:
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
    # deactivate duplicate snippet 8
    st, sn = call("GET", "/wp-json/code-snippets/v1/snippets/8")
    if st == 200 and isinstance(sn, dict):
        sn["active"] = False
        st2, saved = call("PUT", "/wp-json/code-snippets/v1/snippets/8", {
            "name": sn.get("name"),
            "code": sn.get("code"),
            "scope": sn.get("scope") or "global",
            "active": False,
        })
        print("deactivate 8", st2, saved.get("active") if isinstance(saved, dict) else saved)
    st6, sn6 = call("GET", "/wp-json/code-snippets/v1/snippets/6")
    code = (sn6.get("code") if isinstance(sn6, dict) else "") or ""
    print("snippet6 has c10", "checkout-shell-c10.js" in code)
    html = urllib.request.urlopen(BASE + "/finalizar-pagamento/?pm=c10check", timeout=60).read().decode(
        "utf-8", "replace"
    )
    scripts = re.findall(r"checkout-shell[^\"']*", html)
    print("scripts", scripts)
    js = urllib.request.urlopen(
        BASE + "/wp-content/uploads/pm-home/checkout-shell-c10.js?v=c10", timeout=60
    ).read().decode("utf-8", "replace")
    print("c10 file", len(js), "boot", "__pmShellBoot" in js, "lock", "__pmTotalsLock" in js)


if __name__ == "__main__":
    main()
