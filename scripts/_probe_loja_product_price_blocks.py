# -*- coding: utf-8 -*-
import json
import re
import urllib.request

BASE = "https://loja.pellomenos.com.br"
UA = {"User-Agent": "pm-price-probe2", "Cache-Control": "no-cache"}

PRODUCTS = [
    "perna-cera",
    "axilas-laser",
    "virilha-laser",
    "bracos-laser",
    "axila-cera",
    "meia-perna-cera",
]


def fetch(url: str) -> str:
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=60
    ).read().decode("utf-8", "replace")


def main() -> None:
    home = fetch(BASE + "/?v=price2")
    print("HOME hero baked snippets:")
    for label, pat in [
        ("73", r"73[,.]0?2"),
        ("359", r"359[,.]"),
        ("836", r"836"),
        ("576", r"576"),
        ("81,61", r"81[,.]61"),
        ("77,31", r"77[,.]31"),
    ]:
        print(" ", label, len(re.findall(pat, home)))

    # home product rails: look near href produto
    for pid in PRODUCTS:
        m = re.search(
            rf'href="/produto/{re.escape(pid)}/"[\s\S]{{0,900}}',
            home,
        )
        if not m:
            print("home card", pid, "NOT FOUND")
            continue
        chunk = m.group(0)
        prices = re.findall(r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}", chunk)
        print("home card", pid, prices[:6])

    print("\nPRODUCT pages main block:")
    for pid in PRODUCTS:
        html = fetch(f"{BASE}/produto/{pid}/?v=price2")
        # prefer product price region
        markers = [
            "js-product-price",
            "data-pm-price",
            "priceCents",
            "oldPriceCents",
            "product-price",
            "font-display",
        ]
        for mk in markers:
            if mk in html:
                i = html.find(mk)
                chunk = html[max(0, i - 100) : i + 500]
                prices = re.findall(r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}|R\$\s*\d+", chunk.replace("\xa0", " "))
                if prices:
                    print(pid, mk, prices[:8])
                    break
        else:
            # fallback: first non-gift prices after h1
            h1 = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html)
            start = h1.end() if h1 else 0
            chunk = html[start : start + 2500]
            prices = re.findall(r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}", chunk.replace("\xa0", " "))
            print(pid, "after-h1", prices[:10])

    # cart-related
    try:
        cr = json.loads(fetch(BASE + "/wp-content/uploads/pm-home/cart-related.json?v=price2"))
        for pid in PRODUCTS:
            item = None
            if isinstance(cr, dict):
                item = cr.get(pid)
                if item is None:
                    for k, v in cr.items():
                        if isinstance(v, dict) and (k == pid or v.get("id") == pid):
                            item = v
                            break
            if isinstance(item, dict):
                keys = {k: item.get(k) for k in item if "price" in k.lower() or "cent" in k.lower() or k in ("id", "name")}
                print("cart-related", pid, keys)
            else:
                print("cart-related", pid, type(cr), "missing")
    except Exception as e:
        print("cart-related fail", e)

    # black-nov json
    try:
        bn = fetch(BASE + "/wp-content/uploads/pm-home/black-nov-campaign.json?v=price2")
        print("black-nov json head", bn[:200])
    except Exception as e:
        print("bn fail", e)


if __name__ == "__main__":
    main()
