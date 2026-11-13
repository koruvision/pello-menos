# -*- coding: utf-8 -*-
"""Audita preços Esquenta: vitrine HTML, Woo regular/sale, expectativa de campanha."""
from __future__ import annotations

import base64
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
DATA = ROOT / "src" / "lib" / "data.ts"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return {
        "url": e["PM_LOJA_URL"].rstrip("/"),
        "user": e["PM_LOJA_USER"],
        "password": e["PM_LOJA_APP_PASSWORD"],
    }


def call(c, path):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        headers={
            "Authorization": "Basic " + tok,
            "Accept": "application/json",
            "User-Agent": "pm-esquenta-audit",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def http_get(url: str) -> str:
    req = urllib.request.Request(
        url, headers={"User-Agent": "pm-esquenta-audit", "Cache-Control": "no-cache"}
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("utf-8", "replace")


def parse_seed_original(pid: str) -> int | None:
    text = DATA.read_text(encoding="utf-8")
    # { id: "axila-cera", ... originalCents: 1234,
    m = re.search(
        rf'id:\s*"{re.escape(pid)}"[^}}]*?originalCents:\s*(\d+)',
        text,
    )
    return int(m.group(1)) if m else None


def expect_esquenta(original: int, family: str, multi: bool = False) -> int:
    if family == "laser":
        rate = 0.65 if multi else 0.6
    else:
        rate = 0.2 if multi else 0.15
    return int(round(original * (1 - rate)))


def money(cents: int) -> str:
    return f"R$ {cents/100:.2f}".replace(".", ",")


def main():
    c = cfg()
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    samples = [
        ("axila-cera", "cera_esf"),
        ("axilas-laser", "laser"),
        ("bracos-laser", "laser"),
        ("abdomen-cera", "cera_esf"),
        ("buco-linha", "excluded"),
    ]

    print("=== PHASE CHECK (black-nov json live) ===")
    try:
        j = http_get(c["url"] + "/wp-content/uploads/pm-home/black-nov-campaign.json")
        cfgj = json.loads(j)
        print("esquenta", cfgj.get("esquentaStart"), "->", cfgj.get("esquentaEnd"))
        print("black", cfgj.get("blackWeekStart"), "->", cfgj.get("blackWeekEnd"))
    except Exception as err:
        print("json fail", err)

    print("\n=== HOME HTML price sniff ===")
    home = http_get(c["url"] + "/")
    for needle in ("15% OFF", "60% OFF", "Desconto Esquenta", "Esquenta", "5% OFF", "oldPrice", "line-through"):
        print(needle, home.count(needle))
    # product card prices near axila
    for pid in ("axila-cera", "axilas-laser"):
        idx = home.find(pid)
        snippet = home[max(0, idx - 200) : idx + 400] if idx >= 0 else ""
        prices = re.findall(r"R\$\s*[\d.]+,\d{2}", snippet)
        print("home near", pid, "found", idx >= 0, "prices", prices[:6])

    print("\n=== PDP + WOO vs EXPECTED ===")
    for catalog_id, family in samples:
        original = parse_seed_original(catalog_id)
        info = bridge.get(catalog_id) or {}
        woo_id = info.get("productId")
        print(f"\n-- {catalog_id} family={family} originalCents={original} woo={woo_id}")
        if original:
            if family == "excluded":
                print("  expect catalog: 5% or full (linha excluded)")
            else:
                print(
                    "  expect esquenta any",
                    money(expect_esquenta(original, family, False)),
                    "multi",
                    money(expect_esquenta(original, family, True)),
                    "vs 5% only",
                    money(int(round(original * 0.95))),
                )
        if woo_id:
            p = call(c, f"/wp-json/wc/v3/products/{woo_id}")
            print(
                "  woo regular",
                p.get("regular_price"),
                "sale",
                p.get("sale_price"),
                "price",
                p.get("price"),
            )
            # meta catalog
            meta = {m.get("key"): m.get("value") for m in (p.get("meta_data") or [])}
            print("  _pm_catalog_id", meta.get("_pm_catalog_id"))
        # live PDP
        try:
            html = http_get(c["url"] + f"/produto/{catalog_id}/")
        except Exception:
            slug = info.get("slug") or catalog_id
            html = http_get(c["url"] + f"/produto/{slug}/")
        # data attributes often used
        attrs = {
            k: v
            for k, v in re.findall(
                r'data-(rj-sale|sp-sale|rj-regular|sp-regular|sale|regular|price)="([^"]+)"',
                html,
            )
        }
        print("  pdp data-*", attrs)
        prices = re.findall(r"R\$\s*[\d.]+,\d{2}", html)
        print("  pdp prices sample", prices[:8])
        # campaign badge
        for b in ("15%", "60%", "20%", "65%", "5%"):
            if b in html:
                print("  badge hit", b)


if __name__ == "__main__":
    main()
