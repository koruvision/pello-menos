import { test, expect } from '@playwright/test';

const STORE = 'https://loja.pellomenos.com.br';

test('unidade e dados voltam depois de recarregar o checkout (falha do pagamento)', async ({ page }) => {
  await page.goto(`${STORE}/produto/axila-cera/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const sel = page.locator('[data-pm-unit]');
  await sel.waitFor({ state: 'visible', timeout: 20000 });
  await sel.selectOption({ value: 'sp-avp' });
  await page.locator('[data-pm-add], button:has-text("Adicionar"), button[type="submit"]').first().click();
  await page.waitForTimeout(3500);

  await page.goto(`${STORE}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(6000);

  // preenche alguns campos e garante a unidade
  await page.evaluate(() => {
    const set = (n: string, v: string) => {
      const el = document.querySelector(`[name="${n}"]`) as HTMLInputElement | null;
      if (el) { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }
    };
    set('your-name', 'Cliente Teste');
    set('cpf', '12345678901');
    set('cep', '01310-100');
    set('endereco', 'Avenida Paulista');
    set('numero', '1000');
    set('bairro', 'Bela Vista');
    const u = document.querySelector('select[name="unit"]') as HTMLSelectElement | null;
    if (u) { u.value = 'SP - Capital - Av. Paulista'; u.dispatchEvent(new Event('change', { bubbles: true })); }
  });
  await page.waitForTimeout(1200);

  const draft = await page.evaluate(() => localStorage.getItem('pm-ck-draft-v1'));
  console.log('draft salvo:', draft);

  // simula o retorno da "compra não realizada" (recarregar o checkout)
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);

  const after = await page.evaluate(() => {
    const u = document.querySelector('select[name="unit"]') as HTMLSelectElement | null;
    const name = document.querySelector('[name="your-name"]') as HTMLInputElement | null;
    const cep = document.querySelector('[name="cep"]') as HTMLInputElement | null;
    return {
      unit: u ? u.value : null,
      unitValid: u ? Array.from(u.options).some((o) => (o as HTMLOptionElement).value === u.value) : false,
      name: name ? name.value : null,
      cep: cep ? cep.value : null,
    };
  });
  console.log('depois do reload:', JSON.stringify(after));

  expect(after.unit).toBe('SP - Capital - Av. Paulista');
  expect(after.unitValid).toBe(true);
  expect(after.name).toBe('Cliente Teste');
  expect(after.cep).toBe('01310-100');
});