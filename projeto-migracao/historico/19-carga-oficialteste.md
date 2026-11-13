# 19 — Carga oficialteste (GET-only)

- Gerado em: `20261028T172126Z` (UTC)
- Destino: `https://pellomenosoficialteste.companygenesis.com.br`
- Método: GET concorrente (http.client + ThreadPoolExecutor, **somente IPv4**); **sem POST** checkout/pagamento
- Alvos: `/`, `/masculino/`, 2 PDPs, `/carrinho/`, `home.css`/`home.js`; `/finalizar-pagamento/` só no warm-up leve
- Nota: resolução AAAA/IPv6 neste host devolveu `TLSV1_ALERT_INTERNAL_ERROR` e inflava erro; teste força IPv4 + SNI.

## Resultados por degrau

| Degrau | Workers | Reqs | OK | Err% | RPS | p50 ms | p95 ms | p95 HTML ms |
|--------|---------|------|----|------|-----|--------|--------|-------------|
| `warmup` | 5 | 541 | 541 | 0.0 | 18.03 | 176.4 | 660.5 | 689.0 |
| `vu20` | 20 | 3652 | 3652 | 0.0 | 30.43 | 529.9 | 1265.4 | 1334.1 |
| `vu50` | 50 | 3336 | 3336 | 0.0 | 27.8 | 1288.4 | 3773.0 | 4061.8 |
| `vu100` | 100 | 1148 | 1148 | 0.0 | 9.57 | 6859.0 | 22521.8 | 23201.8 |

## Critérios de abort
- Erro > 5% ou p95 HTML > 8000 ms → abort
- **Abortado:** vu100: p95_html 23201.8 ms > 8000

## Notas

- Números medidos só neste ambiente (oficialteste). Não inferir capacidade da loja oficial.
- Checkout/pagamento: fora do stress (apenas GET leve no warm-up, baixa concorrência).
