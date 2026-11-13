# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import BASE, OUT, REF, ENV_FILE, read_env, cart_state, clear_cart, choose_unit, add_current, local_cart  # noqa: E402
import json
import re
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REF = REF.read_text(encoding="utf-8")
bust = str(int(time.time()))
report = {}


def badge_geometry(page):
    link = page.locator('a[href="/carrinho/"], a[href="/carrinho"]').first
    badge = page.locator("[data-pm-badge]").first
    if not badge.count():
        return {"missing": True}
    box = badge.bounding_box()
    host = link.bounding_box()
    return {
        "text": badge.inner_text().strip(),
        "outside": bool(box and host and box["y"] < host["y"] and box["x"] + box["width"] >= host["x"] + host["width"] - 4),
        "badge_top": round(box["y"]), "link_top": round(host["y"]), "badge_right": round(box["x"] + box["width"]), "link_right": round(host["x"] + host["width"]),
    }


def markers(html):
    return {"form1831": "wpcf7-f1831" in html, "cpf_input": bool(re.search(r'name=["\']cpf["\']', html)), "cart_number": html.count("cart-number"), "mask": html.lower().count("jquery.mask"), "wpcf7cf": html.count("wpcf7cf"), "recaptcha": "recaptcha" in html.lower(), "shell": "checkout-shell" in html}


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    r = page.goto(f"{BASE}/carrinho/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1500)
    report["carrinho_vazio"] = {"status": r.status, "pm_home": "pm-home" in page.content(), "theme_header": page.locator("header.header_wrap").count(), "texto": page.locator("[data-pm-cart-page]").inner_text()[:80] if page.locator("[data-pm-cart-page]").count() else None}
    clear_cart(page)

    page.goto(f"{BASE}/produto/axila-cera/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1200)
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(800)
    choose_unit(page, "first")
    add_current(page)
    api = cart_state(page)

    page.goto(f"{BASE}/carrinho/?pm={bust}a", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1500)
    text = page.locator("[data-pm-cart-page]").inner_text()
    report["carrinho_com_item"] = {"mostra_axila": "Axila" in text, "asa_norte": "Asa Norte" in text, "api": api, "pay_link": page.locator('a[href="/finalizar-pagamento/"]').count(), "badge": badge_geometry(page)}
    page.screenshot(path=str(OUT / "treino-fase3-carrinho.png"))

    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(1200)
    report["recarregar"] = {"mostra_axila": "Axila" in page.locator("[data-pm-cart-page]").inner_text(), "api": cart_state(page)}

    # mais um pela página do carrinho
    if page.locator("[data-inc]").count():
        page.locator("[data-inc]").first.click()
        page.wait_for_timeout(2500)
        text = page.locator("[data-pm-cart-page]").inner_text()
        report["qty2_no_carrinho"] = {"api": cart_state(page), "pay_links": page.locator('a[href="/finalizar-pagamento/"]').count(), "aviso": "Ajuste a quantidade" in text}
        page.locator("[data-dec]").first.click()
        page.wait_for_timeout(2500)
        report["qty_volta_1"] = {"api": cart_state(page), "pay_links": page.locator('a[href="/finalizar-pagamento/"]').count()}

    page.locator("[data-remove]").first.click()
    page.wait_for_timeout(2500)
    report["remover"] = {"texto_vazio": "vazio" in page.locator("[data-pm-cart-page]").inner_text().lower(), "api": cart_state(page), "badge": page.locator("[data-pm-badge]").count()}

    # mobile: badge também fora do círculo
    mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
    mobile.goto(f"{BASE}/produto/axila-cera/?pm={bust}m", wait_until="domcontentloaded", timeout=120000)
    mobile.wait_for_timeout(1200)
    choose_unit(mobile, "first")
    add_current(mobile)
    mobile.goto(f"{BASE}/carrinho/?pm={bust}m", wait_until="domcontentloaded", timeout=120000)
    mobile.wait_for_timeout(1500)
    report["mobile"] = {"mostra_axila": "Axila" in mobile.locator("[data-pm-cart-page]").inner_text(), "badge": badge_geometry(mobile), "overflow_x": mobile.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")}
    mobile.screenshot(path=str(OUT / "treino-fase3-carrinho-mobile.png"))
    mobile.locator("[data-remove]").first.click()
    mobile.wait_for_timeout(2500)
    report["mobile_remove_api"] = cart_state(mobile)

    # conta ainda é o tema; pagamento cru igual à fase 0
    r = page.goto(f"{BASE}/minha-conta/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(800)
    report["conta_tema"] = {"status": r.status, "theme_header": page.locator("header.header_wrap").count(), "pm_home": "pm-home" in page.content()}
    report["page_errors"] = errors[:5]
    browser.close()

req = urllib.request.Request(f"{BASE}/finalizar-pagamento/?pm={bust}", headers={"User-Agent": "pm"})
pay = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")
report["pagamento_cru_igual_fase0"] = markers(pay) == markers(REF)
(OUT / "treino_fase3.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
