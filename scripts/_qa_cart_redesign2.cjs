/**
 * QA do carrinho: carrossel Netflix, barra rosa, recomendacoes por unidade.
 * Uso: node scripts/_qa_cart_redesign2.cjs   (com _qa_cart_server.cjs rodando)
 */
const { chromium } = require("playwright");

const BASE = "http://localhost:8899";
const item = (id, name, unitId, unitName, city, uf, price, key) => ({
  lineId: id + "::" + unitId, id, name, image: "/images/products/" + id + ".webp",
  duration: "~15 min • Avulso", sku: "PM-X", unitId, unitName, city, stateName: uf,
  priceCents: price, productId: "0", variationId: key, wooId: key, qty: 1, wooKey: key,
});

const CASES = {
  "avp-virilha": [item("virilha-cera", "Virilha Total – Cera", "sp-avp", "Avenida Paulista", "São Paulo", "SP", 5990, "k1")],
  "avp-axila": [item("axila-cera", "Axila – Cera", "sp-avp", "Avenida Paulista", "São Paulo", "SP", 2933, "k2")],
  "bot-esfoliacao": [item("esfoliacao-axilas", "Axilas – Esfoliação", "bot", "Botafogo", "Rio de Janeiro", "RJ", 4990, "k3")],
  "ipa-virilha": [item("virilha-cera", "Virilha Total – Cera", "ipa", "Ipanema", "Rio de Janeiro", "RJ", 5990, "k4")],
  "dfano-perna": [item("perna-cera", "Perna Inteira – Cera", "df-ano", "Asa Norte", "Brasília", "DF", 8990, "k5")],
  "masc-axila": [item("axila-cera-masc", "Axila – Cera", "sp-avp", "Avenida Paulista", "São Paulo", "SP", 3990, "k6")],
};

