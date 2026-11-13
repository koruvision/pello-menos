# 17 — Baseline PageSpeed Insights (oficialteste)

- Gerado em: `20261028T154832Z` (UTC)
- Destino: `https://pellomenosoficialteste.companygenesis.com.br`
- Corridas por URL/estratégia: `3` (mediana); `checkout-get-only` ficou com `2` runs válidas (timeouts na 3ª)
- Fonte: Google PageSpeed Insights API v5 + GET medido dos assets
- Checkout: `/finalizar-pagamento/` medido só em GET; **zero alteração de código**
- Chave PSI: variável `PM_PAGESPEED_API_KEY` (não versionada)

## Resumo scores (mediana)

| Página | Mobile | Desktop | LCP mobile (ms) | TBT mobile (ms) | CLS mobile | Bytes total (PSI mobile) |
|--------|--------|---------|-----------------|-----------------|------------|--------------------------|
| `home-fem` | 60 | 95 | 8397.2 | 101.0 | 0.0 | 1.10 MB |
| `home-masc` | 89 | 95 | 3311.5 | 267.5 | 0.001 | 1.16 MB |
| `pdp-cera` | 87 | 98 | 3634.5 | 165.0 | 0.001 | 709.2 KB |
| `pdp-laser` | 80 | 81 | 3576.1 | 330.5 | 0.001 | 707.7 KB |
| `carrinho` | 89 | 96 | 1995.5 | 157.0 | 0.175 | 705.5 KB |
| `checkout-get-only` | 42 | 34 | 5415.0 | 1004.2 | 0.012 | 2.36 MB |

## `home-fem` (`/`)

- HTML GET medido: **487.5 KB** em **4581.3 ms** (HTTP 200)

### mobile (mediana de 3 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 60 |
| FCP (ms) | 5163.8 |
| LCP (ms) | 8397.2 |
| TBT (ms) | 101.0 |
| CLS | 0.0 |
| Speed Index (ms) | 6028.8 |
| TTI (ms) | 8464.7 |
| INP (ms) | None |
| Total byte weight | 1.10 MB |

Oportunidades PSI (savings_ms):

- **Reduce unused JavaScript** (`unused-javascript`): 600.0 ms — Est savings of 111 KiB
- **Minify CSS** (`unminified-css`): 150.0 ms — Est savings of 2 KiB
- **Initial server response time was short** (`server-response-time`): 78.0 ms — Root document took 180 ms

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 111 KiB; savings 114.1 KB; 600.0 ms)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (3.9 s)

### desktop (mediana de 3 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 95 |
| FCP (ms) | 345.5 |
| LCP (ms) | 768.0 |
| TBT (ms) | 159.0 |
| CLS | 0.001 |
| Speed Index (ms) | 1010.3 |
| TTI (ms) | 2008.3 |
| INP (ms) | None |
| Total byte weight | 2.03 MB |

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 112 KiB; savings 114.2 KB)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (3.8 s)

## `home-masc` (`/masculino/`)

- HTML GET medido: **465.3 KB** em **316.3 ms** (HTTP 200)

### mobile (mediana de 3 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 89 |
| FCP (ms) | 1370.0 |
| LCP (ms) | 3311.5 |
| TBT (ms) | 267.5 |
| CLS | 0.001 |
| Speed Index (ms) | 3462.8 |
| TTI (ms) | 7634.6 |
| INP (ms) | None |
| Total byte weight | 1.16 MB |

Oportunidades PSI (savings_ms):

- **Reduce unused JavaScript** (`unused-javascript`): 850.0 ms — Est savings of 111 KiB

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 111 KiB; savings 113.7 KB; 850.0 ms)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (5.8 s)

### desktop (mediana de 3 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 95 |
| FCP (ms) | 376.0 |
| LCP (ms) | 750.0 |
| TBT (ms) | 175.0 |
| CLS | 0.002 |
| Speed Index (ms) | 934.0 |
| TTI (ms) | 1991.5 |
| INP (ms) | None |
| Total byte weight | 2.40 MB |

Oportunidades PSI (savings_ms):

- **Initial server response time was short** (`server-response-time`): 43.0 ms — Root document took 140 ms
- **Minify CSS** (`unminified-css`): 40.0 ms — Est savings of 2 KiB

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 112 KiB; savings 114.3 KB)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (4.0 s)

## `pdp-cera` (`/produto/axila-cera/`)

- HTML GET medido: **72.8 KB** em **539.8 ms** (HTTP 200)

### mobile (mediana de 3 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 87 |
| FCP (ms) | 947.5 |
| LCP (ms) | 3634.5 |
| TBT (ms) | 165.0 |
| CLS | 0.001 |
| Speed Index (ms) | 2844.2 |
| TTI (ms) | 6991.0 |
| INP (ms) | None |
| Total byte weight | 709.2 KB |

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 111 KiB; savings 114.1 KB)

