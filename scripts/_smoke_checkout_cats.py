# -*- coding: utf-8 -*-
"""Smoke checkout oficialteste: 1 item por categoria; sem cartão neste script."""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = "https://pellomenosoficialteste.companygenesis.com.br"

# wooId = variationId (Store API); parent products are variable.
CASES = [
    {"label": "fem_cera", "id": "axila-cera", "wooId": 40121, "name": "Axila Cera"},
    {"label": "masculino", "id": "antebraco-cera-masc", "wooId": 40123, "name": "Antebraco Cera Masc"},
    {"label": "esfoliacao", "id": "esfoliacao-meia-perna", "wooId": 40113, "name": "Esfoliacao Meia Perna"},
    {"label": "assinatura", "id": "plano-silver", "wooId": 40179, "name": "Plano Silver"},
    {"label": "laser", "id": "buco-laser", "wooId": 40128, "name": "Buco Laser"},
]


def clear_and_add(page, woo_id):
    page.goto(BASE + "/carrinho/?pm=seed", wait_until="domcontentloaded", timeout=90000)
    result = page.evaluate(
        """async (wooId) => {
          localStorage.setItem('pm-cart-v1', '[]');
          localStorage.setItem('pm-coupon-v1', '[]');
          const cartRes = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
          let nonce = cartRes.headers.get('Nonce') || cartRes.headers.get('nonce') || '';
          const cart = await cartRes.json();
          for (const it of (cart.items || [])) {
            const rr = await fetch('/wp-json/wc/store/v1/cart/remove-item', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce },
              body: JSON.stringify({ key: it.key })
            });
            nonce = rr.headers.get('Nonce') || nonce;
          }
          const add = await fetch('/wp-json/wc/store/v1/cart/add-item?id=' + wooId + '&quantity=1', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', Nonce: nonce }
          });
          nonce = add.headers.get('Nonce') || nonce;
          const body = await add.json().catch(() => ({}));
          return {
            ok: add.ok,
            status: add.status,
            items: (body.items || []).length,
            names: (body.items || []).map(i => i.name),
            error: body.message || body.code || null,
            raw: add.ok ? null : JSON.stringify(body).slice(0, 400)
          };
        }""",
        woo_id,
    )
    return result


def sync_local(page, case):
    """Keep pm-cart-v1 aligned so shell totals paints don't race empty."""
    page.evaluate(
        """(item) => {
          localStorage.setItem('pm-cart-v1', JSON.stringify([{
            lineId: item.id + '::U', id: item.id,
            name: item.name, image: '', duration: '', sku: 'PM',
            unitId: 'U', unitName: 'Unidade', city: 'SP', stateName: 'SP',
            priceCents: 100, wooId: String(item.wooId), qty: 1
          }]));
        }""",
        case,
    )


def read_checkout(page, viewport_name):
    page.goto(BASE + "/finalizar-pagamento/?pm=catsmoke", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_function("() => !!window.__pmShellBoot", timeout=45000)
    page.wait_for_selector("#pm-checkout-cart", timeout=45000)
    page.wait_for_timeout(2500)
    return page.evaluate(
        """async (viewport) => {
          const r = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
          const d = await r.json();
          const names = Array.from(document.querySelectorAll('.pm-checkout-line__name'))
            .map(n => n.textContent || '');
          const bg = getComputedStyle(document.body).backgroundImage;
          const layout = document.getElementById('pm-checkout-layout');
          const brandLink = Array.from(document.querySelectorAll('link[rel=stylesheet]'))
            .map(l => l.href).find(h => h && h.includes('checkout-brand'));
          const shellSrc = Array.from(document.querySelectorAll('script[src]'))
            .map(s => s.src).find(h => h && h.includes('checkout-shell'));
          const fullvalue = (document.querySelector('input[name=fullvalue]') || {}).value || '';
          const totalamount = (document.querySelector('input[name=totalamount]') || {}).value || '';
          const entityLeak = names.some(n => n.includes('&#') || n.includes('&amp;'));
          return {
            viewport,
            items: (d.items || []).length,
            wooNames: (d.items || []).map(i => i.name),
            panelNames: names,
            entityLeak,
            bgImage: bg,
            hasLayout: !!layout,
            brandLink,
            shellSrc,
            fullvalue,
            totalamount,
            bodyHasBrand: document.body.classList.contains('pm-checkout-brand'),
          };
        }""",
        viewport_name,
    )


def main():
    results = []
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        for case in CASES:
            print("===", case["label"], case["wooId"])
            try:
                seeded = clear_and_add(page, case["wooId"])
                print("  seed", json.dumps(seeded, ensure_ascii=False)[:400])
                if not seeded.get("ok") or seeded.get("items", 0) < 1:
                    errors.append(f"{case['label']}: seed failed {seeded}")
                    results.append({"case": case["label"], "ok": False, "seed": seeded})
                    continue
                sync_local(page, case)
                desktop = read_checkout(page, "desktop")
                print(
                    "  desktop",
                    desktop["items"],
                    desktop["panelNames"],
                    "entity",
                    desktop["entityLeak"],
                    "brand",
                    "brand3" in (desktop.get("brandLink") or ""),
                )
                if desktop["items"] != 1:
                    errors.append(f"{case['label']}: expected 1 item got {desktop['items']}")
                if desktop["entityLeak"]:
                    errors.append(f"{case['label']}: entity leak {desktop['panelNames']}")
                if not desktop["bodyHasBrand"] or not desktop["hasLayout"]:
                    errors.append(f"{case['label']}: missing brand/layout")
                if "brand3" not in (desktop.get("brandLink") or ""):
                    errors.append(f"{case['label']}: brand css not brand3")
                if "c12" not in (desktop.get("shellSrc") or ""):
                    errors.append(f"{case['label']}: shell not c12")

                if page.locator("[data-pm-qty-inc]").count():
                    page.click("[data-pm-qty-inc]")
                    page.wait_for_timeout(2500)
                    qty = page.locator(".pm-checkout-qty span").first.inner_text().strip()
                    print("  qty after inc", qty)
                    if qty != "2":
                        errors.append(f"{case['label']}: qty inc expected 2 got {qty}")

                page.set_viewport_size({"width": 390, "height": 844})
                mobile = read_checkout(page, "mobile")
                print("  mobile items", mobile["items"])
                if mobile["items"] < 1:
                    errors.append(f"{case['label']}: mobile empty")
                page.set_viewport_size({"width": 1440, "height": 900})
                results.append({"case": case["label"], "ok": True})
            except Exception as e:
                errors.append(f"{case['label']}: {e}")
                results.append({"case": case["label"], "ok": False, "error": str(e)})
                print("FAIL", e)

        browser.close()

    print("\n=== SUMMARY ===")
    print("cases", len(results), "errors", len(errors))
    for e in errors:
        print("ERR", e)
    if errors:
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
