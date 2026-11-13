# -*- coding: utf-8 -*-
"""Debug CF7 submit on loja: capture invalid fields + demo mode."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CARD_ENV = ROOT / "projeto-migracao" / ".secrets" / "ot-test-card.env"
SKUS = json.loads((ROOT / "scripts" / "_loja_esquenta_test_skus.json").read_text(encoding="utf-8"))
BASE = "https://loja.pellomenos.com.br"
WOO_ID = int(SKUS["pm-teste-esquenta-laser"])


def load_card():
    for line in CARD_ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    return {
        "holder": os.environ["PM_TEST_CARD_HOLDER"].strip(),
        "number": os.environ["PM_TEST_CARD_NUMBER"].strip().replace(" ", ""),
        "exp": os.environ["PM_TEST_CARD_EXP"].strip(),
        "cvv": os.environ["PM_TEST_CARD_CVV"].strip(),
    }


def main():
    card = load_card()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE + "/carrinho/?pm=cf7dbg", wait_until="domcontentloaded", timeout=90000)
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
              await fetch('/wp-json/wc/store/v1/cart/add-item', {
                method: 'POST', credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json', Nonce: nonce },
                body: JSON.stringify({ id: wooId, quantity: 1, pm_catalog_id: 'pm-teste-esquenta-laser' })
              });
            }""",
            {"wooId": WOO_ID},
        )
        page.goto(BASE + "/finalizar-pagamento/?pm=cf7dbg", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function(
            """() => String((document.querySelector('input[name=totalamount]')||{}).value||'').replace(',','.')==='2.00'""",
            timeout=90000,
        )
        email = f"teste.loja.cf7dbg.{int(time.time())}@example.com"
        person = {
            "your-name": "Teste CF7 Loja",
            "your-email": email,
            "your-phone": "21988887777",
            "cpf": "52998224725",
            "cep": "22041080",
            "cidade": "Rio de Janeiro",
            "estado": "RJ",
            "endereco": "Rua Teste",
            "bairro": "Copacabana",
            "numero": "10",
            "complemento": "1",
        }
        page.evaluate(
            """(person) => {
              for (const [name, value] of Object.entries(person)) {
                for (const el of document.querySelectorAll('[name=\"'+name+'\"]')) {
                  if (el.type === 'checkbox' || el.type === 'radio') continue;
                  el.value = value;
                  el.dispatchEvent(new Event('change', { bubbles: true }));
                }
              }
            }""",
            person,
        )
        fill_js = """() => {
          function setSelect(name) {
            let val = '';
            for (const el of document.querySelectorAll('select[name=\"'+name+'\"]')) {
              const opt = Array.from(el.options).find(o => o.value && !/selecione/i.test(o.textContent||''));
              if (!opt) continue;
              el.selectedIndex = opt.index; el.value = opt.value; val = opt.value;
              el.classList.remove('wpcf7-not-valid','first_null');
              el.setAttribute('aria-invalid','false');
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            return val;
          }
          const unit = setSelect('unit');
          for (const el of document.querySelectorAll('[name=\"easyunit\"]')) {
            el.value = unit; el.classList.remove('wpcf7-not-valid');
            el.dispatchEvent(new Event('change', { bubbles: true }));
          }
          for (const n of ['installments','cerainstallments','allinstallments','siteinstallment']) setSelect(n);
          const decl = document.querySelector('input[name=\"declaracao\"]');
          if (decl) { decl.checked = true; decl.dispatchEvent(new Event('change', { bubbles: true })); }
          return unit;
        }"""
        page.evaluate(fill_js)
        pay = page.locator(".nav-pills .nav-link", has_text="Pagamento")
        if pay.count():
            pay.first.click(force=True)
            page.wait_for_timeout(1200)
        for name in ("unit", "installments", "cerainstallments", "allinstallments"):
            loc = page.locator(f"select[name='{name}']")
            if loc.count():
                try:
                    loc.first.select_option(index=1)
                except Exception:
                    pass
        page.evaluate(fill_js)
        page.evaluate(
            """(card) => {
              function set(name, value) {
                for (const el of document.querySelectorAll('[name=\"'+name+'\"]')) {
                  if (el.type === 'hidden') continue;
                  el.focus(); el.value = value;
                  ['input','change','keyup','blur'].forEach(ev => el.dispatchEvent(new Event(ev, { bubbles: true })));
                }
              }
              set('holder', card.holder); set('cart-number', card.number);
              set('expiration', card.exp); set('securityCode', card.cvv);
              for (const el of document.querySelectorAll('[name=\"totalamount\"]')) el.value = '2.00';
            }""",
            card,
        )
        page.evaluate(fill_js)
        pre = page.evaluate(
            """() => {
              const names = ['your-name','your-email','cpf','unit','easyunit','cart','cartqtd','totalamount','cart-number','holder','expiration','securityCode','installments','allinstallments','declaracao'];
              const out = {};
              for (const n of names) {
                const el = document.querySelector('[name=\"'+n+'\"]');
                if (!el) { out[n] = null; continue; }
                out[n] = el.type === 'checkbox' ? el.checked : el.value;
              }
              out.formClass = (document.querySelector('.wpcf7-form')||{}).className || '';
              out.demo = !!document.querySelector('.wpcf7-form.demo');
              return out;
            }"""
        )
        print("pre", json.dumps(pre, ensure_ascii=False))

        resp_info = {}
        try:
            with page.expect_response(lambda r: "contact-form-7" in (r.url or "") or "wpcf7" in (r.url or ""), timeout=120000) as ri:
                page.evaluate("""() => { const b=document.querySelector('button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit'); if(b) b.click(); }""")
            r = ri.value
            body = r.text()
            resp_info = {"status": r.status, "url": r.url, "body": body[:2500]}
        except Exception as err:
            resp_info = {"error": str(err)}
        page.wait_for_timeout(5000)
        after = page.evaluate(
            """() => ({
              className: (document.querySelector('.wpcf7-form')||{}).className||'',
              response: ((document.querySelector('.wpcf7-response-output')||{}).textContent||'').trim(),
              invalid: Array.from(document.querySelectorAll('.wpcf7-not-valid-tip, .wpcf7-not-valid')).map(el => ({
                text: (el.textContent||'').trim().slice(0,160),
                name: el.getAttribute('data-name') || (el.previousElementSibling && el.previousElementSibling.name) || el.className
              })).slice(0,30),
              url: location.href,
            })"""
        )
        print("cf7", json.dumps(resp_info, ensure_ascii=False)[:2000])
        print("after", json.dumps(after, ensure_ascii=False))
        Path("scripts/_loja_cf7_debug_charge_result.json").write_text(
            json.dumps({"pre": pre, "cf7": resp_info, "after": after, "email": email}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        browser.close()


if __name__ == "__main__":
    main()
