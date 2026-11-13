# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import BASE, OUT, REF, ENV_FILE, read_env, cart_state, clear_cart, choose_unit, add_current, local_cart  # noqa: E402
import json
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

REF = REF.read_text(encoding="utf-8")
bust = str(int(time.time()))
report = {}


def pay_markers(html):
    return {
        "form1831": "wpcf7-f1831" in html,
        "cpf_input": bool(re.search(r'name=["\']cpf["\']', html)),
        "cart_number": html.count("cart-number"),
        "mask": html.lower().count("jquery.mask"),
        "wpcf7cf": html.count("wpcf7cf"),
        "recaptcha": "recaptcha" in html.lower(),
        "shell": "checkout-shell" in html,
    }


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    failed = []
    page.on("requestfailed", lambda r: failed.append(r.url))

    response = page.goto(f"{BASE}/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(2500)
    html = page.content()
    header = page.locator("header.fixed").first
    cart_link = page.locator('a[href="/carrinho/"], a[href="/carrinho"]').first
    product_links = page.locator('a[href^="/produto/"]')
    css_ok = page.evaluate("() => getComputedStyle(document.body).fontFamily")
    logo = page.locator("header img").first
    report["home"] = {
        "status": response.status,
        "php": response.headers.get("x-powered-by"),
        "project_header": header.count() > 0 and "pm-home" in html,
        "theme_header": page.locator("header.header_wrap").count(),
        "cart_link": cart_link.count(),
        "product_links": product_links.count(),
        "first_product_href": product_links.first.get_attribute("href") if product_links.count() else None,
        "assets_from_destino": html.count("pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home"),
        "assets_from_clone": html.count("pellomenos.companygenesis.com.br/wp-content/uploads/pm-home") - html.count("pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home"),
        "body_font": css_ok,
        "logo_loaded": page.evaluate("() => { const i = document.querySelector('header img'); return i ? i.naturalWidth > 0 : null; }"),
        "page_errors": errors[:5],
        "failed_requests": [u for u in failed if "pm-home" in u][:5],
    }
    page.screenshot(path=str(OUT / "treino-fase1-home.png"), full_page=False)

    # o link de produto ainda abre a ficha do tema nesta fase
    href = report["home"]["first_product_href"]
    if href:
        r2 = page.goto(f"{BASE}{href}?pm={bust}", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(1500)
        report["produto_tema"] = {"status": r2.status, "theme_header": page.locator("header.header_wrap").count(), "pm_home": "pm-home" in page.content(), "woo": "woocommerce" in page.content().lower()}

    for path, key in (("/carrinho/", "carrinho_tema"), ("/minha-conta/", "conta_tema"), ("/loja/", "loja_tema")):
        r3 = page.goto(f"{BASE}{path}?pm={bust}", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(1000)
        report[key] = {"status": r3.status, "theme_header": page.locator("header.header_wrap").count(), "pm_home": "pm-home" in page.content()}

    r4 = page.goto(f"{BASE}/finalizar-pagamento/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(2000)
    pay = page.content()
    report["pagamento"] = {"status": r4.status, **pay_markers(pay), "ref": pay_markers(REF), "theme_header": page.locator("header.header_wrap").count()}
    report["pagamento"]["igual_fase0"] = {k: report["pagamento"][k] for k in ("form1831", "cpf_input", "cart_number", "mask", "wpcf7cf", "recaptcha")} == {k: report["pagamento"]["ref"][k] for k in ("form1831", "cpf_input", "cart_number", "mask", "wpcf7cf", "recaptcha")}
    page.screenshot(path=str(OUT / "treino-fase1-pay.png"), full_page=False)

    # mobile
    mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
    mobile.goto(f"{BASE}/?pm={bust}m", wait_until="domcontentloaded", timeout=120000)
    mobile.wait_for_timeout(2000)
    report["home_mobile"] = {"overflow_x": mobile.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth"), "cart_link": mobile.locator('a[href="/carrinho/"]').count()}
    mobile.screenshot(path=str(OUT / "treino-fase1-home-mobile.png"))
    browser.close()

(OUT / "treino_fase1.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
