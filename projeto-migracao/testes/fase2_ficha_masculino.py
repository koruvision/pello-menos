# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import BASE, OUT, REF, ENV_FILE, read_env, cart_state, clear_cart, choose_unit, add_current, local_cart  # noqa: E402
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

bust = str(int(time.time()))
report = {}


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    r = page.goto(f"{BASE}/masculino/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1500)
    report["masculino"] = {"status": r.status, "pm_home": "pm-home" in page.content(), "theme_header": page.locator("header.header_wrap").count(), "audience": page.locator("[data-audience=masculino]").count()}

    r = page.goto(f"{BASE}/produto/axila-cera/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1500)
    report["ficha"] = {"status": r.status, "pm_home": "pm-home" in page.content(), "theme_header": page.locator("header.header_wrap").count(), "unit_select": page.locator("[data-pm-unit]").count(), "add_button": page.locator("[data-pm-add]").count()}
    page.screenshot(path=str(OUT / "treino-fase2-ficha.png"))

    # slug só do projeto (404 no tema na fase 1)
    r = page.goto(f"{BASE}/produto/abdomen-cera/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(800)
    report["ficha_slug_projeto"] = {"status": r.status, "pm_home": "pm-home" in page.content()}

    page.goto(f"{BASE}/produto/axila-cera/?pm={bust}a", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1200)
    clear_cart(page)
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    unit = choose_unit(page, "first")
    added = add_current(page)
    api = cart_state(page)
    local = local_cart(page)
    report["incluir"] = {"unit": unit, **added, "api": api, "local_items": len((local or {}).get("items", [])) if isinstance(local, dict) else local}

    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(1500)
    report["recarregar"] = {"api": cart_state(page), "badge": page.locator("[data-pm-badge]").first.inner_text().strip() if page.locator("[data-pm-badge]").count() else None}

    # o carrinho do tema (fase 3 ainda não entrou) tem de mostrar a mesma linha
    r = page.goto(f"{BASE}/carrinho/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1500)
    theme_cart = page.content()
    item_name = api["items"][0]["name"] if api["items"] else ""
    report["carrinho_tema"] = {"status": r.status, "theme_header": page.locator("header.header_wrap").count(), "pm_home": "pm-home" in theme_cart, "mostra_item": bool(item_name) and item_name.split(" ")[0] in theme_cart, "remove_links": page.locator("td.product-remove a.remove, a.remove").count()}
    page.screenshot(path=str(OUT / "treino-fase2-carrinho-tema.png"))

    # remover pelo carrinho do tema
    table_remove = page.locator(".woocommerce-cart-form a.remove, td.product-remove a")
    if table_remove.count():
        href = table_remove.first.get_attribute("href")
        page.goto(href, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(2500)
        report["remover"] = {"via": "tabela do carrinho do tema", "api": cart_state(page), "tema_vazio": "carrinho está vazio" in page.content().lower() or "cart-empty" in page.content()}
    else:
        report["remover"] = {"via": "sem link na tabela", "api": cart_state(page)}

    # outra unidade recusada
    page.goto(f"{BASE}/produto/axila-cera/?pm={bust}b", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1200)
    page.evaluate("() => localStorage.removeItem('pm-cart-v1')")
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(800)
    choose_unit(page, "first")
    add_current(page)
    page.goto(f"{BASE}/produto/sobrancelha-cera/?pm={bust}b", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1000)
    other = choose_unit(page, "last")
    blocked = add_current(page)
    report["outra_unidade"] = {"unit": other, **blocked, "api": cart_state(page)}

    # quantidade 2: a ficha deixa incluir? e o aviso?
    clear_cart(page)
    page.goto(f"{BASE}/produto/axila-cera/?pm={bust}c", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1000)
    choose_unit(page, "first")
    if page.locator("[data-pm-inc]").count():
        page.locator("[data-pm-inc]").first.click()
    qty2 = add_current(page)
    report["qty2"] = {**qty2, "api": cart_state(page)}
    clear_cart(page)
    report["api_final"] = cart_state(page)
    report["page_errors"] = errors[:5]
    browser.close()

(OUT / "treino_fase2.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
