# 23 — Baseline PageSpeed Insights (loja)

- Gerado em: `20261031T010403Z` (UTC)
- Destino: `https://loja.pellomenos.com.br`
- Corridas por URL/estratégia: `1` (mediana)
- Fonte: Google PageSpeed Insights API v5 + GET medido dos assets
- Checkout: `/finalizar-pagamento/` medido só em GET; **zero alteração de código**
- Chave PSI: variável `PM_PAGESPEED_API_KEY` (não versionada)

## Resumo scores (mediana)

| Página | Mobile | Desktop | LCP mobile (ms) | TBT mobile (ms) | CLS mobile | Bytes total (PSI mobile) |
|--------|--------|---------|-----------------|-----------------|------------|--------------------------|
| `home-fem` | 91 | 99 | 2131.0 | 276.0 | 0.001 | 2.28 MB |
| `home-masc` | 54 | 90 | 3303.0 | 4084.0 | 0.001 | 2.55 MB |
| `pdp-cera` | 96 | 95 | 1876.1 | 140.5 | 0.001 | 1.07 MB |
| `pdp-laser` | 96 | 88 | 2253.7 | 183.0 | 0.001 | 904.2 KB |
| `carrinho` | 70 | 71 | 7851.1 | 218.0 | 0.001 | 1.31 MB |
| `checkout-get-only` | 47 | 34 | 4951.0 | 751.0 | 0.012 | 4.54 MB |

## `home-fem` (`/`)

- HTML GET medido: **473.9 KB** em **2524.2 ms** (HTTP 200)

### mobile (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 91 |
| FCP (ms) | 1231.0 |
| LCP (ms) | 2131.0 |
| TBT (ms) | 276.0 |
| CLS | 0.001 |
| Speed Index (ms) | 3999.2 |
| TTI (ms) | 7583.4 |
| INP (ms) | None |
| Total byte weight | 2.28 MB |

Oportunidades PSI (savings_ms):

- **Initial server response time was short** (`server-response-time`): 41.0 ms — Root document took 140 ms

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 116 KiB; savings 118.8 KB)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (6.4 s)

### desktop (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 99 |
| FCP (ms) | 329.0 |
| LCP (ms) | 446.0 |
| TBT (ms) | 104.0 |
| CLS | 0.001 |
| Speed Index (ms) | 1139.3 |
| TTI (ms) | 1819.6 |
| INP (ms) | None |
| Total byte weight | 3.50 MB |

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 116 KiB; savings 118.8 KB)
- `total-byte-weight` score=0.5 — Avoid enormous network payloads (Total size was 3,421 KiB)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (3.8 s)

## `home-masc` (`/masculino/`)

- HTML GET medido: **454.9 KB** em **1523.9 ms** (HTTP 200)

### mobile (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 54 |
| FCP (ms) | 1203.0 |
| LCP (ms) | 3303.0 |
| TBT (ms) | 4084.0 |
| CLS | 0.001 |
| Speed Index (ms) | 8759.5 |
| TTI (ms) | 16266.7 |
| INP (ms) | None |
| Total byte weight | 2.55 MB |

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 116 KiB; savings 118.9 KB)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (14.2 s)
- `bootup-time` score=0 — Reduce JavaScript execution time (1.9 s)

### desktop (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 90 |
| FCP (ms) | 341.0 |
| LCP (ms) | 1317.0 |
| TBT (ms) | 173.0 |
| CLS | 0.001 |
| Speed Index (ms) | 1499.8 |
| TTI (ms) | 2380.6 |
| INP (ms) | None |
| Total byte weight | 4.00 MB |

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 116 KiB; savings 118.3 KB)
- `total-byte-weight` score=0.5 — Avoid enormous network payloads (Total size was 3,910 KiB)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (3.6 s)

## `pdp-cera` (`/produto/axila-cera/`)

- HTML GET medido: **72.2 KB** em **1476.7 ms** (HTTP 200)

