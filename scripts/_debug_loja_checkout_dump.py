# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

SKUS = json.loads(Path("scripts/_loja_esquenta_test_skus.json").read_text(encoding="utf-8"))
BASE = "https://loja.pellomenos.com.br"
WOO_ID = int(SKUS["pm-teste-esquenta-laser"])

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(BASE + "/", wait_until="domcontentloaded", timeout=60000)
    home = page.evaluate("""() => ({ title: document.title, text: (document.body.innerText||'').slice(0,300), status: document.body && document.body.dataset })""")
    print("home", home)
    page.goto(BASE + "/carrinho/", wait_until="domcontentloaded", timeout=60000)
    page.evaluate(
        """async ({ wooId }) => {
          localStorage.setItem('pm-cart-v1', JSON.stringify([{
            lineId: 'pm-teste-esquenta-laser::U', id: 'pm-teste-esquenta-laser', name: 'T',
            priceCents: 200, originalCents: 500, method: 'laser', wooId: String(wooId), qty: 1,
            unitId: 'U', unitName: 'U'
          }]));
          const cartRes = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
          let nonce = cartRes.headers.get('Nonce') || '';
          const cart = await cartRes.json();
          for (const it of (cart.items || [])) {
            const rr = await fetch('/wp-json/wc/store/v1/cart/remove-item', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce },
              body: JSON.stringify({ key: it.key })
            });
            nonce = rr.headers.get('Nonce') || nonce;
          }
          return fetch('/wp-json/wc/store/v1/cart/add-item', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', Nonce: nonce },
            body: JSON.stringify({ id: wooId, quantity: 1, pm_catalog_id: 'pm-teste-esquenta-laser' })
          }).then(r => r.json());
        }""",
        {"wooId": WOO_ID},
    )
    page.goto(BASE + "/finalizar-pagamento/", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(8000)
    dump = page.evaluate(
        """() => ({
          title: document.title,
          url: location.href,
          text: (document.body.innerText||'').slice(0,500),
          hasForm: !!document.querySelector('.wpcf7-form'),
          totalamount: (document.querySelector('input[name=totalamount]')||{}).value||null,
          ui: window.__pmCheckoutUiTotalCents||null,
          phase: window.__PM_BLACK_PHASE__||null,
          pmBlack: !!(window.pmBlackNov),
          scripts: Array.from(document.querySelectorAll('script[src]')).map(s=>s.src).filter(s=>/pm-home|checkout|black|shell/.test(s)).slice(0,20),
        })"""
    )
    print(json.dumps(dump, ensure_ascii=False, indent=2))
    browser.close()
