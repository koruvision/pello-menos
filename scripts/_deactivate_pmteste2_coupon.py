# -*- coding: utf-8 -*-
"""Desativa cupom PMTESTE2 após ensaio."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
COUPON_ID = 49523


def main():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    base = e["PM_LOJA_URL"].rstrip("/")
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    payload = {"status": "draft", "amount": "2"}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        base + f"/wp-json/wc/v3/coupons/{COUPON_ID}",
        data=data,
        method="PUT",
        headers={
            "Authorization": "Basic " + auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-deactivate-teste2",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.loads(r.read().decode())
            print("deactivated", r.status, body.get("id"), body.get("status"), body.get("code"))
    except urllib.error.HTTPError as err:
        print("fail", err.code, err.read()[:300])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
