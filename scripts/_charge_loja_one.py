# -*- coding: utf-8 -*-
"""Um charge Esquenta R$2 na loja com fill/select/parity robustos."""
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


FILL = """(cfg) => {
  function setText(name, value) {
    document.querySelectorAll('[name=\"'+name+'\"]').forEach((el) => {
      if (el.type === 'checkbox' || el.type === 'radio') return;
      el.removeAttribute('readonly'); el.removeAttribute('disabled');
      el.value = value;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
  }
  function setSelect(name, value) {
    document.querySelectorAll('select[name=\"'+name+'\"]').forEach((el) => {
      el.removeAttribute('disabled');
      let opt = Array.from(el.options).find((o) => o.value === value);
      if (!opt) opt = Array.from(el.options).find((o) => o.value);
      if (!opt) return;
      el.selectedIndex = opt.index;
      el.value = opt.value;
      el.classList.remove('first_null','not_chosen','wpcf7-not-valid');
      el.setAttribute('aria-invalid','false');
      if (window.jQuery) {
        try { window.jQuery(el).val(opt.value).trigger('change').trigger('chosen:updated'); } catch (e) {}
      }
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
  }
  Object.entries(cfg.person).forEach(([k,v]) => setText(k,v));
  setSelect('unit', cfg.unit);
  setSelect('easyunit', cfg.unit);
  setSelect('installments', '1x');
  setSelect('cerainstallments', '1x');
  setSelect('allinstallments', '1x');
  const decl = document.querySelector('input[name=\"declaracao\"]');
  if (decl) { decl.checked = true; decl.dispatchEvent(new Event('change', { bubbles: true })); }
  setText('holder', cfg.card.holder);
  setText('cart-number', cfg.card.number);
  setText('expiration', cfg.card.exp);
  setText('securityCode', cfg.card.cvv);
  setText('totalamount', '2.00');
  try {
    Object.defineProperty(window, '__pmCheckoutUiTotalCents', {
      configurable: true, get: () => 200, set: () => {}
    });
  } catch (e) { window.__pmCheckoutUiTotalCents = 200; }
  return {
    unit: (document.querySelector('select[name=unit]')||{}).value,
    easy: (document.querySelector('select[name=easyunit]')||{}).value,
    inst: (document.querySelector('select[name=installments]')||{}).value,
    cera: (document.querySelector('select[name=cerainstallments]')||{}).value,
    all: (document.querySelector('select[name=allinstallments]')||{}).value,
    total: (document.querySelector('input[name=totalamount]')||{}).value,
  };
}"""


