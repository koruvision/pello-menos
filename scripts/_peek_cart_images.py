# -*- coding: utf-8 -*-
"""Inspect Store API images for cart items on checkout."""
from playwright.sync_api import sync_playwright

BASE = "https://pellomenosoficialteste.companygenesis.com.br"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(BASE + "/carrinho/?pm=img", wait_until="domcontentloaded", timeout=90000)
    info = page.evaluate(
        """async () => {
          const r = await fetch('/wp-json/wc/store/v1/cart', { credentials: 'same-origin' });
          let n = r.headers.get('Nonce') || '';
          const d = await r.json();
          for (const it of (d.items || [])) {
            const rr = await fetch('/wp-json/wc/store/v1/cart/remove-item', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json', Nonce: n },
              body: JSON.stringify({ key: it.key })
            });
            n = rr.headers.get('Nonce') || n;
          }
          // body splash 48219 used in coupon tests; also try axila variation
          const add = await fetch('/wp-json/wc/store/v1/cart/add-item?id=48219&quantity=1', {
            method: 'POST', credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', Nonce: n }
          });
          n = add.headers.get('Nonce') || n;
          const body = await add.json();
          return (body.items || []).map(it => ({
            name: it.name,
            id: it.id,
            images: it.images,
            permalink: it.permalink,
          }));
        }"""
    )
    print(info)
    browser.close()
