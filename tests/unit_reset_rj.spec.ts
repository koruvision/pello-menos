import { test, expect } from '@playwright/test';

const STORE = 'https://loja.pellomenos.com.br';

async function addProduct(page: any, catalog: string, unit: string) {
  await page.goto(`${STORE}/produto/${catalog}/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const sel = page.locator('[data-pm-unit]');
  await sel.waitFor({ state: 'visible', timeout: 20000 });
  await sel.selectOption({ value: unit });
  await page.locator('[data-pm-add], button:has-text("Adicionar"), button[type="submit"]').first().click();
  await page.waitForTimeout(3500);
  return page.evaluate(() => (JSON.parse(localStorage.getItem('pm-cart-v1') || '[]'))[0] || null);
}

test('regressao RJ - Ipanema continua valida apos clique em Finalizar', async ({ page }) => {
  const item = await addProduct(page, 'axila-cera', 'ipa');
  console.log('RJ cart item:', JSON.stringify({ unitId: item && item.unitId, wooOption: item && item.wooOption }));
  await page.goto(`${STORE}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(6000);

  const read = () =>
    page.evaluate(() => {
      const s = document.querySelector('select[name="unit"]') as HTMLSelectElement | null;
      return s ? { value: s.value, valid: Array.from(s.options).some((o) => (o as HTMLOptionElement).value === s.value) } : null;
    });

  const before = await read();
  await page.evaluate(() => {
    const btn = document.querySelector('button.pm-checkout-submit, button.wpcf7-submit') as HTMLElement | null;
    if (btn) btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
  });
  await page.waitForTimeout(2500);
  const after = await read();
  console.log('RJ antes:', JSON.stringify(before), 'depois:', JSON.stringify(after));
  expect(after && after.valid).toBe(true);
  expect(after!.value).toBe('RJ - Ipanema');
});