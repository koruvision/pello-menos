# 34 — Matriz promos Black Nov + cupom + charges mínimos (OT)

Data: 02/11/2026.

## Store API (`scripts/_matrix_ot_promos_coupon.py`) → MATRIX_OK

| Caso | Total (centavos) |
|---|---|
| Esquenta laser 60% | 200 |
| Esquenta laser multi 65% | 525 |
| Esquenta cera 15% | 425 |
| Esquenta cera multi 20% | 1200 |
| Esquenta laser + PRIMEIRACOMPRA5 | 190 (−10) |
| Black Week laser 70% | 150 |
| Black Week laser multi 75% | 375 |
| Black Week cera P 40% (tabela) | 1980 |
| Black Week cera M 30% (tabela) | 3493 |
| Black Week cera G 25% (tabela) | 6443 |
| Black Week esfoliação 15% (tabela) | 1403 |
| FORCE=off produto-r-1 | 199 |
| FORCE=off + PRIMEIRACOMPRA5 | 189 (−10) |
| FORCE=off laser teste full | 500 |

FORCE restaurado para `esquenta` ao fim.

## Charges Accesstage (valores baixos) → 5/5 OK

Snippet sync #25 validado em todos (`total` = `_pm_cf7_totalamount`).

| Caso | Pedido | Total Woo / cobrado |
|---|---|---|
| Normal produto R$1,99 | **#48512** | 1.99 |
| Normal + PRIMEIRACOMPRA5 | **#48508** | 1.89 |
| Esquenta laser | **#48509** | 2.00 |
| Black Week laser | **#48510** | 1.50 |
| Esquenta laser + cupom | **#48511** | 1.90 |

Notas:

- 1ª tentativa do caso `normal` falhou em redirect (`finalizar-pagamento/undefined`); retry OK (#48512).
- Linhas Woo de SKUs teste podem continuar a R$5; grand total alinhado ao charge.
- SKU laser ensaio voltou a `draft` + hidden.
- Cupom `PRIMEIRACOMPRA5` (id 48397) 5%, 1× por usuário — cada charge usou e-mail novo.

## Scripts

- `scripts/_matrix_ot_promos_coupon.py`
- `scripts/_charge_ot_matrix_min.py`
- `scripts/_charge_ot_normal_retry.py`
