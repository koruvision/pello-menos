import { test, expect } from '@playwright/test';

const STORE = process.env.PM_SITE || 'https://loja.pellomenos.com.br';

test('cesta da Isabella (pedido 51248): 4 servicos, nenhum duplicado', async ({ page }) => {
  const itens = [
    { slug: 'coxa-cera', unit: 'ipa' },
    { slug: 'virilha-cavada-cera', unit: 'ipa' },
    { slug: 'esfoliacao-nadegas', unit: 'ipa' },
    { slug: 'esfoliacao-coxa', unit: 'ipa' },
  ];

  await page.goto(`${STORE}/produto/coxa-cera/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  for (const it of itens) {
    await page.goto(`${STORE}/produto/${it.slug}/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    const sel = page.locator('[data-pm-unit]');
    await sel.waitFor({ state: 'visible', timeout: 20000 });
    await sel.selectOption({ value: it.unit });
    await page.locator('[data-pm-add], button:has-text("Adicionar"), button[type="submit"]').first().click();
    await page.waitForTimeout(2600);
  }

  const cart = await page.evaluate(() => JSON.parse(localStorage.getItem('pm-cart-v1') || '[]'));
  console.log('carrinho:', JSON.stringify(cart.map((i: any) => ({ id: i.id, pid: i.productId, vid: i.variationId, preco: i.priceCents })), null, 1));

  const pids = cart.map((i: any) => String(i.productId));
  expect(new Set(pids).size).toBe(4);
  expect(pids).toContain('3601');   // coxa cera
  expect(pids).toContain('4382');   // virilha cavada
  expect(pids).toContain('50422');  // esfoliacao nadegas
  expect(pids).toContain('50250');  // esfoliacao coxa

  // vai ao checkout e confere o campo oculto `cart` (o que o PHP vai ler)
  await page.goto(`${STORE}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(7000);

  const ocultos = await page.evaluate(() => {
    const g = (n: string) => {
      const el = document.querySelector(`[name="${n}"]`) as HTMLInputElement | null;
      return el ? el.value : null;
    };
    return { cart: g('cart'), cartqtd: g('cartqtd'), totalamount: g('totalamount'), unit: (document.querySelector('select[name="unit"]') as HTMLSelectElement | null)?.value };
  });
  console.log('campos ocultos:', JSON.stringify(ocultos));

  const ids = String(ocultos.cart || '').split(',').filter(Boolean);
  console.log('variacoes enviadas ao pedido:', ids);
  expect(new Set(ids).size).toBe(4);
  expect(ids).toContain('50270'); // esfoliacao coxa em ipanema
  expect(ids).toContain('50442'); // esfoliacao nadegas em ipanema
  expect(ocultos.unit).toBe('RJ - Ipanema');
});