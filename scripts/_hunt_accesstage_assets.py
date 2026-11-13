# -*- coding: utf-8 -*-
"""Hunt Accesstage / payment PHP-JS in publicly readable theme/plugin assets."""
from __future__ import annotations

import re
import urllib.error
import urllib.request

BASE = "https://pellomenosoficialteste.companygenesis.com.br"
CANDIDATES = [
    "/wp-content/themes/shopwise/functions.php",
    "/wp-content/themes/shopwise/js/custom.js",
    "/wp-content/themes/shopwise/assets/js/custom.js",
    "/wp-content/plugins/shopwise-core/shopwise-core.php",
    "/wp-content/plugins/shopwise-core/inc/woo.php",
    "/wp-content/plugins/shopwise-core/inc/woocommerce.php",
    "/wp-content/plugins/shopwise-core/assets/js/custom.js",
    "/wp-content/mu-plugins/",
    "/wp-content/plugins/shopwise-core/",
]

KEYWORDS = (
    "accesstage",
    "accessstage",
    "cart-number",
    "removeitemcartpl",
    "redirectSuccess",
    "Pedido Accesstage",
    "easyunit",
)


def fetch(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "pm-hunt"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.headers.get("Content-Type"), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type") if e.headers else "", e.read()
    except Exception as ex:
        return None, str(ex), b""


def main():
    # discover shopwise theme slug from HTML
    st, ct, body = fetch("/")
    html = body.decode("utf-8", "replace")
    themes = sorted(set(re.findall(r"/wp-content/themes/([^/\"']+)/", html)))
    plugins_js = sorted(set(re.findall(r"/wp-content/plugins/([^/\"']+)/[^\"']+\.js", html)))
    print("themes on home", themes)
    print("plugin js on home", plugins_js[:40])

    st, ct, body = fetch("/finalizar-pagamento/")
    html = body.decode("utf-8", "replace")
    themes2 = sorted(set(re.findall(r"/wp-content/themes/([^/\"']+)/", html)))
    all_js = sorted(set(re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html, flags=re.I)))
    print("themes on checkout", themes2)
    print("all js count", len(all_js))
    for u in all_js:
        if any(k in u.lower() for k in ("shopwise", "theme", "custom", "checkout", "pay", "cart", "mask", "cf7")):
            print(" ", u)

    # Grep each JS for keywords
    for u in all_js:
        if u.startswith("//"):
            u = "https:" + u
        if u.startswith("/"):
            url = BASE + u
        elif u.startswith("http"):
            url = u
        else:
            continue
        if "googleapis" in url or "gstatic" in url or "recaptcha" in url or "googletagmanager" in url:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "pm-hunt"})
            with urllib.request.urlopen(req, timeout=30) as r:
                txt = r.read().decode("utf-8", "replace", errors="replace")
        except Exception as ex:
            continue
        low = txt.lower()
        hits = [k for k in KEYWORDS if k.lower() in low]
        if hits or "acces" in low:
            print("\nHIT FILE", url, "hits", hits, "len", len(txt))
            for k in hits + ["accesstage", "token", "authorization", "merchant"]:
                for m in re.finditer(r".{0,60}" + re.escape(k) + r".{0,60}", txt, flags=re.I):
                    print(" ", m.group(0).replace("\n", " ")[:160])

    # Try reading likely PHP via direct URL (usually forbidden)
    for path in CANDIDATES:
        st, ct, body = fetch(path)
        print(f"PROBE {path} -> {st} {ct} bytes={len(body or b'')}")


if __name__ == "__main__":
    main()
