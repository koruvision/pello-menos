# -*- coding: utf-8 -*-
"""Create Woo coupons, exercise cart apply, check checkout CF7 totals."""
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ENV = Path("projeto-migracao/.secrets/oficialteste.env")
BASE = "https://pellomenosoficialteste.companygenesis.com.br"


def load_env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def woo(method, path, payload=None):
    cfg = load_env()
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        cfg["PM_OFICIALTESTE_URL"].rstrip("/") + path,
        data=data,
        method=method,
        headers={"Authorization": "Basic " + token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode() or "{}"
            return r.status, json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw) if raw.strip() else {}
        except Exception:
            parsed = {"raw": raw[:300]}
        return e.code, parsed


def delete_coupon_code(code):
    st, rows = woo("GET", f"/wp-json/wc/v3/coupons?code={code}")
    if st == 200 and isinstance(rows, list):
        for row in rows:
            woo("DELETE", f"/wp-json/wc/v3/coupons/{row['id']}?force=true")


def create_coupon(payload):
    delete_coupon_code(payload["code"])
    st, created = woo("POST", "/wp-json/wc/v3/coupons", payload)
    print("create", payload["code"], st, created.get("id") if isinstance(created, dict) else created)
    if st not in (200, 201):
        raise SystemExit(f"coupon create failed: {st} {created}")
    return created["id"]


def seed_cart(page):
    page.goto(BASE + "/carrinho/?pm=couponval", wait_until="domcontentloaded", timeout=90000)
    page.evaluate(
        """() => {
          localStorage.setItem('pm-cart-v1', JSON.stringify([{
            lineId: 'body-splash::FLA', id: 'body-splash',
            name: 'Body Splash', image: '', duration: '', sku: 'PM',
            unitId: 'FLA', unitName: 'Flamengo', city: 'RJ', stateName: 'RJ',
            priceCents: 100, wooId: '48219', qty: 1
          }]));
          localStorage.setItem('pm-coupon-v1', '[]');
        }"""
    )
    page.reload(wait_until="domcontentloaded", timeout=90000)
    page.wait_for_function("() => !!(window.pmWoo && window.pmWoo.reconcile)", timeout=60000)
    page.evaluate(
        """async () => {
          const items = JSON.parse(localStorage.getItem('pm-cart-v1'));
          await window.pmWoo.reconcile(items);
        }"""
    )


def apply_ui_coupon(page, code):
    page.reload(wait_until="domcontentloaded", timeout=90000)
    page.wait_for_selector("[data-pm-coupon-input]", timeout=60000)
    page.fill("[data-pm-coupon-input]", code)
    page.click("[data-pm-coupon-apply]")
    page.wait_for_timeout(2500)
    return page.evaluate(
        """async () => {
          const r = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
          const d = await r.json();
          return {
            coupons: (d.coupons||[]).map(c => (c.code||'').toLowerCase()),
            discount: d.totals && d.totals.total_discount,
            items: d.totals && d.totals.total_items,
            total: d.totals && d.totals.total_price,
            ui: Array.from(document.querySelectorAll('[data-pm-coupon-remove]')).map(
              n => n.getAttribute('data-pm-coupon-remove')
            ),
          };
        }"""
    )


