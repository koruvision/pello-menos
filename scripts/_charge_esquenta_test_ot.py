# -*- coding: utf-8 -*-
"""Compra mínima Esquenta no OT (1 laser teste → R$ 2,00). Cartão só via .secrets."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CARD_ENV = ROOT / "projeto-migracao" / ".secrets" / "ot-test-card.env"
SKUS = json.loads((ROOT / "scripts" / "_ot_esquenta_test_skus.json").read_text(encoding="utf-8"))
BASE = "https://pellomenosoficialteste.companygenesis.com.br"
WOO_ID = int(SKUS["pm-teste-esquenta-laser"])
CATALOG_ID = "pm-teste-esquenta-laser"
# Unidades com chave Accesstage no child theme OT
PREFERRED_UNITS = ("flamengo", "copacabana1", "copacabana2", "ipanema", "botafogo")


def load_card():
    if CARD_ENV.is_file():
        for line in CARD_ENV.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    holder = os.environ.get("PM_TEST_CARD_HOLDER", "").strip()
    number = os.environ.get("PM_TEST_CARD_NUMBER", "").strip().replace(" ", "")
    exp = os.environ.get("PM_TEST_CARD_EXP", "").strip()
    cvv = os.environ.get("PM_TEST_CARD_CVV", "").strip()
    if not all([holder, number, exp, cvv]):
        raise SystemExit("missing card env")
    return {"holder": holder, "number": number, "exp": exp, "cvv": cvv}


def set_fields(page, values):
    return page.evaluate(
        """(values) => {
          const out = {};
          for (const [name, value] of Object.entries(values)) {
            const nodes = Array.from(document.querySelectorAll('[name=\"' + name + '\"]'));
            let n = 0;
            for (const el of nodes) {
              if (el.type === 'checkbox' || el.type === 'radio') continue;
              el.removeAttribute('readonly');
              el.removeAttribute('disabled');
              el.focus();
              el.value = value;
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
              n++;
            }
            out[name] = n;
          }
          return out;
        }""",
        values,
    )


def main():
    card = load_card()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE + "/carrinho/?pm=esquenta-seed", wait_until="domcontentloaded", timeout=90000)
        seeded = page.evaluate(
            """async ({ wooId, catalogId }) => {
              localStorage.setItem('pm-cart-v1', JSON.stringify([{
                lineId: catalogId + '::U', id: catalogId, name: 'PM Teste Esquenta Laser',
                image: '', duration: 'Ensaio', sku: catalogId, unitId: 'U', unitName: 'Unidade',
                city: 'RJ', stateName: 'RJ', priceCents: 200, originalCents: 500,
                method: 'laser', wooId: String(wooId), qty: 1
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
              const add = await fetch('/wp-json/wc/store/v1/cart/add-item', {
                method: 'POST', credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json', Nonce: nonce },
                body: JSON.stringify({ id: wooId, quantity: 1, pm_catalog_id: catalogId })
              });
              const body = await add.json().catch(() => ({}));
              const totals = body.totals || {};
              const item = (body.items || [])[0] || {};
              const prices = item.prices || {};
              return {
                ok: add.ok,
                items: (body.items || []).length,
                total_price: totals.total_price,
                price: prices.price,
                regular: prices.regular_price,
                phase: window.__PM_BLACK_PHASE__ || null,
              };
            }""",
            {"wooId": WOO_ID, "catalogId": CATALOG_ID},
        )
        print("seed", seeded)
        if not seeded.get("ok") or int(seeded.get("total_price") or 0) != 200:
            raise SystemExit(f"seed price not R$2,00: {seeded}")

        page.goto(BASE + "/finalizar-pagamento/?pm=esquenta-charge", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function(
            """() => {
              const ui = Number(window.__pmCheckoutUiTotalCents || 0);
              const tot = (document.querySelector('input[name=totalamount]') || {}).value || '';
              const ready = window.pmBlackNov && window.pmBlackNov.ready && window.pmBlackNov.ready();
              return ready && ui === 200 && String(tot).replace(',', '.') === '2.00';
            }""",
            timeout=90000,
        )

        snap = page.evaluate(
            """() => {
              const totalamount = (document.querySelector('input[name=totalamount]') || {}).value || '';
              const fullvalue = (document.querySelector('input[name=fullvalue]') || {}).value || '';
              const ui = window.__pmCheckoutUiTotalCents;
              const phase = window.__PM_BLACK_PHASE__ || (window.pmBlackNov && window.pmBlackNov.phaseAt && window.pmBlackNov.phaseAt());
              const hasForm = !!document.querySelector('.wpcf7-form, form.wpcf7');
              return { totalamount, fullvalue, ui, phase, hasForm, c37: !!document.querySelector('script[src*=\"c37\"]') };
            }"""
        )
        print("checkout snap", snap)

        page.evaluate(
            """() => {
              const el = document.querySelector('input[name=\"declaracao\"]');
              if (el && !el.checked) {
                el.checked = true;
                el.dispatchEvent(new Event('change', { bubbles: true }));
              }
            }"""
        )

        test_email = f"teste.esquenta.{int(time.time())}@example.com"
        person = {
            "your-name": "Teste Esquenta PM",
            "your-email": test_email,
            "your-phone": "21988887777",
            "cpf": "52998224725",
            "cep": "22041080",
            "cidade": "Rio de Janeiro",
            "estado": "RJ",
            "endereco": "Rua Teste Esquenta",
            "bairro": "Copacabana",
            "numero": "10",
            "complemento": "Sala 1",
        }
        print("person", set_fields(page, person))
        page.wait_for_timeout(1200)
        set_fields(page, person)
        unit_info = page.evaluate(
            """(preferred) => {
              const sel = document.querySelector('select[name=\"unit\"]');
              const options = sel
                ? Array.from(sel.options).map((o) => ({ value: o.value, text: (o.textContent || '').trim() }))
                : [];
              let value = '';
              for (const pref of preferred) {
                const hit = options.find((o) => o.value === pref);
                if (hit) { value = hit.value; break; }
              }
              if (!value) {
                const first = options.find((o) => o.value);
                value = first ? first.value : '';
              }
              if (sel && value) {
                sel.value = value;
                sel.dispatchEvent(new Event('input', { bubbles: true }));
                sel.dispatchEvent(new Event('change', { bubbles: true }));
              }
              for (const name of ['easyunit', 'unit']) {
                const nodes = Array.from(document.querySelectorAll('[name=\"' + name + '\"]'));
                for (const el of nodes) {
                  if (el.tagName === 'SELECT') continue;
                  el.value = value;
                  el.dispatchEvent(new Event('input', { bubbles: true }));
                  el.dispatchEvent(new Event('change', { bubbles: true }));
                }
              }
              function setSelectOrHidden(names, val) {
                for (const name of names) {
                  const nodes = Array.from(document.querySelectorAll('[name=\"' + name + '\"]'));
                  for (const el of nodes) {
                    if (el.tagName === 'SELECT') {
                      const ok = Array.from(el.options).some((o) => o.value === val);
                      if (ok) el.value = val;
                      else if (el.options.length) {
                        const withVal = Array.from(el.options).find((o) => o.value);
                        if (withVal) el.value = withVal.value;
                      }
                    } else {
                      el.value = val;
                    }
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                  }
                }
              }
              setSelectOrHidden(['installments', 'cerainstallments', 'allinstallments', 'siteinstallment'], '1');
              return {
                value,
                options: options.slice(0, 12),
                unit: (document.querySelector('select[name=unit]') || {}).value || '',
                easyunit: (document.querySelector('[name=easyunit]') || {}).value || '',
                installments: (document.querySelector('[name=installments]') || {}).value || '',
                allinstallments: (document.querySelector('[name=allinstallments]') || {}).value || '',
              };
            }""",
            list(PREFERRED_UNITS),
        )
        print("unit", unit_info)
        if not unit_info.get("value"):
            raise SystemExit("no Accesstage unit available on form")

        pay_tab = page.locator(".nav-pills .nav-link", has_text="Pagamento")
        if pay_tab.count():
            pay_tab.first.click(force=True)
            page.wait_for_timeout(1000)

        # Reaplica unidade/parcelas após troca de tab (CF7 conditional fields)
        page.evaluate(
            """(unitValue) => {
              const sel = document.querySelector('select[name=\"unit\"]');
              if (sel && unitValue) {
                sel.value = unitValue;
                sel.dispatchEvent(new Event('change', { bubbles: true }));
              }
              for (const name of ['easyunit']) {
                const el = document.querySelector('[name=\"' + name + '\"]');
                if (el && unitValue) {
                  el.value = unitValue;
                  el.dispatchEvent(new Event('change', { bubbles: true }));
                }
              }
              for (const name of ['installments', 'cerainstallments', 'allinstallments', 'siteinstallment']) {
                const nodes = Array.from(document.querySelectorAll('[name=\"' + name + '\"]'));
                for (const el of nodes) {
                  if (el.tagName === 'SELECT') {
                    const one = Array.from(el.options).find((o) => o.value === '1') || Array.from(el.options).find((o) => o.value);
                    if (one) el.value = one.value;
                  } else {
                    el.value = '1';
                  }
                  el.dispatchEvent(new Event('change', { bubbles: true }));
                }
              }
            }""",
            unit_info.get("value") or "",
        )

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
        print("card fields", filled)
        if page.locator('input[name="holder"]:visible').count():
            page.locator('input[name="holder"]:visible').first.fill(card["holder"])
        if page.locator('input[name="cart-number"]:visible').count():
            page.locator('input[name="cart-number"]:visible').first.fill(card["number"])
        if page.locator('input[name="expiration"]:visible').count():
            page.locator('input[name="expiration"]:visible').first.fill(card["exp"])
        if page.locator('input[name="securityCode"]:visible').count():
            page.locator('input[name="securityCode"]:visible').first.fill(card["cvv"])

        page.evaluate(
            """() => {
              const el = document.querySelector('input[name=\"declaracao\"]');
              if (el) { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })); }
            }"""
        )

        response_info = {}
        try:
            with page.expect_response(
                lambda r: ("contact-form-7" in (r.url or ""))
                or ("wpcf7" in (r.url or ""))
                or ("admin-ajax.php" in (r.url or "")),
                timeout=120000,
            ) as resp_info:
                page.evaluate(
                    """() => {
                      const btn = document.querySelector('button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit');
                      if (btn) btn.click();
                    }"""
                )
            resp = resp_info.value
            response_info = {"status": resp.status, "url": resp.url, "body": (resp.text() or "")[:1500]}
        except Exception as err:
            response_info = {"error": str(err)}
            page.evaluate(
                """() => {
                  const btn = document.querySelector('button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit');
                  if (btn) btn.click();
                }"""
            )
        print("cf7", response_info)
        page.wait_for_timeout(25000)
        try:
            page.wait_for_function(
                """() => {
                  const f = document.querySelector('.wpcf7-form');
                  if (!f) return false;
                  return f.classList.contains('sent') || f.classList.contains('failed') || f.classList.contains('invalid') || f.classList.contains('spam');
                }""",
                timeout=90000,
            )
        except Exception as wait_err:
            print("wait form class", wait_err)
        result = page.evaluate(
            """() => ({
              className: (document.querySelector('.wpcf7-form') || {}).className || '',
              response: ((document.querySelector('.wpcf7-response-output') || {}).textContent || '').trim(),
              mailSent: !!document.querySelector('.wpcf7-form.sent, .wpcf7-mail-sent-ok'),
              invalid: !!document.querySelector('.wpcf7-not-valid, .wpcf7-validation-errors'),
              invalidFields: Array.from(document.querySelectorAll('.wpcf7-not-valid, .wpcf7-not-valid-tip')).map((el) => ({
                name: el.name || el.getAttribute('data-name') || '',
                text: (el.textContent || '').trim().slice(0, 120),
                className: el.className,
              })).slice(0, 20),
              unit: (document.querySelector('select[name=unit]') || {}).value || '',
              easyunit: (document.querySelector('[name=easyunit]') || {}).value || '',
              cardLen: String((document.querySelector('[name=cart-number]') || {}).value || '').replace(/\\D/g, '').length,
              url: location.href,
              totalamount: (document.querySelector('input[name=totalamount]') || {}).value || '',
            })"""
        )
        print("result", result)
        out = ROOT / "scripts" / "_charge_esquenta_test_ot_result.json"
        payload = {
            "email": test_email,
            "seed": seeded,
            "snap": snap,
            "unit": unit_info,
            "cf7": response_info,
            "result": result,
        }
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print("wrote", out)
        browser.close()

        received = re.search(r"order-received/(\d+)", str(result.get("url") or ""))
        mail_ok = bool(result.get("mailSent")) or ("sent" in str(result.get("className") or ""))
        success = bool(received) or mail_ok
        if success:
            time.sleep(3)
            if received:
                peek = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "_peek_order.py"), received.group(1)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                print(peek.stdout)
                try:
                    peeked = json.loads(peek.stdout)
                except json.JSONDecodeError:
                    peeked = {}
                if str(peeked.get("total")) != "2.00" or str(peeked.get("pm_cf7_totalamount")) != "2.00":
                    raise SystemExit(f"order {received.group(1)} total sync failed: {peeked}")
                print("REST assert OK order", received.group(1))
            else:
                rc = subprocess.call(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "_assert_accesstage_order_total.py"),
                        "--email",
                        test_email,
                        "--expect",
                        "2.00",
                    ]
                )
                if rc != 0:
                    raise SystemExit("REST assert failed after charge")
                print("REST assert OK for", test_email)
        else:
            print("CHARGE_BLOCKED", {"response": result.get("response"), "invalid": result.get("invalidFields")})
            raise SystemExit("charge did not complete")


if __name__ == "__main__":
    main()

