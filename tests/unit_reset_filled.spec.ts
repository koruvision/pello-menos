import { test, expect } from '@playwright/test';

const STORE = 'https://loja.pellomenos.com.br';

test('handler de submit restaura unidade SP quando o select volta vazio', async ({ page }) => {
  await page.goto(`${STORE}/produto/axila-cera/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const sel = page.locator('[data-pm-unit]');
  await sel.waitFor({ state: 'visible', timeout: 20000 });
  await sel.selectOption({ value: 'sp-avp' });
  await page.locator('[data-pm-add], button:has-text("Adicionar"), button[type="submit"]').first().click();
  await page.waitForTimeout(3500);

  await page.goto(`${STORE}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(6000);

  // Preenche o mínimo para o handler nao abortar em validateEstadoUfField/name
  await page.evaluate(() => {
    const set = (n: string, v: string) => {
      const el = document.querySelector(`[name="${n}"]`) as HTMLInputElement | null;
      if (el) { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }
    };
    set('your-name', 'Teste Cliente');
    set('estado', 'SP');
    // Simula o retorno do pagamento: CF7 limpa o select
    const s = document.querySelector('select[name="unit"]') as HTMLSelectElement | null;
    if (s) { s.selectedIndex = 0; s.value = ''; }
  });

  const before = await page.evaluate(() => {
    const s = document.querySelector('select[name="unit"]') as HTMLSelectElement | null;
    return s ? s.value : null;
  });
  console.log('valor antes do clique:', JSON.stringify(before));

  await page.evaluate(() => {
    const btn = document.querySelector('button.pm-checkout-submit, button.wpcf7-submit') as HTMLElement | null;
    if (btn) btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
  });
  await page.waitForTimeout(2500);

  const after = await page.evaluate(() => {
    const s = document.querySelector('select[name="unit"]') as HTMLSelectElement | null;
    if (!s) return null;
    const valid = Array.from(s.options).some((o) => (o as HTMLOptionElement).value === s.value);
    return { value: s.value, text: (s.options[s.selectedIndex] || {}).text, valid };
  });
  console.log('valor depois do clique:', JSON.stringify(after));

  expect(after).not.toBeNull();
  expect(after!.valid).toBe(true);
  expect(after!.value).toBe('SP - Capital - Av. Paulista');
});