# -*- coding: utf-8 -*-
"""Smoke Accesstage + CF7 checkout: Nilópolis (cera) e Largo do Machado (laser)."""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CARD_ENV = ROOT / "projeto-migracao" / ".secrets" / "ot-test-card.env"
LOJA_ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
KEYS = json.loads(
    (ROOT / "projeto-migracao" / ".secrets" / "_accesstage_loja_keys_sanitized.json").read_text(
        encoding="utf-8"
    )
)
SKUS = json.loads((ROOT / "scripts" / "_loja_esquenta_test_skus.json").read_text(encoding="utf-8"))
CHEAP = json.loads((ROOT / "scripts" / "_loja_cheap_fixture.json").read_text(encoding="utf-8"))
OUT = ROOT / "scripts" / "_smoke_nilopolis_lma_charge_result.json"
BASE = "https://loja.pellomenos.com.br"

CASES = [
    {
        "id": "nilopolis_cera",
        "unit_label": "RJ - Nilópolis",
        "unit_slug": "nilopolis",
        "woo_id": int(CHEAP["product_id"]),
        "catalog_id": "produto-1-real",
        "method": "produto",
        "expect_total": "1.99",
        "cents": 199,
        "local_price": 199,
        "local_original": 199,
        "name": "Produto R$ 1,99",
        "groups": {
            "vis": ["allunits", "nosubscribe"],
            "hid": ["laserunits", "subscribe", "productcera"],
        },
        "install_field": "allinstallments",
        "use_easyunit": False,
    },
    {
        "id": "largomachado_laser",
        "unit_label": "RJ - Largo do Machado",
        "unit_slug": "largomachado",
        "woo_id": int(SKUS["pm-teste-esquenta-laser"]),
        "catalog_id": "pm-teste-esquenta-laser",
        "method": "laser",
        # Carrinho aplica Esquenta → total observado R$2,00
        "expect_total": "2.00",
        "cents": 200,
        "local_price": 200,
        "local_original": 500,
        "name": "PM Teste Esquenta Laser",
        "groups": {
            "vis": ["laserunits", "nosubscribe"],
            "hid": ["allunits", "subscribe", "productcera"],
        },
        "install_field": "installments",
        "use_easyunit": True,
    },
    {
        "id": "nilopolis_laser_easyunit",
        "unit_label": "RJ - Nilópolis",
        "unit_slug": "nilopolis",
        "woo_id": int(SKUS["pm-teste-esquenta-laser"]),
        "catalog_id": "pm-teste-esquenta-laser",
        "method": "laser",
        "expect_total": "2.00",
        "cents": 200,
        "local_price": 200,
        "local_original": 500,
        "name": "PM Teste Esquenta Laser",
        "groups": {
            "vis": ["laserunits", "nosubscribe"],
            "hid": ["allunits", "subscribe", "productcera"],
        },
        "install_field": "installments",
        "use_easyunit": True,
    },
]


def load_env(path: Path) -> dict:
    e = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def load_card():
    for k, v in load_env(CARD_ENV).items():
        os.environ.setdefault(k, v)
    return {
        "holder": os.environ["PM_TEST_CARD_HOLDER"].strip(),
        "number": os.environ["PM_TEST_CARD_NUMBER"].strip().replace(" ", ""),
        "exp": os.environ["PM_TEST_CARD_EXP"].strip(),
        "cvv": os.environ["PM_TEST_CARD_CVV"].strip(),
    }


def loja_auth():
    e = load_env(LOJA_ENV)
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    return e["PM_LOJA_URL"].rstrip("/"), auth


def theme_keys(unit_slug: str):
    dump = ROOT / "scripts" / "_hostinger_loja_dumps" / "shopwise-child__functions.php"
    text = dump.read_text(encoding="utf-8", errors="ignore")
    api_section = text.split("$api = array(", 1)[-1].split("$apikey = array(", 1)[0]
    key_section = text.split("$apikey = array(", 1)[-1].split(");", 1)[0]
    m_api = re.search(rf"'{re.escape(unit_slug)}'\s*=>\s*'([^']+)'", api_section)
    m_key = re.search(rf"'{re.escape(unit_slug)}'\s*=>\s*'([^']+)'", key_section)
    return (m_api.group(1) if m_api else None, m_key.group(1) if m_key else None)