### desktop (mediana de 3 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 98 |
| FCP (ms) | 544.0 |
| LCP (ms) | 817.0 |
| TBT (ms) | 121.1 |
| CLS | 0.001 |
| Speed Index (ms) | 901.3 |
| TTI (ms) | 1901.4 |
| INP (ms) | None |
| Total byte weight | 992.9 KB |

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 111 KiB; savings 113.6 KB)

## `pdp-laser` (`/produto/axilas-laser/`)

- HTML GET medido: **67.8 KB** em **304.2 ms** (HTTP 200)

### mobile (mediana de 3 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 80 |
| FCP (ms) | 1888.1 |
| LCP (ms) | 3576.1 |
| TBT (ms) | 330.5 |
| CLS | 0.001 |
| Speed Index (ms) | 3096.1 |
| TTI (ms) | 7122.6 |
| INP (ms) | None |
| Total byte weight | 707.7 KB |

Oportunidades PSI (savings_ms):

- **Reduce unused JavaScript** (`unused-javascript`): 750.0 ms — Est savings of 112 KiB

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 112 KiB; savings 114.4 KB; 750.0 ms)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (2.1 s)

### desktop (mediana de 3 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 81 |
| FCP (ms) | 316.1 |
| LCP (ms) | 938.1 |
| TBT (ms) | 411.0 |
| CLS | 0.001 |
| Speed Index (ms) | 902.9 |
| TTI (ms) | 2097.6 |
| INP (ms) | None |
| Total byte weight | 955.3 KB |

Oportunidades PSI (savings_ms):

- **Reduce unused JavaScript** (`unused-javascript`): 40.0 ms — Est savings of 112 KiB

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 112 KiB; savings 114.3 KB; 40.0 ms)

## `carrinho` (`/carrinho/`)

- HTML GET medido: **43.9 KB** em **288.2 ms** (HTTP 200)

### mobile (mediana de 3 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 89 |
| FCP (ms) | 1710.5 |
| LCP (ms) | 1995.5 |
| TBT (ms) | 157.0 |
| CLS | 0.175 |
| Speed Index (ms) | 2498.4 |
| TTI (ms) | 6822.3 |
| INP (ms) | None |
| Total byte weight | 705.5 KB |

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 111 KiB; savings 114.0 KB)

### desktop (mediana de 3 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 96 |
| FCP (ms) | 487.8 |
| LCP (ms) | 763.8 |
| TBT (ms) | 156.5 |
| CLS | 0.01 |
| Speed Index (ms) | 637.9 |
| TTI (ms) | 1813.3 |
| INP (ms) | None |
| Total byte weight | 767.0 KB |

Oportunidades PSI (savings_ms):

- **Reduce unused JavaScript** (`unused-javascript`): 40.0 ms — Est savings of 111 KiB

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 111 KiB; savings 113.3 KB; 40.0 ms)

## `checkout-get-only` (`/finalizar-pagamento/`)

- HTML GET medido: **321.5 KB** em **553.1 ms** (HTTP 200)

### mobile (mediana de 2 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 42 |
| FCP (ms) | 4858.5 |
| LCP (ms) | 5415.0 |
| TBT (ms) | 1004.2 |
| CLS | 0.012 |
| Speed Index (ms) | 9351.1 |
| TTI (ms) | 18113.5 |
| INP (ms) | None |
| Total byte weight | 2.36 MB |

Oportunidades PSI (savings_ms):

- **Reduce unused JavaScript** (`unused-javascript`): 750.0 ms — Est savings of 563 KiB
- **Reduce unused CSS** (`unused-css-rules`): 600.0 ms — Est savings of 117 KiB
- **Minify CSS** (`unminified-css`): 150.0 ms — Est savings of 12 KiB
- **Initial server response time was short** (`server-response-time`): 54.0 ms — Root document took 150 ms

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 563 KiB; savings 576.5 KB; 750.0 ms)
- `unused-css-rules` score=0 — Reduce unused CSS (Est savings of 117 KiB; savings 120.2 KB; 600.0 ms)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (19.2 s)
- `bootup-time` score=0 — Reduce JavaScript execution time (3.5 s)

### desktop (mediana de 2 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 34 |
| FCP (ms) | 991.5 |
| LCP (ms) | 1067.5 |
| TBT (ms) | 1170.2 |
| CLS | 1.439 |
| Speed Index (ms) | 3913.9 |
| TTI (ms) | 4101.6 |
| INP (ms) | None |
| Total byte weight | 2.36 MB |

Oportunidades PSI (savings_ms):

- **Reduce unused CSS** (`unused-css-rules`): 100.0 ms — Est savings of 117 KiB
- **Reduce unused JavaScript** (`unused-javascript`): 80.0 ms — Est savings of 562 KiB
- **Initial server response time was short** (`server-response-time`): 48.0 ms — Root document took 150 ms

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 562 KiB; savings 575.9 KB; 80.0 ms)
- `unused-css-rules` score=0 — Reduce unused CSS (Est savings of 117 KiB; savings 120.2 KB; 100.0 ms)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (9.4 s)
- `bootup-time` score=0 — Reduce JavaScript execution time (2.5 s)

## Inventário de assets críticos (GET no oficialteste)

