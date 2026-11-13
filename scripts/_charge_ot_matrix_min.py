# -*- coding: utf-8 -*-
"""Charges mínimos OT: normal / cupom / Esquenta / Black Week (R$1,50–R$2)."""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
CARD_ENV = ROOT / "projeto-migracao" / ".secrets" / "ot-test-card.env"
SNIPPET_SRC = ROOT / "scripts" / "pm_black_nov_snippet.php"
SKUS = json.loads((ROOT / "scripts" / "_ot_esquenta_test_skus.json").read_text(encoding="utf-8"))
OUT = ROOT / "scripts" / "_charge_ot_matrix_min_result.json"
BASE = "https://pellomenosoficialteste.companygenesis.com.br"
NORMAL_ID = 48216
LASER_ID = int(SKUS["pm-teste-esquenta-laser"])
LASER_CATALOG = "pm-teste-esquenta-laser"

CASES = [
    {
        "id": "normal",
        "force": "off",
        "woo_id": NORMAL_ID,
        "catalog_id": None,
        "coupon": False,
        "expect_ui_cents": 199,
        "expect_total": "1.99",
        "local_price": 199,
        "local_original": 199,
        "method": "produto",
        "name": "Produto R$ 1,99",
    },
    {
        "id": "normal_coupon",
        "force": "off",
        "woo_id": NORMAL_ID,
        "catalog_id": None,
        "coupon": True,
        "expect_ui_cents": 189,
        "expect_total": "1.89",
        "local_price": 199,
        "local_original": 199,
        "method": "produto",
        "name": "Produto R$ 1,99",
    },
    {
        "id": "esquenta_laser",
        "force": "esquenta",
        "woo_id": LASER_ID,
        "catalog_id": LASER_CATALOG,
        "coupon": False,
        "expect_ui_cents": 200,
        "expect_total": "2.00",
        "local_price": 200,
        "local_original": 500,
        "method": "laser",
        "name": "PM Teste Esquenta Laser",
    },
    {
        "id": "black_week_laser",
        "force": "black_week",
        "woo_id": LASER_ID,
        "catalog_id": LASER_CATALOG,
        "coupon": False,
        "expect_ui_cents": 150,
        "expect_total": "1.50",
        "local_price": 150,
        "local_original": 500,
        "method": "laser",
        "name": "PM Teste Black Week Laser",
    },
    {
        "id": "esquenta_laser_coupon",
        "force": "esquenta",
        "woo_id": LASER_ID,
        "catalog_id": LASER_CATALOG,
        "coupon": True,
        "expect_ui_cents": 190,
        "expect_total": "1.90",
        "local_price": 200,
        "local_original": 500,
        "method": "laser",
        "name": "PM Teste Esquenta Laser Cupom",
    },
]


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def wp_call(method, path, payload=None):
    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    token = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
        "User-Agent": "pm-charge-matrix",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body.strip()[:1] in "{[" else body
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            return err.code, json.loads(body)
        except json.JSONDecodeError:
            return err.code, body[:400]


def put_force(force: str):
    code = SNIPPET_SRC.read_text(encoding="utf-8").replace(
        "define('PM_BLACK_NOV_FORCE', '');",
        f"define('PM_BLACK_NOV_FORCE', '{force}');",
        1,
    )
    st, sn = wp_call("GET", "/wp-json/code-snippets/v1/snippets/24")
    payload = {
        "name": sn.get("name") or "pm-black-nov-pricing",
        "code": code,
        "scope": "global",
        "active": True,
    }
    st, saved = wp_call("PUT", "/wp-json/code-snippets/v1/snippets/24", payload)
    print("FORCE", force, st, isinstance(saved, dict) and saved.get("active"))


def set_product_status(pid: int, status: str):
    st, body = wp_call(
        "PUT",
        f"/wp-json/wc/v3/products/{pid}",
        {"status": status, "catalog_visibility": "hidden" if pid == LASER_ID else "visible"},
    )
    print("product", pid, status, st, body.get("status") if isinstance(body, dict) else body)


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


