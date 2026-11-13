# -*- coding: utf-8 -*-
"""READ-ONLY: list Unidade options for Linha products on loja.pellomenos.com.br."""
from __future__ import annotations

import base64
import html
import json
import urllib.request
from pathlib import Path

LOJA = "https://loja.pellomenos.com.br"
ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "loja-readonly.env"
PRODUCTS = [
    (16394, "buco-linha-2"),
    (17216, "queixo-linha"),
    (17255, "faixa-linha"),
]


def load_env():
    d = {}
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def get(url, auth=None):
    h = {"User-Agent": "pm-peek-linha-readonly", "Accept": "application/json"}
    if auth:
        h["Authorization"] = "Basic " + auth
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def main():
    e = load_env()
    user = e.get("PM_LOJA_USER") or e.get("WP_USER") or e.get("LOJA_USER")
    pwd = e.get("PM_LOJA_APP_PASSWORD") or e.get("WP_APP_PASSWORD") or e.get("LOJA_APP_PASSWORD")
    auth = base64.b64encode(f"{user}:{pwd}".encode()).decode() if user and pwd else None
    print("loja", LOJA)
    print("auth_keys_present", bool(auth), "user", user)

    for pid, slug_hint in PRODUCTS:
        print("\n" + "=" * 60)
        # Public Store API first (no write; enough for unit list)
        p = get(f"{LOJA}/wp-json/wc/store/v1/products/{pid}")
        print(
            "STORE",
            p.get("id"),
            "|",
            p.get("slug") or slug_hint,
            "|",
            html.unescape(p.get("name") or ""),
            "| type=",
            p.get("type"),
        )
        unit_labels = []
        for a in p.get("attributes") or []:
            terms = a.get("terms") or a.get("options") or []
            names = []
            for t in terms:
                if isinstance(t, dict):
                    names.append(html.unescape(t.get("name") or t.get("label") or ""))
                else:
                    names.append(html.unescape(str(t)))
            label = a.get("name") or a.get("taxonomy") or "?"
            print(f"  attr {label}: {len(names)} terms")
            for n in names:
                print(f"   - {n}")
                if n:
                    unit_labels.append(n)
        vars_ = p.get("variations") or []
        print(f"  store variations={len(vars_)}")
        # Store API often returns only variation IDs; fetch each if needed
        detailed = []
        if vars_ and isinstance(vars_[0], int):
            for vid in vars_:
                try:
                    v = get(f"{LOJA}/wp-json/wc/store/v1/products/{vid}")
                    detailed.append(v)
                except Exception as ex:
                    print(f"   var {vid}: fetch_fail {ex}")
        elif vars_ and isinstance(vars_[0], dict):
            detailed = vars_

        for v in detailed:
            attrs = v.get("attributes") or {}
            if isinstance(attrs, dict):
                vals = [html.unescape(str(x)) for x in attrs.values()]
            elif isinstance(attrs, list):
                vals = []
                for x in attrs:
                    if isinstance(x, dict):
                        vals.append(
                            html.unescape(
                                str(x.get("value") or x.get("option") or x.get("name") or "")
                            )
                        )
                    else:
                        vals.append(html.unescape(str(x)))
            else:
                vals = [html.unescape(str(attrs))]
            price = v.get("prices", {}).get("price") if isinstance(v.get("prices"), dict) else v.get("price")
            print(
                f"   var {v.get('id')}: {vals} in_stock={v.get('is_in_stock')} price={price}"
            )

        print(f"  UNIQUE_UNITS={len(sorted(set(unit_labels)))}")
        for u in sorted(set(unit_labels)):
            print(f"  UNIT {u}")

        # Optional WC3 if auth still works
        if auth:
            try:
                p2 = get(f"{LOJA}/wp-json/wc/v3/products/{pid}", auth)
                opts = []
                for a in p2.get("attributes") or []:
                    if a.get("variation") or "unidad" in (a.get("name") or "").lower():
                        opts = a.get("options") or []
                        print(f"  WC3 attr '{a.get('name')}' options={len(opts)}")
                if opts:
                    for o in opts:
                        print(f"   WC3 - {o}")
            except Exception as ex:
                print("  WC3_skip", ex)


if __name__ == "__main__":
    main()
