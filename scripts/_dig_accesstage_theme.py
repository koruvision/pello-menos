# -*- coding: utf-8 -*-
"""Cava tema Shopwise + gateways Woo no OT por vestígios Accesstage."""
from __future__ import annotations

import base64
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": e["PM_OFICIALTESTE_URL"].rstrip("/"),
        "user": e["PM_OFICIALTESTE_USER"],
        "password": e["PM_OFICIALTESTE_APP_PASSWORD"],
    }


def fetch(c, path, auth=False):
    headers = {"User-Agent": "pm-dig-acc/1.0"}
    if auth:
        tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
        headers["Authorization"] = "Basic " + tok
        headers["Accept"] = "application/json"
    req = urllib.request.Request(c["url"] + path, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read()


def main():
    c = cfg()
    # Woo payment gateways
    st, body = fetch(c, "/wp-json/wc/v3/payment_gateways", auth=True)
    gates = json.loads(body.decode())
    print("gateways", len(gates))
    for g in gates:
        print(
            " GW",
            g.get("id"),
            "enabled=",
            g.get("enabled"),
            "title=",
            g.get("title"),
            "method_title=",
            g.get("method_title"),
        )

    paths = [
        "/wp-content/themes/shopwise/assets/js/scripts.js?ver=1.0",
        "/wp-content/themes/shopwise-child/style.css",
        "/wp-content/themes/shopwise-child/functions.php",
        "/wp-content/plugins/shopwise-core/elementor/custom-scripts.js?ver=7.1.4",
        "/wp-content/themes/pellomenos/style.css",
        "/wp-content/themes/pellomenos/functions.php",
    ]
    keys = ("accesstage", "accessstage", "cart-number", "Pedido Accesstage", "redirectSuccess", "holder", "securityCode")
    for path in paths:
        try:
            st, body = fetch(c, path)
            text = body.decode("utf-8", "replace")
            hits = [k for k in keys if k.lower() in text.lower()]
            print(path, st, "bytes", len(body), "hits", hits)
            if hits:
                for k in hits:
                    for m in re.finditer(r".{0,50}" + re.escape(k) + r".{0,50}", text, flags=re.I):
                        print("  ", m.group(0).replace("\n", " ")[:140])
                        break
        except Exception as ex:
            print(path, type(ex).__name__, ex)

    # Inline scripts on checkout mentioning Accesstage-ish fields
    st, body = fetch(c, "/finalizar-pagamento/")
    html = body.decode("utf-8", "replace")
    for pat in (
        r"<script[^>]*>[\s\S]{0,200}?accesstage[\s\S]{0,400}?</script>",
        r"<script[^>]*>[\s\S]{0,200}?Pedido Accesstage[\s\S]{0,400}?</script>",
        r"<script[^>]*>[\s\S]{0,200}?redirectSuccess[\s\S]{0,400}?</script>",
        r"<script[^>]*>[\s\S]{0,200}?cart-number[\s\S]{0,400}?</script>",
    ):
        ms = re.findall(pat, html, flags=re.I)
        print("inline matches", pat[20:40], len(ms))
        if ms:
            print(ms[0][:500].replace("\n", " "))

    # plugin folders via empty index listing sometimes leaks names — try common names
    for slug in (
        "accesstage",
        "acces-stage",
        "accessstage",
        "pm-accesstage",
        "pello-accesstage",
        "gateway-accesstage",
        "wc-accesstage",
        "woocommerce-gateway-accesstage",
        "easy-pagamentos",
        "argobot",
    ):
        for base in ("/wp-content/plugins/", "/wp-content/mu-plugins/"):
            path = base + slug + "/"
            try:
                st, body = fetch(c, path)
                print("dir", path, st, len(body))
            except Exception as ex:
                print("dir", path, type(ex).__name__)


if __name__ == "__main__":
    main()
