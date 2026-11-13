import { test, expect } from '@playwright/test';

const STORE = process.env.PM_SITE || 'https://loja.pellomenos.com.br';

for (const path of ['/', '/masculino']) {
  test(`imagens carregam em ${path}`, async ({ page }) => {
    const falhas: string[] = [];
    page.on('response', (r) => {
      const u = r.url();
      if (!/\.(png|jpe?g|webp|gif|avif|svg)(\?|$)/i.test(u)) return;
      if (r.status() >= 400) falhas.push(`${r.status()} ${u}`);
    });

    await page.goto(STORE + path, { waitUntil: 'networkidle', timeout: 90000 });
    // percorre a pagina para disparar o lazy-load
    await page.evaluate(async () => {
      const step = window.innerHeight * 0.8;
      for (let y = 0; y < document.body.scrollHeight; y += step) {
        window.scrollTo(0, y);
        await new Promise((r) => setTimeout(r, 120));
      }
      window.scrollTo(0, 0);
    });
    await page.waitForTimeout(2000);

    // imagens que o navegador tentou carregar e ficaram sem dimensão
    const quebradas = await page.evaluate(() =>
      Array.from(document.images)
        .filter((i) => i.complete && i.naturalWidth === 0)
        .map((i) => i.currentSrc || i.src),
    );

    const resumo = await page.evaluate(() => {
      const imgs = Array.from(document.images);
      return {
        total: imgs.length,
        carregadas: imgs.filter((i) => i.complete && i.naturalWidth > 0).length,
        host: imgs[0] ? new URL(imgs[0].currentSrc || imgs[0].src).host : null,
      };
    });

    console.log(`${path} -> ${JSON.stringify(resumo)}`);
    console.log(`   falhas de rede: ${falhas.length} | sem dimensão: ${quebradas.length}`);
    if (falhas.length) console.log('   ', falhas.slice(0, 5));
    if (quebradas.length) console.log('    quebradas:', quebradas.slice(0, 5));

    // carrega cada URL explicitamente (nao depende de lazy-load / viewport)
    const urls = await page.evaluate(() =>
      Array.from(new Set(Array.from(document.images).map((i) => i.currentSrc || i.src))),
    );
    const ruins = await page.evaluate(async (list: string[]) => {
      const falhas: string[] = [];
      await Promise.all(
        list.map(
          (u) =>
            new Promise<void>((resolve) => {
              const img = new Image();
              img.onload = () => resolve();
              img.onerror = () => { falhas.push(u); resolve(); };
              img.src = u;
            }),
        ),
      );
      return falhas;
    }, urls);

    console.log(`   urls testadas: ${urls.length} | quebradas: ${ruins.length}`);
    if (ruins.length) console.log('   ', ruins.slice(0, 5));

    expect(falhas).toEqual([]);
    expect(quebradas).toEqual([]);
    expect(ruins).toEqual([]);
  });
}

test('banners do feminino carregam', async ({ page }) => {
  await page.goto(STORE + '/', { waitUntil: 'networkidle', timeout: 90000 });
  await page.waitForTimeout(2000);
  const banners = await page.evaluate(() => {
    const out: any[] = [];
    document.querySelectorAll('img, [style*="background-image"]').forEach((el) => {
      const src = (el as HTMLImageElement).currentSrc || (el as HTMLImageElement).src || '';
      const bg = getComputedStyle(el as HTMLElement).backgroundImage || '';
      const u = src || (bg.match(/url\(["']?([^)"']+)/) || [])[1] || '';
      if (!/hero|banner|promo|destaque/i.test(u)) return;
      const el2 = el as HTMLElement;
      out.push({
        url: u.split('/').pop()?.slice(0, 48),
        visivel: el2.offsetParent !== null,
        w: (el as HTMLImageElement).naturalWidth || null,
      });
    });
    return out.slice(0, 12);
  });
  console.log('banners encontrados:', JSON.stringify(banners, null, 1));
  const semDimensao = banners.filter((b: any) => b.w === 0);
  expect(semDimensao).toEqual([]);
});