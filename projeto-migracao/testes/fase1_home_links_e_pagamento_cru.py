# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import BASE, OUT, REF, ENV_FILE, read_env, cart_state, clear_cart, choose_unit, add_current, local_cart  # noqa: E402
import json
import re
import time
import urllib.request
from pathlib import Path

REF = REF.read_text(encoding="utf-8")
routes = json.loads((Path(__file__).resolve().parents[2] / "wordpress-loja" / "pm-home" / "routes.json").read_text(encoding="utf-8"))
bust = str(int(time.time()))


def fetch(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "pm-fase1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status, r.read().decode("utf-8", "replace")


def markers(html):
    return {
        "form1831": "wpcf7-f1831" in html,
        "cpf_input": bool(re.search(r'name=["\']cpf["\']', html)),
        "cart_number": html.count("cart-number"),
        "mask": html.lower().count("jquery.mask"),
        "wpcf7cf": html.count("wpcf7cf"),
        "recaptcha": "recaptcha" in html.lower(),
        "shell": "checkout-shell" in html,
        "form_fields": sorted(set(re.findall(r'<input[^>]*name=["\']([^"\']+)["\']', html))),
    }


status, pay = fetch(f"/finalizar-pagamento/?pm={bust}")
now, ref = markers(pay), markers(REF)
print("PAY raw igual fase0:", now == ref)
for key in now:
    if now[key] != ref[key]:
        print("  difere", key, ref[key], "->", now[key])

status, home = fetch(f"/?pm={bust}")
hrefs = sorted(set(re.findall(r'href="(/produto/[^"]+)"', home)))
slugs = [h.strip("/").split("/")[-1] for h in hrefs]
# quais slugs do projeto existem como produto Woo no destino?
req = urllib.request.Request(BASE + "/wp-json/wc/store/v1/products?per_page=100", headers={"User-Agent": "pm"})
woo = json.loads(urllib.request.urlopen(req, timeout=120).read().decode("utf-8"))
woo_slugs = {p.get("slug") for p in woo}
in_routes = [s for s in slugs if s in routes]
in_woo = [s for s in slugs if s in woo_slugs]
print("links /produto/ distintos na home:", len(slugs))
print("  com arquivo em routes.json:", len(in_routes))
print("  com slug igual no WooCommerce:", len(in_woo))
print("  sem nada (404 na fase 1):", [s for s in slugs if s not in routes and s not in woo_slugs][:10])
print("  exemplo 404 na fase 1 e ok na fase 2:", [s for s in slugs if s in routes and s not in woo_slugs][:8])
