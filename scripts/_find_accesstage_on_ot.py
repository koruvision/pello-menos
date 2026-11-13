# -*- coding: utf-8 -*-
"""Procura Accesstage no OficialTeste: plugins REST + assets públicos no checkout."""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
OUT = ROOT / "scripts" / "_find_accesstage_on_ot.json"

KEYWORDS = (
    "accesstage",
    "accessstage",
    "acces stage",
    "pedido accesstage",
    "cart-number",
    "securitycode",
    "removeitemcartpl",
    "redirectsuccess",
)


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


def call(c, path, auth=True):
    headers = {"User-Agent": "pm-find-acc/1.0", "Accept": "*/*"}
    if auth:
        tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
        headers["Authorization"] = "Basic " + tok
        headers["Accept"] = "application/json"
    req = urllib.request.Request(c["url"] + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            return r.status, r.headers.get("Content-Type"), body
    except urllib.error.HTTPError as err:
        return err.code, err.headers.get("Content-Type") if err.headers else "", err.read()
    except Exception as ex:
        return 0, str(ex), b""


def main():
    c = cfg()
    report = {"url": c["url"], "plugins": [], "themes": [], "checkout_js_hits": [], "probes": []}

    st, _, body = call(c, "/wp-json/wp/v2/plugins")
    plugins = json.loads(body.decode()) if body[:1] in b"[{" else []
    print("plugins", st, len(plugins) if isinstance(plugins, list) else plugins)
    if isinstance(plugins, list):
        for p in plugins:
            blob = " ".join(
                [
                    str(p.get("plugin") or ""),
                    str(p.get("name") or ""),
                    str(p.get("description") or "")[:200],
                    str(p.get("author") or ""),
                ]
            ).lower()
            interesting = any(
                x in blob
                for x in (
                    "acces",
                    "access",
                    "stage",
                    "pay",
                    "gateway",
                    "cf7",
                    "contact",
                    "woo",
                    "checkout",
                    "vivid",
                )
            )
            row = {
                "plugin": p.get("plugin"),
                "name": p.get("name"),
                "status": p.get("status"),
                "interesting": interesting,
            }
            if interesting or "acces" in blob or "stage" in blob:
                report["plugins"].append(row)
                print("PLUGIN", row["status"], row["plugin"], "|", row["name"])

    st, _, body = call(c, "/wp-json/wp/v2/themes")
    themes = json.loads(body.decode()) if body[:1] in b"[{" else []
    if isinstance(themes, list):
        for t in themes:
            row = {
                "stylesheet": t.get("stylesheet"),
                "status": t.get("status"),
                "name": t.get("name"),
            }
            report["themes"].append(row)
            print("THEME", row["status"], row["stylesheet"], row["name"])

    # Checkout HTML: scripts + inline
    st, _, body = call(c, "/finalizar-pagamento/", auth=False)
    html = body.decode("utf-8", "replace")
    print("checkout html", st, len(html))
    scripts = sorted(set(re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html, flags=re.I)))
    report["checkout_script_count"] = len(scripts)
    inline_hits = [k for k in KEYWORDS if k in html.lower()]
    report["checkout_html_keyword_hits"] = inline_hits
    print("html keyword hits", inline_hits)

    for u in scripts:
        if u.startswith("//"):
            u = "https:" + u
        if u.startswith("/"):
            url = c["url"] + u
        elif u.startswith("http"):
            url = u
        else:
            continue
        low_u = url.lower()
        if any(x in low_u for x in ("googleapis", "gstatic", "recaptcha", "googletagmanager", "facebook", "hotjar")):
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "pm-find-acc/1.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                txt = r.read().decode("utf-8", "replace")
        except Exception as ex:
            continue
        low = txt.lower()
        hits = [k for k in KEYWORDS if k in low]
        if hits or "accesstage" in low or "accessstage" in low:
            report["checkout_js_hits"].append({"url": url, "hits": hits, "bytes": len(txt)})
            print("JS HIT", url, hits)

    # Direct probes (usually 403 for PHP)
    for path in (
        "/wp-content/mu-plugins/",
        "/wp-content/plugins/",
        "/wp-content/plugins/accesstage/",
        "/wp-content/plugins/accesstage-payment/",
        "/wp-content/plugins/woocommerce-accesstage/",
        "/wp-content/mu-plugins/accesstage.php",
        "/wp-content/mu-plugins/accesstage/",
        "/wp-json/",
    ):
        st, ct, body = call(c, path, auth=False)
        report["probes"].append({"path": path, "status": st, "ctype": ct, "bytes": len(body or b"")})
        print("PROBE", path, st, ct, len(body or b""))

    # Routes that mention payment
    st, _, body = call(c, "/wp-json/")
    index = json.loads(body.decode()) if body[:1] == b"{" else {}
    routes = sorted((index.get("routes") or {}).keys()) if isinstance(index, dict) else []
    pay_routes = [r for r in routes if any(x in r.lower() for x in ("acces", "pay", "cf7", "contact-form", "woo"))]
    report["wp_json_payish_routes"] = pay_routes[:80]
    print("payish routes", len(pay_routes))
    for r in pay_routes[:40]:
        print(" ", r)

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
