# -*- coding: utf-8 -*-
"""Force APE/13M variation attrs via pa_unidade + strip sgo from bridges."""
from __future__ import annotations

import base64
import json
import shutil
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
BRIDGE_WP = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"

LINHA = {
    "buco-linha": None,
    "queixo-linha": None,
    "faixa-linha": None,
}
LABELS = {
    "ape": "RJ - Tijuca - Afonso Pena",
    "13m": "RJ - Centro - Rua Treze de Maio",
}


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
            "User-Agent": "pm-fix-ape13m",
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
            return e.code, body[:600]


def main():
    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))

    # strip sgo hard
    stripped = 0
    for pid, row in list(bridge.items()):
        if not isinstance(row, dict):
            continue
        units = row.get("units")
        if isinstance(units, dict) and "sgo" in units:
            del units["sgo"]
            stripped += 1
    print("stripped sgo", stripped)

    for pid in LINHA:
        row = bridge[pid]
        wid = row["productId"]
        st, product = api("GET", f"{base}/wp-json/wc/v3/products/{wid}", auth)
        assert st == 200
        # find attribute
        attr = None
        for a in product.get("attributes") or []:
            if a.get("variation") or (a.get("name") or "").lower() == "unidade":
                attr = a
                break
        print(pid, "attr", attr)
        opts = list((attr or {}).get("options") or [])
        for lab in LABELS.values():
            if lab not in opts:
                opts.append(lab)
        # remove goncalo
        opts = [o for o in opts if "goncalo" not in o.lower() and "gonçalo" not in o.lower()]
        put_attrs = [
            {
                "id": (attr or {}).get("id"),
                "name": (attr or {}).get("name") or "Unidade",
                "visible": True,
                "variation": True,
                "options": opts,
            }
        ]
        st, _ = api(
            "PUT",
            f"{base}/wp-json/wc/v3/products/{wid}",
            auth,
            {"attributes": put_attrs},
        )
        print(pid, "parent attrs put", st, "n_opts", len(opts))

        st, vars_ = api(
            "GET", f"{base}/wp-json/wc/v3/products/{wid}/variations?per_page=100", auth
        )
        # find vars that should be ape/13m — by id from previous attempt or empty/wrong
        by_id = {v["id"]: v for v in vars_}
        # known vids from prior run
        candidates = {
            "buco-linha": {"ape": 48384, "13m": 48385},
            "queixo-linha": {"ape": 48386, "13m": 48387},
            "faixa-linha": {"ape": 48388, "13m": 48389},
        }[pid]

        attr_name = (attr or {}).get("name") or "Unidade"
        attr_id = (attr or {}).get("id")

        for uid, vid in candidates.items():
            label = LABELS[uid]
            payload = {
                "regular_price": "1.00",
                "status": "publish",
                "stock_status": "instock",
                "attributes": [
                    {
                        "id": attr_id,
                        "name": attr_name,
                        "option": label,
                    }
                ],
            }
            st, upd = api(
                "PUT",
                f"{base}/wp-json/wc/v3/products/{wid}/variations/{vid}",
                auth,
                payload,
            )
            print(pid, "PUT", vid, uid, st, "attrs", (upd.get("attributes") if isinstance(upd, dict) else upd))
            if st in (200, 201) and isinstance(upd, dict):
                opt = ""
                for a in upd.get("attributes") or []:
                    opt = a.get("option") or opt
                if opt:
                    row.setdefault("units", {})[uid] = {
                        "variationId": int(vid),
                        "option": opt,
                    }
                else:
                    # create fresh variation instead
                    st2, created = api(
                        "POST",
                        f"{base}/wp-json/wc/v3/products/{wid}/variations",
                        auth,
                        payload,
                    )
                    print(pid, "POST new", uid, st2, created.get("id") if isinstance(created, dict) else created)
                    if isinstance(created, dict) and created.get("id"):
                        opt2 = ""
                        for a in created.get("attributes") or []:
                            opt2 = a.get("option") or opt2
                        if opt2:
                            row.setdefault("units", {})[uid] = {
                                "variationId": int(created["id"]),
                                "option": opt2,
                            }
                        else:
                            print(pid, "STILL EMPTY ATTR on create", created.get("attributes"))

        # verify
        st, vars_ = api(
            "GET", f"{base}/wp-json/wc/v3/products/{wid}/variations?per_page=100", auth
        )
        for v in vars_:
            opts = [a.get("option") for a in (v.get("attributes") or [])]
            if any(LABELS[u] in (opts or []) for u in LABELS) or not any(opts):
                print("  var", v["id"], "status", v.get("status"), "attrs", v.get("attributes"))

        print(pid, "bridge units count", len(row.get("units") or {}), "has ape/13m", "ape" in (row.get("units") or {}), "13m" in (row.get("units") or {}))

    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(BRIDGE, BRIDGE_WP)
    # recount sgo
    left = sum(
        1
        for r in bridge.values()
        if isinstance(r, dict) and isinstance(r.get("units"), dict) and "sgo" in r["units"]
    )
    print("sgo left", left)
    print("saved")


if __name__ == "__main__":
    main()
