# 20 — PSI pós-otimização (oficialteste)

- Gerado em: `20261028T172425Z` (UTC)
- Destino: `https://pellomenosoficialteste.companygenesis.com.br`
- Corridas: `1` run **mobile** em `home-fem` + `carrinho` (plano: remedir após otimização)
- Baseline: `historico/17-psi-oficialteste-baseline.md`
- Checkout: **intocado**
- Chave PSI: variável `PM_PAGESPEED_API_KEY` (não versionada)

## Delta vs baseline (17)

| Página | Score mobile baseline → pós | Δ | LCP mobile baseline → pós | Δ LCP |
|--------|-----------------------------:|---|---------------------------:|------:|
| `home-fem` | 60 → **95** | **+35** | 8397 → **1445** ms | **−6953 ms** |
| `carrinho` | 89 → **85** | −4 | 1996 → **2831** ms | +835 ms |

- Home: salto forte (heróis JPEG ~100 KB, ScrollTrigger adiado, purge/compress). TBT mobile 101 → 226 ms (trade-off menor vs LCP).
- Carrinho: variação de uma corrida; score ainda alto; CLS ~0.18 igual ao baseline.
- Unused JS (~112 KiB) ainda aparece (GSAP core no path crítico); ScrollTrigger segue no inventário CDN mas deixa de bloquear first paint no `home.js`.

## Resumo scores (pós)

| Página | Mobile | Desktop | LCP mobile (ms) | TBT mobile (ms) | CLS mobile | Bytes total (PSI mobile) |
|--------|--------|---------|-----------------|-----------------|------------|--------------------------|
| `home-fem` | 95 | — | 1444.5 | 226.0 | 0.001 | 1.00 MB |
| `carrinho` | 85 | — | 2830.7 | 135.5 | 0.176 | 705.0 KB |

## `home-fem` (`/`)

- HTML GET medido: **489.4 KB** em **363.5 ms** (HTTP 200)

### mobile (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 95 |
| FCP (ms) | 1219.5 |
| LCP (ms) | 1444.5 |
| TBT (ms) | 226.0 |
| CLS | 0.001 |
| Speed Index (ms) | 3663.2 |
| TTI (ms) | 7576.3 |
| INP (ms) | None |
| Total byte weight | 1.00 MB |

Oportunidades PSI (savings_ms):

- **Initial server response time was short** (`server-response-time`): 108.0 ms — Root document took 210 ms

Diagnósticos com score < 1:

- `unused-javascript` score=0.5 — Reduce unused JavaScript (Est savings of 112 KiB; savings 114.5 KB)
- `mainthread-work-breakdown` score=0 — Minimize main-thread work (5.3 s)

### desktop: sem dados

## `carrinho` (`/carrinho/`)

- HTML GET medido: **43.9 KB** em **129.8 ms** (HTTP 200)

### mobile (mediana de 1 run(s))

| Métrica | Valor |
|---------|-------|
| Performance score | 85 |
| FCP (ms) | 1707.7 |
| LCP (ms) | 2830.7 |
| TBT (ms) | 135.5 |
| CLS | 0.176 |
| Speed Index (ms) | 2705.8 |
| TTI (ms) | 6741.2 |
| INP (ms) | None |
| Total byte weight | 705.0 KB |

Oportunidades PSI (savings_ms):

- **Reduce unused JavaScript** (`unused-javascript`): 300.0 ms — Est savings of 112 KiB

Diagnósticos com score < 1:

- `unused-javascript` score=0 — Reduce unused JavaScript (Est savings of 112 KiB; savings 114.2 KB; 300.0 ms)

### desktop: sem dados

## Inventário de assets críticos (GET no oficialteste)

| Asset | Bytes | ms | Status | Cache-Control | Encoding |
|-------|------:|---:|-------:|---------------|----------|
| `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/home.js` | 23514 | 148.3 | 200 | `public, max-age=604800` | `` |
| `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/home.css` | 100097 | 139.8 | 200 | `public, max-age=604800` | `` |
| `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/cart.js` | 23702 | 182.6 | 200 | `public, max-age=604800` | `` |
| `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/product.js` | 22171 | 129.7 | 200 | `public, max-age=604800` | `` |
| `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/whatsapp-float.js` | 5081 | 120.6 | 200 | `public, max-age=604800` | `` |
| `https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js` | 72927 | 203.7 | 200 | `public, max-age=31536000, s-maxage=31536000, immutable` | `` |
| `https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/ScrollTrigger.min.js` | 44575 | 179.8 | 200 | `public, max-age=31536000, s-maxage=31536000, immutable` | `` |

