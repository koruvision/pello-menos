# -*- coding: utf-8 -*-
"""Inspect CF7 response-output and overflow sources on checkout."""
import re
import urllib.request

from playwright.sync_api import sync_playwright

BASE = "https://pellomenosoficialteste.companygenesis.com.br"

html = urllib.request.urlopen(BASE + "/finalizar-pagamento/?pm=val", timeout=60).read().decode(
    "utf-8", "replace"
)
idx = html.find("wpcf7-response-output")
print("html snippet", html[max(0, idx - 80) : idx + 120])
print("not-valid-tip count in source", html.count("wpcf7-not-valid-tip"))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(BASE + "/finalizar-pagamento/?pm=val", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_function("() => !!window.__pmShellBoot", timeout=45000)
    page.wait_for_timeout(2000)

    # try submit empty to trigger validation
    page.locator("#pills-dados-tab").click(force=True)
    page.wait_for_timeout(400)
    # go to pay and click submit if possible, or next then submit
    page.locator("#pills-pagamento-tab").click(force=True)
    page.wait_for_timeout(800)
    if page.locator("button.pm-checkout-submit, .wpcf7-submit").count():
        page.locator("button.pm-checkout-submit, .wpcf7-submit").first.click(force=True)
        page.wait_for_timeout(2500)

    info = page.evaluate(
        """() => {
          const doc = document.documentElement;
          const body = document.body;
          const overflowX = Math.max(doc.scrollWidth, body.scrollWidth) - Math.max(doc.clientWidth, body.clientWidth);
          const wide = Array.from(document.querySelectorAll('body *')).map(el => {
            const r = el.getBoundingClientRect();
            if (r.width < 2) return null;
            const overflowRight = r.right - window.innerWidth;
            const overflowLeft = -r.left;
            if (overflowRight <= 2 && overflowLeft <= 2) return null;
            const cs = getComputedStyle(el);
            return {
              tag: el.tagName,
              cls: (el.className && String(el.className).slice(0,80)) || '',
              id: el.id || '',
              right: Math.round(overflowRight),
              left: Math.round(overflowLeft),
              w: Math.round(r.width),
              pos: cs.position,
              overflow: cs.overflow + '/' + cs.overflowX,
            };
          }).filter(Boolean).sort((a,b) => Math.max(b.right,b.left) - Math.max(a.right,a.left)).slice(0,12);

          const resp = document.querySelector('.wpcf7-response-output');
          const tips = Array.from(document.querySelectorAll('.wpcf7-not-valid-tip')).slice(0,8).map(t => t.textContent.trim());
          const invalids = document.querySelectorAll('.wpcf7-not-valid').length;
          const formClass = (document.querySelector('.wpcf7-form')||{}).className || '';
          return {
            overflowX,
            scrollWidth: doc.scrollWidth,
            clientWidth: doc.clientWidth,
            wide,
            resp: resp && {
              text: (resp.textContent||'').trim(),
              display: getComputedStyle(resp).display,
              aria: resp.getAttribute('aria-hidden'),
              cls: resp.className,
              h: Math.round(resp.getBoundingClientRect().height),
            },
            tips,
            invalids,
            formClass,
          };
        }"""
    )
    print(info)
    browser.close()
