import { test, expect } from '@playwright/test';

const STORE = 'https://loja.pellomenos.com.br';

const FILL = `(() => {
  const set = (n, v) => {
    const el = document.querySelector('[name="' + n + '"]');
    if (!el) return;
    el.value = v;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('blur', { bubbles: true }));
  };
  set('your-name', 'Cliente Teste');
  set('your-email', 'teste.cliente@example.com');
  set('your-phone', '21999998888');
  set('cpf', '123.456.789-01');
  set('cep', '01310-100');
  set('endereco', 'Avenida Paulista');
  set('numero', '1000');
  set('complemento', 'Sala 10');
  set('bairro', 'Bela Vista');
  set('cidade', 'Sao Paulo');
  set('estado', 'SP');
  const u = document.querySelector('select[name="unit"]');
  if (u) { u.value = 'SP - Capital - Av. Paulista'; u.dispatchEvent(new Event('change', { bubbles: true })); }
  return true;
})()`;

async function setupCheckout(page: any) {
  await page.goto(`${STORE}/produto/axila-cera/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const sel = page.locator('[data-pm-unit]');
  await sel.waitFor({ state: 'visible', timeout: 20000 });
  await sel.selectOption({ value: 'sp-avp' });
  await page.locator('[data-pm-add], button:has-text("Adicionar"), button[type="submit"]').first().click();
  await page.waitForTimeout(3000);
  await page.goto(`${STORE}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(5000);
}

const snapshot = () => {
  const g = (n: string) => {
    const el = document.querySelector(`[name="${n}"]`) as HTMLInputElement | null;
    return el ? el.value : null;
  };
  const u = document.querySelector('select[name="unit"]') as HTMLSelectElement | null;
  return {
    name: g('your-name'), email: g('your-email'), phone: g('your-phone'),
    cpf: g('cpf'), cep: g('cep'), endereco: g('endereco'), numero: g('numero'),
    complemento: g('complemento'), bairro: g('bairro'), cidade: g('cidade'), estado: g('estado'),
    unit: u ? u.value : null,
  };
};

test('falha de pagamento NAO apaga os dados preenchidos', async ({ page }) => {
  await setupCheckout(page);
  await page.evaluate(FILL);
  await page.waitForTimeout(1200);

  const antes = await page.evaluate(snapshot);
  console.log('antes:', JSON.stringify(antes));

  // simula o retorno "Compra não realizada" do gateway (wpcf7mailsent com mensagem de falha)
  await page.evaluate(() => {
    const out = document.querySelector('.wpcf7-response-output');
    if (out) out.textContent = 'Compra não realizada. Verifique os dados do cartão.';
    const form = document.querySelector('form.wpcf7-form') as HTMLFormElement | null;
    form!.dispatchEvent(
      new CustomEvent('wpcf7mailsent', {
        bubbles: true,
        detail: { apiResponse: { message: 'Compra não realizada. Verifique os dados do cartão.' } },
      }),
    );
  });
  await page.waitForTimeout(1500);

  const depois = await page.evaluate(snapshot);
  console.log('depois da falha:', JSON.stringify(depois));

  const draft = await page.evaluate(() => localStorage.getItem('pm-ck-draft-v1'));
  console.log('draft preservado:', !!draft);

  expect(depois.name).toBe('Cliente Teste');
  expect(depois.unit).toBe('SP - Capital - Av. Paulista');
  expect(draft).not.toBeNull();
});

test('dados voltam depois de recarregar o checkout na falha', async ({ page }) => {
  await setupCheckout(page);
  await page.evaluate(FILL);
  await page.waitForTimeout(1200);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);

  const depois = await page.evaluate(snapshot);
  console.log('apos reload:', JSON.stringify(depois));
  expect(depois.name).toBe('Cliente Teste');
  expect(depois.email).toBe('teste.cliente@example.com');
  expect(depois.cpf).not.toBe('');
  expect(depois.cep).toBe('01310-100');
  expect(depois.unit).toBe('SP - Capital - Av. Paulista');
});

test('rascunho NAO restaura apos sucesso', async ({ page }) => {
  await setupCheckout(page);
  await page.evaluate(FILL);
  await page.waitForTimeout(1200);
  await page.evaluate(() => {
    const out = document.querySelector('.wpcf7-response-output');
    if (out) out.textContent = 'Obrigado, seu pedido foi recebido.';
    const form = document.querySelector('form.wpcf7-form') as HTMLFormElement | null;
    form!.dispatchEvent(new CustomEvent('wpcf7mailsent', {
      bubbles: true,
      detail: { apiResponse: { message: 'Obrigado, seu pedido foi recebido.' } },
    }));
  });
  await page.waitForTimeout(1500);
  const draft = await page.evaluate(() => localStorage.getItem('pm-ck-draft-v1'));
  console.log('draft apos sucesso:', draft);
  expect(draft).toBeNull();
});
