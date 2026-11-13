# -*- coding: utf-8 -*-
"""Smoke: conta checking, sample product images, checkout overlay assets."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "scripts" / "_drive_image_report.json"

SITES = {
    "ot": "https://pellomenosoficialteste.companygenesis.com.br",
    "loja": "https://loja.pellomenos.com.br",
}

SAMPLES = [
    "/wp-content/uploads/pm-home/media/images/products/axila-cera.webp",
    "/wp-content/uploads/pm-home/media/images/products/male/axila-cera-masc.webp",
    "/wp-content/uploads/pm-home/media/images/products/cartao-presente.webp",
    "/wp-content/uploads/pm-home/account.js?v=conta-check1",
    "/wp-content/uploads/pm-home/conta.html",
    "/wp-content/uploads/pm-home/checkout-loading.js?v=load3",
    "/wp-content/uploads/pm-home/checkout-shell-c24.js?v=c35",
    "/wp-content/uploads/pm-home/checkout-brand.css?v=brand19",
]


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "pm-smoke/1.0", "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read()
    except Exception as err:
        return 0, str(err).encode()


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    print(
        "drive report replaced",
        len(report.get("replaced") or []),
        "missing",
        len(report.get("missing_official") or []),
        "gifts",
        report.get("skipped_gift_cards"),
    )

    for name, base in SITES.items():
        print("\n==", name, base)
        for path in SAMPLES:
            st, body = fetch(base + path)
            flags = []
            if "account.js" in path:
                flags.append(("paintChecking", b"paintChecking" in body))
                flags.append(("Verificando", "Verificando login".encode() in body))
            if "conta.html" in path:
                flags.append(("guest-hidden", b'data-pm-guest class="mx-auto hidden' in body))
                flags.append(("conta-check1", b"conta-check1" in body))
            if "checkout-loading" in path:
                flags.append(("pmCheckoutLoading", b"pmCheckoutLoading" in body))
                flags.append(("killTweensOf", b"killTweensOf" in body))
                flags.append(("no-pulseHolding", b"pulseHolding" not in body))
            if "checkout-shell" in path:
                flags.append(("openCheckoutLoading", b"openCheckoutLoading" in body))
                flags.append(("failsafe90", b"90000" in body))
            if "brand.css" in path:
                flags.append(("veil-gold", b"rgba(255, 187, 58, 0.16)" in body))
            if path.endswith(".webp"):
                flags.append(("bytes", len(body) if st == 200 else 0))
            print(path.split("/")[-1][:48], st, flags or len(body))

        # pages
        for page in ("/minha-conta/", "/finalizar-pagamento/"):
            st, body = fetch(base + page)
            text = body.decode("utf-8", "replace") if isinstance(body, (bytes, bytearray)) else ""
            markers = []
            if "minha-conta" in page:
                markers = [
                    ("conta-check1", "conta-check1" in text),
                    ("account.js", "account.js" in text),
                    ("maint?", "manuten" in text.lower() or "em breve" in text.lower()),
                ]
            else:
                markers = [
                    ("load3", "checkout-loading.js?v=load3" in text),
                    ("c35", "checkout-shell-c24.js?v=c35" in text),
                    ("brand19", "checkout-brand.css?v=brand19" in text),
                    ("maint?", "manuten" in text.lower()),
                ]
            print(page, st, markers)


if __name__ == "__main__":
    main()
