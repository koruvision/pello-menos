# -*- coding: utf-8 -*-
"""Smoke: after remove/qty edit, CF7 cart/cartqtd must match Store API."""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = "https://pellomenosoficialteste.companygenesis.com.br"
# SKUs that share a Woo cart (some products clear incompatible lines).
ITEMS = [
    {"wooId": 48219, "name": "Body Splash", "id": "body-splash"},
    {"wooId": 40128, "name": "Buco Laser", "id": "buco-laser"},
]


def seed(page):
    page.goto(BASE + "/carrinho/?pm=sync-seed", wait_until="domcontentloaded", timeout=90000)
    return page.evaluate(
        """async (items) => {
          localStorage.setItem('pm-cart-v1', '[]');
          localStorage.setItem('pm-coupon-v1', '[]');
          let r = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
          let nonce = r.headers.get('Nonce') || '';
          let cart = await r.json();
          for (const it of (cart.items || [])) {
            const rr = await fetch('/wp-json/wc/store/v1/cart/remove-item', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce },
              body: JSON.stringify({ key: it.key })
            });
            nonce = rr.headers.get('Nonce') || nonce;
          }
          const local = [];
          const added = [];
          for (const item of items) {
            const add = await fetch('/wp-json/wc/store/v1/cart/add-item?id=' + item.wooId + '&quantity=1', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce }
            });
            nonce = add.headers.get('Nonce') || nonce;
            const body = await add.json().catch(() => ({}));
            if (!add.ok) {
              added.push({ wooId: item.wooId, ok: false, status: add.status, err: body.message || body.code });
              continue;
            }
            const live = body.items || [];
            const line = live.find(i => String(i.id) === String(item.wooId))
              || live[live.length - 1];
            // rebuild local from live cart after each add (Woo may drop incompatible lines)
            local.length = 0;
            live.forEach(function (li) {
              local.push({
                lineId: String(li.id) + '::U', id: String(li.id), name: li.name || '', image: '',
                duration: '', sku: 'PM', unitId: 'U', unitName: 'Unidade',
                city: 'SP', stateName: 'SP', priceCents: 100,
                wooId: String(li.id), wooKey: li.key || '', qty: li.quantity || 1
              });
            });
            added.push({
              wooId: item.wooId, ok: true, id: line && line.id, key: line && line.key,
              cartCount: live.length, cartIds: live.map(i => i.id)
            });
          }
          localStorage.setItem('pm-cart-v1', JSON.stringify(local));
          const final = await (await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' })).json();
          return {
            added,
            count: (final.items || []).length,
            ids: (final.items || []).map(i => String(i.id)),
            qtys: (final.items || []).map(i => String(i.quantity)),
          };
        }""",
        ITEMS,
    )


def snapshot(page):
    return page.evaluate(
        """async () => {
          const cart = (document.querySelector('input[name=cart]') || {}).value || '';
          const cartqtd = (document.querySelector('input[name=cartqtd]') || {}).value || '';
          const fullvalue = (document.querySelector('input[name=fullvalue]') || {}).value || '';
          const totalamount = (document.querySelector('input[name=totalamount]') || {}).value || '';
          const r = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
          const d = await r.json();
          const ids = (d.items || []).map(i => String(i.id));
          const qtys = (d.items || []).map(i => String(i.quantity));
          return {
            cart, cartqtd, fullvalue, totalamount,
            wooIds: ids, wooQtys: qtys,
            matchCart: cart === ids.join(','),
            matchQty: cartqtd === qtys.join(','),
            panelCount: document.querySelectorAll('.pm-checkout-line').length,
            shell: (Array.from(document.querySelectorAll('script[src]')).map(s => s.src)
              .find(h => h && h.includes('checkout-shell')) || ''),
          };
        }"""
    )


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        seeded = seed(page)
        print("SEED", json.dumps(seeded, ensure_ascii=False))
        if seeded["count"] < 2:
            print("FAIL need at least 2 items")
            browser.close()
            sys.exit(1)

        page.goto(BASE + "/finalizar-pagamento/?pm=sync-smoke", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function("() => !!window.__pmShellBoot", timeout=45000)
        page.locator("#pills-pagamento-tab").click(force=True)
        page.wait_for_selector("#pm-checkout-cart .pm-checkout-line", timeout=45000, state="attached")
        page.wait_for_timeout(2500)

        before = snapshot(page)
        print("BEFORE", json.dumps(before, ensure_ascii=False))
        if "c20" not in before.get("shell", ""):
            print("WARN shell not c20:", before.get("shell"))

        # remove first line
        page.locator("[data-pm-remove]").first.click()
        page.wait_for_timeout(3000)
        after_remove = snapshot(page)
        print("AFTER_REMOVE", json.dumps(after_remove, ensure_ascii=False))

        # bump qty on remaining first line if possible
        inc = page.locator("[data-pm-qty-inc]")
        if inc.count():
            inc.first.click()
            page.wait_for_timeout(3000)
        after_qty = snapshot(page)
        print("AFTER_QTY", json.dumps(after_qty, ensure_ascii=False))

        ok = (
            after_remove["matchCart"]
            and after_remove["matchQty"]
            and after_qty["matchCart"]
            and after_qty["matchQty"]
            and after_remove["cart"] != before["cart"]
        )
        print("OK" if ok else "FAIL")
        browser.close()
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
