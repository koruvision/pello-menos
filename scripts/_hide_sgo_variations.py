# -*- coding: utf-8 -*-
"""Set all São Gonçalo (saogoncalo) Woo variations to private/outofstock on oficialteste."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "oficialteste.env"
BRIDGE = Path(__file__).resolve().parents[1] / "src" / "lib" / "woo-bridge.json"


def env():
    d = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def api(method, url, auth, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + auth,
            "User-Agent": "pm-hide-sgo",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body[:1] in "[{" else body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body[:300]


def main():
    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    # unique parent product ids
    parents = sorted(
        {
            int(row["productId"])
            for row in bridge.values()
            if isinstance(row, dict) and row.get("productId")
        }
    )
    print("parents", len(parents))
    hidden = 0
    for wid in parents:
        st, vars_ = api(
            "GET", f"{base}/wp-json/wc/v3/products/{wid}/variations?per_page=100", auth
        )
        if st != 200 or not isinstance(vars_, list):
            continue
        for v in vars_:
            option = ""
            for a in v.get("attributes") or []:
                option = a.get("option") or option
            opt_l = (option or "").lower()
            slugish = opt_l.replace(" ", "")
            if (
                "goncalo" in opt_l
                or "gonçalo" in opt_l
                or option.strip() == "saogoncalo"
                or "partage" in opt_l
            ):
                st2, _ = api(
                    "PUT",
                    f"{base}/wp-json/wc/v3/products/{wid}/variations/{v['id']}",
                    auth,
                    {"status": "private", "stock_status": "outofstock"},
                )
                hidden += 1
                print("hide", wid, v["id"], option, st2)
    print("hidden", hidden)


if __name__ == "__main__":
    main()
