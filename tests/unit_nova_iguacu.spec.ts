import { test, expect } from '@playwright/test';

const OT = process.env.PM_SITE || 'https://loja.pellomenos.com.br';

test('Nova Iguacu I nao vira II no checkout', async ({ page }) => {
  await page.goto(`${OT}/produto/axila-cera/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const sel = page.locator('[data-pm-unit]');
  await sel.waitFor({ state: 'visible', timeout: 20000 });
  // 'nig' = Nova Iguaçu I (Rua Otávio Tarquino)
  await sel.selectOption({ value: 'nig' });
  const escolha = await sel.locator('option:checked').textContent();
  console.log('produto: escolhido =', JSON.stringify(escolha?.trim()));

  await page.locator('[data-pm-add], button:has-text("Adicionar"), button[type="submit"]').first().click();
  await page.waitForTimeout(3500);
  const item = await page.evaluate(() => (JSON.parse(localStorage.getItem('pm-cart-v1') || '[]'))[0] || null);
  console.log('carrinho:', JSON.stringify({ unitId: item?.unitId, wooOption: item?.wooOption, city: item?.city }));

  await page.goto(`${OT}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(6000);

  // preenche o minimo para o handler de submit nao abortar
  await page.evaluate(() => {
    const set = (n: string, v: string) => {
      const el = document.querySelector(`[name="${n}"]`) as HTMLInputElement | null;
      if (el) { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }
    };
    set('your-name', 'Teste Unidade');
    set('estado', 'RJ');
  });
  await page.waitForTimeout(500);

  await page.evaluate(() => {
    const btn = document.querySelector('button.pm-checkout-submit, button.wpcf7-submit') as HTMLElement | null;
    if (btn) btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
  });
  await page.waitForTimeout(3000);

  const st = await page.evaluate(() => {
    const read = (n: string) => {
      const el = document.querySelector(`select[name="${n}"]`) as HTMLSelectElement | null;
      if (!el) return null;
      return { value: el.value, text: (el.options[el.selectedIndex] || {}).text };
    };
    return { unit: read('unit'), easy: read('easyunit') };
  });
  console.log('depois do clique:', JSON.stringify(st));

  // unit deve ser a Iguaçu I; easyunit (laser) não pode estar apontando para a II
  expect(st.unit?.value).toBe('RJ - Nova Iguaçu I - Rua Otávio Tarquino');
  expect(st.easy?.value || '').not.toContain('II');
});

test('Nova Iguacu II continua funcionando', async ({ page }) => {
  await page.goto(`${OT}/produto/axila-cera/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const sel = page.locator('[data-pm-unit]');
  await sel.waitFor({ state: 'visible', timeout: 20000 });
  await sel.selectOption({ value: 'nig2' });
  await page.locator('[data-pm-add], button:has-text("Adicionar"), button[type="submit"]').first().click();
  await page.waitForTimeout(3500);

  await page.goto(`${OT}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(6000);
  await page.evaluate(() => {
    const set = (n: string, v: string) => {
      const el = document.querySelector(`[name="${n}"]`) as HTMLInputElement | null;
      if (el) { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); }
    };
    set('your-name', 'Teste Unidade');
    set('estado', 'RJ');
    const btn = document.querySelector('button.pm-checkout-submit, button.wpcf7-submit') as HTMLElement | null;
    if (btn) btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
  });
  await page.waitForTimeout(3000);

  const val = await page.evaluate(() => {
    const el = document.querySelector('select[name="unit"]') as HTMLSelectElement | null;
    return el ? el.value : null;
  });
  console.log('NI II -> unit =', JSON.stringify(val));
  expect(val).toBe('RJ - Nova Iguaçu II - Ao lado TOP Shopping Nova Iguaçu');
});