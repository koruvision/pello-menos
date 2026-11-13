# -*- coding: utf-8 -*-
"""Probe cart/cartqtd/unit format on oficialteste checkout (read-only, no pay)."""
import json

from playwright.sync_api import sync_playwright

BASE = "https://pellomenosoficialteste.companygenesis.com.br"
ITEMS = [
    {"wooId": 48219, "name": "Body Splash", "id": "body-splash"},
    {"wooId": 40128, "name": "Buco Laser", "id": "buco-laser"},
    {"wooId": 40179, "name": "Plano Silver", "id": "plano-silver"},
]


def seed(page):
    page.goto(BASE + "/carrinho/?pm=probe-seed", wait_until="domcontentloaded", timeout=90000)
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
          for (const item of items) {
            const add = await fetch('/wp-json/wc/store/v1/cart/add-item?id=' + item.wooId + '&quantity=1', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce }
            });
            nonce = add.headers.get('Nonce') || nonce;
            const body = await add.json().catch(() => ({}));
            const line = (body.items || []).find(i => String(i.id) === String(item.wooId))
              || (body.items || [])[(body.items || []).length - 1];
            local.push({
              lineId: item.id + '::U', id: item.id, name: item.name, image: '',
              duration: '', sku: 'PM', unitId: 'U', unitName: 'Unidade',
              city: 'SP', stateName: 'SP', priceCents: 100,
              wooId: String(item.wooId), wooKey: line && line.key ? line.key : '', qty: 1
            });
          }
          localStorage.setItem('pm-cart-v1', JSON.stringify(local));
          const final = await (await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' })).json();
          return {
            count: (final.items || []).length,
            names: (final.items || []).map(i => i.name),
            ids: (final.items || []).map(i => i.id),
            qtys: (final.items || []).map(i => i.quantity),
          };
        }""",
        ITEMS,
    )


def read_fields(page):
    return page.evaluate(
        """async () => {
          const names = ['cart','cartqtd','unit','category','easyunit','cupom','cupomamount','fullvalue','totalamount'];
          const fields = {};
          for (const n of names) {
            const nodes = Array.from(document.querySelectorAll('[name=\"' + n + '\"]'));
            fields[n] = nodes.map(el => ({
              tag: el.tagName, type: el.type || '', value: el.value || '',
              id: el.id || '', className: String(el.className || '').slice(0, 80)
            }));
          }
          const r = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
          const d = await r.json();
          const panel = Array.from(document.querySelectorAll('.pm-checkout-line')).map(li => ({
            name: (li.querySelector('.pm-checkout-line__name') || {}).textContent || '',
            key: li.getAttribute('data-pm-key') || ''
          }));
          // peek inline scripts mentioning cartqtd
          const inlineHits = Array.from(document.querySelectorAll('script:not([src])'))
            .map(s => s.textContent || '')
            .filter(t => t.includes('cartqtd') || t.includes('name=\"cart\"') || t.includes(\"[name='cart']\"))
            .map(t => t.slice(0, 2500));
          return {
            fields,
            woo: {
              count: (d.items || []).length,
              items: (d.items || []).map(i => ({
                id: i.id, name: i.name, qty: i.quantity, key: i.key,
                prices: i.prices || null, totals: i.totals || null
              })),
              totals: d.totals || {}
            },
            panel,
            inlineHits: inlineHits.length,
            inlineSample: inlineHits[0] || ''
          };
        }"""
    )


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        seeded = seed(page)
        print("SEED", json.dumps(seeded, ensure_ascii=False))

        page.goto(BASE + "/finalizar-pagamento/?pm=probe-cart", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function("() => !!window.__pmShellBoot", timeout=45000)
        page.wait_for_timeout(2000)
        # fields exist on load; cart panel only visible on payment tab
        before = read_fields(page)
        try:
            page.locator("#pills-pagamento-tab").click(force=True)
            page.wait_for_timeout(1500)
        except Exception as e:
            print("TAB_ERR", e)
        page.wait_for_selector("#pm-checkout-cart .pm-checkout-line", timeout=45000, state="attached")
        page.wait_for_timeout(1500)
        before = read_fields(page)
        print("BEFORE", json.dumps({
            "fields": {k: v for k, v in before["fields"].items()},
            "woo": before["woo"],
            "panel": before["panel"],
            "inlineHits": before["inlineHits"],
        }, ensure_ascii=False, indent=2))
        if before.get("inlineSample"):
            print("INLINE_SAMPLE_START")
            print(before["inlineSample"][:2000])
            print("INLINE_SAMPLE_END")

        # remove first line via panel button if present
        removed = page.evaluate(
            """async () => {
              const rem = document.querySelector('[data-pm-remove]');
              if (rem) {
                const key = rem.getAttribute('data-pm-remove');
                rem.click();
                await new Promise(r => setTimeout(r, 2800));
                return { ok: true, via: 'click', key };
              }
              let r = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
              let nonce = r.headers.get('Nonce') || '';
              const cart = await r.json();
              const it = (cart.items || [])[0];
              if (!it) return { ok: false, reason: 'empty' };
              const rr = await fetch('/wp-json/wc/store/v1/cart/remove-item', {
                method: 'POST', credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json', Nonce: nonce },
                body: JSON.stringify({ key: it.key })
              });
              await new Promise(r => setTimeout(r, 2000));
              return { ok: rr.ok, via: 'api', key: it.key, status: rr.status };
            }"""
        )
        print("REMOVE", json.dumps(removed, ensure_ascii=False))
        page.wait_for_timeout(1500)
        after = read_fields(page)
        print("AFTER", json.dumps({
            "fields": after["fields"],
            "woo": after["woo"],
            "panel": after["panel"],
        }, ensure_ascii=False, indent=2))
        browser.close()


if __name__ == "__main__":
    main()
