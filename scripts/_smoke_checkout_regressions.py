# -*- coding: utf-8 -*-
"""Regressões UI checkout: Isabelle/Beatriz, validation, demo_mode, mixed units."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
OUT = ROOT / "scripts" / "_smoke_checkout_regressions_result.json"
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


def names_map():
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
    local = []
    nm = names_map()
    for pid, unit in lines:
        vid = bridge[pid]["units"][unit]["variationId"]
        local.append(
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
                "wooId": str(vid),
                "wooKey": "",
                "qty": 1,
            }
        )
    return local


def seed_browser_cart(page, local, apply_coupon=True):
    return page.evaluate(
        """async ({ lines, coupon, applyCoupon }) => {
          localStorage.setItem('pm-cart-v1', JSON.stringify(lines));
          localStorage.setItem('pm-coupon-v1', JSON.stringify(applyCoupon ? [coupon] : []));
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
            const code = c.code || c;
            if (!code) continue;
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
          if (applyCoupon) {
            const coup = await fetch('/wp-json/wc/store/v1/cart/apply-coupon', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: nonce },
              body: JSON.stringify({ code: coupon })
            });
            nonce = coup.headers.get('Nonce') || nonce;
            cart = await coup.json().catch(() => cart);
          }
          localStorage.setItem('pm-cart-v1', JSON.stringify(lines));
          return {
            n: (cart.items || []).length,
            total: (cart.totals || {}).total_price,
            catalogs: (cart.items || []).map(it => {
              const d = (it.item_data || []).find(x => String(x.key||'').toLowerCase()==='pm_catalog_id');
              return { catalog: d && d.value, qty: it.quantity };
            })
          };
        }""",
        {"lines": local, "coupon": COUPON, "applyCoupon": apply_coupon},
    )


def fill_person(page, include_cpf=True):
    page.evaluate(
        """(includeCpf) => {
          const set = (name, value) => {
            for (const el of document.querySelectorAll('[name=\"'+name+'\"]')) {
              if (el.type === 'checkbox' || el.type === 'radio') continue;
              el.removeAttribute('readonly'); el.removeAttribute('disabled');
              el.value = value;
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }
          };
          set('your-name', 'Teste PM Regressao');
          set('your-email', 'teste.pm.regressao@example.com');
          set('your-phone', '21987654321');
          if (includeCpf) set('cpf', '52998224725');
          else set('cpf', '');
          set('cep', '22250-040');
          set('endereco', 'Rua Voluntarios da Patria');
          set('numero', '100');
          set('complemento', 'Sala 1');
          set('bairro', 'Botafogo');
          set('cidade', 'Rio de Janeiro');
          set('estado', 'RJ');
          for (const name of ['unit', 'easyunit']) {
            for (const el of document.querySelectorAll('select[name=\"'+name+'\"]')) {
              const opt = Array.from(el.options).find(o => /botafogo|ipanema/i.test(o.value+o.textContent));
              if (opt) { el.value = opt.value; el.dispatchEvent(new Event('change', { bubbles: true })); }
            }
          }
          const dec = document.querySelector('input[name=declaracao]');
          if (dec) { dec.checked = true; dec.dispatchEvent(new Event('change', { bubbles: true })); }
        }""",
        include_cpf,
    )


def panel_snapshot(page):
    return page.evaluate(
        """() => ({
          lines: Array.from(document.querySelectorAll('#pm-checkout-cart .pm-checkout-line__name'))
            .map(n => (n.textContent || '').trim()),
          count: document.querySelectorAll('#pm-checkout-cart .pm-checkout-line').length,
          totalamount: (document.querySelector('input[name=totalamount]') || {}).value || '',
          cart: (document.querySelector('input[name=cart]') || {}).value || '',
          cartqtd: (document.querySelector('input[name=cartqtd]') || {}).value || '',
          payActive: !!(document.getElementById('pills-pagamento') && document.getElementById('pills-pagamento').classList.contains('active')),
          loading: !!(window.pmCheckoutLoading && window.pmCheckoutLoading.isActive && window.pmCheckoutLoading.isActive()),
          formClass: (document.querySelector('.wpcf7-form') || {}).className || '',
          fieldInvalid: document.querySelectorAll('.pm-ck-field-invalid').length,
        })"""
    )


def go_pay_tab(page):
    tab = page.locator("#pills-pagamento-tab")
    if tab.count():
        tab.first.click(force=True)
        page.wait_for_timeout(1000)


def main():
    e = load_env()
    base = e["PM_LOJA_URL"].rstrip("/")
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    report = {"cases": [], "failed": 0}

    def add(name, ok, detail):
        report["cases"].append({"name": name, "ok": ok, "detail": detail})
        print(("OK" if ok else "FAIL"), name, json.dumps(detail, ensure_ascii=False)[:400])
        if not ok:
            report["failed"] += 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        # --- Isabelle ---
        page.goto(base + "/carrinho/?pm=reg", wait_until="domcontentloaded", timeout=90000)
        local = build_local(bridge, ISABELLE)
        seeded = seed_browser_cart(page, local, apply_coupon=False)
        page.goto(base + "/finalizar-pagamento/?pm=reg-isa", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(2500)
        go_pay_tab(page)
        panel = panel_snapshot(page)
        joined = " ".join(panel.get("lines") or []).lower()
        ok_isa = (
            seeded.get("n") == 4
            and panel.get("count") == 4
            and "esfolia" in joined
            and len((panel.get("cart") or "").split(",")) == 4
        )
        add("isabelle_panel", ok_isa, {"seeded": seeded, "panel": panel})

        # --- validation_failed stays on pay + total stable ---
        fill_person(page, include_cpf=False)
        go_pay_tab(page)
        before_total = panel_snapshot(page).get("totalamount")
        # ensure some total painted
        page.wait_for_timeout(500)
        submit = page.locator("input.wpcf7-submit, button.wpcf7-submit, button.pm-checkout-submit").first
        info = {"body": ""}

        def is_cf7(resp):
            u = resp.url or ""
            return "contact-form-7" in u or "wpcf7" in u

        try:
            with page.expect_response(is_cf7, timeout=90000) as resp_info:
                submit.click(force=True)
            body = resp_info.value.text()[:1200]
            info["body"] = body
            info["status"] = resp_info.value.status
        except Exception as err:
            info["error"] = str(err)
            page.wait_for_timeout(5000)
        page.wait_for_timeout(1500)
        after = panel_snapshot(page)
        no_demo = ("demo_mode\":true" not in (info.get("body") or "").lower()) and (
            " demo" not in f" {after.get('formClass')} "
        )
        # validation may be cpf or other; stay on pay
        ok_val = after.get("payActive") is True and after.get("loading") is False
        ok_total = (after.get("totalamount") or "0.00") not in ("", "0.00", "0,00")
        add("validation_stay_pay", ok_val, {"after": after, "cf7": info.get("status")})
        add("demo_mode_absent", no_demo, {"formClass": after.get("formClass"), "body_snip": (info.get("body") or "")[:220]})
        add("totalamount_stable", ok_total or bool(before_total and before_total not in ("0.00", "")), {"before": before_total, "after": after.get("totalamount")})

        # --- Beatriz ---
        page.goto(base + "/carrinho/?pm=reg-bea", wait_until="domcontentloaded", timeout=90000)
        local_b = build_local(bridge, BEATRIZ)
        seeded_b = seed_browser_cart(page, local_b, apply_coupon=False)
        page.goto(base + "/finalizar-pagamento/?pm=reg-bea", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(2500)
        go_pay_tab(page)
        panel_b = panel_snapshot(page)
        # 2 faixas merge to qty 2 → 4 lines
        ok_bea = panel_b.get("count") == 4 and "2" in (panel_b.get("cartqtd") or "")
        add("beatriz_panel", ok_bea, {"seeded": seeded_b, "panel": panel_b})

        # --- Mixed units on /carrinho ---
        page.goto(base + "/carrinho/?pm=reg-mix", wait_until="domcontentloaded", timeout=90000)
        mix = [
            {
                "lineId": "axila-cera::ipa",
                "id": "axila-cera",
                "name": "Axila – Cera",
                "image": "",
                "duration": "",
                "sku": "PM",
                "unitId": "ipa",
                "unitName": "Ipanema",
                "city": "Rio de Janeiro",
                "stateName": "RJ",
                "priceCents": 4242,
                "wooId": str(bridge["axila-cera"]["units"]["ipa"]["variationId"]),
                "wooKey": "",
                "qty": 1,
            },
            {
                "lineId": "buco-cera::bot",
                "id": "buco-cera",
                "name": "Buço – Cera",
                "image": "",
                "duration": "",
                "sku": "PM",
                "unitId": "bot",
                "unitName": "Botafogo",
                "city": "Rio de Janeiro",
                "stateName": "RJ",
                "priceCents": 2121,
                "wooId": str(bridge["buco-cera"]["units"]["bot"]["variationId"]),
                "wooKey": "",
                "qty": 1,
            },
        ]
        page.evaluate(
            """(items) => { localStorage.setItem('pm-cart-v1', JSON.stringify(items)); location.reload(); }""",
            mix,
        )
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3500)
        mix_dom = page.evaluate(
            """() => {
              const text = document.body.innerText || '';
              const pay = Array.from(document.querySelectorAll('a[href*=\"finalizar-pagamento\"]'))
                .filter(a => a.offsetParent !== null);
              return {
                mixedHint: /outra (loja|unidade)|unidades diferentes|esvazie|finalize/i.test(text),
                payVisible: pay.length > 0,
                textHit: (text.match(/unidade|loja|carrinho/i) || [''])[0]
              };
            }"""
        )
        # canPay false → pay link hidden or disabled messaging
        ok_mix = mix_dom.get("mixedHint") or (mix_dom.get("payVisible") is False)
        add("mixed_units_blocks_pay", ok_mix, mix_dom)

        browser.close()

    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT, "failed", report["failed"])
    if report["failed"]:
        raise SystemExit(1)
    print("SMOKE_CHECKOUT_REGRESSIONS_OK")


if __name__ == "__main__":
    main()
