# -*- coding: utf-8 -*-
"""READ-ONLY payment audit on oficialteste via WP App Password.

Does NOT submit checkout, charge cards, or change settings.
Prints structure / names only — redacts long secret-looking values.
"""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
OUT = ROOT / "projeto-migracao" / ".secrets" / "_audit_payment_oficialteste.json"


def load_env():
    d = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def redact(s: str, keep: int = 6) -> str:
    s = str(s or "")
    if len(s) <= keep * 2:
        if re.search(r"(sk_|pk_|key|secret|token|password|api)", s, re.I) and len(s) > 8:
            return s[:3] + "…REDACTED…"
        return s
    return s[:keep] + f"…({len(s)} chars)…" + s[-keep:]


def looks_secret(k: str, v) -> bool:
    kl = (k or "").lower()
    if any(x in kl for x in ("password", "secret", "token", "api_key", "apikey", "private", "auth")):
        return True
    if isinstance(v, str) and len(v) > 40 and re.fullmatch(r"[A-Za-z0-9_\-\.=+/]+", v or ""):
        return True
    return False


def scrub(obj, path=""):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if looks_secret(k, v) and isinstance(v, (str, int, float)):
                out[k] = f"<redacted len={len(str(v))}>"
            else:
                out[k] = scrub(v, f"{path}.{k}")
        return out
    if isinstance(obj, list):
        return [scrub(x, path) for x in obj[:200]]
    if isinstance(obj, str) and len(obj) > 2000:
        return obj[:800] + f"\n…TRUNC({len(obj)})…\n" + obj[-400:]
    return obj


