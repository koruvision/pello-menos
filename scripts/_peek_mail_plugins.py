# -*- coding: utf-8 -*-
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/oficialteste.env")


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    return values


def main():
    cfg = env()
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    base = cfg["PM_OFICIALTESTE_URL"].rstrip("/")
    headers = {"Authorization": "Basic " + token, "Accept": "application/json"}
    req = urllib.request.Request(base + "/wp-json/wp/v2/plugins", headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        plugs = json.loads(r.read().decode())
    keys = ("mail", "smtp", "woocommerce", "contact-form", "payment", "cielo", "pag")
    for p in plugs:
        sl = (p.get("plugin") or "").lower()
        name = (p.get("name") or "").lower()
        if any(k in sl or k in name for k in keys):
            print(p.get("status"), "|", p.get("plugin"), "|", (p.get("name") or "")[:70])

    for path in (
        "/wp-json/contact-form-7/v1/contact-forms/1831",
        "/wp-json/wc/v3/settings/email",
    ):
        req = urllib.request.Request(base + path, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(path, r.status, r.read()[:180])
        except urllib.error.HTTPError as e:
            print(path, e.code, e.read()[:120])


if __name__ == "__main__":
    main()
