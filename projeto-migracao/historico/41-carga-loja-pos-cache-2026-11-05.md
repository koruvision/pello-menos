# Carga loja (GET-only)

- Gerado em: `20261105T214807Z` (UTC)
- Destino: `https://loja.pellomenos.com.br`
- Método: GET concorrente (http.client + ThreadPoolExecutor, **somente IPv4**); **sem POST** checkout/pagamento
- Alvos: `/`, `/masculino/`, 2 PDPs, `/carrinho/`, `home.css`/`home.js`; `/finalizar-pagamento/` só no warm-up leve
- Nota: resolução AAAA/IPv6 neste host devolveu `TLSV1_ALERT_INTERNAL_ERROR` e inflava erro; teste força IPv4 + SNI.

## Resultados por degrau

| Degrau | Workers | Reqs | OK | Err% | RPS | p50 ms | p95 ms | p95 HTML ms |
|--------|---------|------|----|------|-----|--------|--------|-------------|
| `warmup` | 5 | 116 | 116 | 0.0 | 3.87 | 1240.5 | 1673.5 | 1782.3 |
| `vu20` | 20 | 475 | 475 | 0.0 | 10.56 | 1668.8 | 2971.2 | 3039.3 |
| `vu50` | 50 | 630 | 630 | 0.0 | 14.0 | 2717.7 | 6697.4 | 7195.7 |
| `vu100` | 100 | 540 | 540 | 0.0 | 12.0 | 5095.6 | 13453.6 | 14536.5 |

## Critérios de abort
- Erro > 5% ou p95 HTML > 8000 ms → abort
- **Abortado:** vu100: p95_html 14536.5 ms > 8000
- **Capacidade segura (último estável):** `vu50` (50 workers, p95 HTML 7195.7 ms, err 0.0%)

## Notas

- Checkout/pagamento: fora do stress (apenas GET leve no warm-up, baixa concorrência).
- Não inclui sessão Woo autenticada nem Store API write.