def api(base, auth, method, path, timeout=90):
    url = base.rstrip("/") + path
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "Authorization": "Basic " + auth,
            "User-Agent": "pm-payment-audit-readonly",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            try:
                data = json.loads(body) if body[:1] in "[{" else body
            except Exception:
                data = body[:2000]
            return r.status, data, dict(r.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            data = json.loads(body)
        except Exception:
            data = body[:800]
        return e.code, data, dict(e.headers)


def main():
    e = load_env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    user = e["PM_OFICIALTESTE_USER"]
    pwd = e["PM_OFICIALTESTE_APP_PASSWORD"]
    auth = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    report = {"base": base, "user": user, "sections": {}}

    print("=== AUTH CHECK ===")
    st, me, _ = api(base, auth, "GET", "/wp-json/wp/v2/users/me")
    print("users/me", st, me.get("name") if isinstance(me, dict) else me)
    report["sections"]["me"] = scrub(me) if isinstance(me, dict) else me

    print("\n=== ACTIVE PLUGINS (payment-ish) ===")
    # try several endpoints
    plugins = None
    for path in (
        "/wp-json/wp/v2/plugins?status=active&per_page=100",
        "/wp-json/wp/v2/plugins?per_page=100",
    ):
        st, plugins, _ = api(base, auth, "GET", path)
        print("plugins", path, st, type(plugins).__name__, len(plugins) if isinstance(plugins, list) else "")
        if st == 200 and isinstance(plugins, list):
            break
    pay_plugins = []
    if isinstance(plugins, list):
        keys = (
            "pay",
            "pag",
            "cielo",
            "stone",
            "rede",
            "getnet",
            "stripe",
            "mercado",
            "asaas",
            "pix",
            "gateway",
            "checkout",
            "cart",
            "woo",
            "contact-form",
            "cf7",
            "cpf",
            "smtp",
            "snippet",
            "subscription",
            "recaptcha",
        )
        for p in plugins:
            slug = (p.get("plugin") or p.get("name") or "").lower()
            name = (p.get("name") or "").lower()
            if any(k in slug or k in name for k in keys):
                row = {
                    "plugin": p.get("plugin"),
                    "name": p.get("name"),
                    "status": p.get("status"),
                    "version": p.get("version"),
                }
                pay_plugins.append(row)
                print(" ", row["status"], row["plugin"], "|", row["name"], row["version"])
    report["sections"]["plugins_payment_ish"] = pay_plugins
    report["sections"]["plugins_count"] = len(plugins) if isinstance(plugins, list) else None

    print("\n=== WOO PAYMENT GATEWAYS ===")
    for path in (
        "/wp-json/wc/v3/payment_gateways",
        "/wp-json/wc/v2/payment_gateways",
        "/wp-json/wc/v3/settings/checkout",
        "/wp-json/wc/v3/settings",
    ):
        st, data, _ = api(base, auth, "GET", path)
        print(path, st)
        if st == 200:
            if isinstance(data, list):
                for g in data:
                    if isinstance(g, dict) and ("id" in g or "id" in str(g)):
                        print(
                            "  gateway",
                            g.get("id"),
                            "|",
                            g.get("title"),
                            "| enabled=",
                            g.get("enabled"),
                            "| method_title=",
                            g.get("method_title"),
                        )
                        # scrub settings
                        settings = g.get("settings") or {}
                        interesting = {}
                        for sk, sv in (settings.items() if isinstance(settings, dict) else []):
                            if isinstance(sv, dict):
                                val = sv.get("value")
                                interesting[sk] = {
                                    "label": sv.get("label") or sv.get("description"),
                                    "value": "<redacted>" if looks_secret(sk, val) else val,
                                }
                            else:
                                interesting[sk] = "<redacted>" if looks_secret(sk, sv) else sv
                        if interesting:
                            print("    settings keys:", list(interesting.keys())[:40])
                        report.setdefault("sections", {}).setdefault("gateways", []).append(
                            {
                                "id": g.get("id"),
                                "title": g.get("title"),
                                "enabled": g.get("enabled"),
                                "method_title": g.get("method_title"),
                                "method_description": (g.get("method_description") or "")[:300],
                                "order": g.get("order"),
                                "settings": interesting,
                            }
                        )
            else:
                report["sections"][path] = scrub(data)

    print("\n=== CF7 FORM 1831 ===")
    st, form, _ = api(base, auth, "GET", "/wp-json/contact-form-7/v1/contact-forms/1831")
    print("cf7 1831", st)
    if st == 200 and isinstance(form, dict):
        report["sections"]["cf7_1831_keys"] = list(form.keys())
        for key in ("title", "locale", "properties", "additional_settings"):
            if key in form:
                print(" key", key, type(form[key]).__name__)
        props = form.get("properties") or {}
        if isinstance(props, dict):
            print(" properties keys", list(props.keys()))
            report["sections"]["cf7_properties_keys"] = list(props.keys())
            for pk in (
                "form",
                "mail",
                "mail_2",
                "messages",
                "additional_settings",
            ):
                if pk in props:
                    val = props[pk]
                    if isinstance(val, dict):
                        print(f"\n--- properties.{pk} dict keys", list(val.keys()))
                        for mk, mv in val.items():
                            if isinstance(mv, str):
                                print(f"  {mk}:\n{mv[:2500]}")
                                if len(mv) > 2500:
                                    print(f"  …TRUNC total={len(mv)}")
                            else:
                                print(f"  {mk}:", scrub(mv))
                        report["sections"][f"cf7_{pk}"] = scrub(val)
                    elif isinstance(val, str):
                        print(f"\n--- properties.{pk} ---\n{val[:4000]}")
                        if len(val) > 4000:
                            print(f"…TRUNC total={len(val)}")
                        report["sections"][f"cf7_{pk}"] = val if len(val) < 15000 else val[:12000] + "\n…TRUNC…"
        # top-level mail sometimes
        for pk in ("form", "mail", "mail_2", "additional_settings"):
            if pk in form and pk not in (props or {}):
                print(f"\n--- top.{pk} ---")
                print(str(form[pk])[:3000])
                report["sections"][f"cf7_top_{pk}"] = scrub(form[pk])

    print("\n=== CF7CF / META FOR FORM ===")
    # post meta for contact form CPT
    st, posts, _ = api(
        base,
        auth,
        "GET",
        "/wp-json/wp/v2/wpcf7_contact_form/1831?context=edit",
    )
    print("wpcf7_contact_form edit", st)
    if st == 200 and isinstance(posts, dict):
        meta = posts.get("meta") or {}
        print(" meta keys", list(meta.keys())[:50] if isinstance(meta, dict) else type(meta))
        report["sections"]["cf7_post_meta_keys"] = list(meta.keys()) if isinstance(meta, dict) else None
        # search unit-related
        if isinstance(meta, dict):
            for k, v in meta.items():
                ks = k.lower()
                if any(x in ks for x in ("cf7cf", "unit", "pay", "condition", "wpcf7cf")):
                    print(" meta", k, "=", redact(json.dumps(v, ensure_ascii=False)[:500]))
            report["sections"]["cf7_post_meta"] = scrub(meta)

    print("\n=== CODE SNIPPETS (payment keywords) ===")
    for path in (
        "/wp-json/code-snippets/v1/snippets?per_page=100",
        "/wp-json/wp/v2/code-snippets?per_page=100",
        "/wp-json/snippet/v1/snippets?per_page=100",
    ):
        st, snips, _ = api(base, auth, "GET", path)
        print(path, st, type(snips).__name__)
        if st == 200 and isinstance(snips, list):
            report["sections"]["snippets_endpoint"] = path
            hits = []
            for s in snips:
                code = s.get("code") or s.get("content") or ""
                name = s.get("name") or s.get("title") or ""
                blob = (name + "\n" + str(code)).lower()
                if any(
                    k in blob
                    for k in (
                        "pay",
                        "pag",
                        "cielo",
                        "stone",
                        "cart-number",
                        "wpcf7",
                        "gateway",
                        "charge",
                        "credit",
                        "unit",
                        "pedido",
                        "order",
                        "recipient",
                        "split",
                    )
                ):
                    hits.append(
                        {
                            "id": s.get("id"),
                            "name": name,
                            "active": s.get("active") or s.get("status"),
                            "code_len": len(str(code)),
                            "code_preview": str(code)[:1500],
                            "mentions_unit": "unit" in blob,
                            "mentions_pay": any(
                                k in blob for k in ("pay", "pag", "cielo", "stone", "gateway", "charge")
                            ),
                        }
                    )
                    print(
                        " SNIP",
                        s.get("id"),
                        name,
                        "active=",
                        s.get("active"),
                        "len=",
                        len(str(code)),
                        "unit=",
                        "unit" in blob,
                    )
            report["sections"]["snippets_hits"] = hits
            break

    print("\n=== RECENT ORDERS (payment_method + unit meta) ===")
    st, orders, _ = api(
        base,
        auth,
        "GET",
        "/wp-json/wc/v3/orders?per_page=20&orderby=date&order=desc",
    )
    print("orders", st, len(orders) if isinstance(orders, list) else orders)
    order_rows = []
    if isinstance(orders, list):
        for o in orders:
            meta = {m.get("key"): m.get("value") for m in (o.get("meta_data") or []) if isinstance(m, dict)}
            unit_keys = {k: v for k, v in meta.items() if "unit" in (k or "").lower() or "loja" in (k or "").lower() or "unidade" in (k or "").lower()}
            line_units = []
            for item in o.get("line_items") or []:
                attrs = item.get("meta_data") or []
                for a in attrs:
                    if isinstance(a, dict) and "unidad" in (a.get("key") or a.get("display_key") or "").lower():
                        line_units.append(a.get("display_value") or a.get("value"))
                # variation attrs
                for a in item.get("meta_data") or []:
                    pass
            row = {
                "id": o.get("id"),
                "status": o.get("status"),
                "total": o.get("total"),
                "payment_method": o.get("payment_method"),
                "payment_method_title": o.get("payment_method_title"),
                "transaction_id": redact(o.get("transaction_id") or ""),
                "created_via": o.get("created_via"),
                "customer_note": (o.get("customer_note") or "")[:200],
                "unit_meta": scrub(unit_keys),
                "line_units": line_units[:10],
                "line_items": [
                    {
                        "name": li.get("name"),
                        "product_id": li.get("product_id"),
                        "variation_id": li.get("variation_id"),
                        "sku": li.get("sku"),
                        "total": li.get("total"),
                        "meta": [
                            {
                                "key": m.get("display_key") or m.get("key"),
                                "value": m.get("display_value") or m.get("value"),
                            }
                            for m in (li.get("meta_data") or [])[:8]
                        ],
                    }
                    for li in (o.get("line_items") or [])[:5]
                ],
            }
            order_rows.append(row)
            print(
                " order",
                row["id"],
                row["status"],
                "pay=",
                row["payment_method"],
                "/",
                row["payment_method_title"],
                "total=",
                row["total"],
                "units=",
                line_units or unit_keys,
            )
    report["sections"]["orders_sample"] = order_rows

    print("\n=== WC SYSTEM STATUS / SETTINGS PAYMENT KEYWORDS ===")
    for path in (
        "/wp-json/wc/v3/system_status",
        "/wp-json/wc/v3/settings/general",
        "/wp-json/wc/v3/data/continents",
    ):
        st, data, _ = api(base, auth, "GET", path)
        print(path, st)
        if path.endswith("system_status") and st == 200 and isinstance(data, dict):
            active = data.get("active_plugins") or []
            print(" active_plugins", len(active))
            payish = [
                p
                for p in active
                if any(
                    k in json.dumps(p).lower()
                    for k in ("pay", "pag", "cielo", "stone", "rede", "stripe", "mercado", "pix", "gateway")
                )
            ]
            print(" payish plugins from status:", len(payish))
            for p in payish:
                print("  ", p.get("plugin") if isinstance(p, dict) else p)
            report["sections"]["system_status_pay_plugins"] = scrub(payish)
            report["sections"]["system_status_environment"] = scrub(
                {
                    "home_url": (data.get("environment") or {}).get("home_url"),
                    "site_url": (data.get("environment") or {}).get("site_url"),
                    "version": (data.get("environment") or {}).get("version"),
                    "external_object_cache": (data.get("environment") or {}).get("external_object_cache"),
                }
            )

    print("\n=== FINALIZAR-PAGAMENTO HTML (scripts / gateway hints) ===")
    req = urllib.request.Request(
        base + "/finalizar-pagamento/?pm=pay-audit",
        headers={"User-Agent": "pm-payment-audit-readonly"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        html = r.read().decode("utf-8", "replace")
    print("html len", len(html))
    # script srcs
    srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, flags=re.I)
    pay_srcs = [
        s
        for s in srcs
        if any(
            k in s.lower()
            for k in (
                "pay",
                "pag",
                "cielo",
                "stone",
                "mask",
                "cf7",
                "checkout",
                "recaptcha",
                "cpf",
                "woo",
            )
        )
    ]
    print("pay-ish script srcs", len(pay_srcs))
    for s in pay_srcs:
        print(" ", s)
    # inline keywords
    for kw in (
        "pagarme",
        "pagar.me",
        "cielo",
        "stone",
        "getnet",
        "rede",
        "stripe",
        "mercadopago",
        "asaas",
        "iugu",
        "vindi",
        "yapay",
        "koin",
        "maxipago",
        "e-rede",
        "erede",
        "adyen",
        "braintree",
        "apiKey",
        "encryptionKey",
        "publicKey",
        "merchant",
        "recipient",
        "split",
        "unit",
        "easyunit",
        "cart-number",
    ):
        c = html.lower().count(kw.lower())
        if c:
            print(f"  keyword '{kw}': {c}")
    # extract inline script snippets mentioning charge/unit
    inlines = re.findall(r"<script(?![^>]+src=)[^>]*>(.*?)</script>", html, flags=re.I | re.S)
    print("inline scripts", len(inlines))
    interesting_inline = []
    for i, code in enumerate(inlines):
        low = code.lower()
        if any(
            k in low
            for k in (
                "unit",
                "cart-number",
                "pagarme",
                "cielo",
                "stone",
                "charge",
                "payment",
                "gateway",
                "token",
                "encrypt",
                "installment",
            )
        ):
            interesting_inline.append({"index": i, "len": len(code), "preview": code[:2000]})
            print(f" inline[{i}] len={len(code)} preview:\n{code[:1200]}\n---")
    report["sections"]["checkout_html"] = {
        "len": len(html),
        "pay_script_srcs": pay_srcs,
        "keyword_counts": {
            kw: html.lower().count(kw.lower())
            for kw in (
                "pagarme",
                "cielo",
                "stone",
                "getnet",
                "rede",
                "stripe",
                "mercadopago",
                "asaas",
                "recipient",
                "split",
                "easyunit",
                "cart-number",
            )
            if html.lower().count(kw.lower())
        },
        "interesting_inline": interesting_inline[:20],
    }

    # CF7CF options from HTML
    m = re.search(r'name="_wpcf7cf_options"[^>]*value="([^"]*)"', html)
    if m:
        import html as htmlmod

        raw = htmlmod.unescape(m.group(1))
        try:
            opts = json.loads(raw)
            conds = opts.get("conditions") or opts
            print("\nCF7CF conditions count", len(conds) if isinstance(conds, list) else type(conds))
            # summarize unit-related conditions
            unit_conds = []
            blob = json.dumps(conds, ensure_ascii=False)
            report["sections"]["cf7cf_options_preview"] = scrub(conds) if isinstance(conds, list) else scrub(opts)
            print("CF7CF blob has 'unit'", "unit" in blob.lower())
            print("CF7CF blob has flamengo/copacabana", "flamengo" in blob.lower(), "copacabana" in blob.lower())
        except Exception as ex:
            print("CF7CF parse fail", ex)

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\nWROTE", OUT)


if __name__ == "__main__":
    main()
