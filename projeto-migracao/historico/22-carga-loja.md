# Carga loja (GET-only)

- Gerado em: `20261031T011736Z` (UTC)
- Destino: `https://loja.pellomenos.com.br`
- Método: GET concorrente (http.client + ThreadPoolExecutor, **somente IPv4**); **sem POST** checkout/pagamento
- Alvos: `/`, `/masculino/`, 2 PDPs, `/carrinho/`, `home.css`/`home.js`; `/finalizar-pagamento/` só no warm-up leve
- Nota: resolução AAAA/IPv6 neste host devolveu `TLSV1_ALERT_INTERNAL_ERROR` e inflava erro; teste força IPv4 + SNI.

## Resultados por degrau

| Degrau | Workers | Reqs | OK | Err% | RPS | p50 ms | p95 ms | p95 HTML ms |
|--------|---------|------|----|------|-----|--------|--------|-------------|
| `warmup` | 5 | 100 | 100 | 0.0 | 3.33 | 1356.1 | 2144.5 | 3102.2 |
| `vu20` | 20 | 716 | 716 | 0.0 | 15.91 | 1159.3 | 1787.6 | 1854.2 |
| `vu50` | 50 | 1050 | 1043 | 0.67 | 23.33 | 2476.0 | 3251.8 | 3362.1 |
| `vu100` | 100 | 1081 | 1045 | 3.33 | 24.02 | 5096.1 | 7386.0 | 7607.8 |

## Critérios de abort
- Erro > 5% ou p95 HTML > 8000 ms → abort
- Não abortado; bateria completa.
- **Capacidade observada:** até `vu100` (100 workers) sem estouro dos critérios.

## Notas

- Checkout/pagamento: fora do stress (apenas GET leve no warm-up, baixa concorrência).
- Não inclui sessão Woo autenticada nem Store API write.
