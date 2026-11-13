import { test, expect } from '@playwright/test';

const STORE = 'https://loja.pellomenos.com.br';

test('unit SP stays valid after clicking Finalizar', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });

  await page.goto(`${STORE}/produto/axila-cera/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const sel = page.locator('[data-pm-unit]');
  await sel.waitFor({ state: 'visible', timeout: 20000 });
  await sel.selectOption({ value: 'sp-avp' });
  console.log('produto: unidade sp-avp selecionada');

  const cart = await page.evaluate(() => JSON.parse(localStorage.getItem('pm-cart-v1') || '[]'));
  console.log('carrinho vazio antes do add:', cart.length === 0);

  await page.locator('[data-pm-add], button:has-text("Adicionar"), button[type="submit"]').first().click();
  await page.waitForTimeout(3500);

  const item = await page.evaluate(() => (JSON.parse(localStorage.getItem('pm-cart-v1') || '[]'))[0] || null);
  console.log('cart item:', JSON.stringify({
    unitId: item && item.unitId,
    unitName: item && item.unitName,
    wooOption: item && item.wooOption,
    city: item && item.city,
    stateName: item && item.stateName,
  }));

  await page.goto(`${STORE}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(6000);

  // abre a aba de dados (Iniciar) e depois pagamento, como a cliente
  const state1 = await page.evaluate(() => {
    const s = document.querySelector('select[name="unit"]') as HTMLSelectElement | null;
    if (!s) return { found: false };
    const valid = Array.from(s.options).some((o) => o.value === s.value);
    return { found: true, value: s.value, text: (s.options[s.selectedIndex] || {}).text, valid };
  });
  console.log('ANTES do clique:', JSON.stringify(state1));

  // dispara o handler de submit (é aqui que ensureAccesstageUnitFromCart roda)
  await page.evaluate(() => {
    const btn = document.querySelector('button.wpcf7-submit, button.pm-checkout-submit, input.wpcf7-submit');
    if (btn) btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
  });
  await page.waitForTimeout(2500);

  const state2 = await page.evaluate(() => {
    const s = document.querySelector('select[name="unit"]') as HTMLSelectElement | null;
    if (!s) return { found: false };
    const valid = Array.from(s.options).some((o) => o.value === s.value);
    const injected = Array.from(s.options).filter((o) => /Avenida Paulista/.test(o.text));
    return {
      found: true,
      value: s.value,
      text: (s.options[s.selectedIndex] || {}).text,
      valid,
      injectedOptions: injected.map((o) => ({ v: o.value, t: o.text })),
    };
  });
  console.log('DEPOIS do clique:', JSON.stringify(state2));
  console.log('console errors:', errors.slice(0, 5));

  expect(state1.found).toBe(true);
  expect(state1.valid).toBe(true);
  expect(state2.valid).toBe(true);
  expect(state2.value).not.toBe('sp-avp');
  expect(String(state2.text || '')).not.toMatch(/^RJ - Avenida Paulista$/);
});