### mobile (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 96 |
| FCP (ms) | 1854.1 |
| LCP (ms) | 1876.1 |
| TBT (ms) | 140.5 |
| CLS | 0.001 |
| Speed Index (ms) | 2909.5 |
| TTI (ms) | 7209.5 |
| INP (ms) | None |
| Total byte weight | 1.07 MB |

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 116 KiB; savings 119.1 KB)

### desktop (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 95 |
| FCP (ms) | 297.5 |
| LCP (ms) | 1321.5 |
| TBT (ms) | 95.0 |
| CLS | 0.001 |
| Speed Index (ms) | 927.7 |
| TTI (ms) | 1769.2 |
| INP (ms) | None |
| Total byte weight | 2.54 MB |

Oportunidades PSI (savings_ms):

- **Reduce unused JavaScript** (`unused-javascript`): 120.0 ms — Est savings of 115 KiB

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 115 KiB; savings 117.6 KB; 120.0 ms)

## `pdp-laser` (`/produto/axilas-laser/`)

- HTML GET medido: **67.1 KB** em **1169.9 ms** (HTTP 200)

### mobile (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 96 |
| FCP (ms) | 937.6 |
| LCP (ms) | 2253.7 |
| TBT (ms) | 183.0 |
| CLS | 0.001 |
| Speed Index (ms) | 2153.0 |
| TTI (ms) | 7064.1 |
| INP (ms) | None |
| Total byte weight | 904.2 KB |

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 116 KiB; savings 118.6 KB)

### desktop (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 88 |
| FCP (ms) | 291.5 |
| LCP (ms) | 890.5 |
| TBT (ms) | 267.0 |
| CLS | 0.001 |
| Speed Index (ms) | 834.9 |
| TTI (ms) | 1937.1 |
| INP (ms) | None |
| Total byte weight | 2.31 MB |

Oportunidades PSI (savings_ms):

- **Reduce unused JavaScript** (`unused-javascript`): 40.0 ms — Est savings of 116 KiB

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 116 KiB; savings 119.1 KB; 40.0 ms)

## `carrinho` (`/carrinho/`)

- HTML GET medido: **43.7 KB** em **1584.5 ms** (HTTP 200)

### mobile (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 70 |
| FCP (ms) | 1694.4 |
| LCP (ms) | 7851.1 |
| TBT (ms) | 218.0 |
| CLS | 0.001 |
| Speed Index (ms) | 3609.0 |
| TTI (ms) | 7911.1 |
| INP (ms) | None |
| Total byte weight | 1.31 MB |

Oportunidades PSI (savings_ms):

- **Reduce unused JavaScript** (`unused-javascript`): 600.0 ms — Est savings of 116 KiB

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 116 KiB; savings 119.1 KB; 600.0 ms)

### desktop (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 71 |
| FCP (ms) | 493.6 |
| LCP (ms) | 2298.8 |
| TBT (ms) | 389.0 |
| CLS | 0.0 |
| Speed Index (ms) | 1122.4 |
| TTI (ms) | 2300.8 |
| INP (ms) | None |
| Total byte weight | 2.13 MB |

Oportunidades PSI (savings_ms):

- **Reduce unused JavaScript** (`unused-javascript`): 210.0 ms — Est savings of 116 KiB

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 116 KiB; savings 119.1 KB; 210.0 ms)

## `checkout-get-only` (`/finalizar-pagamento/`)

- HTML GET medido: **317.2 KB** em **1599.7 ms** (HTTP 200)

### mobile (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 47 |
| FCP (ms) | 3800.0 |
| LCP (ms) | 4951.0 |
| TBT (ms) | 751.0 |
| CLS | 0.012 |
| Speed Index (ms) | 9884.8 |
| TTI (ms) | 23837.3 |
| INP (ms) | None |
| Total byte weight | 4.54 MB |

Oportunidades PSI (savings_ms):

