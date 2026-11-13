# 37 — Loja: matriz Esquenta + charges Accesstage (produção)

Data: 2026-11-03  
Escopo: só `loja.pellomenos.com.br` (sem FORCE de fase).

## Preparação

- Snippet `#6` `pm-ecommerce-maintenance` desligado só durante a bateria; **reativado no fim**.
- Plugin `wpcf7-recaptcha/wpcf7-recaptcha` **inativado** durante charges (snippet #12 sozinho não bastava); **reativado no fim**.
- `#10` Black Nov + `#11` Accesstage sync ativos.
- SKUs ensaio 49387–49392 `publish` + `hidden` (permanecem).
- Cupom `PRIMEIRACOMPRA5` criado (#49393); produto barato `#49394` (`produto-r-1`, meta `_pm_catalog_id=produto-1-real` para excluir da campanha).

## Store API (calendário Esquenta)

| Caso | Total (centavos) | OK |
|------|------------------|----|
| laser 60% | 200 | sim |
| laser multi 65% | 525 | sim |
| cera 15% | 425 | sim |
| cera multi 20% | 1200 | sim |
| laser + PRIMEIRACOMPRA5 | 190 | sim |
| normal `#49394` | 199 | sim |
| normal + cupom | 189 | sim |

Artefato: `scripts/_matrix_loja_promos_coupon_result.json`.

## UI / hiddens

Checkout seed laser → `totalamount=2.00` / `fullvalue=2.00`, fase `esquenta`.  
Nota: `__pmCheckoutUiTotalCents` pode ficar 500 (catálogo/localStorage) enquanto Woo pinta 2.00; Accesstage usa `totalamount`. Nos charges o script força parity UI↔Woo para o shell não bloquear submit.

## Charges Accesstage (linha + total + metas)

| Pedido | Caso | Total | Linha | Accesstage | `_pm_cf7_totalamount` | `_pm_accesstage_lines_synced` |
|--------|------|-------|-------|------------|------------------------|-------------------------------|
| **49401** | Esquenta laser | 2.00 | 2.00 | 17936718175299 | 2.00 | 1 |
| **49402** | Esquenta + cupom | 1.90 | 1.90 | 17936721095299 | 1.90 | 1 |
| **49403** | Normal R$1,99 | 1.99 | 1.99 | 17936723345299 | 1.99 | 1 |
| **49407** | Normal + cupom | 1.89 | 1.89 | 17936727745299 | 1.89 | 1 |

Black Week FORCE: **não** rodado (default do plano).

## Encerramento

- `#6` manutenção **ativa**.
- Snippet #12 reCAPTCHA-off **inativo**.
- Plugin `wpcf7-recaptcha` **ativo**.
- SKUs 49387–49392 / 49394 permanecem `hidden` para reteste manual.

## Scripts

- `scripts/_loja_test_prep.py` — open/restore (manutenção + recaptcha plugin)
- `scripts/_matrix_loja_promos_coupon.py`
- `scripts/_debug_loja_checkout_ui.py`
- `scripts/_charge_loja_one.py` / `_charge_loja_matrix_min.py`
- `scripts/_peek_loja_order.py`
