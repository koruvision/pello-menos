# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import re
import urllib.request
from pathlib import Path

OT = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "oficialteste.env"


def env():
    e = {}
    for line in OT.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def call(base, auth, path):
    req = urllib.request.Request(
        base + path,
        headers={"Authorization": "Basic " + auth, "Accept": "application/json", "User-Agent": "pm"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def main():
    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()

    for sid in (6, 24):
        sn = call(base, auth, f"/wp-json/code-snippets/v1/snippets/{sid}")
        code = sn.get("code") or ""
        print(f"\n===== SNIPPET {sid} {sn.get('name')} active={sn.get('active')} bytes={len(code)} =====")
        for pat in (
            r"FORCE.{0,40}",
            r"__PM_BLACK_PHASE__.{0,60}",
            r"checkout-shell[^\s\"']+",
            r"blackWeekStart.{0,40}",
            r"set_price\([^)]{0,80}",
            r"pm_catalog",
        ):
            ms = re.findall(pat, code)
            print(pat, "->", ms[:5])
        # print FORCE region
        i = code.find("FORCE")
        if i >= 0:
            print("FORCE CONTEXT:\n", code[max(0, i - 80) : i + 200])

    form = call(base, auth, "/wp-json/contact-form-7/v1/contact-forms/1831")
    props = form.get("properties") or form
    form_html = props.get("form") if isinstance(props, dict) else None
    if isinstance(form_html, dict):
        form_html = form_html.get("body") or json.dumps(form_html)
    if not isinstance(form_html, str):
        # dump keys
        print("CF7 keys", list(form.keys()) if isinstance(form, dict) else type(form))
        if isinstance(props, dict):
            print("props keys", list(props.keys()))
            for k, v in props.items():
                print(" prop", k, type(v), (str(v)[:120] if not isinstance(v, dict) else list(v.keys())[:20]))
        form_html = json.dumps(form)[:2000]
    print("\n===== CF7 form sample =====")
    print(str(form_html)[:1500])
    text = str(form_html)
    for field in (
        "totalamount",
        "fullvalue",
        "cart",
        "cartqtd",
        "cupom",
        "cupomamount",
        "unit",
        "easyunit",
        "cart-number",
        "securityCode",
    ):
        print(field, "PRESENT" if field in text else "MISSING")


if __name__ == "__main__":
    main()
