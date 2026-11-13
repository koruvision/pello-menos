# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import BASE, OUT, REF, ENV_FILE, read_env, cart_state, clear_cart, choose_unit, add_current, local_cart  # noqa: E402
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright
bust = str(int(time.time()))

def badges(page):
    return page.evaluate("() => Array.from(document.querySelectorAll('[data-pm-badge]')).map(b => ({text: b.textContent, visible: !!(b.offsetWidth || b.offsetHeight)}))")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto(f"{BASE}/produto/axila-cera/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1000)
    clear_cart(page); page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(800)
    choose_unit(page, "first"); add_current(page)
    page.goto(f"{BASE}/carrinho/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1500)
    print("antes de remover", json.dumps(badges(page)))
    page.locator("[data-remove]").first.click()
    page.wait_for_timeout(3000)
    print("depois de remover", json.dumps(badges(page)), "api", json.dumps(cart_state(page)))
    page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(1200)
    print("depois de recarregar", json.dumps(badges(page)))
    # e o inc/dec: badge acompanha?
    page.goto(f"{BASE}/produto/axila-cera/?pm={bust}b", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1000); choose_unit(page, "first"); add_current(page)
    page.goto(f"{BASE}/carrinho/?pm={bust}b", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1500)
    page.locator("[data-inc]").first.click(); page.wait_for_timeout(2500)
    print("depois de +1", json.dumps(badges(page)), "api", json.dumps(cart_state(page)))
    clear_cart(page)
    browser.close()
