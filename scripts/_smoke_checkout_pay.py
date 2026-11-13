# -*- coding: utf-8 -*-
"""Fill + submit CF7 payment once on oficialteste. Card from env only — never commit secrets."""
import json
import os
import sys

from playwright.sync_api import sync_playwright

BASE = "https://pellomenosoficialteste.companygenesis.com.br"
VARIATION = 40121  # axila-cera RJ Tijuca


def require_card():
    holder = os.environ.get("PM_TEST_CARD_HOLDER", "").strip()
    number = os.environ.get("PM_TEST_CARD_NUMBER", "").strip().replace(" ", "")
    exp = os.environ.get("PM_TEST_CARD_EXP", "").strip()
    cvv = os.environ.get("PM_TEST_CARD_CVV", "").strip()
    if not all([holder, number, exp, cvv]):
        raise SystemExit(
            "Set PM_TEST_CARD_HOLDER, PM_TEST_CARD_NUMBER, PM_TEST_CARD_EXP, PM_TEST_CARD_CVV"
        )
    return {"holder": holder, "number": number, "exp": exp, "cvv": cvv}


def seed(page):
    page.goto(BASE + "/carrinho/?pm=payseed", wait_until="domcontentloaded", timeout=90000)
    seeded = page.evaluate(
        """async (wooId) => {
          localStorage.setItem('pm-cart-v1', JSON.stringify([{
            lineId: 'axila-cera::U', id: 'axila-cera', name: 'Axila Cera',
            image: '', duration: '', sku: 'PM', unitId: 'U', unitName: 'Unidade',
            city: 'RJ', stateName: 'RJ', priceCents: 100, wooId: String(wooId), qty: 1
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
          const add = await fetch('/wp-json/wc/store/v1/cart/add-item?id=' + wooId + '&quantity=1', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', Nonce: nonce }
          });
          const body = await add.json().catch(() => ({}));
          return { ok: add.ok, items: (body.items || []).length, total: body.totals && body.totals.total_price };
        }""",
        VARIATION,
    )
    print("seed", seeded)
    if not seeded.get("ok"):
        raise SystemExit("seed failed")


def set_fields(page, values):
    return page.evaluate(
        """(values) => {
          const out = {};
          for (const [name, value] of Object.entries(values)) {
            const nodes = Array.from(document.querySelectorAll('[name=\"' + name + '\"]'));
            let n = 0;
            for (const el of nodes) {
              if (el.type === 'hidden' || el.type === 'checkbox' || el.type === 'radio') continue;
              el.removeAttribute('readonly');
              el.removeAttribute('disabled');
              el.focus();
              el.value = value;
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
              el.dispatchEvent(new Event('blur', { bubbles: true }));
              n++;
            }
            out[name] = n;
          }
          return out;
        }""",
        values,
    )


