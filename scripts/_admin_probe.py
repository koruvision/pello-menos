# -*- coding: utf-8 -*-
from pathlib import Path
from playwright.sync_api import sync_playwright

ENV = Path("projeto-migracao/.secrets/oficialteste.env")
BASE = "https://pellomenosoficialteste.companygenesis.com.br"


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def main():
    cfg = env()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE + "/wp-login.php", wait_until="domcontentloaded", timeout=90000)
        page.fill("#user_login", cfg["PM_OFICIALTESTE_WP_ADMIN_USER"])
        page.fill("#user_pass", cfg["PM_OFICIALTESTE_WP_ADMIN_PASSWORD"])
        page.click("#wp-submit")
        page.wait_for_timeout(4000)
        print("after login url", page.url)
        print("title", page.title())
        # dashboard
        page.goto(BASE + "/wp-admin/", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(2000)
        print("admin url", page.url)
        print("admin title", page.title())
        menu = page.evaluate(
            """() => Array.from(document.querySelectorAll('#adminmenu a')).map(a => ({
              href: a.getAttribute('href'), text: (a.textContent||'').trim()
            })).filter(x => /snippet|code|plugin/i.test(x.text+' '+x.href)).slice(0,40)"""
        )
        print("menu", menu)
        # try plugins list for code snippets
        page.goto(BASE + "/wp-admin/plugins.php", wait_until="domcontentloaded", timeout=90000)
        plugs = page.evaluate(
            """() => Array.from(document.querySelectorAll('tr[data-slug], .plugin-title')).map(n => n.textContent.trim()).filter(t => /snippet|pm-home|code/i.test(t)).slice(0,20)"""
        )
        print("plugins", plugs)
        # REST with cookies
        rest = page.evaluate(
            """async () => {
              const r = await fetch('/wp-json/code-snippets/v1/snippets', { credentials: 'same-origin' });
              const t = await r.text();
              let data;
              try { data = JSON.parse(t); } catch(e) { data = t.slice(0,300); }
              return { status: r.status, data };
            }"""
        )
        print("rest", rest if not isinstance(rest.get('data'), list) else {
            'status': rest['status'],
            'items': [{'id': x.get('id'), 'name': x.get('name'), 'active': x.get('active')} for x in rest['data'][:15]]
        })
        browser.close()


if __name__ == "__main__":
    main()