def run_case(page, card, case):
    email = f"teste.matrix.{case['id']}.{int(time.time())}@example.com"
    put_force(case["force"])
    time.sleep(1)

    page.goto(BASE + f"/carrinho/?pm=matrix-{case['id']}", wait_until="domcontentloaded", timeout=90000)
    seeded = page.evaluate(
        """async (cfg) => {
          const line = {
            lineId: (cfg.catalogId || ('p'+cfg.wooId)) + '::U',
            id: cfg.catalogId || ('p'+cfg.wooId),
            name: cfg.name,
            image: '', duration: 'Ensaio', sku: cfg.catalogId || ('p'+cfg.wooId),
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
          const totals = body.totals || {};
          return {
            ok: add.ok,
            total_price: totals.total_price,
            discount: totals.total_discount,
            coupons: (body.coupons || []).map((x) => x.code),
            items: (body.items || []).length,
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
        return {
            "id": case["id"],
            "ok": False,
            "stage": "seed",
            "seeded": seeded,
            "email": email,
        }

    page.goto(BASE + f"/finalizar-pagamento/?pm=matrix-{case['id']}", wait_until="domcontentloaded", timeout=90000)
    expect = case["expect_ui_cents"]
    expect_major = case["expect_total"]
    try:
        page.wait_for_function(
            """({ expect, major }) => {
              const ui = Number(window.__pmCheckoutUiTotalCents || 0);
              const tot = String((document.querySelector('input[name=totalamount]') || {}).value || '').replace(',', '.');
              const ready = !window.pmBlackNov || (window.pmBlackNov.ready && window.pmBlackNov.ready());
              return ready && ui === expect && tot === major;
            }""",
            arg={"expect": expect, "major": expect_major},
            timeout=90000,
        )
    except Exception as err:
        snap = page.evaluate(
            """() => ({
              ui: window.__pmCheckoutUiTotalCents,
              totalamount: (document.querySelector('input[name=totalamount]') || {}).value || '',
              phase: window.__PM_BLACK_PHASE__ || null,
            })"""
        )
        return {
            "id": case["id"],
            "ok": False,
            "stage": "checkout_wait",
            "error": str(err),
            "snap": snap,
            "email": email,
        }

    page.evaluate(
        """() => {
          const el = document.querySelector('input[name=\"declaracao\"]');
          if (el) { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })); }
        }"""
    )
    person = {
        "your-name": f"Teste Matrix {case['id']}",
        "your-email": email,
        "your-phone": "21988887777",
        "cpf": "52998224725",
        "cep": "22041080",
        "cidade": "Rio de Janeiro",
        "estado": "RJ",
        "endereco": "Rua Teste Matrix",
        "bairro": "Copacabana",
        "numero": "10",
        "complemento": "Apto 1",
    }
    set_fields(page, person)
    page.wait_for_timeout(800)
    set_fields(page, person)

    page.evaluate(
        """() => {
          const sel = document.querySelector('select[name=\"unit\"]');
          if (sel) {
            const opt = Array.from(sel.options).find((o) => o.value);
            if (opt) {
              sel.value = opt.value;
              sel.dispatchEvent(new Event('change', { bubbles: true }));
            }
          }
          const easy = document.querySelector('[name=\"easyunit\"]');
          if (easy && sel && sel.value) {
            easy.value = sel.value;
            easy.dispatchEvent(new Event('change', { bubbles: true }));
          }
          for (const name of ['installments', 'cerainstallments', 'allinstallments', 'siteinstallment']) {
            const nodes = Array.from(document.querySelectorAll('[name=\"' + name + '\"]'));
            for (const el of nodes) {
              if (el.tagName === 'SELECT') {
                const one = Array.from(el.options).find((o) => String(o.value).startsWith('1')) || Array.from(el.options).find((o) => o.value);
                if (one) el.value = one.value;
              } else el.value = '1';
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
          }
        }"""
    )

    pay_tab = page.locator(".nav-pills .nav-link", has_text="Pagamento")
    if pay_tab.count():
        pay_tab.first.click(force=True)
        page.wait_for_timeout(1000)

    page.evaluate(
        """(card) => {
          function set(name, value) {
            for (const el of Array.from(document.querySelectorAll('[name=\"' + name + '\"]'))) {
              if (el.type === 'hidden') continue;
              el.focus(); el.value = value;
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
          }
          set('holder', card.holder);
          set('cart-number', card.number);
          set('expiration', card.exp);
          set('securityCode', card.cvv);
        }""",
        card,
    )
    page.evaluate(
        """() => {
          const el = document.querySelector('input[name=\"declaracao\"]');
          if (el) { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })); }
        }"""
    )

    try:
        with page.expect_navigation(timeout=180000):
            page.evaluate(
                """() => {
                  const btn = document.querySelector('button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit');
                  if (btn) btn.click();
                }"""
            )
    except Exception:
        page.wait_for_timeout(20000)

    url = page.url
    received = re.search(r"order-received/(\d+)", url)
    result = {
        "id": case["id"],
        "email": email,
        "force": case["force"],
        "expect_total": case["expect_total"],
        "url": url,
        "order_id": int(received.group(1)) if received else None,
        "ok": False,
    }
    if not received:
        result["stage"] = "no_order_received"
        result["form"] = page.evaluate(
            """() => ({
              className: (document.querySelector('.wpcf7-form') || {}).className || '',
              response: ((document.querySelector('.wpcf7-response-output') || {}).textContent || '').trim(),
              totalamount: (document.querySelector('input[name=totalamount]') || {}).value || '',
            })"""
        )
        return result

    time.sleep(3)
    peek = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "_peek_order.py"), str(result["order_id"])],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    try:
        order = json.loads(peek.stdout)
    except json.JSONDecodeError:
        order = {"raw": peek.stdout[:500]}
    result["order"] = order
    total_ok = str(order.get("total")) == case["expect_total"]
    meta_ok = str(order.get("pm_cf7_totalamount")) == case["expect_total"]
    acces_ok = bool(order.get("accesstage"))
    result["ok"] = bool(total_ok and meta_ok and acces_ok)
    result["checks"] = {"total_ok": total_ok, "meta_ok": meta_ok, "acces_ok": acces_ok}
    print("ORDER", case["id"], result["order_id"], order.get("total"), order.get("pm_cf7_totalamount"), result["ok"])
    return result


def main():
    card = load_card()
    set_product_status(LASER_ID, "publish")
    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            for case in CASES:
                print("\n====", case["id"], case["expect_total"], "====")
                try:
                    results.append(run_case(page, card, case))
                except Exception as err:
                    results.append({"id": case["id"], "ok": False, "error": str(err)})
                # fresh context cookies between charges
                page.context.clear_cookies()
                page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
            browser.close()
    finally:
        set_product_status(LASER_ID, "draft")
        put_force("esquenta")

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
        raise SystemExit("CHARGE_MATRIX_FAIL")
    print("CHARGE_MATRIX_OK")


if __name__ == "__main__":
    main()
