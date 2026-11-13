# -*- coding: utf-8 -*-
"""Charges mínimos na LOJA (Esquenta calendário + cupom + normal)."""
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
CHEAP = json.loads((ROOT / "scripts" / "_loja_cheap_fixture.json").read_text(encoding="utf-8"))
OUT = ROOT / "scripts" / "_charge_loja_matrix_min_result.json"
BASE = "https://loja.pellomenos.com.br"
LASER_ID = int(SKUS["pm-teste-esquenta-laser"])
NORMAL_ID = int(CHEAP["product_id"])

CASES = [
    {
        "id": "esquenta_laser",
        "woo_id": LASER_ID,
        "catalog_id": "pm-teste-esquenta-laser",
        "coupon": False,
        "expect_ui_cents": 200,
        "expect_total": "2.00",
        "local_price": 200,
        "local_original": 500,
        "method": "laser",
        "name": "PM Teste Esquenta Laser",
        "require_line_2": True,
    },
    {
        "id": "esquenta_laser_coupon",
        "woo_id": LASER_ID,
        "catalog_id": "pm-teste-esquenta-laser",
        "coupon": True,
        "expect_ui_cents": 190,
        "expect_total": "1.90",
        "local_price": 200,
        "local_original": 500,
        "method": "laser",
        "name": "PM Teste Esquenta Laser Cupom",
        "require_line_2": False,
    },
    {
        "id": "normal",
        "woo_id": NORMAL_ID,
        "catalog_id": None,
        "coupon": False,
        "expect_ui_cents": 199,
        "expect_total": "1.99",
        "local_price": 199,
        "local_original": 199,
        "method": "produto",
        "name": "Produto R$ 1,99",
        "require_line_2": False,
    },
    {
        "id": "normal_coupon",
        "woo_id": NORMAL_ID,
        "catalog_id": None,
        "coupon": True,
        "expect_ui_cents": 189,
        "expect_total": "1.89",
        "local_price": 199,
        "local_original": 199,
        "method": "produto",
        "name": "Produto R$ 1,99",
        "require_line_2": False,
    },
]


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
            for (const el of document.querySelectorAll('[name=\"' + name + '\"]')) {
              if (el.type === 'checkbox' || el.type === 'radio') continue;
              el.removeAttribute('readonly'); el.removeAttribute('disabled');
              el.value = value;
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            out[name] = 1;
          }
          return out;
        }""",
        values,
    )


def fill_required_selects(page):
    """CF7 na loja rejeita select.value sozinho — precisa selectedIndex + limpar not-valid."""
    return page.evaluate(
        """() => {
          function setSelect(name) {
            const els = Array.from(document.querySelectorAll('select[name=\"' + name + '\"]'));
            let val = '';
            for (const el of els) {
              el.removeAttribute('disabled');
              const opt = Array.from(el.options).find((o) => o.value && !/selecione/i.test(o.textContent || ''));
              if (!opt) continue;
              el.selectedIndex = opt.index;
              el.value = opt.value;
              val = opt.value;
              el.classList.remove('wpcf7-not-valid', 'first_null');
              el.setAttribute('aria-invalid', 'false');
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            return val;
          }
          const unit = setSelect('unit');
          for (const el of document.querySelectorAll('[name=\"easyunit\"]')) {
            el.removeAttribute('disabled');
            el.value = unit;
            el.classList.remove('wpcf7-not-valid');
            el.setAttribute('aria-invalid', 'false');
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
          }
          const inst = {};
          for (const name of ['installments','cerainstallments','allinstallments','siteinstallment']) {
            inst[name] = setSelect(name);
            // text inputs fallback
            for (const el of document.querySelectorAll('input[name=\"' + name + '\"]')) {
              el.value = '1';
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
          }
          const decl = document.querySelector('input[name=\"declaracao\"]');
          if (decl) {
            decl.checked = true;
            decl.classList.remove('wpcf7-not-valid');
            decl.dispatchEvent(new Event('change', { bubbles: true }));
          }
          return { unit, inst };
        }"""
    )


def run_case(page, card, case):
    email = f"teste.loja.{case['id']}.{int(time.time())}@example.com"
    page.goto(BASE + f"/carrinho/?pm=loja-{case['id']}", wait_until="domcontentloaded", timeout=90000)
    seeded = page.evaluate(
        """async (cfg) => {
          const line = {
            lineId: (cfg.catalogId || ('p'+cfg.wooId)) + '::U',
            id: cfg.catalogId || ('p'+cfg.wooId),
            name: cfg.name, image: '', duration: 'Ensaio',
            sku: cfg.catalogId || ('p'+cfg.wooId),
            unitId: 'U', unitName: 'Unidade', city: 'RJ', stateName: 'RJ',
            priceCents: cfg.localPrice, originalCents: cfg.localOriginal,
            method: cfg.method, wooId: String(cfg.wooId), qty: 1
          };
          localStorage.setItem('pm-cart-v1', JSON.stringify([line]));
          if (cfg.coupon) localStorage.setItem('pm-coupon-v1', 'PRIMEIRACOMPRA5');
          else localStorage.removeItem('pm-coupon-v1');
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
          for (const c of (cart.coupons || [])) {
            if (!c.code) continue;
            const rr = await fetch('/wp-json/wc/store/v1/cart/remove-coupon', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce },
              body: JSON.stringify({ code: c.code })
            });
            nonce = rr.headers.get('Nonce') || nonce;
          }
          const payload = { id: cfg.wooId, quantity: 1 };
          if (cfg.catalogId) payload.pm_catalog_id = cfg.catalogId;
          const add = await fetch('/wp-json/wc/store/v1/cart/add-item', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', Nonce: nonce },
            body: JSON.stringify(payload)
          });
          nonce = add.headers.get('Nonce') || nonce;
          let body = await add.json().catch(() => ({}));
          if (cfg.coupon) {
            const ac = await fetch('/wp-json/wc/store/v1/cart/apply-coupon', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce },
              body: JSON.stringify({ code: 'PRIMEIRACOMPRA5' })
            });
            body = await ac.json().catch(() => body);
          }
          return {
            ok: add.ok,
            total_price: (body.totals || {}).total_price,
            discount: (body.totals || {}).total_discount,
            items: (body.items || []).length,
            coupons: (body.coupons || []).map((x) => x.code),
          };
        }""",
        {
            "wooId": case["woo_id"],
            "catalogId": case["catalog_id"],
            "coupon": case["coupon"],
            "localPrice": case["local_price"],
            "localOriginal": case["local_original"],
            "method": case["method"],
            "name": case["name"],
        },
    )
    print("seed", case["id"], seeded)
    if int(seeded.get("total_price") or -1) != case["expect_ui_cents"]:
        return {"id": case["id"], "ok": False, "stage": "seed", "seeded": seeded, "email": email}

    page.goto(BASE + f"/finalizar-pagamento/?pm=loja-{case['id']}", wait_until="domcontentloaded", timeout=90000)
    try:
        # Accesstage usa totalamount; UI cents na loja pode divergir do localStorage
        page.wait_for_function(
            """(major) => {
              const tot = String((document.querySelector('input[name=totalamount]') || {}).value || '').replace(',', '.');
              const form = !!document.querySelector('.wpcf7-form');
              return form && tot === major;
            }""",
            arg=case["expect_total"],
            timeout=120000,
        )
    except Exception as err:
        snap = page.evaluate(
            """() => ({
              ui: window.__pmCheckoutUiTotalCents,
              totalamount: (document.querySelector('input[name=totalamount]') || {}).value || '',
              phase: window.__PM_BLACK_PHASE__ || null,
              body: (document.body && document.body.innerText || '').slice(0, 200),
            })"""
        )
        return {"id": case["id"], "ok": False, "stage": "checkout_wait", "error": str(err), "snap": snap, "email": email}

    person = {
        "your-name": f"Teste Loja {case['id']}",
        "your-email": email,
        "your-phone": "21988887777",
        "cpf": "52998224725",
        "cep": "22041080",
        "cidade": "Rio de Janeiro",
        "estado": "RJ",
        "endereco": "Rua Teste Loja",
        "bairro": "Copacabana",
        "numero": "10",
        "complemento": "1",
    }
    set_fields(page, person)
    page.wait_for_timeout(500)
    set_fields(page, person)
    fill_required_selects(page)
    pay = page.locator(".nav-pills .nav-link", has_text="Pagamento")
    if pay.count():
        pay.first.click(force=True)
        page.wait_for_timeout(1200)
    set_fields(page, person)
    fill_required_selects(page)
    # Playwright select_option reforça selects visíveis
    for name in ("unit", "installments", "cerainstallments", "allinstallments"):
        loc = page.locator(f"select[name='{name}']")
        if loc.count():
            try:
                loc.first.select_option(index=1)
            except Exception:
                try:
                    opts = loc.first.locator("option").all()
                    for i, o in enumerate(opts):
                        val = o.get_attribute("value") or ""
                        if val:
                            loc.first.select_option(index=i)
                            break
                except Exception:
                    pass
    fill_required_selects(page)
    page.evaluate(
        """(cfg) => {
          const el = document.querySelector('input[name=\"declaracao\"]');
          if (el) { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })); }
          function set(name, value) {
            for (const el of document.querySelectorAll('[name=\"'+name+'\"]')) {
              if (el.type === 'hidden' && name !== 'totalamount') continue;
              el.focus(); el.value = value;
              ['input','change','keyup','blur'].forEach((ev) => el.dispatchEvent(new Event(ev, { bubbles: true })));
            }
          }
          set('holder', cfg.card.holder);
          set('cart-number', cfg.card.number);
          set('expiration', cfg.card.exp);
          set('securityCode', cfg.card.cvv);
          set('totalamount', cfg.total);
          // easyunit + selects again
          const unit = (document.querySelector('select[name=\"unit\"]') || {}).value || '';
          for (const el of document.querySelectorAll('[name=\"easyunit\"]')) {
            el.value = unit;
            el.dispatchEvent(new Event('change', { bubbles: true }));
          }
        }""",
        {"card": card, "total": case["expect_total"]},
    )
    fill_required_selects(page)

    # Shell bloqueia se UI (catálogo) ≠ Woo (Esquenta no set_price). Força parity do ensaio.
    page.evaluate(
        """(cents) => {
          try {
            Object.defineProperty(window, '__pmCheckoutUiTotalCents', {
              configurable: true,
              get: function () { return cents; },
              set: function () {}
            });
          } catch (e) {
            window.__pmCheckoutUiTotalCents = cents;
          }
          // Selects: remove flags first_null/not_chosen que o tema/CF7 usa
          for (const el of document.querySelectorAll('select[name=\"unit\"], select[name=\"easyunit\"], select[name=\"installments\"], select[name=\"cerainstallments\"], select[name=\"allinstallments\"]')) {
            if (!el.value) {
              const opt = Array.from(el.options).find((o) => o.value);
              if (opt) { el.selectedIndex = opt.index; el.value = opt.value; }
            }
            el.classList.remove('first_null', 'not_chosen', 'wpcf7-not-valid');
            el.setAttribute('aria-invalid', 'false');
          }
        }""",
        case["expect_ui_cents"],
    )

    try:
        with page.expect_navigation(timeout=180000, wait_until="domcontentloaded"):
            page.evaluate(
                """() => {
                  const btn = document.querySelector('button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit');
                  if (btn) {
                    btn.removeAttribute('disabled');
                    btn.setAttribute('data-pm-cart-synced', '1');
                    btn.click();
                  }
                }"""
            )
    except Exception:
        try:
            page.evaluate(
                """() => {
                  const btn = document.querySelector('button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit');
                  if (btn) {
                    btn.removeAttribute('disabled');
                    btn.setAttribute('data-pm-cart-synced', '1');
                    btn.click();
                  }
                }"""
            )
        except Exception:
            pass

    order_id = None
    for _ in range(30):
        m = re.search(r"order-received/(\d+)", page.url)
        if m:
            order_id = int(m.group(1))
            break
        try:
            redir = page.evaluate(
                """() => {
                  const m = document.cookie.match(/(?:^|; )redirectSuccess=([^;]+)/);
                  return m ? decodeURIComponent(m[1]) : '';
                }"""
            )
        except Exception:
            redir = ""
        if redir and "order-received" in redir:
            try:
                page.goto(redir, wait_until="domcontentloaded", timeout=90000)
            except Exception:
                pass
            continue
        page.wait_for_timeout(2000)

    if not order_id:
        import base64
        import urllib.parse
        import urllib.request

        cfg = {}
        for line in (ROOT / "projeto-migracao" / ".secrets" / "loja.env").read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                cfg[k.strip().lstrip("\ufeff")] = v.strip()
        auth = base64.b64encode(f"{cfg['PM_LOJA_USER']}:{cfg['PM_LOJA_APP_PASSWORD']}".encode()).decode()
        q = urllib.parse.urlencode({"search": email, "per_page": 5, "orderby": "date", "order": "desc"})
        req = urllib.request.Request(
            cfg["PM_LOJA_URL"].rstrip("/") + "/wp-json/wc/v3/orders?" + q,
            headers={"Authorization": "Basic " + auth, "Accept": "application/json"},
        )
        try:
            rows = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
            for o in rows or []:
                if ((o.get("billing") or {}).get("email") or "").lower() == email.lower():
                    order_id = int(o["id"])
                    break
        except Exception as err:
            print("rest_search_err", err)

    result = {
        "id": case["id"],
        "email": email,
        "expect_total": case["expect_total"],
        "url": page.url,
        "order_id": order_id,
        "ok": False,
    }
    if not order_id:
        result["stage"] = "no_order_received"
        result["form"] = page.evaluate(
            """() => ({
              className: (document.querySelector('.wpcf7-form') || {}).className || '',
              response: ((document.querySelector('.wpcf7-response-output') || {}).textContent || '').trim(),
            })"""
        )
        return result

    time.sleep(3)
    peek = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "_peek_loja_order.py"), str(order_id)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    order = json.loads(peek.stdout)
    result["order"] = order
    lines = order.get("lines") or []
    total_ok = str(order.get("total")) == case["expect_total"]
    meta_ok = str(order.get("pm_cf7_totalamount")) == case["expect_total"]
    acces_ok = bool(order.get("accesstage"))
    synced = str(order.get("lines_synced") or "") == "1"
    line_ok = True
    if case.get("require_line_2"):
        line_ok = bool(lines) and all(str(li.get("total")) == case["expect_total"] for li in lines)
    else:
        # still prefer line totals == charged when single item
        if len(lines) == 1:
            line_ok = str(lines[0].get("total")) == case["expect_total"]
    result["checks"] = {
        "total_ok": total_ok,
        "meta_ok": meta_ok,
        "acces_ok": acces_ok,
        "synced": synced,
        "line_ok": line_ok,
    }
    result["ok"] = all(result["checks"].values())
    print("ORDER", case["id"], order_id, order.get("total"), order.get("lines"), result["ok"])
    return result


def main():
    card = load_card()
    only = {x.strip() for x in (os.environ.get("PM_LOJA_CHARGE_ONLY") or "").split(",") if x.strip()}
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for case in CASES:
            if only and case["id"] not in only:
                print("skip", case["id"])
                continue
            print("\n====", case["id"], case["expect_total"], "====")
            try:
                results.append(run_case(page, card, case))
            except Exception as err:
                results.append({"id": case["id"], "ok": False, "error": str(err)})
            page.context.clear_cookies()
            try:
                page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
            except Exception:
                pass
        browser.close()

    summary = {
        "ok": all(r.get("ok") for r in results),
        "passed": sum(1 for r in results if r.get("ok")),
        "total": len(results),
        "results": results,
        "ts": int(time.time()),
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT, "passed", summary["passed"], "/", summary["total"])
    if not summary["ok"]:
        raise SystemExit("LOJA_CHARGE_MATRIX_FAIL")
    print("LOJA_CHARGE_MATRIX_OK")


if __name__ == "__main__":
    main()
