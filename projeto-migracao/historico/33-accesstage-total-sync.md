# 33 — Accesstage: total Woo = totalamount (OT)

Data: 02/11/2026.

## Problema

`payment_CF7` (child theme) cobrava Accesstage com `totalamount`, mas criava o pedido Woo com preço de catálogo (`add_product` + `calculate_totals`). Ex.: #48504 linha/total **5.00** com Esquenta UI/hiddens **2.00**.

## Correção (só OficialTeste)

- Fonte: [`wordpress-loja/pm-home/pm-accesstage-order-total-sync.php`](../../wordpress-loja/pm-home/pm-accesstage-order-total-sync.php)
- Snippet Code Snippets **#25** `pm-accesstage-order-total-sync` ativo (`scope=global`, hook `wpcf7_before_send_mail` priority **20**)
- Publish: `python scripts/_publish_accesstage_total_sync.py`
- Após sucesso Accesstage: localiza pedido pelo email + meta `Pedido Accesstage` e força `set_total(totalamount)`; grava `_pm_cf7_totalamount`

## Restudo pré-publish

- Accesstage ainda em `shopwise-child/functions.php` (`totalamount*100` + `calculate_totals`)
- Snippet #6 shell `checkout-shell-c24.js?v=c37`; #24 `FORCE=esquenta`
- CF7 #1831 com hiddens `totalamount` / `fullvalue` / `unit`

## Testes

| Teste | Resultado |
|---|---|
| Smoke Store API (`_smoke_esquenta_test_skus.py`) | OK — 1 laser 200; 3 lasers 525; cera 425/1200 |
| UI/hiddens (`_debug_checkout_ui_price.py`) | OK — ui 200, `totalamount=2.00`, c37 |
| Charge Playwright (`_charge_esquenta_test_ot.py`) | OK — redirect `order-received/48507` |
| REST assert | **#48507** total **2.00**, `_pm_cf7_totalamount` **2.00**, meta Accesstage presente; linha ainda 5.00 (esperado — só grand total) |

SKU ensaio `pm-teste-esquenta-laser` (#48498) voltou a `draft` + `catalog_visibility=hidden` após o charge.

## Scripts auxiliares

- `scripts/_ot_test_skus_visibility.py` — publish/draft dos SKUs de ensaio
- `scripts/_assert_accesstage_order_total.py` — assert por email
- `scripts/_peek_order.py` — dump rápido de pedido

## Fora de escopo (ainda)

- Loja produção
- Alinhar preço de cada linha do pedido
- Desligar `FORCE=esquenta` no OT
