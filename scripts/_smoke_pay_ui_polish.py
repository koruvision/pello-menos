# -*- coding: utf-8 -*-
import json
import sys

from playwright.sync_api import sync_playwright

BASE = "https://pellomenosoficialteste.companygenesis.com.br"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE + "/carrinho/?pm=payui", wait_until="domcontentloaded", timeout=90000)
        page.evaluate(
            """async () => {
              const r = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
              let n = r.headers.get('Nonce') || '';
              const d = await r.json();
              for (const it of (d.items || [])) {
                const rr = await fetch('/wp-json/wc/store/v1/cart/remove-item', {
                  method: 'POST', credentials: 'same-origin',
                  headers: { 'Content-Type': 'application/json', Nonce: n },
                  body: JSON.stringify({ key: it.key })
                });
                n = rr.headers.get('Nonce') || n;
              }
              await fetch('/wp-json/wc/store/v1/cart/add-item?id=40121&quantity=1', {
                method: 'POST', credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json', Nonce: n }
              });
            }"""
        )
        page.goto(BASE + "/finalizar-pagamento/?pm=payui", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function("() => !!window.__pmShellBoot", timeout=45000)
        page.wait_for_timeout(2000)
        page.locator("#pills-pagamento-tab").click(force=True)
        page.wait_for_timeout(1500)

        info = page.evaluate(
            """() => {
              const sels = ['installments','allinstallments','cerainstallments'].map(name => {
                const el = document.querySelector('select[name=\"'+name+'\"]');
                if (!el) return { name, missing: true };
                const group = el.closest('[data-id]');
                const cs = group ? getComputedStyle(group) : getComputedStyle(el);
                return {
                  name,
                  value: el.value,
                  group: group && group.getAttribute('data-id'),
                  display: cs.display,
                  visible: cs.display !== 'none' && el.offsetParent !== null,
                };
              });
              const consent = document.querySelector('.pm-checkout-consent, [data-name=declaracao]');
              const submit = document.querySelector('button.pm-checkout-submit, .wpcf7-submit');
              const pay = document.getElementById('pills-pagamento');
              let consentBeforeSubmit = false;
              if (consent && submit && pay) {
                const cTop = consent.getBoundingClientRect().top;
                const sTop = submit.getBoundingClientRect().top;
                consentBeforeSubmit = pay.contains(consent) && cTop < sTop;
              }
              return {
                siteinstallment: (document.querySelector('input[name=siteinstallment]')||{}).value,
                sels,
                hasPremiumBtn: !!document.querySelector('button.pm-checkout-submit'),
                btnText: (document.querySelector('button.pm-checkout-submit')||{}).innerText || '',
                consentBeforeSubmit,
                consentInPay: !!(pay && consent && pay.contains(consent)),
                brand: (document.querySelector('link[href*=checkout-brand]')||{}).href,
                shell: (document.querySelector('script[src*=checkout-shell]')||{}).src,
              };
            }"""
        )
        print(json.dumps(info, ensure_ascii=False, indent=2))
        errors = []
        if "brand6" not in (info.get("brand") or ""):
            errors.append("brand6")
        if "c14" not in (info.get("shell") or ""):
            errors.append("c14")
        if info.get("siteinstallment") != "1":
            errors.append("siteinstallment!=1")
        visible = [s for s in info["sels"] if s.get("visible")]
        if not visible:
            errors.append("no visible installment select")
        if not any(s.get("value") == "1x" for s in visible):
            errors.append("visible installment not 1x")
        if not info.get("hasPremiumBtn"):
            errors.append("no premium button")
        if not info.get("consentBeforeSubmit"):
            errors.append("consent not above submit")
        browser.close()
        for e in errors:
            print("ERR", e)
        if errors:
            sys.exit(1)
        print("PASS")


if __name__ == "__main__":
    main()
