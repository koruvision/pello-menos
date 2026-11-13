# -*- coding: utf-8 -*-
"""Extrai scripts/inline do /finalizar-pagamento/ ligados a cartão/Accesstage."""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

BASE = "https://pellomenosoficialteste.companygenesis.com.br"
OUT = Path(__file__).resolve().parents[1] / "scripts" / "_cf7_pay_inline_extract.json"


def main():
    req = urllib.request.Request(BASE + "/finalizar-pagamento/", headers={"User-Agent": "pm"})
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode("utf-8", "replace")
    scripts = re.findall(r"<script([^>]*)>([\s\S]*?)</script>", html, flags=re.I)
    interesting = []
    for attrs, body in scripts:
        blob = (attrs + "\n" + body).lower()
        if any(
            k in blob
            for k in (
                "accesstage",
                "cart-number",
                "securitycode",
                "redirectsuccess",
                "totalamount",
                "holder",
                "removeitemcartpl",
                "wpcf7",
            )
        ):
            src = re.search(r'src=["\']([^"\']+)["\']', attrs or "", flags=re.I)
            interesting.append(
                {
                    "src": src.group(1) if src else None,
                    "inline_len": len(body or ""),
                    "inline_preview": (body or "")[:1500],
                    "has_accesstage": "accesstage" in blob,
                }
            )
    # also search for API-looking URLs
    urls = sorted(set(re.findall(r"https?://[^\s\"'<>]+", html)))
    apiish = [u for u in urls if any(x in u.lower() for x in ("acces", "pay", "token", "gateway", "api."))]
    OUT.write_text(
        json.dumps({"interesting_scripts": interesting, "apiish_urls": apiish}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("interesting scripts", len(interesting))
    for row in interesting:
        print(" src=", row["src"], "inline", row["inline_len"], "acces", row["has_accesstage"])
    print("apiish", apiish[:30])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
