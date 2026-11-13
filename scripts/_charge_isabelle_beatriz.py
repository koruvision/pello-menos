# -*- coding: utf-8 -*-
"""Charges regressão Isabelle + Beatriz com PMTESTE2 líquido R$1,00."""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
CARD_ENV = ROOT / "projeto-migracao" / ".secrets" / "ot-test-card.env"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
OUT = ROOT / "scripts" / "_charge_isabelle_beatriz_result.json"
BASE = "https://loja.pellomenos.com.br"
COUPON_ID = 49523
COUPON = "PMTESTE2"

ISABELLE = [
    ("esfoliacao-nadegas", "ipa"),
    ("esfoliacao-coxa", "ipa"),
    ("coxa-cera", "ipa"),
    ("virilha-cavada-cera", "ipa"),
]
BEATRIZ = [
    ("faixa-cera", "bot"),
    ("faixa-cera", "bot"),
    ("axila-cera", "bot"),
    ("buco-cera", "bot"),
    ("sobrancelha-cera", "bot"),
]


def load_env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


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


def admin(method, path, payload=None):
    e = load_env()
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        e["PM_LOJA_URL"].rstrip("/") + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + auth,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "pm-charge-isa-bea",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode()
            return r.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode()
        try:
            return err.code, json.loads(body)
        except Exception:
            return err.code, {"raw": body[:400]}


def set_coupon_major(reais: str):
    st, c = admin(
        "PUT",
        f"/wp-json/wc/v3/coupons/{COUPON_ID}",
        {"status": "publish", "amount": reais, "discount_type": "fixed_cart"},
    )
    print("coupon", st, c.get("amount") if isinstance(c, dict) else c)


def names():
    return {
        "esfoliacao-nadegas": "Esfoliação de nádegas",
        "esfoliacao-coxa": "Esfoliação de coxa",
        "coxa-cera": "Coxa – Cera",
        "virilha-cavada-cera": "Virilha Cavada – Cera",
        "faixa-cera": "Faixa – Cera",
        "axila-cera": "Axila – Cera",
        "buco-cera": "Buço – Cera",
        "sobrancelha-cera": "Sobrancelha – Cera",
    }


def build_local(bridge, lines):
    nm = names()
    out = []
    for pid, unit in lines:
        out.append(
            {
                "lineId": f"{pid}::{unit}",
                "id": pid,
                "name": nm.get(pid, pid),
                "image": "",
                "duration": "",
                "sku": "PM",
                "unitId": unit,
                "unitName": "Botafogo" if unit == "bot" else "Ipanema",
                "city": "Rio de Janeiro",
                "stateName": "RJ",
                "priceCents": 2121,
                "wooId": str(bridge[pid]["units"][unit]["variationId"]),
                "wooKey": "",
                "qty": 1,
            }
        )
    return out


def set_fields(page, values):
    page.evaluate(
        """(values) => {
          for (const [name, value] of Object.entries(values)) {
            for (const el of document.querySelectorAll('[name=\"' + name + '\"]')) {
              if (el.type === 'checkbox' || el.type === 'radio') continue;
              el.removeAttribute('readonly'); el.removeAttribute('disabled');
              el.value = value;
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
          }
        }""",
        values,
    )


def fill_selects(page, prefer_unit_text: str):
    page.evaluate(
        """(prefer) => {
          function setSelect(name, preferText) {
            for (const el of document.querySelectorAll('select[name=\"' + name + '\"]')) {
              el.removeAttribute('disabled');
              let opt = Array.from(el.options).find(o => preferText && new RegExp(preferText,'i').test(o.value+o.textContent));
              if (!opt) opt = Array.from(el.options).find(o => o.value && !/selecione/i.test(o.textContent||''));
              if (!opt) continue;
              el.selectedIndex = opt.index; el.value = opt.value;
              el.classList.remove('wpcf7-not-valid','first_null');
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
          }
          setSelect('unit', prefer);
          setSelect('easyunit', prefer);
          for (const name of ['installments','cerainstallments','allinstallments','siteinstallment']) {
            setSelect(name, null);
            for (const el of document.querySelectorAll('input[name=\"'+name+'\"]')) {
              el.value = '1'; el.dispatchEvent(new Event('change', { bubbles: true }));
            }
          }
          const decl = document.querySelector('input[name=declaracao]');
          if (decl) { decl.checked = true; decl.dispatchEvent(new Event('change', { bubbles: true })); }
        }""",
        prefer_unit_text,
    )


