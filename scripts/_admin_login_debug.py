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


def try_login(page, user, password, label):
    page.goto(BASE + "/wp-login.php", wait_until="domcontentloaded", timeout=90000)
    page.fill("#user_login", user)
    page.fill("#user_pass", password)
    page.check("#rememberme") if page.locator("#rememberme").count() else None
    page.click("#wp-submit")
    page.wait_for_timeout(4000)
    err = page.locator("#login_error").inner_text() if page.locator("#login_error").count() else ""
    print(label, "url=", page.url, "err=", (err or "")[:200])


def main():
    cfg = env()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try_login(
            page,
            cfg["PM_OFICIALTESTE_WP_ADMIN_USER"],
            cfg["PM_OFICIALTESTE_WP_ADMIN_PASSWORD"],
            "wp_admin",
        )
        try_login(
            page,
            cfg["PM_OFICIALTESTE_USER"],
            cfg["PM_OFICIALTESTE_WP_ADMIN_PASSWORD"],
            "app_user+admin_pass",
        )
        # app password as login password usually fails, but try
        try_login(
            page,
            cfg["PM_OFICIALTESTE_USER"],
            cfg["PM_OFICIALTESTE_APP_PASSWORD"],
            "app_user+app_pass",
        )
        browser.close()


if __name__ == "__main__":
    main()
