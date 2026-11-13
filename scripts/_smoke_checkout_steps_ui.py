# -*- coding: utf-8 -*-
"""Verify cart panel only on Pagamento step; no coupon; wide form on Dados."""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = "https://pellomenosoficialteste.companygenesis.com.br"
VARIATION = 40121


def seed(page):
    page.goto(BASE + "/carrinho/?pm=stepui", wait_until="domcontentloaded", timeout=90000)
    return page.evaluate(
        """async (wooId) => {
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
          const add = await fetch('/wp-json/wc/store/v1/cart/add-item?id=' + wooId + '&quantity=1', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', Nonce: nonce }
          });
          const body = await add.json().catch(() => ({}));
          return { ok: add.ok, items: (body.items || []).length };
        }""",
        VARIATION,
    )


def snapshot(page, label):
    return page.evaluate(
        """(label) => {
          const layout = document.getElementById('pm-checkout-layout');
          const cart = document.getElementById('pm-checkout-cart');
          const form = document.querySelector('.pm-checkout-form-col');
          const csCart = cart ? getComputedStyle(cart) : null;
          const rect = (el) => el ? el.getBoundingClientRect() : null;
          const lr = rect(layout);
          const fr = rect(form);
          const cr = rect(cart);
          return {
            label,
            brand: (document.querySelector('link[href*=\\"checkout-brand\\"]') || {}).href || '',
            shell: (document.querySelector('script[src*=\\"checkout-shell\\"]') || {}).src || '',
            payStep: !!(layout && layout.classList.contains('is-pay-step')),
            cartDisplay: csCart ? csCart.display : null,
            hasCoupon: !!document.querySelector('[data-pm-coupon], .pm-checkout-coupon'),
            layoutW: lr && Math.round(lr.width),
            formW: fr && Math.round(fr.width),
            cartW: cr && csCart && csCart.display !== 'none' ? Math.round(cr.width) : 0,
            lines: document.querySelectorAll('.pm-checkout-line').length,
            span: !!document.querySelector('.pm-checkout-span'),
          };
        }""",
        label,
    )


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        print("seed", seed(page))
        page.goto(BASE + "/finalizar-pagamento/?pm=stepui", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function("() => !!window.__pmShellBoot", timeout=45000)
        page.wait_for_selector("#pm-checkout-layout", timeout=45000)
        page.wait_for_timeout(2000)

        # Ensure Dados step
        if page.locator("#pills-dados-tab").count():
            page.locator("#pills-dados-tab").click(force=True)
            page.wait_for_timeout(800)

        dados = snapshot(page, "dados")
        print("dados", json.dumps(dados, ensure_ascii=False))
        if "brand4" not in dados["brand"]:
            errors.append("brand4 missing")
        if "c13" not in dados["shell"]:
            errors.append("c13 missing")
        if dados["payStep"]:
            errors.append("dados should not be pay step")
        if dados["cartDisplay"] != "none":
            errors.append("cart should be hidden on dados")
        if dados["hasCoupon"]:
            errors.append("coupon UI should be gone")
        if (dados["formW"] or 0) < 700:
            errors.append(f"form too narrow on dados: {dados['formW']}")

        # Pagamento step
        page.locator("#pills-pagamento-tab").click(force=True)
        page.wait_for_timeout(1000)
        pay = snapshot(page, "pay")
        print("pay", json.dumps(pay, ensure_ascii=False))
        if not pay["payStep"]:
            errors.append("pay step class missing")
        if pay["cartDisplay"] == "none":
            errors.append("cart should show on pagamento")
        if pay["lines"] < 1:
            errors.append("cart lines missing on pagamento")
        if pay["hasCoupon"]:
            errors.append("coupon still present on pay")

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#pills-dados-tab").click(force=True)
        page.wait_for_timeout(600)
        mdados = snapshot(page, "mobile-dados")
        page.locator("#pills-pagamento-tab").click(force=True)
        page.wait_for_timeout(600)
        mpay = snapshot(page, "mobile-pay")
        print("mobile-dados", json.dumps(mdados, ensure_ascii=False))
        print("mobile-pay", json.dumps(mpay, ensure_ascii=False))
        if mdados["cartDisplay"] != "none":
            errors.append("mobile dados cart visible")
        if mpay["cartDisplay"] == "none" or mpay["lines"] < 1:
            errors.append("mobile pay cart missing")

        browser.close()

    for e in errors:
        print("ERR", e)
    if errors:
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