- **Reduce unused JavaScript** (`unused-javascript`): 600.0 ms — Est savings of 1,124 KiB
- **Reduce unused CSS** (`unused-css-rules`): 600.0 ms — Est savings of 117 KiB
- **Initial server response time was short** (`server-response-time`): 213.0 ms — Root document took 310 ms

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 1,124 KiB; savings 1.15 MB; 600.0 ms)
- `unused-css-rules` score=0 — Reduce unused CSS (Est savings of 117 KiB; savings 120.2 KB; 600.0 ms)
- `total-byte-weight` score=0.5 — Avoid enormous network payloads (Total size was 4,432 KiB)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (11.7 s)
- `bootup-time` score=0 — Reduce JavaScript execution time (3.1 s)

### desktop (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 34 |
| FCP (ms) | 794.0 |
| LCP (ms) | 1083.0 |
| TBT (ms) | 1856.5 |
| CLS | 1.437 |
| Speed Index (ms) | 4118.8 |
| TTI (ms) | 5092.3 |
| INP (ms) | None |
| Total byte weight | 4.53 MB |

Oportunidades PSI (savings_ms):

- **Reduce unused CSS** (`unused-css-rules`): 90.0 ms — Est savings of 117 KiB
- **Reduce unused JavaScript** (`unused-javascript`): 20.0 ms — Est savings of 1,122 KiB

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 1,122 KiB; savings 1.15 MB; 20.0 ms)
- `unused-css-rules` score=0 — Reduce unused CSS (Est savings of 117 KiB; savings 120.2 KB; 90.0 ms)
- `total-byte-weight` score=0.5 — Avoid enormous network payloads (Total size was 4,426 KiB)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (12.0 s)
- `bootup-time` score=0 — Reduce JavaScript execution time (4.4 s)

## Inventário de assets críticos (GET no oficialteste)

| Asset | Bytes | ms | Status | Cache-Control | Encoding |
|-------|------:|---:|-------:|---------------|----------|
| `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/home.js` | 24263 | 879.7 | 200 | `public, max-age=604800` | `` |
| `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/home.css` | 105470 | 1713.0 | 200 | `public, max-age=604800` | `` |
| `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/cart.js` | 38901 | 1287.7 | 200 | `public, max-age=604800` | `` |
| `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/product.js` | 30819 | 849.2 | 200 | `public, max-age=604800` | `` |
| `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/whatsapp-float.js` | 5294 | 770.2 | 200 | `public, max-age=604800` | `` |
| `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/checkout-shell-c24.js` | 65309 | 919.7 | 200 | `public, max-age=604800` | `` |
| `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/checkout-loading.js` | 8971 | 909.1 | 200 | `public, max-age=604800` | `` |
| `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/checkout-brand.css` | 36941 | 794.6 | 200 | `public, max-age=604800` | `` |
| `https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js` | 72927 | 297.8 | 200 | `public, max-age=31536000, s-maxage=31536000, immutable` | `` |
| `https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/ScrollTrigger.min.js` | 44575 | 196.5 | 200 | `public, max-age=31536000, s-maxage=31536000, immutable` | `` |

## Assets `pm-home` referenciados na home (GET medido)

- Contagem URLs distintas: **88**
- Soma dos bytes OK: **5.35 MB**

