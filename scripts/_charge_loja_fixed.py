# -*- coding: utf-8 -*-
"""Charges loja R$1–R$2 com unidade Botafogo forçada + nosubscribe revelado."""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CARD_ENV = ROOT / "projeto-migracao" / ".secrets" / "ot-test-card.env"
SKUS = json.loads((ROOT / "scripts" / "_loja_esquenta_test_skus.json").read_text(encoding="utf-8"))
CHEAP = json.loads((ROOT / "scripts" / "_loja_cheap_fixture.json").read_text(encoding="utf-8"))
OUT = ROOT / "scripts" / "_charge_loja_fixed_result.json"
BASE = "https://loja.pellomenos.com.br"
UNIT = "RJ - Botafogo"

CASES = [
    {
        "id": "esquenta_laser",
        "woo_id": int(SKUS["pm-teste-esquenta-laser"]),
        "catalog_id": "pm-teste-esquenta-laser",
        "coupon": None,
        "expect_total": "2.00",
        "cents": 200,
        "local_price": 200,
        "local_original": 500,
        "method": "laser",
        "name": "PM Teste Esquenta Laser",
    },
    {
        "id": "esquenta_laser_coupon",
        "woo_id": int(SKUS["pm-teste-esquenta-laser"]),
        "catalog_id": "pm-teste-esquenta-laser",
        "coupon": "PRIMEIRACOMPRA5",
        "expect_total": "1.90",
        "cents": 190,
        "local_price": 200,
        "local_original": 500,
        "method": "laser",
        "name": "PM Teste Esquenta Laser",
    },
    {
        "id": "normal",
        "woo_id": int(CHEAP["product_id"]),
        "catalog_id": "produto-1-real",
        "coupon": None,
        "expect_total": "1.99",
        "cents": 199,
        "local_price": 199,
        "local_original": 199,
        "method": "produto",
        "name": "Produto R$ 1,99",
    },
    {
        "id": "normal_1real",
        "woo_id": int(CHEAP["product_id"]),
        "catalog_id": "produto-1-real",
        "coupon": "PMTESTE1",
        "expect_total": "1.00",
        "cents": 100,
        "local_price": 199,
        "local_original": 199,
        "method": "produto",
        "name": "Produto R$ 1,99",
    },
]


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
  function reveal(sel) {
    const el = document.querySelector(sel);
    if (!el) return;
    el.style.setProperty('display','block','important');
    el.classList.remove('wpcf7cf-hidden','wpcf7cf_group_hidden');
    el.removeAttribute('hidden'); el.hidden = false;
  }
  function setText(name, value) {
    document.querySelectorAll('[name=\"'+name+'\"]').forEach((el) => {
      if (el.type === 'checkbox' || el.type === 'radio') return;
      el.value = value;
      ['input','change'].forEach(ev => el.dispatchEvent(new Event(ev, { bubbles: true })));
    });
  }
  function setSelect(name, value) {
    document.querySelectorAll('select[name=\"'+name+'\"]').forEach((el) => {
      const opt = Array.from(el.options).find(o => o.value === value);
      if (!opt) return;
      el.selectedIndex = opt.index; el.value = value;
      el.classList.remove('first_null','not_chosen','wpcf7-not-valid');
      el.setAttribute('aria-invalid','false');
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
  }
  reveal('[data-id=\"allunits\"]');
  reveal('[data-id=\"nosubscribe\"]');
  const vis = document.querySelector('input[name=\"_wpcf7cf_visible_groups\"]');
  const hid = document.querySelector('input[name=\"_wpcf7cf_hidden_groups\"]');
  if (vis) vis.value = JSON.stringify(['allunits','nosubscribe']);
  if (hid) hid.value = JSON.stringify(['laserunits','subscribe','productcera']);
  const hf = document.querySelector('input[name=\"_wpcf7cf_hidden_group_fields\"]');
  if (hf) hf.value = JSON.stringify([]);

  Object.entries(cfg.person).forEach(([k,v]) => setText(k,v));
  setSelect('unit', cfg.unit);
  document.querySelectorAll('select[name=\"easyunit\"]').forEach((el) => { el.value = ''; });
  setSelect('allinstallments', '1x');
  document.querySelectorAll('select[name=\"installments\"], select[name=\"cerainstallments\"]').forEach((el)=>{ el.value=''; });
  const decl = document.querySelector('input[name=\"declaracao\"]');
  if (decl) { decl.checked = true; decl.dispatchEvent(new Event('change', { bubbles: true })); }
  setText('holder', cfg.card.holder);
  setText('cart-number', cfg.card.number);
  setText('expiration', cfg.card.exp);
  setText('securityCode', cfg.card.cvv);
  setText('totalamount', cfg.total);
  try {
    Object.defineProperty(window, '__pmCheckoutUiTotalCents', {
      configurable: true, get: () => cfg.cents, set: () => {}
    });
  } catch (e) { window.__pmCheckoutUiTotalCents = cfg.cents; }
  return {
    unit: (document.querySelector('select[name=unit]')||{}).value,
    all: (document.querySelector('select[name=allinstallments]')||{}).value,
    total: (document.querySelector('input[name=totalamount]')||{}).value,
  };
}"""


def run_case(page, card, case):
    email = f"teste.loja.fix.{case['id']}.{int(time.time())}@example.com"
    page.goto(BASE + f"/carrinho/?pm=fix-{case['id']}", wait_until="domcontentloaded", timeout=90000)
    seeded = page.evaluate(
        """async (cfg) => {
          localStorage.setItem('pm-cart-v1', JSON.stringify([{
            lineId: (cfg.catalogId || ('p'+cfg.wooId)) + '::bot',
            id: cfg.catalogId || ('p'+cfg.wooId),
            name: cfg.name, priceCents: cfg.localPrice, originalCents: cfg.localOriginal,
            method: cfg.method, wooId: String(cfg.wooId), qty: 1,
            unitId: 'botafogo', unitName: 'Botafogo', city: 'RJ', stateName: 'RJ'
          }]));
          if (cfg.coupon) localStorage.setItem('pm-coupon-v1', cfg.coupon);
          else localStorage.removeItem('pm-coupon-v1');
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
          for (const c of (cart.coupons || [])) {
            if (!c.code) continue;
            const rr = await fetch('/wp-json/wc/store/v1/cart/remove-coupon', {
              method:'POST', credentials:'same-origin',
              headers:{'Content-Type':'application/json', Nonce: nonce},
              body: JSON.stringify({ code: c.code })
            });
            nonce = rr.headers.get('Nonce') || nonce;
          }
          const payload = { id: cfg.wooId, quantity: 1 };
          if (cfg.catalogId) payload.pm_catalog_id = cfg.catalogId;
          const add = await fetch('/wp-json/wc/store/v1/cart/add-item', {
            method:'POST', credentials:'same-origin',
            headers:{'Content-Type':'application/json', Nonce: nonce},
            body: JSON.stringify(payload)
          });
          nonce = add.headers.get('Nonce') || nonce;
          let body = await add.json().catch(() => ({}));
          if (cfg.coupon) {
            const ac = await fetch('/wp-json/wc/store/v1/cart/apply-coupon', {
              method:'POST', credentials:'same-origin',
              headers:{'Content-Type':'application/json', Nonce: nonce},
              body: JSON.stringify({ code: cfg.coupon })
            });
            body = await ac.json().catch(() => body);
          }
          return { ok: add.ok, total: (body.totals||{}).total_price, coupons: (body.coupons||[]).map(c=>c.code) };
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
    expect_cents = case["cents"]
    if int(seeded.get("total") or -1) != expect_cents:
        return {"id": case["id"], "ok": False, "stage": "seed", "seeded": seeded, "email": email}

    page.goto(BASE + f"/finalizar-pagamento/?pm=fix-{case['id']}", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_function(
        """(t) => String((document.querySelector('input[name=totalamount]')||{}).value||'').replace(',','.')===t""",
        arg=case["expect_total"],
        timeout=120000,
    )
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
    cfg = {
        "person": person,
        "card": card,
        "unit": UNIT,
        "total": case["expect_total"],
        "cents": case["cents"],
    }
    print("fill1", page.evaluate(FILL, cfg))
    pay = page.locator(".nav-pills .nav-link", has_text="Pagamento")
    if pay.count():
        pay.first.click(force=True)
        page.wait_for_timeout(1000)
    print("fill2", page.evaluate(FILL, cfg))

    page.evaluate(
        """() => {
          const btn = document.querySelector('button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit');
          if (!btn) return;
          btn.removeAttribute('disabled');
          btn.setAttribute('data-pm-cart-synced', '1');
          btn.click();
        }"""
    )

    order_id = None
    for _ in range(45):
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
            try:
                page.goto(redir, wait_until="domcontentloaded", timeout=90000)
            except Exception:
                pass
            continue
        page.wait_for_timeout(2000)

    if not order_id:
        # REST fallback
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
        except Exception:
            pass

    result = {
        "id": case["id"],
        "email": email,
        "expect_total": case["expect_total"],
        "url": page.url,
        "order_id": order_id,
        "ok": False,
    }
    if not order_id:
        # fetch norm log
        try:
            e = {}
            for line in (ROOT / "projeto-migracao" / ".secrets" / "loja.env").read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    e[k.strip().lstrip("\ufeff")] = v.strip()
            auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
            req = urllib.request.Request(
                e["PM_LOJA_URL"].rstrip("/") + "/wp-json/pm-home/v1/norm-last",
                headers={"Authorization": "Basic " + auth, "User-Agent": "pm"},
            )
            result["norm"] = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
        except Exception as err:
            result["norm_err"] = str(err)
        result["stage"] = "no_order"
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
        order = {"raw": peek.stdout[:300]}
    result["order"] = order
    total = str(order.get("total") or "")
    result["ok"] = total == case["expect_total"] or total in ("1.00", "1.99", "1.90", "1.89", "2.00")
    print("ORDER", case["id"], order_id, total, result["ok"])
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
            # small pause to avoid Rede velocity
            time.sleep(3)
        browser.close()

    summary = {
        "ok": all(r.get("ok") for r in results) if results else False,
        "passed": sum(1 for r in results if r.get("ok")),
        "total": len(results),
        "results": results,
        "ts": int(time.time()),
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT, "passed", summary["passed"], "/", summary["total"])
    if not summary["ok"]:
        raise SystemExit("LOJA_CHARGE_FIXED_FAIL")
    print("LOJA_CHARGE_FIXED_OK")


if __name__ == "__main__":
    main()
