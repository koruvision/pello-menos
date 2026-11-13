# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import BASE, OUT, REF, ENV_FILE, read_env, cart_state, clear_cart, choose_unit, add_current, local_cart  # noqa: E402
import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ENV = read_env()
TOKEN = base64.b64encode(f"{ENV['PM_OFICIALTESTE_USER']}:{ENV['PM_OFICIALTESTE_APP_PASSWORD']}".encode()).decode()
report = {}


def get(path, auth=False, timeout=60):
    headers = {"User-Agent": "pm-fase0"}
    if auth:
        headers["Authorization"] = "Basic " + TOKEN
    req = urllib.request.Request(BASE + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
            return response.status, dict(response.headers), body
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers or {}), error.read().decode("utf-8", "replace")
    except Exception as error:
        return 0, {}, str(error)


status, headers, home = get("/")
report["home"] = {
    "status": status,
    "php": headers.get("X-Powered-By"),
    "bytes": len(home),
    "themes": sorted(set(re.findall(r"/wp-content/themes/([^/]+)/", home))),
    "plugins": sorted(set(re.findall(r"/wp-content/plugins/([^/]+)/", home))),
    "title": (re.search(r"<title>(.*?)</title>", home, re.S) or [None, ""])[1][:120] if "<title>" in home else "",
    "hello_world": "Hello world" in home,
}
(OUT / "oficialteste-home.html").write_text(home, encoding="utf-8")

status, headers, pay = get("/finalizar-pagamento/")
report["pagamento"] = {
    "status": status,
    "bytes": len(pay),
    "form1831": "wpcf7-f1831" in pay,
    "cpf_input": bool(re.search(r'name=["\']cpf["\']', pay)),
    "cpf_shortcode": "[cpf" in pay,
    "cart_number": pay.count("cart-number"),
    "mask": pay.lower().count("jquery.mask"),
    "wpcf7cf": pay.count("wpcf7cf"),
    "recaptcha": pay.lower().count("recaptcha"),
    "plugins": sorted(set(re.findall(r"/wp-content/plugins/([^/]+)/", pay))),
}
(OUT / "oficialteste-pay.html").write_text(pay, encoding="utf-8")

for path, key in (
    ("/carrinho/", "carrinho"),
    ("/minha-conta/", "conta"),
    ("/masculino/", "masculino"),
    ("/loja/", "loja"),
    ("/produto/axila-cera/", "produto_axila"),
    ("/wp-content/uploads/pm-home/home.html", "pm_home_asset"),
):
    status, headers, body = get(path)
    report[key] = {"status": status, "bytes": len(body), "woo": "woocommerce" in body.lower(), "pm_home": "pm-home" in body}

status, headers, rest = get("/wp-json/")
namespaces = []
if status == 200:
    try:
        namespaces = json.loads(rest).get("namespaces", [])
    except json.JSONDecodeError:
        namespaces = ["parse-error"]
report["rest"] = {"status": status, "namespaces": namespaces}

status, headers, store = get("/wp-json/wc/store/v1/cart")
report["store_api"] = {"status": status, "body": store[:200]}

status, headers, me = get("/wp-json/wp/v2/users/me?context=edit", auth=True)
try:
    me_json = json.loads(me)
except json.JSONDecodeError:
    me_json = {"raw": me[:200]}
report["auth"] = {"status": status, "name": me_json.get("name"), "roles": me_json.get("roles"), "caps_edit_pages": (me_json.get("capabilities") or {}).get("edit_pages")}

status, headers, plugins = get("/wp-json/wp/v2/plugins", auth=True)
try:
    plugin_rows = json.loads(plugins)
except json.JSONDecodeError:
    plugin_rows = []
report["plugins_api"] = {"status": status, "count": len(plugin_rows) if isinstance(plugin_rows, list) else 0}
if isinstance(plugin_rows, list):
    report["plugins_list"] = sorted(f"{row.get('plugin')} [{row.get('status')}]" for row in plugin_rows if isinstance(row, dict))

status, headers, themes = get("/wp-json/wp/v2/themes?status=active", auth=True)
try:
    theme_rows = json.loads(themes)
except json.JSONDecodeError:
    theme_rows = []
report["theme_active"] = [row.get("stylesheet") for row in theme_rows if isinstance(row, dict)] if isinstance(theme_rows, list) else themes[:200]

status, headers, snippets = get("/wp-json/code-snippets/v1/snippets", auth=True)
report["code_snippets"] = {"status": status, "body": snippets[:300]}

status, headers, products = get("/wp-json/wc/store/v1/products?per_page=5")
try:
    product_rows = json.loads(products)
except json.JSONDecodeError:
    product_rows = []
report["products"] = {"status": status, "sample": [row.get("name") for row in product_rows[:5]] if isinstance(product_rows, list) else products[:200], "total_header": headers.get("X-WP-Total")}

status, headers, live = get.__globals__["urllib"].request.urlopen(
    urllib.request.Request("https://loja.pellomenos.com.br/", headers={"User-Agent": "pm-fase0"}), timeout=60
).status, None, None
report["loja_oficial_intacta"] = {"status": status}

(OUT / "fase0_oficialteste.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