def main():
    card = require_card()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        seed(page)
        page.goto(BASE + "/finalizar-pagamento/?pm=paysmoke", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function("() => !!window.__pmShellBoot", timeout=45000)
        page.wait_for_selector("#pm-checkout-cart .pm-checkout-line", timeout=45000)
        page.wait_for_timeout(2000)

        # Consent if present
        if page.locator('input[name="declaracao"]').count():
            page.locator('input[name="declaracao"]').first.check(force=True)

        person = {
            "your-name": "Teste Checkout PM",
            "your-email": "teste.checkout.pm@example.com",
            "your-phone": "21999990000",
            "cpf": "52998224725",
            "cep": "22041-080",
            "cidade": "Rio de Janeiro",
            "estado": "RJ",
            "endereco": "Rua Teste PM",
            "bairro": "Copacabana",
            "numero": "100",
            "complemento": "Apto 1",
        }
        print("fields", set_fields(page, person))
        page.wait_for_timeout(1500)
        # CEP lookup may overwrite; force again
        print("fields2", set_fields(page, {
            "cidade": "Rio de Janeiro",
            "estado": "RJ",
            "endereco": "Rua Teste PM",
            "bairro": "Copacabana",
        }))

        # Advance to payment step if nav pill exists
        pay_tab = page.locator(".nav-pills .nav-link", has_text="Pagamento")
        if pay_tab.count():
            pay_tab.first.click(force=True)
            page.wait_for_timeout(1000)

        # Card fields — fill visible ones; masks may reformat
        filled = page.evaluate(
            """(card) => {
              function set(name, value) {
                const nodes = Array.from(document.querySelectorAll('[name=\"' + name + '\"]'));
                let n = 0;
                for (const el of nodes) {
                  if (el.type === 'hidden') continue;
                  el.focus();
                  el.value = value;
                  el.dispatchEvent(new Event('input', { bubbles: true }));
                  el.dispatchEvent(new Event('change', { bubbles: true }));
                  el.dispatchEvent(new Event('keyup', { bubbles: true }));
                  el.dispatchEvent(new Event('blur', { bubbles: true }));
                  n++;
                }
                return n;
              }
              return {
                holder: set('holder', card.holder),
                number: set('cart-number', card.number),
                exp: set('expiration', card.exp),
                cvv: set('securityCode', card.cvv),
              };
            }""",
            card,
        )
        print("card fields filled counts", filled)

        # Prefer jQuery mask friendly fill via Playwright for visible card inputs
        if page.locator('input[name="holder"]:visible').count():
            page.locator('input[name="holder"]:visible').first.fill(card["holder"])
        nums = page.locator('input[name="cart-number"]:visible')
        if nums.count():
            nums.first.fill(card["number"])
        if page.locator('input[name="expiration"]:visible').count():
            page.locator('input[name="expiration"]:visible').first.fill(card["exp"])
        if page.locator('input[name="securityCode"]:visible').count():
            page.locator('input[name="securityCode"]:visible').first.fill(card["cvv"])

        # Snapshot values (mask-safe: only lengths / last4)
        snap = page.evaluate(
            """() => {
              const v = (name) => {
                const el = Array.from(document.querySelectorAll('[name=\"' + name + '\"]'))
                  .find(e => e.type !== 'hidden' && e.offsetParent !== null) ||
                  document.querySelector('[name=\"' + name + '\"]');
                const val = el ? String(el.value || '') : '';
                if (name === 'cart-number') return { len: val.replace(/\\D/g,'').length, last4: val.replace(/\\D/g,'').slice(-4) };
                if (name === 'securityCode') return { len: val.length };
                return { len: val.length, sample: val.slice(0, 4) };
              };
              return {
                holder: v('holder'),
                number: v('cart-number'),
                exp: v('expiration'),
                cvv: v('securityCode'),
                fullvalue: (document.querySelector('input[name=fullvalue]')||{}).value || '',
                totalamount: (document.querySelector('input[name=totalamount]')||{}).value || '',
              };
            }"""
        )
        print("snap", json.dumps(snap, ensure_ascii=False))

        submit = page.locator('input.wpcf7-submit, .wpcf7-submit').first
        print("submit visible", submit.count() > 0 and submit.is_visible())
        response_info = {"submitted": False}

        def is_cf7(resp):
            u = resp.url or ""
            return ("contact-form-7" in u) or ("wpcf7" in u) or ("admin-ajax.php" in u)

        try:
            with page.expect_response(is_cf7, timeout=90000) as resp_info:
                submit.click(force=True)
                response_info["submitted"] = True
            resp = resp_info.value
            body = ""
            try:
                body = resp.text()[:1200]
            except Exception:
                body = ""
            response_info.update({"status": resp.status, "url": resp.url, "body": body})
        except Exception as e:
            response_info["error"] = str(e)
            submit.click(force=True)
            response_info["submitted"] = True
            page.wait_for_timeout(8000)

        page.wait_for_timeout(3000)
        dom = page.evaluate(
            """() => {
              const invalid = Array.from(document.querySelectorAll('.wpcf7-not-valid, .wpcf7-not-valid-tip'))
                .slice(0, 8)
                .map(n => (n.name || n.getAttribute('data-name') || '') + ':' + (n.textContent || '').trim())
                .filter(Boolean);
              return {
                url: location.href,
                formClass: (document.querySelector('.wpcf7-form') || {}).className || '',
                mailSent: !!document.querySelector('.wpcf7-mail-sent-ok, .wpcf7-form.sent'),
                validation: !!document.querySelector('.wpcf7-validation-errors, .wpcf7-not-valid'),
                response: ((document.querySelector('.wpcf7-response-output') || {}).textContent || '').trim(),
                failed: !!document.querySelector('.wpcf7-form.failed, .wpcf7-mail-sent-ng'),
                invalid,
              };
            }"""
        )
        print("response", json.dumps({
            "submitted": response_info.get("submitted"),
            "status": response_info.get("status"),
            "url": (response_info.get("url") or "")[:160],
            "body": (response_info.get("body") or "")[:500],
            "error": response_info.get("error"),
        }, ensure_ascii=False))
        print("dom", json.dumps(dom, ensure_ascii=False))
        browser.close()

    if not response_info.get("submitted"):
        sys.exit(1)
    print("PAY_SMOKE_DONE")


if __name__ == "__main__":
    main()
