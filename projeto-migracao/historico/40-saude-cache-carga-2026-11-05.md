# 40 — Saúde cache/carga + melhorias (05/11/2026 noite)

Implementação do roadmap da análise 03–05/11.

## 1. Demanda 03–05/11 (Woo)

| Dia | Pedidos |
|-----|--------:|
| 03/11 | 19 |
| 04/11 | 18 |
| 05/11 | 24 |
| Média | **~20,3/dia** |

Pico ~**6/h** → ~2,5 concurrent GET (proxy). **Saudável** vs capacidade vu20.

## 2. Cache seletivo (aplicado)

| Rota | Cache-Control |
|------|---------------|
| `/`, `/masculino/`, PDP | `public, max-age=300, s-maxage=600` + `Vary: Cookie` |
| `/carrinho/`, `/minha-conta/` | `private, no-store` |
| Estáticos `pm-home` | `max-age=604800` (inalterado) |

Snippet `pm-home` republished. Probe confirmou headers acima.

### Audit v2 (2 GETs)

- Headers `Age` / `X-LiteSpeed-Cache` **não** aparecem neste cliente (Server: LiteSpeed).
- Conclusão: política de Cache-Control correta; taxa HIT CDN não observável daqui — OK operacional via TTL.

Artefato: `scripts/_audit_loja_cache_headers_v2.json`.

## 3. GSAP sob demanda (PSI P1)

- Removido `wp_enqueue_script('pm-gsap')` do boot do checkout.
- `checkout-loading.js?v=load6` carrega GSAP no `open()` (clique Finalizar).
- Shell `c44`. Overlay continua sem GSAP se o script falhar.

## 4. Re-carga GET (pós-cache)

Ver [`41-carga-loja-pos-cache-2026-11-05.md`](41-carga-loja-pos-cache-2026-11-05.md).

| Ensaio | vu20 p95 HTML | vu50 p95 HTML | vu100 |
|--------|--------------:|--------------:|-------|
| 31/10 | ~1,9 s | ~3,4 s | ~7,6 s (pass) |
| 05/11 tarde | ~2,8 s | **9,2 s abort** | — |
| **05/11 noite (pós-TTL)** | ~3,0 s | **~7,2 s pass** | **14,5 s abort** |

- vu50 **voltou a passar** o critério 8 s (melhor que a tarde).
- RPS ainda flat (~10–14); host satura perto de 50–100.
- Demanda 03–05 (~2,5 concurrent) continua **folgada** em vu20.

## 5. Saúde por área (pós-fix)

| Área | Saúde | Nota |
|------|-------|------|
| Demanda 03–05 | OK | ~20 ped/dia; folga vs vu20 |
| Cache vitrine | OK+ | TTL ↑ 2,5× |
| Cache carrinho/conta | OK | private sempre |
| Capacidade host | Amarela | vu50 OK de novo; vu100 lento |
| Checkout first paint | Melhor | −73 KB GSAP no boot |
| GA4 | Gap | proxy Woo permanece |

**Veredito:** tráfego atual saudável; cache/GSAP aplicados; host ainda é o teto para BF (monitorar vu50).
