# -*- coding: utf-8 -*-
"""Login to WP admin and point checkout shell to uncached file."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ENV = Path("projeto-migracao/.secrets/oficialteste.env")
BASE = "https://pellomenosoficialteste.companygenesis.com.br"
OLD = "checkout-shell.js?v=shell7"
NEW = "checkout-shell-c10.js?v=c10"


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
    user = cfg["PM_OFICIALTESTE_WP_ADMIN_USER"]
    password = cfg["PM_OFICIALTESTE_WP_ADMIN_PASSWORD"]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE + "/wp-login.php", wait_until="domcontentloaded", timeout=90000)
        page.fill("#user_login", user)
        page.fill("#user_pass", password)
        page.click("#wp-submit")
        page.wait_for_timeout(3000)
        # Code Snippets edit id 6
        page.goto(BASE + "/wp-admin/admin.php?page=edit-snippet&id=6", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(2000)
        content = page.content()
        print("edit page has shell7", OLD in content)
        print("edit page has code editor", "snippet_code" in content or "codeeditor" in content.lower())
        # Try CodeMirror / textarea
        updated = page.evaluate(
            """({ oldStr, newStr }) => {
              const areas = Array.from(document.querySelectorAll('textarea'));
              let hit = null;
              for (const a of areas) {
                if ((a.value || '').includes('checkout-shell')) { hit = a; break; }
              }
              if (!hit) {
                // CodeMirror
                const cm = document.querySelector('.CodeMirror');
                if (cm && cm.CodeMirror) {
                  const v = cm.CodeMirror.getValue();
                  if (!v.includes(oldStr) && !v.includes('checkout-shell.js')) {
                    return { ok: false, reason: 'no-shell-in-cm', sample: v.slice(0, 200) };
                  }
                  const next = v.split(oldStr).join(newStr)
                    .split('checkout-shell.js?v=shell9').join(newStr)
                    .split('checkout-shell.js?v=shell10').join(newStr)
                    .split('checkout-shell.js?v=shell8').join(newStr);
                  cm.CodeMirror.setValue(next);
                  return { ok: true, via: 'codemirror', changed: next !== v, hasNew: next.includes(newStr) };
                }
                return { ok: false, reason: 'no-editor', areas: areas.map(a => a.name || a.id) };
              }
              const v = hit.value;
              const next = v.split(oldStr).join(newStr)
                .split('checkout-shell.js?v=shell9').join(newStr)
                .split('checkout-shell.js?v=shell10').join(newStr)
                .split('checkout-shell.js?v=shell8').join(newStr);
              hit.value = next;
              hit.dispatchEvent(new Event('input', { bubbles: true }));
              hit.dispatchEvent(new Event('change', { bubbles: true }));
              return { ok: true, via: 'textarea', name: hit.name || hit.id, changed: next !== v, hasNew: next.includes(newStr) };
            }""",
            {"oldStr": OLD, "newStr": NEW},
        )
        print("updated", updated)
        if not updated.get("ok"):
            # list links to find snippet
            page.goto(BASE + "/wp-admin/admin.php?page=snippets", wait_until="domcontentloaded", timeout=90000)
            links = page.evaluate(
                """() => Array.from(document.querySelectorAll('a[href*=\"edit-snippet\"]')).map(a => ({href:a.href, text:a.textContent.trim()})).slice(0,20)"""
            )
            print("snippet links", links)
            browser.close()
            raise SystemExit(1)
        # Save
        saved = False
        for sel in ('#save_snippet_extra', 'input#save_snippet', 'button:has-text("Save Changes")', 'input[name="save_snippet"]', 'text=Save Changes', 'text=Update'):
            try:
                loc = page.locator(sel).first
                if loc.count():
                    loc.click(timeout=3000)
                    saved = True
                    print("clicked", sel)
                    break
            except Exception as e:
                print("skip", sel, e)
        if not saved:
            page.keyboard.press("Control+s")
            print("tried ctrl+s")
        page.wait_for_timeout(4000)
        # Verify front
        page.goto(BASE + "/finalizar-pagamento/?pm=shellc10", wait_until="networkidle", timeout=90000)
        src = page.evaluate(
            """() => (document.querySelector('script[src*=\"checkout-shell\"]')||{}).src || null"""
        )
        print("front src", src)
        browser.close()
        if not src or "c10" not in src:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
