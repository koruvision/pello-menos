# -*- coding: utf-8 -*-
"""Publica UI de labels Black Nov (carrinho/checkout) no OficialTeste."""
from __future__ import annotations

import base64
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
HOME_SNIPPET = ROOT / "scripts" / "pm_home_snippet.php"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"

FILES = [
    "black-nov-campaign.js",
    "black-nov-campaign.json",
    "cart.js",
    "cart-related.json",
    "product.js",
    "checkout-shell-c24.js",
    "checkout-shell.js",
    "checkout-brand.css",
]


def read_env():
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


def call(cfg, method, path, payload=None, raw=None, content_type="application/json", timeout=180):
    data = raw if raw is not None else (None if payload is None else json.dumps(payload).encode("utf-8"))
    token = base64.b64encode(f"{cfg['user']}:{cfg['password']}".encode()).decode()
    req = urllib.request.Request(
        cfg["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + token,
            "User-Agent": "pm-cart-labels/1.0",
            "Content-Type": content_type,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body[:1] in "[{" else body)


def patch_carrinho_html(html: str, asset_base: str) -> str:
    force = "<script>window.__PM_BLACK_PHASE__='esquenta';</script>"
    black = f'<script src="{asset_base}/black-nov-campaign.js?v=black2"></script>'
    cart = f'<script src="{asset_base}/cart.js?v=cart26"></script>'
    # bump existing cart.js query
    html = re.sub(
        r'src="[^"]*/pm-home/cart\.js\?v=[^"]+"',
        f'src="{asset_base}/cart.js?v=cart26"',
        html,
    )
    if "black-nov-campaign.js" not in html:
        inject = force + "\n" + black + "\n" + cart
        if "cart.js?v=cart26" in html:
            html = html.replace(cart, inject, 1)
        else:
            html = html.replace("</body>", inject + "\n</body>", 1)
    else:
        html = re.sub(
            r'src="[^"]*/pm-home/black-nov-campaign\.js\?v=[^"]+"',
            f'src="{asset_base}/black-nov-campaign.js?v=black2"',
            html,
        )
        if "__PM_BLACK_PHASE__" not in html:
            html = html.replace(black, force + "\n" + black, 1)
    return html


def main() -> None:
    cfg = read_env()
    dest = cfg["url"] + "/wp-content/uploads/pm-home"
    print("destino", cfg["url"])

    # Puxa carrinho.html atual (se existir) e bumpa scripts
    try:
        st, raw = call(cfg, "GET", "/wp-content/uploads/pm-home/carrinho.html")
        if st == 200 and isinstance(raw, str) and "<html" in raw.lower():
            (PM / "carrinho.html").write_text(patch_carrinho_html(raw, dest), encoding="utf-8")
            print("carrinho.html patched from OT")
        else:
            print("carrinho.html GET unexpected", st)
    except Exception as err:
        print("carrinho.html fetch skip", err)

    files = [n for n in FILES if (PM / n).is_file()]
    if (PM / "carrinho.html").is_file():
        files.append("carrinho.html")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in files:
            text = (PM / name).read_text(encoding="utf-8")
            text = text.replace(CLONE, dest).replace(
                "https://loja.pellomenos.com.br/wp-content/uploads/pm-home", dest
            )
            z.writestr(name, text.encode("utf-8"))
    st, res = call(
        cfg,
        "POST",
        "/wp-json/pm-home/v1/bundle",
        raw=buf.getvalue(),
        content_type="application/zip",
        timeout=300,
    )
    print("bundle", st, res)

    # Atualiza snippet pm-home (enqueue shell c34 + black-nov)
    code = HOME_SNIPPET.read_text(encoding="utf-8")
    st, rows = call(cfg, "GET", "/wp-json/code-snippets/v1/snippets")
    updated = False
    if isinstance(rows, list):
        for row in rows:
            sn_id = row.get("id")
            st, sn = call(cfg, "GET", f"/wp-json/code-snippets/v1/snippets/{sn_id}")
            if not isinstance(sn, dict):
                continue
            existing = sn.get("code") or ""
            if "pm_home_enqueue_shell" not in existing:
                continue
            payload = {
                "name": sn.get("name"),
                "code": code,
                "scope": sn.get("scope") or "global",
                "active": True,
            }
            st, saved = call(cfg, "PUT", f"/wp-json/code-snippets/v1/snippets/{sn_id}", payload)
            print(
                "home snippet",
                sn.get("name"),
                st,
                saved.get("id") if isinstance(saved, dict) else saved,
            )
            updated = True
            break
    if not updated:
        print("WARN: pm-home snippet com enqueue_shell não encontrado")

    for probe in (
        "/wp-content/uploads/pm-home/cart.js",
        "/wp-content/uploads/pm-home/black-nov-campaign.js",
        "/wp-content/uploads/pm-home/checkout-shell-c24.js",
        "/wp-content/uploads/pm-home/checkout-brand.css",
    ):
        st, body = call(cfg, "GET", probe)
        text = body if isinstance(body, str) else ""
        checks = []
        if "cart.js" in probe:
            checks.append(("catalogPriced", "catalogPriced" in text))
            checks.append(("Esquenta label", "Desconto Esquenta Black" in text or "discountLabel" in text))
        if "black-nov" in probe:
            checks.append(("discountLabel fn", "function discountLabel" in text))
        if "c24" in probe:
            checks.append(("campaignSavings", "campaignSavings" in text))
            checks.append(("Esquenta", "Desconto Esquenta Black" in text))
        if "brand" in probe:
            checks.append(("line__list", "pm-checkout-line__list" in text))
        print(probe, st, checks)


if __name__ == "__main__":
    main()
