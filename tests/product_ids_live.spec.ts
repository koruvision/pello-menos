import { test, expect } from '@playwright/test';

const STORE = process.env.PM_SITE || 'https://loja.pellomenos.com.br';

const CASOS = [
  { slug: 'esfoliacao-coxa', pid: '50250', unit: 'ipa', variacaoEsperada: '50270', nome: 'Esfoliação de coxa' },
  { slug: 'esfoliacao-nadegas', pid: '50422', unit: 'ipa', variacaoEsperada: '50442', nome: 'Esfoliação de nádegas' },
  { slug: 'esfoliacao-axilas', pid: '49939', unit: 'ban', variacaoEsperada: null, nome: 'Esfoliação de axilas' },
  { slug: 'axila-cera-masc', pid: '49975', unit: 'ban', variacaoEsperada: null, nome: 'Axila – Cera' },
  { slug: 'coxa-cera', pid: '3601', unit: 'ipa', variacaoEsperada: '13034', nome: 'Coxa – Cera' },
];

for (const c of CASOS) {
  test(`pagina ${c.slug} envia o produto correto ao carrinho`, async ({ page }) => {
    await page.goto(`${STORE}/produto/${c.slug}/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    const unitSel = page.locator('[data-pm-unit]');
    await unitSel.waitFor({ state: 'visible', timeout: 20000 });

    const htmlIds = await page.evaluate(() => {
      const box = document.querySelector('[data-pm-buy]') as HTMLElement | null;
      return box ? box.getAttribute('data-product-id') : null;
    });
    console.log(`${c.slug}: data-product-id na pagina =`, htmlIds);
    expect(htmlIds).toBe(c.pid);

    const temUnidade = await unitSel.locator(`option[value="${c.unit}"]`).count();
    if (!temUnidade) { test.skip(); return; }
    await unitSel.selectOption({ value: c.unit });

    const varOpt = await page.evaluate((u: string) => {
      const s = document.querySelector('[data-pm-unit]') as HTMLSelectElement | null;
      if (!s) return null;
      const o = Array.from(s.options).find((x) => x.value === u) as HTMLOptionElement | undefined;
      return o ? o.getAttribute('data-variation') : null;
    }, c.unit);
    console.log(`  data-variation de ${c.unit} =`, varOpt);
    if (c.variacaoEsperada) expect(varOpt).toBe(c.variacaoEsperada);

    await page.locator('[data-pm-add], button:has-text("Adicionar"), button[type="submit"]').first().click();
    await page.waitForTimeout(3500);

    const item = await page.evaluate(() => (JSON.parse(localStorage.getItem('pm-cart-v1') || '[]'))[0] || null);
    console.log('  carrinho:', JSON.stringify({ id: item?.id, nome: item?.name, pid: item?.productId, vid: item?.variationId }));
    expect(item?.id).toBe(c.slug);
    expect(String(item?.productId)).toBe(c.pid);
    if (c.variacaoEsperada) expect(String(item?.variationId)).toBe(c.variacaoEsperada);
    // esfoliação nunca pode cair no produto da cera correspondente
    if (c.slug.startsWith('esfoliacao')) {
      expect(String(item?.productId)).not.toBe('3601'); // Coxa – Cera
      expect(String(item?.productId)).not.toBe('3908'); // Nádegas – Cera
      expect(String(item?.productId)).not.toBe('2319'); // Axila – Cera
    }
  });
}