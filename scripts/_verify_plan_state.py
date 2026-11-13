# -*- coding: utf-8 -*-
from pathlib import Path
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def ok(label, cond):
    print(("OK" if cond else "FAIL"), label)
    return bool(cond)


def main():
    fails = 0
    acc = (ROOT / "wordpress-loja/pm-home/account.js").read_text(encoding="utf-8")
    conta = (ROOT / "wordpress-loja/pm-home/conta.html").read_text(encoding="utf-8")
    fails += not ok("account paintChecking", "paintChecking" in acc and "Verificando login" in acc)
    fails += not ok("account boot me", "paintChecking();" in acc and 'call("me")' in acc)
    fails += not ok("conta guest hidden", 'data-pm-guest class="mx-auto hidden' in conta)
    fails += not ok("conta-check1", "conta-check1" in conta)

    sync = (ROOT / "scripts/sync_drive_product_images.py").read_text(encoding="utf-8")
    fails += not ok("gift skip", "is_gift_card" in sync and "skipped_gift_cards" in sync)
    report = json.loads((ROOT / "scripts/_drive_image_report.json").read_text(encoding="utf-8"))
    fails += not ok("report replaced>=100", len(report.get("replaced") or []) >= 100)
    fails += not ok("report gifts", bool(report.get("skipped_gift_cards")))

    load = (ROOT / "wordpress-loja/pm-home/checkout-loading.js").read_text(encoding="utf-8")
    shell = (ROOT / "wordpress-loja/pm-home/checkout-shell-c24.js").read_text(encoding="utf-8")
    css = (ROOT / "wordpress-loja/pm-home/checkout-brand.css").read_text(encoding="utf-8")
    snip = (ROOT / "scripts/pm_home_snippet.php").read_text(encoding="utf-8")
    fails += not ok("overlay api", "pmCheckoutLoading" in load and "killTweensOf" in load and "pulseHolding" not in load)
    fails += not ok("shell failsafe", "openCheckoutLoading" in shell and "90000" in shell)
    fails += not ok("brand19 polish", "brand19" in snip and "rgba(255, 187, 58, 0.16)" in css)
    fails += not ok(
        "webp media",
        (ROOT / "public/images/products/axila-cera.webp").is_file()
        and (ROOT / "wordpress-loja/pm-home/media/images/products/axila-cera.webp").is_file(),
    )

    base = "https://pellomenosoficialteste.companygenesis.com.br"
    probes = [
        ("/wp-content/uploads/pm-home/account.js?v=conta-check1", b"paintChecking"),
        ("/wp-content/uploads/pm-home/conta.html", b"conta-check1"),
        ("/wp-content/uploads/pm-home/checkout-loading.js?v=load3", b"pmCheckoutLoading"),
        ("/wp-content/uploads/pm-home/checkout-shell-c24.js?v=c35", b"openCheckoutLoading"),
        ("/wp-content/uploads/pm-home/checkout-brand.css?v=brand19", b"rgba(255, 187, 58, 0.16)"),
        ("/wp-content/uploads/pm-home/media/images/products/axila-cera.webp", None),
        ("/minha-conta/", b"conta-check1"),
    ]
    for path, needle in probes:
        req = urllib.request.Request(base + path, headers={"User-Agent": "pm-verify/1.0", "Cache-Control": "no-cache"})
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = resp.read()
                st = resp.status
        except Exception as err:
            fails += not ok(f"live {path}", False)
            print(" ", err)
            continue
        good = st == 200 and (needle is None or needle in body)
        fails += not ok(f"live {path}", good)

    # loja assets (pages may be 503 maintenance)
    loja = "https://loja.pellomenos.com.br"
    for path, needle in probes[:-1]:
        req = urllib.request.Request(loja + path, headers={"User-Agent": "pm-verify/1.0", "Cache-Control": "no-cache"})
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = resp.read()
                st = resp.status
            good = st == 200 and (needle is None or needle in body)
        except Exception as err:
            good = False
            print(" ", path, err)
        fails += not ok(f"loja {path.split('/')[-1][:40]}", good)

    print("FAILS", fails)
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