| Asset | Bytes | ms | Status | Cache-Control | Encoding |
|-------|------:|---:|-------:|---------------|----------|
| `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/home.js` | 23514 | 82.8 | 200 | `public, max-age=604800` | `` |
| `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/home.css` | 100097 | 328.4 | 200 | `public, max-age=604800` | `` |
| `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/cart.js` | 23702 | 253.0 | 200 | `public, max-age=604800` | `` |
| `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/product.js` | 22171 | 235.6 | 200 | `public, max-age=604800` | `` |
| `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/whatsapp-float.js` | 5081 | 53.8 | 200 | `public, max-age=604800` | `` |
| `https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js` | 72927 | 43.2 | 200 | `public, max-age=31536000, s-maxage=31536000, immutable` | `` |
| `https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/ScrollTrigger.min.js` | 44575 | 31.5 | 200 | `public, max-age=31536000, s-maxage=31536000, immutable` | `` |

## Assets `pm-home` referenciados na home (GET medido)

- Contagem URLs distintas: **99**
- Soma dos bytes OK: **64.36 MB**

| Bytes | ms | URL |
|------:|---:|-----|
| 1831436 | 789.2 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/hero/hero-campaign-center.png` |
| 1825876 | 370.2 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/hero/hero-campaign-right.png` |
| 1681806 | 833.2 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/hero/hero-campaign-low.png` |
| 1676653 | 358.6 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/hero/hero-campaign-left.png` |
| 1321418 | 145.3 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/social/cliente-1.png` |
| 1054511 | 276.0 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/orelhas-laser.png` |
| 958728 | 640.4 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/design-sobrancelha.png` |
| 923782 | 248.3 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/queixo-cera.png` |
| 916996 | 267.6 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/buco-cera.png` |
| 909198 | 241.1 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/rosto-inteiro-laser.png` |
| 907052 | 245.9 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/sobrancelha-cera.png` |
| 906778 | 257.8 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/design-sobrancelha-realce.png` |
| 902754 | 600.2 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/sobrancelha-realce-cera.png` |
| 901759 | 636.6 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/nariz-laser.png` |
| 892034 | 238.7 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/sobrancelha-henna-simples.png` |
| 874508 | 236.4 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/buco-linha.png` |
| 870876 | 625.2 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/buco-laser.png` |
| 869240 | 223.4 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/sobrancelha-henna.png` |
| 857545 | 1230.6 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/henna.png` |
| 854841 | 644.7 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/realce.png` |
| 850652 | 613.5 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/nariz-cera.png` |
| 836223 | 249.0 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/bracos-cera.png` |
| 835168 | 617.4 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/pescoco-laser.png` |
| 827129 | 613.7 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/queixo-laser.png` |
| 825942 | 608.6 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-braco.png` |
| 820012 | 238.6 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/costas-laser.png` |
| 818057 | 234.5 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/axilas-laser.png` |
| 815838 | 631.9 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/axila-cera.png` |
| 801900 | 614.2 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-axilas.png` |
| 800033 | 226.1 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-meio-braco.png` |
| 788329 | 612.2 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-costas.png` |
| 783809 | 261.4 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/bracos-laser.png` |
| 774335 | 623.1 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/costas-cera.png` |
| 770805 | 239.5 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/antebraco-laser.png` |
| 737059 | 234.3 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/nadegas-laser.png` |
| 731060 | 625.5 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/seios-cera.png` |
| 721885 | 217.8 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/areola-laser.png` |
| 721560 | 214.6 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-virilha-faixa.png` |
| 720982 | 620.4 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/antebraco-cera.png` |
| 710900 | 618.7 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/queixo-linha.png` |
| … | … | (+59 omitidos; ver JSON) |

## Black Friday — leitura só dos números acima

- Gargalos = linhas com pior LCP/TBT/score e oportunidades PSI com maior `savings_ms`.
- **Não tocar agora:** checkout CF7 #1831, Accesstage, `checkout-shell*.js`, fluxo de pagamento.
- Capacidade de host/CDN: ver runbook de migração (`historico/12-cronograma-loja-oficial.md`); este relatório não estima RPS do servidor.

## Remediações candidatas (NÃO aplicadas — aguardam GO)

Cada item abaixo só entra em execução se citado por PSI/inventário nesta baseline; nenhum foi aplicado neste passo.

1. JS não usado (PSI `unused-javascript`): auditar GSAP/ScrollTrigger/GTM na home — **sem** remover scripts de checkout.
2. HTML da home medido em 487.5 KB: avaliar redução de markup exportado (fora checkout).
3. Checkout GET medido score mobile mediana 42 / LCP 5415.0 ms — **somente observação**; remediação de checkout fora de escopo até GO explícito.
4. GSAP CDN medido 72.9 KB + ScrollTrigger 44.6 KB: carregar só onde animações existem (candidato; re-medir após).

## Artefatos

- JSON bruto: `projeto-migracao/.secrets/psi-oficialteste/` (gitignored)
- Limpeza BD pós-migração: `historico/18-limpeza-bd-pos-migracao.md`

