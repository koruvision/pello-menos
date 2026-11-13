# -*- coding: utf-8 -*-
"""Charge Esquenta R$2 com sync completo (linha+total) — fluxo robusto."""
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
OUT = ROOT / "scripts" / "_charge_ot_lines_sync_r2_result.json"
BASE = "https://pellomenosoficialteste.companygenesis.com.br"
WOO_ID = int(SKUS["pm-teste-esquenta-laser"])
CATALOG_ID = "pm-teste-esquenta-laser"


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
    subprocess.check_call(
        [sys.executable, str(ROOT / "scripts" / "_ot_test_skus_visibility.py"), "--mode", "publish", "--only", CATALOG_ID]
    )
    # ensure FORCE esquenta
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "_publish_accesstage_total_sync.py")])

    email = f"teste.linesync.{int(time.time())}@example.com"
    result = {"email": email}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(BASE + "/carrinho/?pm=linesync", wait_until="domcontentloaded", timeout=90000)
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
                  return { ok: add.ok, total_price: (body.totals || {}).total_price, items: (body.items || []).length };
                }""",
                {"wooId": WOO_ID, "catalogId": CATALOG_ID},
            )
            print("seed", seeded)
            result["seed"] = seeded
            if int(seeded.get("total_price") or 0) != 200:
                raise SystemExit(f"seed not 2.00: {seeded}")

            page.goto(BASE + "/finalizar-pagamento/?pm=linesync", wait_until="domcontentloaded", timeout=90000)
            page.wait_for_function(
                """() => {
                  const ui = Number(window.__pmCheckoutUiTotalCents || 0);
                  const tot = String((document.querySelector('input[name=totalamount]') || {}).value || '').replace(',', '.');
                  return ui === 200 && tot === '2.00';
                }""",
                timeout=90000,
            )

            person = {
                "your-name": "Teste Line Sync PM",
                "your-email": email,
                "your-phone": "21988887777",
                "cpf": "52998224725",
                "cep": "22041080",
                "cidade": "Rio de Janeiro",
                "estado": "RJ",
                "endereco": "Rua Line Sync",
                "bairro": "Copacabana",
                "numero": "10",
                "complemento": "1",
            }
            set_fields(page, person)
            page.wait_for_timeout(1000)
            set_fields(page, person)

            page.evaluate(
                """() => {
                  const el = document.querySelector('input[name=\"declaracao\"]');
                  if (el) { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })); }
                  const sel = document.querySelector('select[name=\"unit\"]');
                  if (sel) {
                    const opt = Array.from(sel.options).find((o) => o.value);
                    if (opt) { sel.value = opt.value; sel.dispatchEvent(new Event('change', { bubbles: true })); }
                  }
                  const easy = document.querySelector('[name=\"easyunit\"]');
                  if (easy && sel) { easy.value = sel.value; easy.dispatchEvent(new Event('change', { bubbles: true })); }
                  for (const name of ['installments','cerainstallments','allinstallments','siteinstallment']) {
                    for (const el of document.querySelectorAll('[name=\"'+name+'\"]')) {
                      if (el.tagName === 'SELECT') {
                        const one = Array.from(el.options).find((o) => String(o.value).startsWith('1')) || Array.from(el.options).find((o)=>o.value);
                        if (one) el.value = one.value;
                      } else el.value = '1';
                      el.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                  }
                }"""
            )

            pay = page.locator(".nav-pills .nav-link", has_text="Pagamento")
            if pay.count():
                pay.first.click(force=True)
                page.wait_for_timeout(1200)

            # re-apply after tab
            set_fields(page, person)
            page.evaluate(
                """(card) => {
                  const el = document.querySelector('input[name=\"declaracao\"]');
                  if (el) { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })); }
                  function set(name, value) {
                    for (const el of document.querySelectorAll('[name=\"'+name+'\"]')) {
                      if (el.type === 'hidden') continue;
                      el.focus(); el.value = value;
                      ['input','change','keyup','blur'].forEach((ev) => el.dispatchEvent(new Event(ev, { bubbles: true })));
                    }
                  }
                  set('holder', card.holder);
                  set('cart-number', card.number);
                  set('expiration', card.exp);
                  set('securityCode', card.cvv);
                  // force totalamount
                  for (const el of document.querySelectorAll('[name=\"totalamount\"]')) {
                    el.value = '2.00';
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                  }
                }""",
                card,
            )

            pre = page.evaluate(
                """() => ({
                  totalamount: (document.querySelector('input[name=totalamount]') || {}).value || '',
                  unit: (document.querySelector('select[name=unit]') || {}).value || '',
                  easyunit: (document.querySelector('[name=easyunit]') || {}).value || '',
                  cardLen: String((document.querySelector('[name=\"cart-number\"]') || {}).value || '').replace(/\\D/g,'').length,
                  declaracao: !!(document.querySelector('input[name=\"declaracao\"]') || {}).checked,
                })"""
            )
            print("pre-submit", pre)
            result["pre"] = pre

            # Submit: wait CF7 ajax then poll redirect
            cf7_body = {}
            try:
                with page.expect_response(
                    lambda r: ("contact-form-7" in (r.url or "")) or ("wpcf7" in (r.url or "")),
                    timeout=180000,
                ) as resp_info:
                    page.evaluate(
                        """() => {
                          const btn = document.querySelector('button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit');
                          if (btn) btn.click();
                        }"""
                    )
                resp = resp_info.value
                cf7_body = {"status": resp.status, "url": resp.url, "body": (resp.text() or "")[:2000]}
            except Exception as err:
                cf7_body = {"error": str(err)}
                page.evaluate(
                    """() => {
                      const btn = document.querySelector('button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit');
                      if (btn) btn.click();
                    }"""
                )
            print("cf7", {k: (v[:200] if k == "body" and isinstance(v, str) else v) for k, v in cf7_body.items()})
            result["cf7"] = cf7_body

            # Poll up to 3 min for thank-you URL or cookie redirect
            order_id = None
            for _ in range(60):
                url = page.url
                m = re.search(r"order-received/(\d+)", url)
                if m:
                    order_id = int(m.group(1))
                    break
                # follow redirectSuccess cookie if JS stalled
                redir = page.evaluate(
                    """() => {
                      const m = document.cookie.match(/(?:^|; )redirectSuccess=([^;]+)/);
                      return m ? decodeURIComponent(m[1]) : '';
                    }"""
                )
                if redir and "order-received" in redir:
                    page.goto(redir, wait_until="domcontentloaded", timeout=90000)
                    continue
                page.wait_for_timeout(3000)

            result["url"] = page.url
            result["order_id"] = order_id
            form = page.evaluate(
                """() => ({
                  className: (document.querySelector('.wpcf7-form') || {}).className || '',
                  response: ((document.querySelector('.wpcf7-response-output') || {}).textContent || '').trim(),
                })"""
            )
            result["form"] = form
            print("after", result["url"], "order", order_id, form)
            browser.close()
    finally:
        subprocess.call(
            [sys.executable, str(ROOT / "scripts" / "_ot_test_skus_visibility.py"), "--mode", "draft", "--only", CATALOG_ID]
        )

    if not result.get("order_id"):
        # last chance: search by email
        time.sleep(5)
        try:
            subprocess.check_call(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "_assert_accesstage_order_total.py"),
                    "--email",
                    email,
                    "--expect",
                    "2.00",
                ]
            )
        except subprocess.CalledProcessError:
            OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            raise SystemExit("no order created")

    time.sleep(2)
    peek = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "_peek_order.py"), str(result["order_id"])],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    order = json.loads(peek.stdout)
    result["order"] = order
    lines = order.get("lines") or []
    line_ok = bool(lines) and all(str(li.get("total")) == "2.00" for li in lines)
    total_ok = str(order.get("total")) == "2.00"
    meta_ok = str(order.get("pm_cf7_totalamount")) == "2.00"
    synced = str(order.get("lines_synced") or "") == "1"
    cents_ok = str(order.get("amount_cents") or "") == "200"
    result["checks"] = {
        "line_ok": line_ok,
        "total_ok": total_ok,
        "meta_ok": meta_ok,
        "synced": synced,
        "cents_ok": cents_ok,
        "accesstage": bool(order.get("accesstage")),
    }
    result["ok"] = all(result["checks"].values())
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["checks"], ensure_ascii=False))
    print("order", order)
    if not result["ok"]:
        raise SystemExit("LINE_SYNC_INCOMPLETE")
    print("LINES_SYNC_R2_OK", result["order_id"])


if __name__ == "__main__":
    main()
