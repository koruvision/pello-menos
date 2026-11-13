# -*- coding: utf-8 -*-
"""Toggle status dos SKUs de ensaio OT (publish hidden <-> draft)."""
from __future__ import annotations

import argparse
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
SKUS = json.loads((ROOT / "scripts" / "_ot_esquenta_test_skus.json").read_text(encoding="utf-8"))


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def call(method, path, payload=None):
    cfg = env()
    base = cfg["PM_OFICIALTESTE_URL"].rstrip("/")
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
        "User-Agent": "pm-ot-sku-visibility/1.0",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace") or "null")
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            return err.code, json.loads(body)
        except json.JSONDecodeError:
            return err.code, body[:400]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("publish", "draft"), required=True)
    ap.add_argument("--only", default="", help="Comma catalog ids; default all")
    args = ap.parse_args()
    wanted = [x.strip() for x in args.only.split(",") if x.strip()] or list(SKUS.keys())
    status = "publish" if args.mode == "publish" else "draft"
    for catalog_id in wanted:
        pid = SKUS[catalog_id]
        payload = {
            "status": status,
            "catalog_visibility": "hidden",
        }
        st, body = call("PUT", f"/wp-json/wc/v3/products/{pid}", payload)
        print(catalog_id, pid, st, body.get("status") if isinstance(body, dict) else body)


if __name__ == "__main__":
    main()
