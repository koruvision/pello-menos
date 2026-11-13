import { test, expect } from '@playwright/test';

const STORE = 'https://loja.pellomenos.com.br';

test('guard no wpcf7submit acusa item sem variacao', async ({ page }) => {
  await page.goto(`${STORE}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(5000);

  const res = await page.evaluate(() => {
    localStorage.setItem('pm-cart-v1', JSON.stringify([{
      lineId: 'x', id: 'barba-cera-masc', name: 'Barba', unitId: 'ape',
      unitName: 'Afonso Pena', priceCents: 3990, variationId: '', productId: '24196', qty: 1,
    }]));
    const form = document.querySelector('form.wpcf7-form') as HTMLFormElement | null;
    const tip = () => {
      const t = document.querySelector('.wpcf7-response-output');
      return t ? (t.textContent || '').trim() : '';
    };
    const ev = new Event('wpcf7submit', { bubbles: true, cancelable: true });
    form!.dispatchEvent(ev);
    return { defaultPrevented: ev.defaultPrevented, mensagem: tip() };
  });
  console.log(JSON.stringify(res));
  expect(res.defaultPrevented).toBe(true);
  expect(res.mensagem.toLowerCase()).toContain('não foi possível finalizar');
});

test('guard NAO bloqueia carrinho valido', async ({ page }) => {
  await page.goto(`${STORE}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(5000);

  const res = await page.evaluate(() => {
    localStorage.setItem('pm-cart-v1', JSON.stringify([{
      lineId: 'y', id: 'axila-cera', name: 'Axila', unitId: 'sp-avp',
      unitName: 'Avenida Paulista', wooOption: 'SP - Capital - Av. Paulista',
      priceCents: 2933, variationId: '23138', productId: '2319', qty: 1,
    }]));
    const u = document.querySelector('select[name="unit"]') as HTMLSelectElement | null;
    if (u) { u.value = 'SP - Capital - Av. Paulista'; }
    const form = document.querySelector('form.wpcf7-form') as HTMLFormElement | null;
    const ev = new Event('wpcf7submit', { bubbles: true, cancelable: true });
    form!.dispatchEvent(ev);
    return { defaultPrevented: ev.defaultPrevented };
  });
  console.log(JSON.stringify(res));
  expect(res.defaultPrevented).toBe(false);
});