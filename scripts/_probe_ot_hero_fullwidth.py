# -*- coding: utf-8 -*-
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://pellomenosoficialteste.companygenesis.com.br"
SHOTS = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "hero-width-qa-shots"
SHOTS.mkdir(parents=True, exist_ok=True)

JS = """
() => {
  const hero = document.querySelector('#inicio');
  const img = document.querySelector("#inicio [data-hero-slide='0'] img");
  const r = hero.getBoundingClientRect();
  const ir = img.getBoundingClientRect();
  const cs = getComputedStyle(img);
  const parent = hero.parentElement && hero.parentElement.getBoundingClientRect();
  return {
    vw: window.innerWidth,
    hero: { w: r.width, h: r.height, left: r.left, right: window.innerWidth - r.right },
    img: {
      w: ir.width,
      h: ir.height,
      left: ir.left,
      objectFit: cs.objectFit,
      objectPosition: cs.objectPosition,
      currentSrc: img.currentSrc || img.src,
    },
    parentW: parent ? parent.width : null,
    heroGapL: r.left,
    heroGapR: window.innerWidth - r.right,
  };
}
"""


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for w, h in ((1280, 800), (1440, 900), (1920, 900)):
            page = browser.new_page(viewport={"width": w, "height": h})
            page.goto(BASE + f"/?pm=fw{w}", wait_until="networkidle", timeout=90000)
            page.wait_for_timeout(900)
            info = page.evaluate(JS)
            print(w, info)
            page.locator("#inicio").screenshot(path=str(SHOTS / f"fw-{w}.png"))
            page.close()
        browser.close()


if __name__ == "__main__":
    main()