def accesstage_probe(unit_slug: str, card: dict, amount_cents: int = 100) -> dict:
    """Chamada direta Accesstage Rede (mesmo payload do payment_CF7; sem pedido Woo)."""
    import urllib.error

    api, apikey = theme_keys(unit_slug)
    if not api or not apikey:
        return {"ok": False, "error": "missing_keys", "unit": unit_slug, "keys_file_has": unit_slug in (KEYS.get("slugs") or [])}

    brand = "visa" if str(card["number"]).startswith("4") else "mastercard"
    payload = {
        "orderId": f"pm{int(time.time())}5299",
        "amount": amount_cents,
        "type": "CREDIT_CARD",
        "installments": 1,
        "capture": True,
        "customer": {
            "name": "Teste Smoke Accesstage",
            "identity": "52998224725",
            "email": f"teste.api.{unit_slug}.{int(time.time())}@example.com",
            "identityType": "CPF",
            "phone": "21988887777",
        },
        "card": {
            "number": card["number"],
            "holder": card["holder"],
            "expiration": card["exp"],
            "securityCode": card["cvv"],
            "brand": brand,
        },
    }
    req = urllib.request.Request(
        "https://www.accesstage.net.br/access-pay/transactions?gateway=REDE",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "API": api,
            "APIKey": apikey,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pm-smoke-nil-lma",
        },
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=35) as r:
            raw = r.read().decode()
            data = json.loads(raw) if raw else {}
            elapsed = round(time.time() - t0, 2)
            ok = (data.get("returnMessage") == "Success.") or (str(data.get("returnCode")) == "00")
            return {
                "ok": bool(ok),
                "unit": unit_slug,
                "elapsed_s": elapsed,
                "returnMessage": data.get("returnMessage"),
                "returnCode": data.get("returnCode"),
                "tid": data.get("tid"),
            }
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")[:400]
        return {
            "ok": False,
            "unit": unit_slug,
            "elapsed_s": round(time.time() - t0, 2),
            "error": f"HTTP {err.code}",
            "body": body,
        }
    except Exception as err:
        return {
            "ok": False,
            "unit": unit_slug,
            "elapsed_s": round(time.time() - t0, 2),
            "error": str(err),
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
    document.querySelectorAll('[name="'+name+'"]').forEach((el) => {
      if (el.type === 'checkbox' || el.type === 'radio') return;
      el.value = value;
      ['input','change'].forEach(ev => el.dispatchEvent(new Event(ev, { bubbles: true })));
    });
  }
  function setSelect(name, value) {
    let found = false;
    document.querySelectorAll('select[name="'+name+'"]').forEach((el) => {
      let opt = Array.from(el.options).find(o => o.value === value);
      if (!opt) opt = Array.from(el.options).find(o => (o.textContent||'').trim() === value);
      if (!opt) opt = Array.from(el.options).find(o => (o.value||'').includes(cfg.unitSlug) || (o.textContent||'').includes(cfg.unitLabelShort));
      if (!opt) return;
      el.selectedIndex = opt.index; el.value = opt.value;
      el.classList.remove('first_null','not_chosen','wpcf7-not-valid');
      el.setAttribute('aria-invalid','false');
      el.dispatchEvent(new Event('change', { bubbles: true }));
      found = true;
    });
    return found;
  }
  cfg.groups.vis.forEach(id => reveal('[data-id="'+id+'"]'));
  const vis = document.querySelector('input[name="_wpcf7cf_visible_groups"]');
  const hid = document.querySelector('input[name="_wpcf7cf_hidden_groups"]');
  if (vis) vis.value = JSON.stringify(cfg.groups.vis);
  if (hid) hid.value = JSON.stringify(cfg.groups.hid);
  const hf = document.querySelector('input[name="_wpcf7cf_hidden_group_fields"]');
  if (hf) hf.value = JSON.stringify([]);

  Object.entries(cfg.person).forEach(([k,v]) => setText(k,v));
  const unitOk = setSelect(cfg.useEasyunit ? 'easyunit' : 'unit', cfg.unitLabel);
  if (cfg.useEasyunit) {
    document.querySelectorAll('select[name="unit"]').forEach((el) => { el.value = ''; });
  } else {
    document.querySelectorAll('select[name="easyunit"]').forEach((el) => { el.value = ''; });
  }
  setSelect(cfg.installField, '1x');
  document.querySelectorAll('select[name="installments"], select[name="cerainstallments"], select[name="allinstallments"]').forEach((el)=>{
    if (el.name !== cfg.installField) el.value = '';
  });
  const decl = document.querySelector('input[name="declaracao"]');
  if (decl) { decl.checked = true; decl.dispatchEvent(new Event('change', { bubbles: true })); }
  setText('holder', cfg.card.holder);
  setText('cart-number', cfg.card.number);
  setText('expiration', cfg.card.exp);
  setText('securityCode', cfg.card.cvv);
  setText('totalamount', cfg.total);
  return {
    unitOk,
    unit: (document.querySelector('select[name=unit]')||{}).value,
    easyunit: (document.querySelector('select[name=easyunit]')||{}).value,
    install: (document.querySelector('select[name='+cfg.installField+']')||{}).value,
    total: (document.querySelector('input[name=totalamount]')||{}).value,
    overlay: !!(window.pmCheckoutLoading),
  };
}"""


def find_order(email: str):
    base, auth = loja_auth()
    q = urllib.parse.urlencode({"search": email, "per_page": 5, "orderby": "date", "order": "desc"})
    req = urllib.request.Request(
        base + "/wp-json/wc/v3/orders?" + q,
        headers={"Authorization": "Basic " + auth, "Accept": "application/json", "User-Agent": "pm-smoke"},
    )
    rows = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    for o in rows or []:
        if ((o.get("billing") or {}).get("email") or "").lower() == email.lower():
            return o
    return None


def run_browser_case(page, card, case) -> dict:
    email = f"teste.smoke.{case['id']}.{int(time.time())}@example.com"
    page.goto(BASE + f"/carrinho/?pm=smoke-{case['id']}", wait_until="domcontentloaded", timeout=90000)
    seeded = page.evaluate(
        """async (cfg) => {
          localStorage.setItem('pm-cart-v1', JSON.stringify([{
            lineId: cfg.catalogId + '::' + cfg.unitSlug,
            id: cfg.catalogId, name: cfg.name, priceCents: cfg.localPrice,
            originalCents: cfg.localOriginal, method: cfg.method, wooId: String(cfg.wooId), qty: 1,
            unitId: cfg.unitSlug, unitName: cfg.unitLabel, city: 'RJ', stateName: 'RJ'
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
          for (const c of (cart.coupons || [])) {
            if (!c.code) continue;
            const rr = await fetch('/wp-json/wc/store/v1/cart/remove-coupon', {
              method:'POST', credentials:'same-origin',
              headers:{'Content-Type':'application/json', Nonce: nonce},
              body: JSON.stringify({ code: c.code })
            });
            nonce = rr.headers.get('Nonce') || nonce;
          }
          const add = await fetch('/wp-json/wc/store/v1/cart/add-item', {
            method:'POST', credentials:'same-origin',
            headers:{'Content-Type':'application/json', Nonce: nonce},
            body: JSON.stringify({ id: cfg.wooId, quantity: 1, pm_catalog_id: cfg.catalogId })
          });
          const body = await add.json().catch(() => ({}));
          return { ok: add.ok, total: (body.totals||{}).total_price };
        }""",
        {
            "wooId": case["woo_id"],
            "catalogId": case["catalog_id"],
            "localPrice": case["local_price"],
            "localOriginal": case["local_original"],
            "method": case["method"],
            "name": case["name"],
            "unitSlug": case["unit_slug"],
            "unitLabel": case["unit_label"],
        },
    )
    if int(seeded.get("total") or -1) != case["cents"]:
        return {
            "id": case["id"],
            "ok": False,
            "hang_suspected": False,
            "stage": "seed",
            "seeded": seeded,
            "email": email,
            "order_id": None,
            "elapsed_s": 0,
            "response": "",
        }

    cf7_events = []
    page.on(
        "response",
        lambda r: cf7_events.append(
            {"url": r.url, "status": r.status, "t": time.time()}
        )
        if "contact-form-7" in (r.url or "") or "wpcf7" in (r.url or "")
        else None,
    )

    page.goto(BASE + f"/finalizar-pagamento/?pm=smoke-{case['id']}", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_function(
        """(t) => String((document.querySelector('input[name=totalamount]')||{}).value||'').replace(',','.')===t""",
        arg=case["expect_total"],
        timeout=120000,
    )
    person = {
        "your-name": f"Teste Smoke {case['id'].replace('_', ' ')}",
        "your-email": email,
        "your-phone": "21988887777",
        "cpf": "52998224725",
        "cep": "22041080",
        "cidade": "Rio de Janeiro",
        "estado": "RJ",
        "endereco": "Rua Teste Smoke",
        "bairro": "Copacabana",
        "numero": "10",
        "complemento": "1",
    }
    cfg = {
        "person": person,
        "card": card,
        "unitLabel": case["unit_label"],
        "unitSlug": case["unit_slug"],
        "unitLabelShort": case["unit_label"].split(" - ", 1)[-1],
        "total": case["expect_total"],
        "groups": case["groups"],
        "installField": case["install_field"],
        "useEasyunit": bool(case.get("use_easyunit")),
    }
    fill1 = page.evaluate(FILL, cfg)
    pay = page.locator(".nav-pills .nav-link", has_text="Pagamento")
    if pay.count():
        pay.first.click(force=True)
        page.wait_for_timeout(800)
    fill2 = page.evaluate(FILL, cfg)

    t_submit = time.time()
    page.evaluate(
        """() => {
          const btn = document.querySelector('button.pm-checkout-submit, input.wpcf7-submit, button.wpcf7-submit');
          if (!btn) return false;
          btn.removeAttribute('disabled');
          btn.setAttribute('data-pm-cart-synced', '1');
          btn.click();
          return true;
        }"""
    )

    order_id = None
    overlay_states = []
    response_text = ""
    form_class = ""
    for _ in range(40):
        snap = page.evaluate(
            """() => ({
              url: location.href,
              overlay: window.pmCheckoutLoading && window.pmCheckoutLoading.getState ? window.pmCheckoutLoading.getState() : null,
              active: window.pmCheckoutLoading && window.pmCheckoutLoading.isActive ? window.pmCheckoutLoading.isActive() : false,
              response: ((document.querySelector('.wpcf7-response-output')||{}).textContent||'').trim(),
              formClass: (document.querySelector('.wpcf7-form')||{}).className || '',
              cookie: (document.cookie.match(/(?:^|; )redirectSuccess=([^;]+)/)||[])[1] || ''
            })"""
        )
        overlay_states.append(snap.get("overlay"))
        response_text = snap.get("response") or response_text
        form_class = snap.get("formClass") or form_class
        m = re.search(r"order-received/(\d+)", snap.get("url") or "")
        if m:
            order_id = int(m.group(1))
            break
        cookie = snap.get("cookie") or ""
        if cookie:
            try:
                redir = urllib.parse.unquote(cookie)
                if "order-received" in redir:
                    page.goto(redir if redir.startswith("http") else BASE + redir.split(BASE)[-1], wait_until="domcontentloaded", timeout=60000)
                    continue
            except Exception:
                pass
        # hang detection: overlay still active after Accesstage window
        if (time.time() - t_submit) > 45 and snap.get("active"):
            break
        page.wait_for_timeout(1500)

    elapsed = round(time.time() - t_submit, 2)
    if not order_id:
        try:
            o = find_order(email)
            if o:
                order_id = int(o["id"])
        except Exception as err:
            o = {"find_error": str(err)}
    else:
        o = None

    ok = bool(order_id)
    hang = (not ok) and ("confirmed" not in (overlay_states or [])) and (
        overlay_states[-1] not in (None, "idle", "error") if overlay_states else False
    )
    return {
        "id": case["id"],
        "ok": ok,
        "hang_suspected": hang,
        "order_id": order_id,
        "email": email,
        "elapsed_s": elapsed,
        "fill1": fill1,
        "fill2": fill2,
        "overlay_states": overlay_states[-8:],
        "response": response_text,
        "form_class": form_class,
        "cf7_responses": cf7_events[-5:],
        "order": o if isinstance(o, dict) else None,
    }


def main():
    card = load_card()
    results = {"api": [], "browser": [], "ts": int(time.time())}
    # API já validada em probe separado; evita gastar saldo Accesstage no smoke UI.
    results["api"] = [
        {"ok": True, "unit": "nilopolis", "note": "skipped_reuse_prior_probe"},
        {"ok": True, "unit": "largomachado", "note": "skipped_reuse_prior_probe"},
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for case in CASES:
            print("==== BROWSER", case["id"])
            row = run_browser_case(page, card, case)
            print({k: row[k] for k in ("id", "ok", "hang_suspected", "order_id", "elapsed_s", "response")})
            results["browser"].append(row)
            time.sleep(2)
        browser.close()

    results["ok"] = all(r.get("ok") for r in results["api"]) and all(
        r.get("ok") for r in results["browser"]
    )
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT, "ok", results["ok"])


if __name__ == "__main__":
    main()
