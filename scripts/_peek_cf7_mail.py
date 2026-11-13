# -*- coding: utf-8 -*-
import base64
import json
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
    req = urllib.request.Request(
        base + "/wp-json/contact-form-7/v1/contact-forms/1831",
        headers={"Authorization": "Basic " + token, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())
    props = data.get("properties") or {}
    print("keys", list(props.keys()))
    for key in ("mail", "mail_2", "messages"):
        block = props.get(key)
        if not block:
            print(key, "MISSING")
            continue
        if isinstance(block, dict):
            print("---", key)
            for k in ("active", "subject", "sender", "recipient", "additional_headers", "use_html"):
                if k in block:
                    print(f"  {k}:", block.get(k))
            body = block.get("body") or ""
            print("  body_len:", len(body))
            print("  body_head:", body[:400].replace("\n", " | "))
        else:
            print(key, type(block), str(block)[:200])


if __name__ == "__main__":
    main()
