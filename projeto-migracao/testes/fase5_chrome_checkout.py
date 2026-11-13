# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import BASE, OUT, REF, ENV_FILE, read_env, cart_state, clear_cart, choose_unit, add_current, local_cart  # noqa: E402
import difflib
import json
import re
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REF = REF.read_text(encoding="utf-8")
bust = str(int(time.time()))
report = {}


def form_block(html):
    m = re.search(r'<form[^>]*wpcf7-f1831.*?</form>', html, re.S)
    return m.group(0) if m else ""


def normalize_form(block):
    # nonces e ids de sessão do CF7 mudam a cada GET
    block = re.sub(r'name="_wpcf7_unit_tag" value="[^"]*"', 'name="_wpcf7_unit_tag" value="X"', block)
    block = re.sub(r'wpcf7-f1831-p\d+-o\d+', 'wpcf7-f1831-pX-oX', block)
    block = re.sub(r'name="_wpnonce" value="[^"]*"', 'name="_wpnonce" value="X"', block)
    block = re.sub(r'data-sitekey="[^"]*"', 'data-sitekey="X"', block)
    return block


def markers(html):
    return {"form1831": "wpcf7-f1831" in html, "cpf_input": bool(re.search(r'name=["\']cpf["\']', html)), "cart_number": html.count("cart-number"), "mask": html.lower().count("jquery.mask"), "wpcf7cf": html.count("wpcf7cf"), "recaptcha": "recaptcha" in html.lower(), "cpf_plugin_js": "cpf-e-cnpj-para-contact-form-7-old" in html}


req = urllib.request.Request(f"{BASE}/finalizar-pagamento/?pm={bust}", headers={"User-Agent": "pm"})
pay = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")
(OUT / "treino-fase5-pay.html").write_text(pay, encoding="utf-8")
now, ref = markers(pay), markers(REF)
report["marcadores"] = {"agora": now, "fase0": ref, "iguais": now == ref}
report["shell_enfileirado"] = {"script": "checkout-shell.js?v=shell6" in pay, "css_hide": "header.header_wrap,footer.footer_dark,.section.bg_default{display:none!important}" in pay}
form_now, form_ref = normalize_form(form_block(pay)), normalize_form(form_block(REF))
report["formulario_1831"] = {"len_fase0": len(form_ref), "len_agora": len(form_now), "identico_normalizado": form_now == form_ref}
if form_now != form_ref:
    diff = list(difflib.unified_diff(form_ref.splitlines(), form_now.splitlines(), lineterm="", n=0))
    (OUT / "treino-fase5-form-diff.txt").write_text("\n".join(diff), encoding="utf-8")
    report["formulario_1831"]["diff_linhas"] = len(diff)
    report["formulario_1831"]["diff_amostra"] = diff[:12]
inputs_now = sorted(set(re.findall(r'<input[^>]*name=["\']([^"\']+)["\']', form_now)))
inputs_ref = sorted(set(re.findall(r'<input[^>]*name=["\']([^"\']+)["\']', form_ref)))
report["inputs_do_form"] = {"iguais": inputs_now == inputs_ref, "lista": inputs_now}
# scripts da página fora do shell: mesmos?
scripts_now = sorted(set(re.sub(r'\?.*$', '', s) for s in re.findall(r'<script[^>]*src="([^"]+)"', pay)))
scripts_ref = sorted(set(re.sub(r'\?.*$', '', s) for s in re.findall(r'<script[^>]*src="([^"]+)"', REF)))
report["scripts"] = {"so_agora": [s for s in scripts_now if s not in scripts_ref], "so_fase0": [s for s in scripts_ref if s not in scripts_now]}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    posts = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" and ("wpcf7" in r.url or "feedback" in r.url or "checkout" in r.url) else None)

    # com um item no carrinho, como um cliente de verdade
    page.goto(f"{BASE}/produto/axila-cera/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1000)
    clear_cart(page); page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(800)
    choose_unit(page, "first"); add_current(page)
    page.goto(f"{BASE}/carrinho/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1200)
    page.locator('a[href="/finalizar-pagamento/"]').first.click()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(4000)
    report["pagamento_navegador"] = {
        "url": page.url,
        "header_projeto": page.locator("#pm-shell-header header").count() or page.locator("#pm-shell-header").count(),
        "footer_projeto": page.locator("#pm-shell-footer").count(),
        "header_tema_display": page.locator("header.header_wrap").first.evaluate("el => getComputedStyle(el).display") if page.locator("header.header_wrap").count() else "missing",
        "footer_tema_display": page.locator("footer.footer_dark").first.evaluate("el => getComputedStyle(el).display") if page.locator("footer.footer_dark").count() else "missing",
        "form_visivel": page.locator("form.wpcf7-form").first.is_visible() if page.locator("form.wpcf7-form").count() else False,
        "cpf_visivel_ou_condicional": page.locator('input[name="cpf"]').count(),
        "cartao": page.locator('input[name="cart-number"]').count(),
        "badge": page.locator("[data-pm-badge]").first.inner_text().strip() if page.locator("[data-pm-badge]").count() else None,
        "woo_cart_in_page": "Axila" in page.content(),
        "form_sent": page.locator("form.wpcf7-form.sent, .wpcf7-mail-sent-ok").count(),
        "posts_de_envio": posts,
    }
    page.screenshot(path=str(OUT / "treino-fase5-pay.png"), full_page=False)
    page.screenshot(path=str(OUT / "treino-fase5-pay-full.png"), full_page=True)
    # digitar no CPF para ver a máscara do plugin trabalhando (sem enviar)
    cpf = page.locator('input[name="cpf"]').first
    if cpf.count() and cpf.is_visible():
        cpf.fill("")
        cpf.type("12345678909", delay=30)
        page.wait_for_timeout(500)
        report["cpf_mascara"] = cpf.input_value()
    else:
        report["cpf_mascara"] = "campo oculto pelo condicional"
    mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
    mobile.goto(f"{BASE}/finalizar-pagamento/?pm={bust}m", wait_until="domcontentloaded", timeout=120000)
    mobile.wait_for_timeout(3000)
    report["pagamento_mobile"] = {"header_projeto": mobile.locator("#pm-shell-header").count(), "overflow_x": mobile.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth"), "form_visivel": mobile.locator("form.wpcf7-form").first.is_visible() if mobile.locator("form.wpcf7-form").count() else False}
    mobile.screenshot(path=str(OUT / "treino-fase5-pay-mobile.png"))
    # outras páginas do tema recebem o chrome
    page.goto(f"{BASE}/loja/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(3000)
    report["loja_chrome"] = {"header_projeto": page.locator("#pm-shell-header").count(), "header_tema_display": page.locator("header.header_wrap").first.evaluate("el => getComputedStyle(el).display") if page.locator("header.header_wrap").count() else "missing", "produtos_woo": page.locator("ul.products li.product").count()}
    page.goto(f"{BASE}/minha-conta/lost-password/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(3000)
    report["senha_perdida_chrome"] = {"header_projeto": page.locator("#pm-shell-header").count(), "form_woo": page.locator("form.lost_reset_password, form.woocommerce-ResetPassword").count()}
    clear_cart(page)
    report["api_final"] = cart_state(page)
    report["page_errors"] = errors[:5]
    browser.close()

req = urllib.request.Request(f"{BASE}/wp-admin/?pm={bust}", headers={"User-Agent": "pm"})
with urllib.request.urlopen(req, timeout=120) as r:
    body = r.read().decode("utf-8", "replace")
    report["wp_admin"] = {"status": r.status, "shell": "checkout-shell" in body}
(OUT / "treino_fase5.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
