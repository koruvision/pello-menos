/**
 * QA do redesign do carrinho em harness local (sem tocar producao).
 * Uso: node scripts/_qa_cart_local.cjs   (com _qa_cart_server.cjs rodando)
 */
const { chromium } = require("playwright");

const BASE = "http://localhost:8899";

// item sintetico no formato do localStorage pm-cart-v1 (nao toca a loja)
const seedOne = [
  {
    lineId: "axila-cera::sp-avp",
    id: "axila-cera",
    name: "Axila – Cera",
    image: "/images/products/axila-cera.webp",
    duration: "~15 min • Avulso",
    sku: "PM-0002",
    unitId: "sp-avp",
    unitName: "Avenida Paulista",
    city: "São Paulo",
    stateName: "SP",
    priceCents: 2933,
    variationId: "23138",
    productId: "2319",
    wooOption: "SP - Capital - Av. Paulista",
    qty: 1,
    wooKey: "seed1",
    wooId: "23138",
  },
];

function secondItem() {
  const b = JSON.parse(JSON.stringify(seedOne[0]));
  b.lineId = "perna-cera::sp-avp";
  b.id = "perna-cera";
  b.name = "Perna Inteira – Cera";
  b.image = "https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/perna-cera.webp";
  b.sku = "PM-ALT";
  b.priceCents = 8990;
  b.qty = 2;
  b.wooKey = "fake2";
  b.wooId = "23138";
  b.variationId = "23138";
  b.productId = "3973";
  return b;
}

