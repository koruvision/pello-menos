# -*- coding: utf-8 -*-
"""UI/hiddens checkout loja: Esquenta laser → 2.00."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SKUS = json.loads((ROOT / "scripts" / "_loja_esquenta_test_skus.json").read_text(encoding="utf-8"))
BASE = "https://loja.pellomenos.com.br"
WOO_ID = int(SKUS["pm-teste-esquenta-laser"])
CATALOG_ID = "pm-teste-esquenta-laser"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE + "/carrinho/?pm=loja-dbg", wait_until="domcontentloaded", timeout=90000)
        seeded = page.evaluate(
            """async ({ wooId, catalogId }) => {
              localStorage.setItem('pm-cart-v1', JSON.stringify([{
                lineId: catalogId + '::U', id: catalogId, name: 'PM Teste Esquenta Laser',
                image: '', duration: 'Ensaio', sku: catalogId, unitId: 'U', unitName: 'Unidade',
                city: 'RJ', stateName: 'RJ', priceCents: 200, originalCents: 500,
                method: 'laser', wooId: String(wooId), qty: 1
              }]));
              localStorage.removeItem('pm-coupon-v1');
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
              const add = await fetch('/wp-json/wc/store/v1/cart/add-item', {
                method: 'POST', credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json', Nonce: nonce },
                body: JSON.stringify({ id: wooId, quantity: 1, pm_catalog_id: catalogId })
              });
              const body = await add.json().catch(() => ({}));
              return { ok: add.ok, total_price: (body.totals || {}).total_price, phase: window.__PM_BLACK_PHASE__ || null };
            }""",
            {"wooId": WOO_ID, "catalogId": CATALOG_ID},
        )
        print("seed", seeded)
        if int(seeded.get("total_price") or 0) != 200:
            raise SystemExit(f"seed not R$2: {seeded}")

        page.goto(BASE + "/finalizar-pagamento/?pm=loja-dbg", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function(
            """() => {
              const tot = String((document.querySelector('input[name=totalamount]') || {}).value || '').replace(',', '.');
              return !!document.querySelector('.wpcf7-form') && tot === '2.00';
            }""",
            timeout=120000,
        )
        dbg = page.evaluate(
            """() => ({
              ui: window.__pmCheckoutUiTotalCents,
              totalamount: (document.querySelector('input[name=totalamount]') || {}).value || '',
              fullvalue: (document.querySelector('input[name=fullvalue]') || {}).value || '',
              phase: window.__PM_BLACK_PHASE__ || (window.pmBlackNov && window.pmBlackNov.phaseAt && window.pmBlackNov.phaseAt()),
              ready: window.pmBlackNov && window.pmBlackNov.ready && window.pmBlackNov.ready(),
              url: location.href,
            })"""
        )
        print(json.dumps(dbg, ensure_ascii=False, indent=2))
        if str(dbg.get("totalamount")).replace(",", ".") != "2.00":
            raise SystemExit("totalamount mismatch")
        print("LOJA_DEBUG_UI_OK")

        browser.close()


if __name__ == "__main__":
    main()
