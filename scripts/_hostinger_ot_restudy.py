# -*- coding: utf-8 -*-
"""Restudo rápido OT via Hostinger: pm-home, child theme, mu-plugins."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "hostinger-ot.env"
OT = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
OUT = ROOT / "scripts" / "_hostinger_ot_restudy.json"
BASE = "https://developers.hostinger.com"


def env():
    e = {}
    for path in (ENV, OT):
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def api(token, path, query=None):
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": "pm-hostinger-restudy/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body[:500]}
        return err.code, parsed
    except Exception as err:  # noqa: BLE001
        return 0, {"error": str(err)}


def list_dir(token, user, domain, directory, max_depth=2):
    return api(
        token,
        f"/api/hosting/v1/accounts/{user}/domains/{domain}/files",
        {"directory": directory, "max_depth": max_depth, "max_items": 2000},
    )


def read_file(token, user, domain, file_path):
    st, body = api(
        token,
        f"/api/hosting/v1/accounts/{user}/domains/{domain}/files/content",
        {"path": file_path},
    )
    text = ""
    if st == 200 and isinstance(body, dict):
        for k in ("content", "data", "file_content", "body"):
            v = body.get(k)
            if isinstance(v, str):
                text = v
                break
            if isinstance(v, dict) and isinstance(v.get("content"), str):
                text = v["content"]
                break
    return st, text, body


def main():
    e = env()
    token = e["PM_HOSTINGER_API_TOKEN"]
    user = e["PM_HOSTINGER_ACCOUNT"]
    domain = e.get("PM_HOSTINGER_DOMAIN") or "pellomenosoficialteste.companygenesis.com.br"
    report = {"domain": domain, "dirs": {}, "assets": {}, "notes": []}

    for d in (
        "wp-content/uploads/pm-home",
        "wp-content/themes/shopwise-child",
        "wp-content/mu-plugins",
    ):
        st, data = list_dir(token, user, domain, d, max_depth=2)
        items = (data.get("items") if isinstance(data, dict) else []) or []
        names = sorted([(it.get("path") or it.get("name") or "") for it in items])
        report["dirs"][d] = {
            "status": st,
            "total": data.get("total_items") if isinstance(data, dict) else None,
            "sample": names[:100],
        }
        print("DIR", d, st, data.get("total_items") if isinstance(data, dict) else data, "items", len(items))

    # plugins top-level only (depth 1); tolerate 500
    st, data = list_dir(token, user, domain, "wp-content/plugins", max_depth=1)
    items = (data.get("items") if isinstance(data, dict) else []) or []
    report["dirs"]["wp-content/plugins"] = {
        "status": st,
        "total": data.get("total_items") if isinstance(data, dict) else None,
        "dirs": sorted(
            [it.get("name") for it in items if it.get("type") == "directory" and it.get("name")]
        ),
    }
    print("DIR plugins", st, len(report["dirs"]["wp-content/plugins"]["dirs"]))

    # Known critical pm-home assets + filtered listing
    interesting = [
        "wp-content/uploads/pm-home/checkout-shell-c24.js",
        "wp-content/uploads/pm-home/checkout-shell.js",
        "wp-content/uploads/pm-home/checkout-brand.css",
        "wp-content/uploads/pm-home/pm_black_nov_snippet.php",
        "wp-content/uploads/pm-home/pm-black-nov-snippet.php",
        "wp-content/uploads/pm-home/black-nov-config.json",
        "wp-content/uploads/pm-home/pm-publish-manifest.json",
    ]
    st, data = list_dir(token, user, domain, "wp-content/uploads/pm-home", max_depth=2)
    for it in (data.get("items") if isinstance(data, dict) else []) or []:
        name = (it.get("name") or "").lower()
        path = it.get("path") or it.get("name") or ""
        full = path if str(path).startswith("wp-content/") else f"wp-content/uploads/pm-home/{path}"
        full = str(full).replace("//", "/")
        if it.get("type") == "file" and any(
            x in name
            for x in (
                "checkout-shell-c24",
                "black-nov",
                "pm-black",
                "pm_black",
                "manifest",
                "checkout-brand",
            )
        ):
            interesting.append(full)

    for path in sorted(set(interesting)):
        st, text, _ = read_file(token, user, domain, path)
        meta = {"status": st, "bytes": len(text)}
        if st == 200 and text:
            # version markers
            m = re.search(r"\?v=([a-zA-Z0-9._-]+)", text)
            if m:
                meta["v_query"] = m.group(1)
            if "FORCE" in text or "__PM_BLACK_PHASE__" in text:
                meta["has_force"] = True
                fm = re.search(r"FORCE['\"\s:=]+([a-zA-Z0-9_-]*)", text)
                if fm:
                    meta["force_value"] = fm.group(1)
            if "totalamount" in text:
                meta["mentions_totalamount"] = True
            if "campaignPriceForWooId" in text or "pmBlackNov" in text:
                meta["esquenta_hooks"] = True
            # first 120 chars for shell identity
            if path.endswith(".js"):
                meta["head"] = text[:120].replace("\n", " ")
        report["assets"][path] = meta
        print("ASSET", path, meta)

    # Confirm Accesstage still only in child functions
    st, text, _ = read_file(
        token, user, domain, "wp-content/themes/shopwise-child/functions.php"
    )
    report["accesstage"] = {
        "path": "wp-content/themes/shopwise-child/functions.php",
        "status": st,
        "bytes": len(text),
        "has_payment_CF7": "function payment_CF7" in text,
        "amount_source": "posted_data['totalamount']*100"
        if "totalamount" in text
        else None,
        "woo_order_via": "wc_create_order + add_product + calculate_totals"
        if "wc_create_order" in text and "add_product" in text
        else None,
        "cf7_form_id": 1831 if "1831" in text else None,
        "gateway": "accesstage.net.br/access-pay/transactions?gateway=REDE"
        if "accesstage.net.br" in text
        else None,
    }
    print("ACCESSTAGE", report["accesstage"])

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