(async () => {
  const browser = await chromium.launch();
  const errors = [];

  async function open(width, height, cart, mobile) {
    const ctx = await browser.newContext({ viewport: { width, height }, isMobile: !!mobile, hasTouch: !!mobile });
    await ctx.addInitScript(
      ([items]) => {
        localStorage.setItem("pm-cart-v1", JSON.stringify(items));
      },
      [cart],
    );
    const page = await ctx.newPage();
    page.on("pageerror", (e) => errors.push("PAGEERROR " + e.message));
    page.on("console", (m) => {
      const t = m.text();
      if (m.type() === "error" && !/ERR_FAILED|CORS|font/i.test(t)) errors.push("CONSOLE " + t.slice(0, 160));
    });
    await page.goto(BASE + "/carrinho/", { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForSelector('[data-pm-cart-page]:not([data-pm-cart-state="loading"])', { timeout: 30000 });
    await page.waitForTimeout(1200);
    return { ctx, page };
  }

  const probe = (page) =>
    page.evaluate(() => {
      const q = (s) => document.querySelector(s);
      const rail = q("[data-pm-rail]");
      const track = q("[data-pm-rail-track]");
      const cards = track ? Array.from(track.children) : [];
      const cw = cards.length ? cards[0].getBoundingClientRect().width : 0;
      const paybar = q(".pm-paybar");
      const inline = q(".pm-pay-inline");
      return {
        state: q("[data-pm-cart-page]").getAttribute("data-pm-cart-state"),
        lines: document.querySelectorAll(".pm-line").length,
        footer: q(".site-footer") ? getComputedStyle(q(".site-footer")).display : "none",
        bottomNav: q("nav.fixed.bottom-0") ? getComputedStyle(q("nav.fixed.bottom-0")).display : "none",
        paybar: paybar ? getComputedStyle(paybar).display : "none",
        paybarTotal: q(".pm-paybar__total strong") ? q(".pm-paybar__total strong").textContent : null,
        payLinks: document.querySelectorAll('a[href="/finalizar-pagamento/"]').length,
        inlinePay: inline ? getComputedStyle(inline).display : "none",
        railCards: cards.length,
        setSize: track ? track.getAttribute("data-set-size") : null,
        perView: cw ? +((rail ? rail.clientWidth : 0) / cw).toFixed(2) : 0,
        scrollLeft: rail ? Math.round(rail.scrollLeft) : null,
        mainPadBottom: getComputedStyle(q("[data-pm-cart-page]")).paddingBottom,
        overflowX: document.documentElement.scrollWidth > window.innerWidth,
        paybarBottom: paybar ? Math.round(paybar.getBoundingClientRect().bottom) : null,
        winH: window.innerHeight,
        lastLineBottom: document.querySelector(".pm-line") ? Math.round(document.querySelectorAll(".pm-line")[document.querySelectorAll(".pm-line").length - 1].getBoundingClientRect().bottom + window.scrollY) : null,
      };
    });

  // ---------- mobile 390 ----------
  let { ctx, page } = await open(390, 844, [seedOne[0], secondItem()], true);
  console.log("390 :", JSON.stringify(await probe(page)));

  // loop: avanca 8x
  const startX = await page.evaluate(() => Math.round(document.querySelector("[data-pm-rail]").scrollLeft));
  const wrapTest = await page.evaluate(async () => {
    const r = document.querySelector("[data-pm-rail]");
    const w = r.scrollWidth / 3;
    const out = [];
    for (const f of [1.6, 0.2, 2.4]) {
      r.scrollLeft = w * f;
      r.dispatchEvent(new Event("scroll"));
      await new Promise((res) => setTimeout(res, 150));
      out.push(Math.round(r.scrollLeft / w * 100) / 100);
    }
    return out;
  });
  console.log("wrap (em multiplos do conjunto)", JSON.stringify(wrapTest));
  console.log("scroll inicial no conjunto do meio:", startX);

  // adicionar pelo carrossel (nao deve quebrar)
  const addCount = await page.locator("[data-pm-rail] [data-pm-related-add]").count();
  console.log("botoes adicionar no trilho:", addCount);
  await page.locator("[data-pm-rail] [data-pm-related-add]").nth(6).click({ force: true }).catch((e) => console.log("click err", e.message));
  await page.waitForTimeout(1200);

  // qty + remover
  const qtyBefore = await page.locator(".pm-line").first().locator(".pm-line__qty span").textContent();
  await page.locator("[data-inc]").first().click();
  await page.waitForTimeout(900);
  const qtyAfter = await page.evaluate(() => JSON.parse(localStorage.getItem("pm-cart-v1"))[0].qty);
  console.log("qty", qtyBefore, "->", qtyAfter);

  await page.screenshot({ path: "C:/Users/GC1/Desktop/pello-menos/.tmp-cart-390.png" });
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(600);
  await page.screenshot({ path: "C:/Users/GC1/Desktop/pello-menos/.tmp-cart-390-bottom.png" });
  await ctx.close();

  // ---------- 360 estreito -> 1 por vez ----------
  ({ ctx, page } = await open(360, 780, [seedOne[0], secondItem()], true));
  console.log("360 :", JSON.stringify(await probe(page)));
  await page.screenshot({ path: "C:/Users/GC1/Desktop/pello-menos/.tmp-cart-360.png" });
  await ctx.close();

  // ---------- 768 tablet -> 3 ----------
  ({ ctx, page } = await open(768, 1024, [seedOne[0], secondItem()], true));
  console.log("768 :", JSON.stringify(await probe(page)));
  await page.screenshot({ path: "C:/Users/GC1/Desktop/pello-menos/.tmp-cart-768.png" });
  await ctx.close();

  // ---------- 1280 desktop -> 4 + resumo lateral ----------
  ({ ctx, page } = await open(1280, 900, [seedOne[0], secondItem()], false));
  console.log("1280:", JSON.stringify(await probe(page)));
  await page.screenshot({ path: "C:/Users/GC1/Desktop/pello-menos/.tmp-cart-1280.png" });
  await ctx.close();

  // ---------- vazio ----------
  ({ ctx, page } = await open(390, 844, [], true));
  console.log("vazio:", JSON.stringify(await probe(page)));
  await ctx.close();

  console.log("errors:", errors.slice(0, 12));
  await browser.close();
})();
