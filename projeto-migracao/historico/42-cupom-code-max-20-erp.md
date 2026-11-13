# 42 — Cupom `code` ≤ 20 (sync ERP)

Data: 05/11/2026.

## Problema

Pedidos syncados via WC REST levavam `coupon_lines[].code` com **52** caracteres, ex. no **#49516**:

`pm1l47sq9ahzu3wagdqgstesrte3tswladpyzysu8j3gus7u8uw5`

Sistemas internos da Pello Menos aceitam no máximo **20** caracteres nessa chave.

## Causa

Cupom de **teste interno** linha R$1 (`_pm_linha_1real`), gerado por `scripts/_create_linha_1real_coupon.py` com `PM1L` + 48 chars aleatórios. Não é `PRIMEIRACOMPRA5` nem o TID Accesstage.

## Correção

| Item | Valor |
|------|--------|
| Código novo | **`PM1LTEST01`** (10 chars) |
| Cupom Woo | id **49566** |
| Legado longo | **removido** (id 49506) |
| Guardrail | `woocommerce_before_coupon_object_save` no `pm-home`: trunca `code` > 20 no save |

## Para o time de sync

1. `coupon_lines[].code` → sempre ≤ 20 daqui pra frente (novos cupons).
2. Identificador de pagamento Accesstage: meta **`Pedido Accesstage`**, não o código do cupom.
3. Pedido **#49516**: status REST deve ser **`completed`** (pago). O dump com `processing` estava desatualizado / pré-regra. O `coupon_lines` histórico desse pedido ainda pode mostrar o código longo antigo (linha do pedido não é reescrita); cupons **novos** usam `PM1LTEST01`.

## Arquivos

- `scripts/_create_linha_1real_coupon.py` — `KEEP_CODE=PM1LTEST01`, `gen_code` ≤ 16 chars
- `scripts/pm_home_snippet.php` — guardrail
- `.secrets/linha-1real-coupon.json` — código curto