def main():
    card = load_card()
    email = f"teste.loja.one.{int(time.time())}@example.com"
    unit = "RJ - Botafogo"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE + "/carrinho/?pm=one", wait_until="domcontentloaded", timeout=90000)
        page.evaluate(
            """async ({ wooId }) => {
              localStorage.setItem('pm-cart-v1', JSON.stringify([{
                lineId: 'pm-teste-esquenta-laser::U', id: 'pm-teste-esquenta-laser',
                name: 'PM Teste Esquenta Laser', priceCents: 200, originalCents: 500,
                method: 'laser', wooId: String(wooId), qty: 1, unitId: 'U', unitName: 'U'
              }]));
              localStorage.removeItem('pm-coupon-v1');
              const cartRes = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
              let nonce = cartRes.headers.get('Nonce') || '';
              const cart = await cartRes.json();
              for (const it of (cart.items || [])) {
                const rr = await fetch('/wp-json/wc/store/v1/cart/remove-item', {
                  method:'POST', credentials:'same-origin',
                  headers:{'Content-Type':'application/json', Nonce: nonce},
                  body: JSON.stringify({ key: it.key })
                });
                nonce = rr.headers.get('Nonce') || nonce;
              }
              const add = await fetch('/wp-json/wc/store/v1/cart/add-item', {
                method:'POST', credentials:'same-origin',
                headers:{'Content-Type':'application/json', Nonce: nonce},
                body: JSON.stringify({ id: wooId, quantity: 1, pm_catalog_id: 'pm-teste-esquenta-laser' })
              });
              return add.json();
            }""",
            {"wooId": WOO_ID},
        )
        page.goto(BASE + "/finalizar-pagamento/?pm=one", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function(
            """() => String((document.querySelector('input[name=totalamount]')||{}).value||'').replace(',','.')==='2.00'""",
            timeout=90000,
        )
        person = {
            "your-name": "Teste Loja One",
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
        cfg = {"person": person, "card": card, "unit": unit}
        print("fill1", page.evaluate(FILL, cfg))
        # Playwright native selects
        page.locator("select[name='unit']").select_option(value=unit)
        pay = page.locator(".nav-pills .nav-link", has_text="Pagamento")
        if pay.count():
            pay.first.click(force=True)
            page.wait_for_timeout(1500)
        for name, val in (
            ("unit", unit),
            ("easyunit", unit),
            ("installments", "1x"),
            ("cerainstallments", "1x"),
            ("allinstallments", "1x"),
        ):
            loc = page.locator(f"select[name='{name}']")
            if loc.count():
                try:
                    loc.first.select_option(value=val, force=True)
                except Exception as err:
                    print("select fail", name, err)
        print("fill2", page.evaluate(FILL, cfg))

        cf7 = {}
        order_id = None
        try:
            with page.expect_navigation(timeout=180000, wait_until="domcontentloaded"):
                with page.expect_response(
                    lambda r: "contact-form-7" in (r.url or "") or "wpcf7" in (r.url or ""),
                    timeout=180000,
                ) as ri:
                    page.evaluate(
                        """() => {
                          const btn = document.querySelector('button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit');
                          if (!btn) return;
                          btn.removeAttribute('disabled');
                          btn.setAttribute('data-pm-cart-synced', '1');
                          btn.click();
                        }"""
                    )
                r = ri.value
                try:
                    body = r.text()
                except Exception:
                    body = ""
                cf7 = {"status": r.status, "body": body[:2000]}
        except Exception as err:
            cf7 = {"error": str(err), "url": page.url}
        print("cf7", cf7)
        print("url_after_submit", page.url)

        for _ in range(40):
            m = re.search(r"order-received/(\d+)", page.url)
            if m:
                order_id = int(m.group(1))
                break
            try:
                redir = page.evaluate(
                    """() => { const m=document.cookie.match(/(?:^|; )redirectSuccess=([^;]+)/); return m?decodeURIComponent(m[1]):''; }"""
                )
            except Exception:
                redir = ""
            if redir and "order-received" in redir:
                page.goto(redir, wait_until="domcontentloaded", timeout=90000)
                continue
            # fallback: REST by email
            page.wait_for_timeout(2000)
            break
        if not order_id:
            # search recent by email via peek helper inline
            import base64
            import urllib.parse
            import urllib.request
            from pathlib import Path as P

            e = {}
            for line in (ROOT / "projeto-migracao" / ".secrets" / "loja.env").read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    e[k.strip().lstrip("\ufeff")] = v.strip()
            auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
            q = urllib.parse.urlencode({"search": email, "per_page": 5, "orderby": "date", "order": "desc"})
            req = urllib.request.Request(
                e["PM_LOJA_URL"].rstrip("/") + "/wp-json/wc/v3/orders?" + q,
                headers={"Authorization": "Basic " + auth, "Accept": "application/json"},
            )
            try:
                rows = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
                for o in rows or []:
                    if ((o.get("billing") or {}).get("email") or "").lower() == email.lower():
                        order_id = int(o["id"])
                        break
                print("rest_search", [(o.get("id"), (o.get("billing") or {}).get("email"), o.get("total")) for o in (rows or [])])
            except Exception as err:
                print("rest_search_err", err)
        print("order_id", order_id, "url", page.url)
        if order_id:
            peek = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "_peek_loja_order.py"), str(order_id)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            print(peek.stdout)
            Path("scripts/_charge_loja_one_result.json").write_text(peek.stdout, encoding="utf-8")
        else:
            Path("scripts/_charge_loja_one_result.json").write_text(
                json.dumps({"ok": False, "cf7": cf7, "after": after, "email": email}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            raise SystemExit("NO_ORDER")
        browser.close()
    print("LOJA_ONE_OK")


if __name__ == "__main__":
    main()
