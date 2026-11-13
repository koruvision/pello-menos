# 24 — Desempenho loja: PSI + carga (30–31/10/2026)

Ensaio autorizado na **loja** com DEV LOCK desligado só durante as medições e **reativado** ao fim. Sem POST de pagamento / Accesstage / CF7.

Artefatos:

- PSI: [`23-psi-loja-baseline.md`](23-psi-loja-baseline.md) + JSON em `.secrets/psi-loja/`
- Carga: [`22-carga-loja.md`](22-carga-loja.md)

---

## 1. Capacidade sob carga (GET-only)

| Degrau | Workers | Err% | RPS | p50 ms | p95 HTML ms |
|--------|---------|------|-----|--------|-------------|
| warmup | 5 | 0 | 3.3 | 1356 | 3102 |
| vu20 | 20 | 0 | 15.9 | 1159 | **1854** |
| vu50 | 50 | 0.67 | 23.3 | 2476 | **3362** |
| vu100 | 100 | 3.33 | 24.0 | 5096 | **7608** |

- Critérios de abort (erro >5% ou p95 HTML >8s): **não dispararam** até 100 workers.
- Na prática o host **segura 100**, mas a latência sobe forte: p50 ~5,1s e p95 HTML ~7,6s em vu100; RPS quase não cresce de 50→100 (~23→24) → **saturação**.
- **Capacidade confortável sugerida:** operar mentalmente em torno de **20–50** sessões GET concorrentes neste perfil; acima disso a loja “não cai”, mas fica lenta.

Checkout/pagamento **não** entrou no stress (só GET leve no warm-up).

---

## 2. PageSpeed (mobile) — o que dói

| Página | Score | LCP | TBT | Peso PSI |
|--------|------:|----:|----:|---------:|
| home-fem | **91** | 2,1s | 276ms | 2,3 MB |
| home-masc | **54** | 3,3s | **4,1s** | 2,6 MB |
| PDP cera/laser | **96** | ~1,9–2,3s | ~140–180ms | ~0,9–1,1 MB |
| carrinho | **70** | **7,9s** | 218ms | 1,3 MB |
| finalizar-pagamento | **47** | 5,0s | 751ms | **4,5 MB** |

Piores pontos:

1. **Checkout GET** — score baixo, ~**1,1 MB JS não usado** + CSS não usado (~117 KiB). Quase tudo é **tema Shopwise / Elementor / plugins**, não o overlay (~9 KB) nem o shell (~65 KB). GSAP no checkout (~73 KB) entra no path crítico sem necessidade até o clique.
2. **Home masculina** — TBT altíssimo (main-thread ~14s no diagnóstico); mesmo padrão de unused JS (~116 KiB) da feminina, mas impacto bem pior.
3. **Carrinho** — LCP mobile ~7,9s (uma corrida; investigar imagem/hero/fonte no path LCP).
4. **Home feminina** — já saudável (91); manter.

HTML “frio” medido no ensaio: home ~474 KB / ~2,5s TTFB+download; checkout HTML ~317 KB / ~1,6s.

---

## 3. Overlay de carregamento vs PSI

| Peça | Peso GET | Papel |
|------|----------|--------|
| `checkout-loading.js` | ~9 KB | overlay (leve) |
| `checkout-shell-c24.js` | ~65 KB | chrome + sync |
| `checkout-brand.css` | ~37 KB | UI checkout |
| GSAP core (CDN) | ~73 KB | animação overlay |
| Tema + CF7 + resto | **maioria dos 4,5 MB** | Shopwise/plugins |

Conclusão: o overlay **não** é o vilão do score do checkout. O ganho barato e seguro no nosso código:

1. **Não enfileirar GSAP no boot do checkout** — carregar no 1º clique (overlay já funciona sem GSAP).
2. Garantir que **ScrollTrigger não** entre no `/finalizar-pagamento/` (hoje o inventário crítico lista o arquivo CDN; no snippet só o core).
3. **Não** “limpar” JS do tema às cegas (quebra CF7/máscaras/reCAPTCHA).

---

## 4. Prioridade de otimização (evidência → ação)

| Pri | Ação | Risco | Espera |
|-----|------|-------|--------|
| P1 | GSAP do checkout sob demanda (só no clique Finalizar) | baixo | −73 KB no first paint; TBT/LCP checkout |
| P2 | Investigar LCP do `/carrinho/` (imagem/fonte LCP) | médio | score carrinho |
| P3 | Auditar JS da home masculina (por que TBT explode vs feminina) | médio | score 54→? |
| P4 | Unused CSS/JS do **tema** no checkout | alto se “limpar” | só com inventário fino / GO |
| P5 | CDN/cache já longos em `pm-home` estáticos — OK; HTML dinâmico continua lento sob carga | — | capacidade = host |

**Não mexer:** CF7 #1831, Accesstage, POST pagamento, cupom/totais, DEV LOCK (fica **ligado** após o ensaio).

---

## 5. Operação do ensaio

1. `pm-dev-lock` id 9 → `active: false`
2. PSI 1 run mobile+desktop (6 URLs)
3. Carga warmup→vu100 GET-only
4. `pm-dev-lock` → `active: true` (confirmado: `/` e checkout redirecionam para login)

Scripts atualizados: `pm_psi_audit.py` e `pm_load_test.py` aceitam `--prefix PM_LOJA --permitir-loja`.
