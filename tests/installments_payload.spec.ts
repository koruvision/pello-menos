import { test, expect } from '@playwright/test';

const OT = process.env.PM_SITE || 'https://loja.pellomenos.com.br';

function parseMultipart(body: string): Record<string, string> {
  const out: Record<string, string> = {};
  const re = /name="([^"]+)"[\s\S]{0,40}?\r?\n\r?\n([^\r\n]*)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(body))) out[m[1]] = m[2];
  return out;
}

const CAMPOS = ['installments', 'cerainstallments', 'allinstallments', 'siteinstallment', 'unit', 'easyunit', 'totalamount'];

async function interceptar(page: any) {
  const state: { payload: Record<string, string> | null; raw: string } = { payload: null, raw: '' };
  await page.route('**/contact-form-7/v1/contact-forms/*/feedback', async (route: any) => {
    const raw = route.request().postDataBuffer()?.toString('utf8') || route.request().postData() || '';
    state.raw = raw;
    const all = parseMultipart(raw);
    const sel: Record<string, string> = {};
    for (const k of CAMPOS) if (k in all) sel[k] = all[k];
    state.payload = sel;
    await route.abort();
  });
  return state;
}

async function preencher(page: any) {
  await page.evaluate(() => {
    const set = (n: string, v: string) => {
      const el = document.querySelector(`[name="${n}"]`) as HTMLInputElement | null;
      if (el) {
        el.value = v;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    };
    set('your-name', 'Teste Parcelas');
    set('your-email', 'teste.parcelas@example.com');
    set('your-phone', '21999998888');
    set('cpf', '123.456.789-01');
    set('cep', '01310-100');
    set('endereco', 'Rua Teste');
    set('numero', '100');
    set('bairro', 'Centro');
    set('estado', 'RJ');
    set('cart-number', '4111111111111111');
    set('holder', 'TESTE PARCELAS');
    set('expiration', '12/2030');
    set('securityCode', '123');
    const d = document.querySelector('[name="declaracao"]') as HTMLInputElement | null;
    if (d) d.checked = true;
  });
}

async function clicarFinalizar(page: any) {
  await page.evaluate(() => {
    const btn = document.querySelector('button.pm-checkout-submit, button.wpcf7-submit') as HTMLElement | null;
    if (btn) btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
  });
  await page.waitForTimeout(5000);
}

test('caro: escolher 10x faz o payload sair 10x', async ({ page }) => {
  const state = await interceptar(page);

  await page.goto(`${OT}/produto/virilha-laser/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const unitSel = page.locator('[data-pm-unit]');
  await unitSel.waitFor({ state: 'visible', timeout: 20000 });
  await unitSel.selectOption({ value: 'ban' });
  await page.locator('[data-pm-add], button:has-text("Adicionar"), button[type="submit"]').first().click();
  await page.waitForTimeout(3500);

  await page.goto(`${OT}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(6000);

  // a cliente escolhe 10x no select de parcelas (o único com 1..10)
  await page.evaluate(() => {
    const el = document.querySelector('select[name="allinstallments"]') as HTMLSelectElement | null;
    if (el) {
      el.value = '10x';
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
  await page.waitForTimeout(900);

  const antes = await page.evaluate(() => {
    const g = (n: string) => {
      const el = document.querySelector(`select[name="${n}"]`) as HTMLSelectElement | null;
      return el ? el.value : null;
    };
    return { installments: g('installments'), cerainstallments: g('cerainstallments'), allinstallments: g('allinstallments') };
  });
  console.log('ANTES do envio:', JSON.stringify(antes));

  await preencher(page);
  await page.waitForTimeout(600);
  await clicarFinalizar(page);

  console.log('PAYLOAD:', JSON.stringify(state.payload));
  const p = state.payload || {};
  const phpUsa = p.installments || p.cerainstallments || p.allinstallments;
  console.log('PHP usaria:', JSON.stringify(phpUsa));
  expect(phpUsa).toBe('10x');
});

test('barato: continua 1x e envia sem erro', async ({ page }) => {
  const state = await interceptar(page);

  await page.goto(`${OT}/produto/axila-cera/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const unitSel = page.locator('[data-pm-unit]');
  await unitSel.waitFor({ state: 'visible', timeout: 20000 });
  await unitSel.selectOption({ value: 'ban' });
  await page.locator('[data-pm-add], button:has-text("Adicionar"), button[type="submit"]').first().click();
  await page.waitForTimeout(3000);

  await page.goto(`${OT}/finalizar-pagamento/`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(6000);
  await preencher(page);
  await page.waitForTimeout(600);
  await clicarFinalizar(page);

  console.log('PAYLOAD barato:', JSON.stringify(state.payload));
  const p = state.payload || {};
  const phpUsa = p.installments || p.cerainstallments || p.allinstallments;
  console.log('PHP usaria:', JSON.stringify(phpUsa));
  expect(phpUsa).toBe('1x');
});