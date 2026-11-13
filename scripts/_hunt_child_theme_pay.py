# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import urllib.request

BASE = "https://pellomenosoficialteste.companygenesis.com.br"

PATHS = [
    "/wp-content/themes/shopwise-child/functions.php",
    "/wp-content/themes/shopwise-child/style.css",
    "/wp-content/themes/pellomenos/style.css",
    "/wp-content/themes/pellomenos/functions.php",
    "/wp-content/themes/shopwise-child/js/checkout.js",
    "/wp-content/themes/shopwise-child/assets/js/checkout.js",
    "/wp-content/themes/shopwise-child/assets/js/payment.js",
    "/wp-content/themes/shopwise/assets/js/scripts.js",
    "/wp-content/themes/shopwise/assets/js/custom/quick_ajax.js",
    "/wp-content/plugins/shopwise-core/elementor/custom-scripts.js",
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "pm"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read().decode("utf-8", "replace")


def main():
    st, html = get(BASE + "/finalizar-pagamento/?pm=child")
    # all theme asset urls
    urls = sorted(
        set(
            re.findall(
                r"https?://[^\"']+/wp-content/themes/(?:shopwise-child|pellomenos|shopwise)/[^\"']+",
                html,
            )
        )
    )
    print("theme assets on checkout", len(urls))
    for u in urls:
        print(" ", u)

    # also look for inline that sets redirectSuccess cookie
    if "redirectSuccess" in html:
        for m in re.finditer(r".{0,200}redirectSuccess.{0,200}", html):
            print("REDIR CTX:", m.group(0).replace("\n", " ")[:400])

    if "easyunit" in html.lower():
        for m in re.finditer(r".{0,120}easyunit.{0,120}", html, flags=re.I):
            print("EASYUNIT:", m.group(0).replace("\n", " ")[:300])

    for path in PATHS:
        try:
            st, body = get(BASE + path)
        except Exception as ex:
            print(path, "ERR", ex)
            continue
        print(path, "status", st, "len", len(body))
        low = body.lower()
        for kw in (
            "accesstage",
            "cart-number",
            "removeitemcartpl",
            "wpcf7",
            "payment",
            "token",
            "unidade",
        ):
            if kw in low:
                print("  has", kw)
        if "accesstage" in low or "removeitemcartpl" in low or "cart-number" in low:
            print(body[:2000])


if __name__ == "__main__":
    main()
