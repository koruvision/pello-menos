# -*- coding: utf-8 -*-
"""Checklist readonly pré-publish Accesstage total sync."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "oficialteste.env"
DUMP = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "_hostinger_ot_dumps"
    / "shopwise-child__functions.php"
)


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def main():
    dump = DUMP.read_text(encoding="utf-8") if DUMP.is_file() else ""
    print(
        "dump",
        {
            "bytes": len(dump),
            "totalamount_charge": "totalamount')*100" in dump or 'totalamount"])*100' in dump,
            "calculate_totals": "calculate_totals()" in dump,
            "pedido_meta": "Pedido Accesstage" in dump,
        },
    )

    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()

    def get(path):
        req = urllib.request.Request(
            base + path,
            headers={"Authorization": "Basic " + auth, "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode())

    sn6 = get("/wp-json/code-snippets/v1/snippets/6")
    sn24 = get("/wp-json/code-snippets/v1/snippets/24")
    print(
        "sn6",
        {
            "active": sn6.get("active"),
            "shell_c37": "checkout-shell-c24.js?v=c37" in (sn6.get("code") or ""),
        },
    )
    print(
        "sn24",
        {
            "active": sn24.get("active"),
            "force_esquenta": "define('PM_BLACK_NOV_FORCE', 'esquenta')"
            in (sn24.get("code") or ""),
        },
    )

    form = get("/wp-json/contact-form-7/v1/contact-forms/1831")
    props = form.get("properties") or {}
    form_obj = props.get("form")
    content = form_obj.get("content") if isinstance(form_obj, dict) else form_obj
    text = str(content or "")
    print(
        "cf7",
        {
            f: (f in text)
            for f in ("totalamount", "fullvalue", "unit", "easyunit", "cart", "cartqtd")
        },
    )


if __name__ == "__main__":
    main()
