# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright

BASE = "https://pellomenosoficialteste.companygenesis.com.br"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for w, h, name in [(1440, 900, "desk"), (768, 1024, "tab"), (390, 844, "mob")]:
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(BASE + "/finalizar-pagamento/?pm=ov", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function("() => !!window.__pmShellBoot", timeout=45000)
        page.wait_for_timeout(1500)
        info = page.evaluate(
            """() => {
              const doc = document.documentElement;
              const overflowX = Math.max(doc.scrollWidth, document.body.scrollWidth) - doc.clientWidth;
              const wide = [];
              document.querySelectorAll('body *').forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.width < 8) return;
                const right = r.right - window.innerWidth;
                const left = -r.left;
                if (right <= 1 && left <= 1) return;
                const cs = getComputedStyle(el);
                wide.push({
                  tag: el.tagName + (el.id ? '#'+el.id : '') + '.' + String(el.className||'').split(' ').slice(0,3).join('.'),
                  right: Math.round(right),
                  left: Math.round(left),
                  mw: cs.maxWidth,
                  w: Math.round(r.width),
                });
              });
              wide.sort((a,b) => Math.max(b.right,b.left)-Math.max(a.right,a.left));
              return { overflowX, top: wide.slice(0,8) };
            }"""
        )
        print(name, info)
        page.close()
    browser.close()