def read_checkout(page):
    page.goto(BASE + "/finalizar-pagamento/?pm=couponval", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_function("() => !!window.__pmShellBoot", timeout=30000)
    page.wait_for_timeout(2000)
    return page.evaluate(
        """async () => {
          const r = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
          const d = await r.json();
          const val = (name) => {
            const nodes = Array.from(document.querySelectorAll('[name=\"'+name+'\"]'));
            return nodes.map(n => n.value);
          };
          return {
            boot: !!window.__pmShellBoot,
            syncStarted: !!window.__pmShellSyncStarted,
            last: window.__pmLastTotals || null,
            cart: {
              coupons: (d.coupons||[]).map(c => (c.code||'').toLowerCase()),
              totals: d.totals,
              items: (d.items||[]).length,
            },
            fields: {
              cupom: val('cupom'),
              cupomamount: val('cupomamount'),
              fullvalue: val('fullvalue'),
              totalamount: val('totalamount'),
            },
            shellSrc: (document.querySelector('script[src*=\"checkout-shell\"]')||{}).src || null,
          };
        }"""
    )


def field_ok(fields, key, forbidden=("0", "0.00", "0,00", "", None)):
    vals = fields.get(key) or []
    if not vals:
        return False
    return any(v not in forbidden for v in vals)


def main():
    cases = [
        {
            "code": "PMTEST10",
            "payload": {
                "code": "PMTEST10",
                "discount_type": "percent",
                "amount": "10",
                "individual_use": False,
                "usage_limit": 50,
            },
            "expect_discount": True,
        },
        {
            "code": "PMFIXO10",
            "payload": {
                "code": "PMFIXO10",
                "discount_type": "fixed_cart",
                "amount": "0.10",
                "individual_use": False,
                "usage_limit": 50,
            },
            "expect_discount": True,
        },
        {
            "code": "PMBADZZZ",
            "payload": None,
            "expect_discount": False,
            "expect_fail": True,
        },
    ]
    created_ids = []
    results = []
    try:
        for case in cases:
            if case["payload"]:
                created_ids.append(create_coupon(case["payload"]))

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            seed_cart(page)

            for case in cases:
                code = case["code"]
                print("---", code)
                if case.get("expect_fail"):
                    seed_cart(page)
                    page.reload(wait_until="domcontentloaded", timeout=90000)
                    page.wait_for_selector("[data-pm-coupon-input]", timeout=60000)
                    page.fill("[data-pm-coupon-input]", code)
                    page.click("[data-pm-coupon-apply]")
                    page.wait_for_timeout(2000)
                    err = page.evaluate(
                        """() => {
                          const n = document.querySelector('[data-pm-coupon-error]');
                          return n ? (n.textContent||'').trim() : '';
                        }"""
                    )
                    state = page.evaluate(
                        """async () => {
                          const r = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
                          const d = await r.json();
                          return (d.coupons||[]).map(c => (c.code||'').toLowerCase());
                        }"""
                    )
                    ok = code.lower() not in state and bool(err)
                    print("invalid", json.dumps({"err": err, "coupons": state, "ok": ok}, ensure_ascii=False))
                    results.append(("invalid", ok))
                    continue

                seed_cart(page)
                applied = apply_ui_coupon(page, code)
                print("cart", json.dumps(applied, ensure_ascii=False))
                cart_ok = (
                    code.lower() in applied["coupons"]
                    and str(applied.get("discount") or "0") not in ("0", "0.00", "", "None")
                )
                checkout = read_checkout(page)
                print("checkout", json.dumps(checkout, ensure_ascii=False))
                fv = checkout["fields"]
                checkout_ok = (
                    checkout.get("boot")
                    and checkout.get("syncStarted")
                    and any(code.lower() in (v or "").lower() for v in fv.get("cupom") or [])
                    and field_ok(fv, "cupomamount")
                    and field_ok(fv, "fullvalue")
                    and field_ok(fv, "totalamount")
                )
                print("ok", cart_ok, checkout_ok)
                results.append((code, cart_ok and checkout_ok))

            # restricted product coupon should fail on body-splash-only cart
            rid = create_coupon(
                {
                    "code": "PMONLYX",
                    "discount_type": "percent",
                    "amount": "50",
                    "product_ids": [1],
                    "individual_use": False,
                    "usage_limit": 20,
                }
            )
            created_ids.append(rid)
            seed_cart(page)
            page.reload(wait_until="domcontentloaded", timeout=90000)
            page.wait_for_selector("[data-pm-coupon-input]", timeout=60000)
            page.fill("[data-pm-coupon-input]", "PMONLYX")
            page.click("[data-pm-coupon-apply]")
            page.wait_for_timeout(2500)
            restricted = page.evaluate(
                """async () => {
                  const r = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
                  const d = await r.json();
                  const err = document.querySelector('[data-pm-coupon-error]');
                  return {
                    coupons: (d.coupons||[]).map(c => (c.code||'').toLowerCase()),
                    err: err ? (err.textContent||'').trim() : '',
                  };
                }"""
            )
            restricted_ok = "pmonlyx" not in restricted["coupons"]
            print("restricted", json.dumps({**restricted, "ok": restricted_ok}, ensure_ascii=False))
            results.append(("restricted", restricted_ok))

            browser.close()
    finally:
        for cid in created_ids:
            woo("DELETE", f"/wp-json/wc/v3/coupons/{cid}?force=true")
            print("deleted", cid)
        for code in ("PMTEST10", "PMFIXO10", "PMONLYX"):
            delete_coupon_code(code)

    print("RESULTS", results)
    if not all(ok for _, ok in results):
        raise SystemExit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
