# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import BASE, OUT, REF, ENV_FILE, read_env, cart_state, clear_cart, choose_unit, add_current, local_cart  # noqa: E402
import base64
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REF = REF.read_text(encoding="utf-8")
ENV = read_env()
TOKEN = base64.b64encode(f"{ENV['PM_OFICIALTESTE_USER']}:{ENV['PM_OFICIALTESTE_APP_PASSWORD']}".encode()).decode()
bust = str(int(time.time()))
email = f"pm.treino.{bust}@example.com"
password = "Pm-treino-teste-2026"
report = {"test_email": email}


def markers(html):
    return {"form1831": "wpcf7-f1831" in html, "cpf_input": bool(re.search(r'name=["\']cpf["\']', html)), "cart_number": html.count("cart-number"), "mask": html.lower().count("jquery.mask"), "wpcf7cf": html.count("wpcf7cf"), "recaptcha": "recaptcha" in html.lower(), "shell": "checkout-shell" in html}


def admin(path, method="GET"):
    req = urllib.request.Request(BASE + path, method=method, headers={"User-Agent": "pm", "Authorization": "Basic " + TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    r = page.goto(f"{BASE}/minha-conta/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1500)
    report["conta_visitante"] = {"status": r.status, "pm_home": "pm-home" in page.content(), "theme_header": page.locator("header.header_wrap").count(), "entrar": page.get_by_role("heading", name="Entrar").count(), "cadastrar": page.get_by_text("Cadastre-se", exact=True).count(), "excluir_conta": page.get_by_text("Excluir conta", exact=True).count()}
    page.screenshot(path=str(OUT / "treino-fase4-conta-visitante.png"))

    # login errado
    page.locator("[data-pm-login] input[name=username]").fill("ninguem@example.com")
    page.locator("[data-pm-login] input[name=password]").fill("errada")
    page.locator("[data-pm-login] button").click()
    page.wait_for_timeout(2500)
    report["login_errado"] = {"mensagem": page.locator("[data-pm-message]").inner_text().strip() if page.locator("[data-pm-message]").count() else "", "ainda_entrar": page.get_by_role("heading", name="Entrar").count()}

    # cadastro real no WooCommerce
    page.locator("[data-pm-register] input[name=email]").fill(email)
    page.locator("[data-pm-register] input[name=password]").fill(password)
    page.locator("[data-pm-register] button").click()
    page.wait_for_timeout(3000)
    hello = page.locator("[data-pm-hello]")
    report["cadastro"] = {"hello": hello.inner_text().strip() if hello.count() else "", "pedidos": page.locator("[data-pm-orders]").inner_text().strip()[:80] if page.locator("[data-pm-orders]").count() else None, "header_nome": page.locator("[data-pm-user]").count(), "cookie_logged_in": any(c["name"].startswith("wordpress_logged_in") for c in page.context.cookies())}
    page.screenshot(path=str(OUT / "treino-fase4-conta-logado.png"))

    form = page.locator("[data-pm-address]")
    form.locator('input[name="first_name"]').fill("Treino")
    form.locator('input[name="last_name"]').fill("Migracao")
    form.locator('input[name="address_1"]').fill("Rua do Ensaio 17")
    form.locator('input[name="city"]').fill("Brasilia")
    form.locator('input[name="state"]').fill("DF")
    form.locator('input[name="postcode"]').fill("70000000")
    form.locator('input[name="phone"]').fill("61999999999")
    form.locator('input[name="email"]').fill(email)
    form.locator("button").click()
    page.wait_for_timeout(2500)
    report["endereco"] = {"mensagem": page.locator("[data-pm-message]").inner_text().strip() if page.locator("[data-pm-message]").count() else ""}
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(1500)
    report["endereco"]["mantido_apos_reload"] = page.locator("[data-pm-address] input[name=first_name]").input_value()

    # logado: home e carrinho sem nome no header
    page.goto(f"{BASE}/?pm={bust}l", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1200)
    report["home_logado"] = {"header_nome": page.locator("[data-pm-user]").count(), "pm_home": "pm-home" in page.content(), "cache_control": None}
    resp = page.request.get(f"{BASE}/?pm={bust}l2")
    report["home_logado"]["cache_control"] = resp.headers.get("cache-control")

    # minha-conta do tema continua para a senha perdida
    page.goto(f"{BASE}/minha-conta/lost-password/?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1200)
    report["senha_perdida"] = {"form_woo": page.locator("form.lost_reset_password, form.woocommerce-ResetPassword").count(), "theme_header": page.locator("header.header_wrap").count(), "pm_home": "pm-home" in page.content()}

    # sair
    page.goto(f"{BASE}/minha-conta/?pm={bust}s", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1200)
    page.locator("[data-pm-logout]").click()
    page.wait_for_timeout(2500)
    report["sair"] = {"entrar_de_novo": page.get_by_role("heading", name="Entrar").count(), "cookie_logged_in": any(c["name"].startswith("wordpress_logged_in") for c in page.context.cookies())}

    # entrar de novo com o usuÃ¡rio criado
    page.locator("[data-pm-login] input[name=username]").fill(email)
    page.locator("[data-pm-login] input[name=password]").fill(password)
    page.locator("[data-pm-login] button").click()
    page.wait_for_timeout(3000)
    report["login_real"] = {"hello": page.locator("[data-pm-hello]").inner_text().strip() if page.locator("[data-pm-hello]").count() else "", "endereco_first_name": page.locator("[data-pm-address] input[name=first_name]").input_value() if page.locator("[data-pm-address]").count() else None}
    page.locator("[data-pm-logout]").click()
    page.wait_for_timeout(2000)

    # wp-admin e wp-login seguem do WordPress
    r = page.goto(f"{BASE}/wp-login.php?pm={bust}", wait_until="domcontentloaded", timeout=120000)
    report["wp_login"] = {"status": r.status, "form": page.locator("#loginform").count(), "pm_home": "pm-home" in page.content()}
    report["page_errors"] = errors[:5]
    browser.close()

req = urllib.request.Request(f"{BASE}/finalizar-pagamento/?pm={bust}", headers={"User-Agent": "pm"})
pay = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")
report["pagamento_cru_igual_fase0"] = markers(pay) == markers(REF)
req = urllib.request.Request(f"{BASE}/wp-admin/?pm={bust}", headers={"User-Agent": "pm"})
with urllib.request.urlopen(req, timeout=120) as r:
    report["wp_admin_status"] = r.status

# limpeza: apagar o usuÃ¡rio de teste
status, body = admin("/wp-json/wp/v2/users?search=" + urllib.parse.quote(email) + "&context=edit&per_page=20")
users = json.loads(body) if body.startswith("[") else []
match = [u for u in users if u.get("email") == email]
report["limpeza"] = {"encontrado": len(match)}
if match:
    status, body = admin(f"/wp-json/wp/v2/users/{match[0]['id']}?force=true&reassign=1", "DELETE")
    report["limpeza"]["delete_status"] = status
status, body = admin("/wp-json/wp/v2/users?search=" + urllib.parse.quote(email) + "&context=edit&per_page=20")
report["limpeza"]["restantes"] = len([u for u in (json.loads(body) if body.startswith("[") else []) if u.get("email") == email])

(OUT / "treino_fase4.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))

