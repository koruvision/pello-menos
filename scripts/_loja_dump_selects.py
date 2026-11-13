# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright

BASE = "https://loja.pellomenos.com.br"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(BASE + "/finalizar-pagamento/", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(3000)
    dump = page.evaluate(
        """() => {
          const names = ['unit','easyunit','installments','cerainstallments','allinstallments','siteinstallment'];
          const out = {};
          for (const name of names) {
            out[name] = Array.from(document.querySelectorAll('[name=\"'+name+'\"]')).map((el) => ({
              tag: el.tagName,
              type: el.type || null,
              value: el.value,
              selectedIndex: el.selectedIndex,
              disabled: el.disabled,
              required: el.required || el.classList.contains('wpcf7-validates-as-required'),
              classes: el.className,
              visible: !!(el.offsetParent || el.getClientRects().length),
              options: el.tagName === 'SELECT' ? Array.from(el.options).slice(0,8).map(o => ({v:o.value, t:(o.textContent||'').trim().slice(0,40), idx:o.index})) : null,
            }));
          }
          return out;
        }"""
    )
    import json
    print(json.dumps(dump, ensure_ascii=False, indent=2))
    browser.close()