def run_case(page, card, case_id, lines, prefer_unit):
    email = f"teste.{case_id}.{int(time.time())}@example.com"
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    local = build_local(bridge, lines)

    page.goto(BASE + f"/carrinho/?pm=chg-{case_id}", wait_until="domcontentloaded", timeout=90000)
    seeded = page.evaluate(
        """async ({ lines, coupon }) => {
          localStorage.setItem('pm-cart-v1', JSON.stringify(lines));
          localStorage.setItem('pm-coupon-v1', JSON.stringify([coupon]));
          const cartRes = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
          let nonce = cartRes.headers.get('Nonce') || '';
          let cart = await cartRes.json();
          for (const it of (cart.items || [])) {
            const rr = await fetch('/wp-json/wc/store/v1/cart/remove-item', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce },
              body: JSON.stringify({ key: it.key })
            });
            nonce = rr.headers.get('Nonce') || nonce;
          }
          for (const c of (cart.coupons || [])) {
            const code = c.code || c; if (!code) continue;
            const rr = await fetch('/wp-json/wc/store/v1/cart/remove-coupon', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce },
              body: JSON.stringify({ code })
            });
            nonce = rr.headers.get('Nonce') || nonce;
          }
          for (const line of lines) {
            const add = await fetch('/wp-json/wc/store/v1/cart/add-item', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce },
              body: JSON.stringify({ id: Number(line.wooId), quantity: 1, pm_catalog_id: line.id })
            });
            nonce = add.headers.get('Nonce') || nonce;
            cart = await add.json();
            const match = (cart.items || []).find(it => {
              const d = (it.item_data || []).find(x => String(x.key||'').toLowerCase()==='pm_catalog_id');
              return d && String(d.value) === line.id;
            });
            if (match) line.wooKey = match.key;
          }
          const itemsTotal = Number((cart.totals || {}).total_items || (cart.totals || {}).total_price || 0);
          return { n: (cart.items || []).length, itemsTotal, lines };
        }""",
        {"lines": local, "coupon": COUPON},
    )
    items_total = int(seeded.get("itemsTotal") or 0)
    discount = max(0, items_total - 100)
    set_coupon_major(f"{discount / 100:.2f}")

    # re-apply coupon with tuned amount
    tuned = page.evaluate(
        """async ({ lines, coupon }) => {
          localStorage.setItem('pm-cart-v1', JSON.stringify(lines));
          const cartRes = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
          let nonce = cartRes.headers.get('Nonce') || '';
          let cart = await cartRes.json();
          for (const c of (cart.coupons || [])) {
            const code = c.code || c; if (!code) continue;
            const rr = await fetch('/wp-json/wc/store/v1/cart/remove-coupon', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce },
              body: JSON.stringify({ code })
            });
            nonce = rr.headers.get('Nonce') || nonce;
          }
          const ac = await fetch('/wp-json/wc/store/v1/cart/apply-coupon', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', Nonce: nonce },
            body: JSON.stringify({ code: coupon })
          });
          cart = await ac.json();
          return {
            n: (cart.items || []).length,
            total: Number((cart.totals || {}).total_price || 0),
            discount: Number((cart.totals || {}).total_discount || 0),
          };
        }""",
        {"lines": seeded.get("lines") or local, "coupon": COUPON},
    )
    print(case_id, "seed", seeded.get("n"), "tuned", tuned)
    if int(tuned.get("total") or 0) < 100 or int(tuned.get("total") or 0) > 200:
        return {"id": case_id, "ok": False, "stage": "tune", "tuned": tuned, "email": email}

    page.goto(BASE + f"/finalizar-pagamento/?pm=chg-{case_id}", wait_until="domcontentloaded", timeout=90000)
    try:
        page.wait_for_function(
            """() => {
              const tot = String((document.querySelector('input[name=totalamount]') || {}).value || '').replace(',', '.');
              return !!document.querySelector('.wpcf7-form') && (tot === '1.00' || tot === '1' || tot === '2.00');
            }""",
            timeout=120000,
        )
    except Exception as err:
        snap = page.evaluate(
            """() => ({
              totalamount: (document.querySelector('input[name=totalamount]')||{}).value||'',
              cart: (document.querySelector('input[name=cart]')||{}).value||'',
              lines: Array.from(document.querySelectorAll('#pm-checkout-cart .pm-checkout-line__name')).map(n=>n.textContent.trim())
            })"""
        )
        return {"id": case_id, "ok": False, "stage": "checkout_wait", "error": str(err), "snap": snap, "email": email}

    person = {
        "your-name": f"Teste {case_id}",
        "your-email": email,
        "your-phone": "21988887777",
        "cpf": "52998224725",
        "cep": "22041080",
        "cidade": "Rio de Janeiro",
        "estado": "RJ",
        "endereco": "Rua Teste Checkout",
        "bairro": "Copacabana",
        "numero": "10",
        "complemento": "1",
    }
    set_fields(page, person)
    page.wait_for_timeout(400)
    fill_selects(page, prefer_unit)
    pay = page.locator("#pills-pagamento-tab, .nav-pills .nav-link", has_text="Pagamento")
    if pay.count():
        pay.first.click(force=True)
        page.wait_for_timeout(1000)
    set_fields(page, person)
    fill_selects(page, prefer_unit)

    page.evaluate(
        """(card) => {
          const set = (name, value) => {
            for (const el of document.querySelectorAll('[name=\"'+name+'\"]')) {
              if (el.type === 'hidden') continue;
              el.focus(); el.value = value;
              ['input','change','keyup','blur'].forEach(ev => el.dispatchEvent(new Event(ev,{bubbles:true})));
            }
          };
          set('holder', card.holder); set('cart-number', card.number);
          set('expiration', card.exp); set('securityCode', card.cvv);
        }""",
        card,
    )
    if page.locator('input[name="holder"]:visible').count():
        page.locator('input[name="holder"]:visible').first.fill(card["holder"])
    if page.locator('input[name="cart-number"]:visible').count():
        page.locator('input[name="cart-number"]:visible').first.fill(card["number"])
    if page.locator('input[name="expiration"]:visible').count():
        page.locator('input[name="expiration"]:visible').first.fill(card["exp"])
    if page.locator('input[name="securityCode"]:visible').count():
        page.locator('input[name="securityCode"]:visible').first.fill(card["cvv"])

    submit = page.locator("input.wpcf7-submit, button.wpcf7-submit, button.pm-checkout-submit").first
    cf7_body = ""
    try:
        with page.expect_response(
            lambda r: "contact-form-7" in (r.url or "") or "wpcf7" in (r.url or ""),
            timeout=120000,
        ) as resp_info:
            submit.click(force=True)
        cf7_body = resp_info.value.text()[:800]
    except Exception as err:
        print(case_id, "submit_wait", err)
        page.wait_for_timeout(15000)

    # wait redirect / order
    order_id = None
    for _ in range(30):
        page.wait_for_timeout(2000)
        url = page.url or ""
        m = None
        import re

        m = re.search(r"order-received/(\d+)", url)
        if m:
            order_id = int(m.group(1))
            break
        # cookie redirect
        redir = page.evaluate(
            """() => {
              const m = document.cookie.match(/(?:^|;\\s*)redirectSuccess=([^;]+)/);
              return m ? decodeURIComponent(m[1]) : '';
            }"""
        )
        if redir and "order-received" in redir:
            try:
                page.goto(redir if redir.startswith("http") else BASE + redir, wait_until="domcontentloaded", timeout=90000)
            except Exception:
                pass

    if not order_id:
        # REST search by email
        e = load_env()
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
        except Exception as err:
            print("rest_err", err)

    result = {
        "id": case_id,
        "email": email,
        "order_id": order_id,
        "cf7_snip": cf7_body[:300],
        "demo": "demo_mode\":true" in cf7_body.lower(),
        "url": page.url,
        "ok": False,
    }
    if not order_id:
        result["stage"] = "no_order"
        result["form"] = page.evaluate(
            """() => ({
              className: (document.querySelector('.wpcf7-form')||{}).className||'',
              response: ((document.querySelector('.wpcf7-response-output')||{}).textContent||'').trim(),
              invalid: Array.from(document.querySelectorAll('.wpcf7-not-valid')).map(n=>n.name||n.className).slice(0,8),
              totalamount: (document.querySelector('input[name=totalamount]')||{}).value||'',
            })"""
        )
        return result

    time.sleep(2)
    peek = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "_peek_loja_order.py"), str(order_id)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    try:
        order = json.loads(peek.stdout)
    except Exception:
        order = {"raw": peek.stdout[:400], "err": peek.stderr[:200]}
    total = str(order.get("total") or "")
    result["order"] = {"id": order_id, "total": total, "lines": order.get("lines"), "accesstage": bool(order.get("accesstage"))}
    # Accept 1.00 or 2.00 band
    cents_ok = total in ("1.00", "1", "2.00", "1.99", "1.90", "1.89")
    result["ok"] = cents_ok and not result["demo"]
    print("ORDER", case_id, order_id, total, result["ok"])
    return result


def main():
    card = load_card()
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for case_id, lines, unit in (
            ("isabelle", ISABELLE, "Ipanema"),
            ("beatriz", BEATRIZ, "Botafogo"),
        ):
            print("\n====", case_id, "====")
            try:
                results.append(run_case(page, card, case_id, lines, unit))
            except Exception as err:
                results.append({"id": case_id, "ok": False, "error": str(err)})
            page.context.clear_cookies()
            try:
                page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
            except Exception:
                pass
        browser.close()

    set_coupon_major("2")
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
        raise SystemExit("ISA_BEA_CHARGE_FAIL")
    print("ISA_BEA_CHARGE_OK")


if __name__ == "__main__":
    main()