| Bytes | ms | URL |
|------:|---:|-----|
| 297794 | 1188.7 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/brand/logo-footer.png?v=2b277e2f` |
| 277405 | 1176.3 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/trust/ssl.png?v=4a4472f7` |
| 228463 | 1118.6 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/cartao-presente-80.jpg?v=5f135e34` |
| 129014 | 1318.5 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/hero/assinatura-female.jpg?v=963f8a14` |
| 120163 | 1359.1 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/hero/hero-campaign-center.jpg?v=ab0633d8` |
| 119078 | 1615.9 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/hero/hero-campaign-right.jpg?v=60f8f507` |
| 116154 | 1649.6 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/hero/splash-collection.jpg?v=7bda8b05` |
| 109583 | 1000.7 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/hero/hero-campaign-left.jpg?v=7fc3faa6` |
| 109235 | 987.5 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/hero/hero-campaign-low.jpg?v=7bfd2de0` |
| 105470 | 1487.6 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/home.css?v=premium6` |
| 87581 | 1317.8 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/hero/promo-laser-v5.jpg?v=9db4e790` |
| 75157 | 1170.4 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/hero/hero-campaign-right-m.jpg?v=91a24797` |
| 72301 | 2307.7 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/trust/cards.png?v=a29d1b4a` |
| 70110 | 1275.3 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/rosto-inteiro-laser.webp?v=002c2a9b` |
| 69010 | 858.1 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/orelhas-laser.webp?v=80e7626a` |
| 68870 | 973.9 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/queixo-linha.webp?v=2194b50b` |
| 68548 | 864.9 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/pescoco-laser.webp?v=3d46ad0f` |
| 67806 | 1310.2 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/queixo-laser.webp?v=5c896bf0` |
| 67664 | 918.7 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/hero/hero-campaign-center-m.jpg?v=d80fbd6e` |
| 67334 | 938.3 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-braco.webp?v=f9beb030` |
| 66859 | 1433.4 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/hero/hero-campaign-left-m.jpg?v=a5ae8398` |
| 66704 | 810.6 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/nariz-laser.webp?v=a59d2824` |
| 66402 | 818.2 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/nariz-cera.webp?v=67bb9c39` |
| 66176 | 829.2 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/buco-laser.webp?v=0642c53c` |
| 65476 | 1464.8 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/buco-linha.webp?v=46928791` |
| 64908 | 961.2 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/buco-cera.webp?v=6bfc10e6` |
| 64466 | 1303.0 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/queixo-cera.webp?v=481e2dcd` |
| 63710 | 1487.5 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/bracos-cera.webp?v=1aa33ad4` |
| 63404 | 833.8 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/bracos-laser.webp?v=e8f1e7ac` |
| 62878 | 886.6 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/antebraco-cera.webp?v=0e136d0e` |
| 62664 | 1019.5 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/sobrancelha-henna-simples.webp?v=251d6b10` |
| 62510 | 898.6 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/axila-cera.webp?v=1e7df20e` |
| 62148 | 1409.7 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/design-sobrancelha.webp?v=6592a8de` |
| 61102 | 1269.7 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-axilas.webp?v=5c8ac53c` |
| 58832 | 1116.3 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-meio-braco.webp?v=521572ad` |
| 58508 | 894.5 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/axilas-laser.webp?v=ef9d3b84` |
| 57826 | 1224.4 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/antebraco-laser.webp?v=ddceee15` |
| 51372 | 771.8 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/virilha-comum-faixa-cera.webp?v=c155e981` |
| 50886 | 1087.9 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-virilha-faixa.webp?v=0e06ea3a` |
| 50770 | 1373.0 | `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/media/images/hero/hero-campaign-low-m.jpg?v=81129309` |
| … | … | (+48 omitidos; ver JSON) |

## Black Friday — leitura só dos números acima

- Gargalos = linhas com pior LCP/TBT/score e oportunidades PSI com maior `savings_ms`.
- **Não tocar agora:** checkout CF7 #1831, Accesstage, `checkout-shell*.js`, fluxo de pagamento.
- Capacidade de host/CDN: ver runbook de migração (`historico/12-cronograma-loja-oficial.md`); este relatório não estima RPS do servidor.

## Remediações candidatas (NÃO aplicadas — aguardam GO)

Cada item abaixo só entra em execução se citado por PSI/inventário nesta baseline; nenhum foi aplicado neste passo.

1. JS não usado (PSI `unused-javascript`): auditar GSAP/ScrollTrigger/GTM na home — **sem** remover scripts de checkout.
2. HTML da home medido em 473.9 KB: avaliar redução de markup exportado (fora checkout).
3. Checkout GET medido score mobile mediana 47 / LCP 4951.0 ms — **somente observação**; remediação de checkout fora de escopo até GO explícito.
4. GSAP CDN medido 72.9 KB + ScrollTrigger 44.6 KB: carregar só onde animações existem (candidato; re-medir após).

## Artefatos

- JSON bruto: `projeto-migracao/.secrets/psi-loja/` (gitignored)
- Limpeza BD pós-migração: `historico/18-limpeza-bd-pos-migracao.md`

