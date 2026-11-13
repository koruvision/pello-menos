# -*- coding: utf-8 -*-
"""Reteste Isabelle (4 linhas) + Beatriz (Botafogo) no checkout da loja.

Cartão só via env: PM_TEST_CARD_HOLDER / NUMBER / EXP / CVV — nunca versionar.
Cupom PMTESTE2 é ajustado para deixar total entre R$1 e R$2.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
COUPON_CODE = "PMTESTE2"
COUPON_ID = 49523

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


def admin_call(method, path, payload=None):
    e = load_env()
    base = e["PM_LOJA_URL"].rstrip("/")
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    data = None if payload is None else json.dumps(payload).encode()
    headers = {
        "Authorization": "Basic " + auth,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "pm-retest-checkout",
    }
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode()
            return r.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode()
        try:
            return err.code, json.loads(body)
        except json.JSONDecodeError:
            return err.code, {"raw": body[:400]}


def set_coupon_amount(reais: str):
    st, c = admin_call("PUT", f"/wp-json/wc/v3/coupons/{COUPON_ID}", {
        "amount": reais,
        "discount_type": "fixed_cart",
        "usage_limit": 20,
    })
    print("coupon_amount", st, c.get("amount") if isinstance(c, dict) else c)
    if st not in (200, 201):
        raise SystemExit("coupon update failed")


def store_session(base: str):
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    nonce = token = None

    def call(method, path, payload=None):
        nonlocal nonce, token
        data = None if payload is None else json.dumps(payload).encode()
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-retest-checkout",
        }
        if nonce:
            h["Nonce"] = nonce
        if token:
            h["Cart-Token"] = token
        req = urllib.request.Request(base + path, data=data, method=method, headers=h)
        try:
            with opener.open(req, timeout=90) as resp:
                body = resp.read().decode("utf-8", "replace")
                nonce = resp.headers.get("Nonce") or nonce
                token = resp.headers.get("Cart-Token") or token
                return resp.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body[:400]}
            nonce = err.headers.get("Nonce") or nonce
            token = err.headers.get("Cart-Token") or token
            return err.code, parsed

    return call


def clear_and_add(call, bridge, lines):
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    for it in list(cart.get("items") or []):
        call("POST", "/wp-json/wc/store/v1/cart/remove-item", {"key": it["key"]})
    for code in list((cart.get("coupons") or [])):
        c = code.get("code") if isinstance(code, dict) else code
        if c:
            call("POST", "/wp-json/wc/store/v1/cart/remove-coupon", {"code": c})

    local = []
    for pid, unit in lines:
        vid = bridge[pid]["units"][unit]["variationId"]
        st, cart = call(
            "POST",
            "/wp-json/wc/store/v1/cart/add-item",
            {"id": int(vid), "quantity": 1, "pm_catalog_id": pid},
        )
        if st >= 400:
            raise SystemExit(f"add failed {pid}: {cart}")
        # pick matching line for local mirror
        matched = None
        for it in cart.get("items") or []:
            cid = ""
            for d in it.get("item_data") or []:
                if str(d.get("key") or "").lower() == "pm_catalog_id":
                    cid = str(d.get("value") or "")
            if cid == pid and (not matched or it.get("key") == matched.get("key")):
                matched = it
        if not matched:
            for it in cart.get("items") or []:
                if int(it.get("id") or 0) == int(vid):
                    matched = it
        local.append({
            "lineId": f"{pid}::{unit}",
            "id": pid,
            "name": {
                "esfoliacao-nadegas": "Esfoliação de nádegas",
                "esfoliacao-coxa": "Esfoliação de coxa",
                "coxa-cera": "Coxa – Cera",
                "virilha-cavada-cera": "Virilha Cavada – Cera",
                "faixa-cera": "Faixa – Cera",
                "axila-cera": "Axila – Cera",
                "buco-cera": "Buço – Cera",
                "sobrancelha-cera": "Sobrancelha – Cera",
            }.get(pid, pid),
            "image": "",
            "duration": "",
            "sku": "PM",
            "unitId": unit,
            "unitName": "Botafogo" if unit == "bot" else "Ipanema",
            "city": "Rio de Janeiro",
            "stateName": "RJ",
            "priceCents": 100,
            "wooId": str(vid),
            "wooKey": matched.get("key") if matched else "",
            "qty": 1,
        })
    return cart, local


def tune_coupon_for_total(call, target_cents=100):
    st, cart = call("GET", "/wp-json/wc/store/v1/cart")
    totals = cart.get("totals") or {}
    items_total = int(totals.get("total_items") or totals.get("total_price") or 0)
    # remove existing coupons
    for code in list(cart.get("coupons") or []):
        c = code.get("code") if isinstance(code, dict) else code
        if c:
            call("POST", "/wp-json/wc/store/v1/cart/remove-coupon", {"code": c})
    discount_cents = max(0, items_total - target_cents)
    # Woo amount is major units string
    reais = f"{discount_cents / 100:.2f}"
    set_coupon_amount(reais)
    st, cart = call("POST", "/wp-json/wc/store/v1/cart/apply-coupon", {"code": COUPON_CODE})
    totals = cart.get("totals") or {}
    total = int(totals.get("total_price") or 0)
    print("tuned_total_cents", total, "discount", totals.get("total_discount"), "items", items_total)
    if total < 100 or total > 200:
        raise SystemExit(f"total out of 1-2 range: {total}")
    return cart


def catalog_ids(cart):
    out = []
    for it in cart.get("items") or []:
        cid = ""
        for d in it.get("item_data") or []:
            if str(d.get("key") or "").lower() == "pm_catalog_id":
                cid = str(d.get("value") or "")
        out.append(cid or f"woo:{it.get('id')}:q{it.get('quantity')}")
    return out


def api_isabelle(base, bridge):
    call = store_session(base)
    cart, _ = clear_and_add(call, bridge, ISABELLE)
    ids = catalog_ids(cart)
    print("isabelle_api_items", len(cart.get("items") or []), ids)
    if len(cart.get("items") or []) != 4:
        raise SystemExit("isabelle still merged")
    if sorted(ids) != sorted([p for p, _ in ISABELLE]):
        raise SystemExit(f"isabelle catalog mismatch {ids}")
    print("ISABELLE_API_OK")


def playwright_checkout(base, bridge, scenario, label, do_pay: bool):
    from playwright.sync_api import sync_playwright

    holder = os.environ.get("PM_TEST_CARD_HOLDER", "").strip()
    number = os.environ.get("PM_TEST_CARD_NUMBER", "").strip().replace(" ", "")
    exp = os.environ.get("PM_TEST_CARD_EXP", "").strip()
    cvv = os.environ.get("PM_TEST_CARD_CVV", "").strip()
    if do_pay and not all([holder, number, exp, cvv]):
        raise SystemExit("card env missing for pay")

    call = store_session(base)
    cart, local = clear_and_add(call, bridge, scenario)
    cart = tune_coupon_for_total(call, target_cents=100)
    print(label, "api_lines", len(cart.get("items") or []), catalog_ids(cart))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Warm cookies via API domain then inject cart token path: reuse jar by visiting
        page.goto(base + "/carrinho/?pm=retest", wait_until="domcontentloaded", timeout=90000)
        page.evaluate(
            """(payload) => {
              localStorage.setItem('pm-cart-v1', JSON.stringify(payload.local));
              localStorage.setItem('pm-coupon-v1', JSON.stringify([payload.coupon]));
            }""",
            {"local": local, "coupon": COUPON_CODE},
        )
        # Rebuild woo cart in this browser session (new cookies) with catalog ids
        rebuilt = page.evaluate(
            """async (lines) => {
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
                }) || (cart.items || []).find(it => String(it.id) === String(line.wooId));
                if (match) line.wooKey = match.key;
              }
              const coup = await fetch('/wp-json/wc/store/v1/cart/apply-coupon', {
                method: 'POST', credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json', Nonce: nonce },
                body: JSON.stringify({ code: 'PMTESTE2' })
              });
              cart = await coup.json().catch(() => cart);
              localStorage.setItem('pm-cart-v1', JSON.stringify(lines));
              return {
                n: (cart.items || []).length,
                total: (cart.totals || {}).total_price,
                names: (cart.items || []).map(it => {
                  const d = (it.item_data || []).find(x => String(x.key||'').toLowerCase()==='pm_catalog_id');
                  return { catalog: d && d.value, qty: it.quantity, name: it.name };
                })
              };
            }""",
            local,
        )
        print(label, "browser_cart", rebuilt)

        page.goto(base + "/finalizar-pagamento/?pm=retest", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(2500)
        # go to pay step so panel paints
        pay_tab = page.locator("#pills-pagamento-tab, .nav-pills .nav-link", has_text="Pagamento")
        if pay_tab.count():
            pay_tab.first.click(force=True)
            page.wait_for_timeout(1500)

        panel = page.evaluate(
            """() => {
              const lines = Array.from(document.querySelectorAll('#pm-checkout-cart .pm-checkout-line__name'))
                .map(n => (n.textContent || '').trim());
              return {
                lines,
                count: lines.length,
                totalamount: (document.querySelector('input[name=totalamount]') || {}).value || '',
                cart: (document.querySelector('input[name=cart]') || {}).value || '',
                cartqtd: (document.querySelector('input[name=cartqtd]') || {}).value || '',
                shell: !!(window.__pmShellBoot || document.querySelector('#pm-checkout-cart')),
              };
            }"""
        )
        print(label, "panel", json.dumps(panel, ensure_ascii=False))

        if label == "isabelle" and panel.get("count") != 4:
            raise SystemExit(f"isabelle panel expected 4 got {panel}")
        if label == "isabelle":
            joined = " | ".join(panel.get("lines") or []).lower()
            if "esfolia" not in joined and "nádegas" not in joined and "nadegas" not in joined:
                # still ok if catalog names via localStorage
                print("WARN names may still be woo titles; catalog ids in item_data are source of truth")

        # Fill identity
        page.evaluate(
            """() => {
              const set = (name, value) => {
                for (const el of document.querySelectorAll('[name=\"'+name+'\"]')) {
                  if (el.type === 'checkbox' || el.type === 'radio') continue;
                  el.removeAttribute('readonly'); el.removeAttribute('disabled');
                  el.value = value;
                  el.dispatchEvent(new Event('input', { bubbles: true }));
                  el.dispatchEvent(new Event('change', { bubbles: true }));
                }
              };
              set('your-name', 'Teste PM Checkout');
              set('your-email', 'teste.pm.checkout@example.com');
              set('your-phone', '21987654321');
              set('cpf', '52998224725');
              set('cep', '22250-040');
              set('endereco', 'Rua Voluntarios da Patria');
              set('numero', '100');
              set('complemento', 'Sala 1');
              set('bairro', 'Botafogo');
              set('cidade', 'Rio de Janeiro');
              set('estado', 'RJ');
              for (const name of ['unit', 'easyunit']) {
                for (const el of document.querySelectorAll('select[name=\"'+name+'\"]')) {
                  const opt = Array.from(el.options).find(o => /botafogo/i.test(o.value) || /botafogo/i.test(o.textContent||''));
                  if (opt) { el.value = opt.value; el.dispatchEvent(new Event('change', { bubbles: true })); }
                }
              }
              const dec = document.querySelector('input[name=declaracao]');
              if (dec) { dec.checked = true; dec.dispatchEvent(new Event('change', { bubbles: true })); }
            }"""
        )
        page.wait_for_timeout(800)
        if pay_tab.count():
            pay_tab.first.click(force=True)
            page.wait_for_timeout(800)

        if not do_pay:
            print(label, "FILL_ONLY_OK")
            browser.close()
            return panel

        # Card
        page.evaluate(
            """(card) => {
              const set = (name, value) => {
                for (const el of document.querySelectorAll('[name=\"'+name+'\"]')) {
                  if (el.type === 'hidden') continue;
                  el.focus(); el.value = value;
                  ['input','change','keyup','blur'].forEach(ev => el.dispatchEvent(new Event(ev, { bubbles: true })));
                }
              };
              set('holder', card.holder);
              set('cart-number', card.number);
              set('expiration', card.exp);
              set('securityCode', card.cvv);
            }""",
            {"holder": holder, "number": number, "exp": exp, "cvv": cvv},
        )
        if page.locator('input[name="holder"]:visible').count():
            page.locator('input[name="holder"]:visible').first.fill(holder)
        if page.locator('input[name="cart-number"]:visible').count():
            page.locator('input[name="cart-number"]:visible').first.fill(number)
        if page.locator('input[name="expiration"]:visible').count():
            page.locator('input[name="expiration"]:visible').first.fill(exp)
        if page.locator('input[name="securityCode"]:visible').count():
            page.locator('input[name="securityCode"]:visible').first.fill(cvv)

        submit = page.locator("input.wpcf7-submit, button.wpcf7-submit, button.pm-checkout-submit").first
        info = {"submitted": False}

        def is_cf7(resp):
            u = resp.url or ""
            return ("contact-form-7" in u) or ("wpcf7" in u)

        try:
            with page.expect_response(is_cf7, timeout=120000) as resp_info:
                submit.click(force=True)
                info["submitted"] = True
            resp = resp_info.value
            body = ""
            try:
                body = resp.text()[:800]
            except Exception:
                body = ""
            info.update({"status": resp.status, "body": body})
        except Exception as e:
            info["error"] = str(e)
            page.wait_for_timeout(10000)

        page.wait_for_timeout(4000)
        dom = page.evaluate(
            """() => ({
              url: location.href,
              formClass: (document.querySelector('.wpcf7-form')||{}).className || '',
              response: ((document.querySelector('.wpcf7-response-output')||{}).textContent||'').trim(),
              invalid: Array.from(document.querySelectorAll('.wpcf7-not-valid')).map(n => n.name || n.getAttribute('name') || n.className).slice(0,12),
              payActive: !!(document.getElementById('pills-pagamento') && document.getElementById('pills-pagamento').classList.contains('active')),
              fieldInvalid: document.querySelectorAll('.pm-ck-field-invalid').length,
              totalamount: (document.querySelector('input[name=totalamount]')||{}).value || '',
            })"""
        )
        # Never print card / full PAN
        print(label, "pay", json.dumps({"submitted": info.get("submitted"), "status": info.get("status"), "body": (info.get("body") or "")[:400], "error": info.get("error")}, ensure_ascii=False))
        print(label, "dom", json.dumps(dom, ensure_ascii=False))
        browser.close()
        return {"panel": panel, "dom": dom, "info": info}


def main():
    e = load_env()
    base = e["PM_LOJA_URL"].rstrip("/")
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    do_pay = os.environ.get("PM_DO_PAY", "0") == "1"

    api_isabelle(base, bridge)
    playwright_checkout(base, bridge, ISABELLE, "isabelle", do_pay=False)
    playwright_checkout(base, bridge, BEATRIZ, "beatriz", do_pay=do_pay)

    # restore small coupon amount for safety
    set_coupon_amount("2")
    print("RETEST_DONE")


if __name__ == "__main__":
    main()
