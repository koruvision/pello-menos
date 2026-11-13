# -*- coding: utf-8 -*-
import json
from playwright.sync_api import sync_playwright

BASE = "https://pellomenosoficialteste.companygenesis.com.br"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        logs = []
        page.on("console", lambda m: logs.append(f"{m.type}: {m.text}"))
        page.on("pageerror", lambda e: logs.append(f"PAGEERROR: {e}"))
        page.on(
            "requestfailed",
            lambda r: logs.append(f"REQFAIL: {r.url} {r.failure}"),
        )
        page.goto(BASE + "/finalizar-pagamento/", wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(3000)
        info = page.evaluate(
            """async () => {
              const scripts = Array.from(document.querySelectorAll('script[src*=\"checkout-shell\"]')).map(s => ({
                src: s.src, async: s.async, defer: s.defer, type: s.type, ready: s.readyState || null
              }));
              let fetched = null;
              try {
                const r = await fetch(scripts[0] ? scripts[0].src : '/wp-content/uploads/pm-home/checkout-shell.js?v=shell7', {credentials:'same-origin'});
                const t = await r.text();
                fetched = { status: r.status, len: t.length, bootLine: t.includes('__pmShellBoot'), head: t.slice(0,80) };
              } catch (e) {
                fetched = { error: String(e) };
              }
              return {
                boot: window.__pmShellBoot || null,
                sync: window.__pmShellSyncStarted || null,
                scripts,
                fetched,
              };
            }"""
        )
        print(json.dumps(info, ensure_ascii=False, indent=2))
        print("LOGS:")
        for line in logs[-40:]:
            print(line)
        # Try manually injecting
        injected = page.evaluate(
            """async () => {
              const r = await fetch('/wp-content/uploads/pm-home/checkout-shell.js?v=shell7&x=' + Date.now());
              const t = await r.text();
              try {
                (0, eval)(t);
              } catch (e) {
                return { evalError: String(e), stack: e.stack };
              }
              return {
                boot: window.__pmShellBoot || null,
                sync: !!window.__pmShellSyncStarted,
                last: window.__pmLastTotals || null,
              };
            }"""
        )
        print("INJECT", json.dumps(injected, ensure_ascii=False))
        page.wait_for_timeout(1500)
        after = page.evaluate(
            """() => ({
              boot: window.__pmShellBoot || null,
              last: window.__pmLastTotals || null,
              fullvalue: (document.querySelector('[name=fullvalue]')||{}).value,
              cupomamount: (document.querySelector('[name=cupomamount]')||{}).value,
              totalamount: (document.querySelector('[name=totalamount]')||{}).value,
            })"""
        )
        print("AFTER", json.dumps(after, ensure_ascii=False))
        browser.close()


if __name__ == "__main__":
    main()