(async () => {
  const browser = await chromium.launch();
  const errors = [];

  for (const [name, cart] of Object.entries(CASES)) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    await ctx.addInitScript(([items]) => localStorage.setItem("pm-cart-v1", JSON.stringify(items)), [cart]);
    const page = await ctx.newPage();
    page.on("pageerror", (e) => errors.push(name + " PAGEERROR " + e.message));
    await page.goto(BASE + "/carrinho/?" + Date.now(), { waitUntil: "networkidle" });
    await page.waitForSelector('[data-pm-cart-page][data-pm-cart-state="ready"]', { timeout: 30000 });
    await page.waitForTimeout(900);

    const out = await page.evaluate(() => {
      const rail = document.querySelector("[data-pm-rail]");
      const track = rail && rail.querySelector("[data-pm-rail-track]");
      const cards = track ? Array.from(track.children) : [];
      const setSize = track ? Number(track.getAttribute("data-set-size")) : 0;
      const ids = cards.slice(0, setSize).map((c) => c.querySelector("[data-pm-related-add]").getAttribute("data-pm-related-add"));
      const cw = cards.length ? cards[0].getBoundingClientRect().width : 0;
      const peek = rail ? rail.clientWidth - (cw * Math.min(2, setSize) + 10 * (Math.min(2, setSize) - 1)) : 0;
      const addBtn = cards[0] && cards[0].querySelector(".pm-rail__add");
      const total = document.querySelector(".pm-paybar__total strong");
      const bar = document.querySelector(".pm-paybar");
      return {
        ids, setSize, dupSlides: cards.length === setSize * 3,
        cardW: Math.round(cw), railW: rail ? rail.clientWidth : 0,
        peekPx: Math.round(peek),
        addColor: addBtn ? getComputedStyle(addBtn).color : null,
        addBg: addBtn ? getComputedStyle(addBtn).backgroundColor : null,
        totalFont: total ? getComputedStyle(total).fontFamily.split(",")[0] : null,
        totalSize: total ? getComputedStyle(total).fontSize : null,
        barBg: bar ? getComputedStyle(bar).backgroundImage.slice(0, 60) : null,
      };
    });

    // disponibilidade real de cada recomendacao na unidade do carrinho
    const check = await page.evaluate(async ([unitId, ids]) => {
      const rel = await fetch("/wp-content/uploads/pm-home/cart-related.json").then((r) => r.json());
      return ids.map((id) => {
        const row = rel.products[id];
        const meta = row && row.units && row.units[unitId];
        return { id, ok: !!(meta && meta.variationId), option: meta ? meta.option : null };
      });
    }, [cart[0].unitId, out.ids]);

    console.log(`\n== ${name} (${cart[0].unitName}) ==`);
    console.log("  picks:", out.ids.join(", ") || "(nenhum)");
    console.log("  units ok:", check.every((c) => c.ok), check.filter((c) => !c.ok).map((c) => c.id));
    console.log("  slides:", out.setSize, "x3 =", out.dupSlides, "| card", out.cardW, "px | peek", out.peekPx, "px");
    console.log("  botao:", out.addColor, "bg", out.addBg);
    console.log("  total:", out.totalFont, out.totalSize, "| barra:", out.barBg);
    await ctx.close();
  }

  // loop + arraste + adicionar
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
  await ctx.addInitScript(([items]) => localStorage.setItem("pm-cart-v1", JSON.stringify(items)), [CASES["avp-virilha"]]);
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push("loop PAGEERROR " + e.message));
  await page.goto(BASE + "/carrinho/?" + Date.now(), { waitUntil: "networkidle" });
  await page.waitForSelector('[data-pm-cart-page][data-pm-cart-state="ready"]', { timeout: 30000 });
  await page.waitForTimeout(800);

  const wrap = await page.evaluate(async () => {
    const r = document.querySelector("[data-pm-rail]");
    const w = r.scrollWidth / 3;
    const out = [];
    for (const f of [2.4, 0.3, 1.5]) {
      r.scrollLeft = w * f;
      r.dispatchEvent(new Event("scroll"));
      await new Promise((res) => setTimeout(res, 160));
      out.push(+(r.scrollLeft / w).toFixed(2));
    }
    return out;
  });
  console.log("\nloop (posicao em conjuntos, sempre ~0.5-1.5):", JSON.stringify(wrap));

  const bw = await page.locator("[data-pm-rail]").boundingBox();
  await page.mouse.move(bw.x + bw.width - 30, bw.y + 100);
  await page.mouse.down();
  await page.mouse.move(bw.x + 20, bw.y + 100, { steps: 12 });
  await page.mouse.up();
  await page.waitForTimeout(700);
  console.log("arraste -> scrollLeft:", await page.evaluate(() => Math.round(document.querySelector("[data-pm-rail]").scrollLeft)));

  const addId = await page.locator("[data-pm-rail] [data-pm-related-add]").first().getAttribute("data-pm-related-add");
  await page.locator("[data-pm-rail] [data-pm-related-add]").first().click();
  await page.waitForTimeout(3500);
  console.log("adicionar", addId, "-> linhas:", await page.locator(".pm-line").count(),
    "| total:", await page.locator(".pm-paybar__total strong").textContent());
  await page.screenshot({ path: "C:/Users/GC1/Desktop/pello-menos/.tmp-q-390.png" });
  await ctx.close();

  // desktop: 4 + peek
  const d = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  await d.addInitScript(([items]) => localStorage.setItem("pm-cart-v1", JSON.stringify(items)), [CASES["avp-virilha"]]);
  const dp = await d.newPage();
  await dp.goto(BASE + "/carrinho/?" + Date.now(), { waitUntil: "networkidle" });
  await dp.waitForSelector('[data-pm-cart-page][data-pm-cart-state="ready"]', { timeout: 30000 });
  await dp.waitForTimeout(900);
  console.log("\ndesktop:", JSON.stringify(await dp.evaluate(() => {
    const r = document.querySelector("[data-pm-rail]");
    const cards = Array.from(r.querySelector("[data-pm-rail-track]").children);
    const cw = cards[0].getBoundingClientRect().width;
    return { railW: r.clientWidth, cardW: Math.round(cw), full: Math.floor(r.clientWidth / cw), peek: Math.round(r.clientWidth - Math.floor(r.clientWidth / cw) * (cw + 12)) };
  })));
  await dp.screenshot({ path: "C:/Users/GC1/Desktop/pello-menos/.tmp-q-1280.png" });
  await d.close();

  console.log("\nerrors:", errors.slice(0, 8));
  await browser.close();
})();
