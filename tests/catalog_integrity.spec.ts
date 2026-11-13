import { test, expect } from '@playwright/test';

const STORE = 'https://loja.pellomenos.com.br';

test('catalogo: productId e variacoes coerentes com o WooCommerce', async ({ request }) => {
  const cr = await (await request.get(`${STORE}/wp-content/uploads/pm-home/cart-related.json`)).json();
  const products = cr.products;

  // amostra representativa
  const keys = ['axila-cera', 'virilha-cera', 'virilha-comum-cera', 'virilha-laser',
    'virilha-comum-laser', 'perna-cera', 'abdomen-laser', 'plano-gold', 'virilha-cera-masc'];

  const failures: string[] = [];
  for (const key of keys) {
    const row = products[key];
    if (!row) { failures.push(`${key}: ausente`); continue; }
    const pid = String(row.productId || '');
    const prod = await (await request.get(`${STORE}/wp-json/wc/store/v1/products/${pid}`)).json().catch(() => null);
    if (!prod || !prod.id) { failures.push(`${key}: productId ${pid} inexistente`); continue; }
    const varsRes = await request.get(`${STORE}/wp-json/wc/store/v1/products?type=variation&parent=${pid}&per_page=100`);
    const vars = varsRes.ok() ? await varsRes.json() : [];
    const ids = new Set((Array.isArray(vars) ? vars : []).map((v: any) => String(v.id)));
    const units = row.units || {};
    const vids = Object.values(units).map((m: any) => String(m.variationId)).filter(Boolean);
    const bad = vids.filter((v) => !ids.has(v));
    console.log(`${key}: pid=${pid} (${prod.name}) units=${vids.length} fora=${bad.length}`);
    if (bad.length) failures.push(`${key}: ${bad.length} variacoes fora do produto ${pid}`);
  }
  expect(failures).toEqual([]);
});

test('checkout: unidade SP valida e nao injeta opcao fake', async ({ page }) => {
  await page.goto(`${STORE}/produto/axila-cera/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const sel = page.locator('[data-pm-unit]');
  await sel.waitFor({ state: 'visible', timeout: 20000 });
  await sel.selectOption({ value: 'sp-avp' });
  await page.locator('[data-pm-add], button:has-text("Adicionar"), button[type="submit"]').first().click();
  await page.waitForTimeout(3500);

  await page.goto(`${STORE}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(6000);

  const st = await page.evaluate(() => {
    const s = document.querySelector('select[name="unit"]') as HTMLSelectElement | null;
    if (!s) return null;
    const vals = Array.from(s.options).map((o) => (o as HTMLOptionElement).value);
    return {
      value: s.value,
      valid: vals.includes(s.value),
      texto: (s.options[s.selectedIndex] || {}).text,
      injetadas: vals.filter((v) => v === 'sp-avp').length,
      total: vals.length,
    };
  });
  console.log('checkout:', JSON.stringify(st));
  expect(st).not.toBeNull();
  expect(st!.valid).toBe(true);
  expect(st!.value).toBe('SP - Capital - Av. Paulista');
  expect(st!.injetadas).toBe(0);
});