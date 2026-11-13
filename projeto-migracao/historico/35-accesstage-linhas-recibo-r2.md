# 35 — Recibo completo alinhado ao cartão (linhas + total)

Data: 02/11/2026. Escopo: OficialTeste.

## O que mudou

Snippet **#25** `pm-accesstage-order-total-sync` agora, após o Accesstage:

1. Redistribui o `totalamount` nas **linhas** (`subtotal`/`total` de cada item)
2. Zera desconto/shipping/tax auxiliares no recibo
3. `set_total(totalamount)`
4. Metas: `_pm_cf7_totalamount`, `_pm_accesstage_lines_synced=1`, `_pm_accesstage_amount_cents`
5. Nota no pedido com o valor sincronizado

Fonte: `wordpress-loja/pm-home/pm-accesstage-order-total-sync.php`

## Prova (charge R$ 2,00 Esquenta)

Pedido **#48514**

| Campo | Valor |
|---|---|
| Linha PM Teste Esquenta Laser A | **2.00** / **2.00** |
| Total Woo | **2.00** |
| `_pm_cf7_totalamount` | **2.00** |
| `_pm_accesstage_amount_cents` | **200** |
| `_pm_accesstage_lines_synced` | **1** |
| `Pedido Accesstage` | 17936613725299 |
| Unidade | largobicao |
| discount_total | 0.00 |

Antes (#48509): linha 5.00 / total 2.00.  
Agora (#48514): linha 2.00 / total 2.00 — mesmo valor enviado à Accesstage.

Amanhã: conferir débito ~R$ 2,00 no extrato do cartão de ensaio.
