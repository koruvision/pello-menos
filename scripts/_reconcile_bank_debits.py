# -*- coding: utf-8 -*-
"""Lista pedidos recentes loja (+OT se env) e marca valores próximos de 2 / 3,99 / 19,95."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {200, 190, 199, 189, 399, 1995, 1950, 2000, 525, 425, 1200}


def load_env(name):
    path = ROOT / "projeto-migracao" / ".secrets" / name
    if not path.is_file():
        return None
    e = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def list_orders(label, url, user, password, per_page=40):
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = urllib.request.Request(
        url.rstrip("/") + f"/wp-json/wc/v3/orders?per_page={per_page}&orderby=date&order=desc",
        headers={"Authorization": "Basic " + auth, "Accept": "application/json", "User-Agent": "pm-recon"},
    )
    orders = json.loads(urllib.request.urlopen(req, timeout=90).read().decode())
    print(f"\n=== {label} ({url}) ===")
    for o in orders:
        total = o.get("total") or "0"
        cents = int(round(float(total) * 100))
        meta = {m.get("key"): m.get("value") for m in (o.get("meta_data") or [])}
        email = ((o.get("billing") or {}).get("email") or "")[:50]
        lines = ", ".join(
            f"{li.get('name','')[:28]}={li.get('total')}" for li in (o.get("line_items") or [])
        )
        flag = ""
        if cents in TARGETS or abs(cents - 399) <= 1 or abs(cents - 1995) <= 5 or abs(cents - 200) <= 1:
            flag = " <<<"
        print(
            f"{o['id']} {o.get('date_created')} {o.get('status')} R${total} "
            f"acc={meta.get('Pedido Accesstage') or '-'} cf7={meta.get('_pm_cf7_totalamount') or '-'} "
            f"{email} | {lines}{flag}"
        )


def main():
    loja = load_env("loja.env")
    if loja:
        list_orders(
            "LOJA",
            loja["PM_LOJA_URL"],
            loja["PM_LOJA_USER"],
            loja["PM_LOJA_APP_PASSWORD"],
        )
    ot = load_env("oficialteste.env")
    if ot:
        list_orders(
            "OT",
            ot["PM_OFICIALTESTE_URL"],
            ot["PM_OFICIALTESTE_USER"],
            ot["PM_OFICIALTESTE_APP_PASSWORD"],
        )


if __name__ == "__main__":
    main()