## Assets `pm-home` referenciados na home (GET medido)

- Contagem URLs distintas: **100**
- Soma dos bytes OK: **45.11 MB**

| Bytes | ms | URL |
|------:|---:|-----|
| 1321418 | 379.8 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/social/cliente-1.png` |
| 836223 | 325.4 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/bracos-cera.png` |
| 835168 | 385.3 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/pescoco-laser.png` |
| 827129 | 323.8 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/queixo-laser.png` |
| 825942 | 298.6 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-braco.png` |
| 820012 | 378.1 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/costas-laser.png` |
| 818057 | 211.7 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/axilas-laser.png` |
| 815838 | 356.2 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/axila-cera.png` |
| 801900 | 217.5 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-axilas.png` |
| 800033 | 354.5 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-meio-braco.png` |
| 788329 | 293.4 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-costas.png` |
| 783809 | 294.5 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/bracos-laser.png` |
| 774335 | 397.7 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/costas-cera.png` |
| 770805 | 343.4 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/antebraco-laser.png` |
| 737059 | 339.5 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/nadegas-laser.png` |
| 731060 | 210.6 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/seios-cera.png` |
| 721885 | 333.7 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/areola-laser.png` |
| 721560 | 302.9 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-virilha-faixa.png` |
| 720982 | 284.7 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/antebraco-cera.png` |
| 710900 | 176.7 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/queixo-linha.png` |
| 709368 | 244.0 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/virilha-cavada-faixa-laser.png` |
| 694401 | 385.1 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/abdomen-laser.png` |
| 693569 | 363.1 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/meia-nadega-cera.png` |
| 686407 | 197.7 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-abdomen.png` |
| 667325 | 290.4 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/psd-m-laser.png` |
| 660824 | 223.0 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-faixa.png` |
| 657609 | 252.4 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/meia-nadega-laser.png` |
| 654154 | 230.5 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/esfoliacao-meia-nadega.png` |
| 644835 | 329.7 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/psd-g-laser.png` |
| 642242 | 366.6 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/meia-perna-laser.png` |
| 641702 | 316.5 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/virilha-laser.png` |
| 640860 | 335.2 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/intergluteos-laser.png` |
| 629435 | 208.5 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/psd-p-laser.png` |
| 628175 | 258.1 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/abdomen-cera.png` |
| 625462 | 373.8 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/virilha-faixa-laser.png` |
| 624792 | 325.2 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/intergluteos-cera.png` |
| 623125 | 317.3 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/virilha-cavada-cera.png` |
| 622671 | 177.6 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/virilha-comum-laser.png` |
| 622094 | 344.3 | `https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/pm-home/media/images/products/virilha-cavada-laser.png` |
| … | … | (+60 omitidos; ver JSON) |

## Black Friday — leitura só dos números acima

- Gargalos = linhas com pior LCP/TBT/score e oportunidades PSI com maior `savings_ms`.
- **Não tocar agora:** checkout CF7 #1831, Accesstage, `checkout-shell*.js`, fluxo de pagamento.
- Capacidade de host/CDN: ver runbook de migração (`historico/12-cronograma-loja-oficial.md`); este relatório não estima RPS do servidor.

## Remediações candidatas (NÃO aplicadas — aguardam GO)

Cada item abaixo só entra em execução se citado por PSI/inventário nesta baseline; nenhum foi aplicado neste passo.

1. JS não usado (PSI `unused-javascript`): auditar GSAP/ScrollTrigger/GTM na home — **sem** remover scripts de checkout.
2. HTML da home medido em 489.4 KB: avaliar redução de markup exportado (fora checkout).
3. GSAP CDN medido 72.9 KB + ScrollTrigger 44.6 KB: carregar só onde animações existem (candidato; re-medir após).

## Artefatos

- JSON bruto: `projeto-migracao/.secrets/psi-oficialteste/` (gitignored)
- Limpeza BD pós-migração: `historico/18-limpeza-bd-pos-migracao.md`

