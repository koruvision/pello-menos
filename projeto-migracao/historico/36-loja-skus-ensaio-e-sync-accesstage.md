# 36 — Loja: SKUs ensaio + snippet Accesstage sync

Data: 03/11/2026.

## Produtos criados na loja (hidden)

| Nome | SKU | Woo ID |
|---|---|---|
| PM Teste Esquenta Laser A | `pm-teste-esquenta-laser` | **49387** |
| PM Teste Esquenta Laser B | `pm-teste-esquenta-laser-b` | **49388** |
| PM Teste Esquenta Laser C | `pm-teste-esquenta-laser-c` | **49389** |
| PM Teste Esquenta Cera A | `pm-teste-esquenta-cera` | **49390** |
| PM Teste Esquenta Cera B | `pm-teste-esquenta-cera-b` | **49391** |
| PM Teste Esquenta Cera C | `pm-teste-esquenta-cera-c` | **49392** |

- Preço tabela: R$ 5,00  
- `catalog_visibility=hidden`, `status=publish`  
- Meta `_pm_catalog_id` = SKU  
- IDs: `scripts/_loja_esquenta_test_skus.json`

## Snippet na loja

- **#11** `pm-accesstage-order-total-sync` — **ativo**
- Código = `wordpress-loja/pm-home/pm-accesstage-order-total-sync.php`
- Alinha linhas + total do pedido Woo ao `totalamount` do CF7 #1831 após sucesso Accesstage

Também ativo: `#10` `pm-black-nov-pricing` (sem FORCE — calendário real; Esquenta a partir de 03/11).

## Atenção

Snippet `#6` `pm-ecommerce-maintenance` continua **ativo** na loja — front pode estar em manutenção. Para testar checkout no browser, desativar manutenção temporariamente.

## OficialTeste (referência)

Mesmos SKUs OT: 48498–48503; sync snippet #25; prova recibo completo pedido **#48514**.
