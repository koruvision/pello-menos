# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="PM_LOJA")
    args = ap.parse_args()
    path = ROOT / "projeto-migracao" / ".secrets" / (
        "loja.env" if args.prefix == "PM_LOJA" else "oficialteste.env"
    )
    e = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    url = e[f"{args.prefix}_URL"].rstrip("/")
    tok = base64.b64encode(
        f"{e[f'{args.prefix}_USER']}:{e[f'{args.prefix}_APP_PASSWORD']}".encode()
    ).decode()
    headers = {
        "Authorization": "Basic " + tok,
        "Content-Type": "application/json",
        "User-Agent": "pm-wcar-install/1.0",
        "Accept": "application/json",
    }
    plug = "woo-cart-abandonment-recovery/woo-cart-abandonment-recovery"
    try:
        req = urllib.request.Request(
            url + f"/wp-json/wp/v2/plugins/{plug}", headers=headers
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.loads(r.read())
            print("exists", body.get("status"))
            if body.get("status") != "active":
                req2 = urllib.request.Request(
                    url + f"/wp-json/wp/v2/plugins/{plug}",
                    data=json.dumps({"status": "active"}).encode(),
                    method="POST",
                    headers=headers,
                )
                with urllib.request.urlopen(req2, timeout=60) as r2:
                    print("activated", json.loads(r2.read()).get("status"))
            return
    except urllib.error.HTTPError as err:
        if err.code != 404:
            print("get fail", err.code, err.read()[:200])
            return
    req = urllib.request.Request(
        url + "/wp-json/wp/v2/plugins",
        data=json.dumps(
            {"slug": "woo-cart-abandonment-recovery", "status": "active"}
        ).encode(),
        method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            print("installed", r.status, json.loads(r.read()).get("plugin"))
    except urllib.error.HTTPError as err:
        print("install fail", err.code, err.read()[:400])


if __name__ == "__main__":
    main()
