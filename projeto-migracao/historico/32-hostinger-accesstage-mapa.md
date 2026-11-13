# 32 — Hostinger API + mapa Accesstage (OficialTeste)

Data: 02/11/2026. Fontes: Hostinger Files API (`hostinger-ot.env`) + WP REST OT (`oficialteste.env`).

## Hostinger

- Token API OK na conta `u956483026` / domínio `pellomenosoficialteste.companygenesis.com.br`.
- Child theme `shopwise-child` só tem `functions.php` + `style.css` + screenshot.
- **Não existe plugin Accesstage** (44 pastas em `wp-content/plugins`; nenhum nome de gateway Accesstage/Rede).
- Accesstage está **hardcoded** em `wp-content/themes/shopwise-child/functions.php` (`payment_CF7` no hook `wpcf7_before_send_mail`, form CF7 **#1831**).
- Dump local com chaves de API/unidade: `scripts/_hostinger_ot_dumps/` (**gitignore**; não versionar).

## Fluxo de cobrança (o que importa)

1. Shell preenche hiddens CF7 (`totalamount`, `fullvalue`, `cart`, …).
2. Accesstage cobra: `amount = floatval(posted_data['totalamount']) * 100` (centavos) → Rede via `accesstage.net.br/access-pay/transactions?gateway=REDE`.
3. **Só depois** do sucesso cria o pedido Woo: `wc_create_order()` + `add_product(get_product(id))` + `calculate_totals()`.
4. Meta gravada: `Pedido Accesstage`, `Unidade`, `CPF`, `Modalidade`, `Cartão`.

### Consequência Esquenta / Black Nov

| Camada | Fonte do preço | Estado OT |
|---|---|---|
| UI + hiddens CF7 `totalamount` | shell `checkout-shell-c24.js?v=c37` + `pmBlackNov` / `campaignPriceForWooId` | alinhado (smoke R$2 em SKU R$5) |
| Charge Accesstage | **só** `totalamount` do CF7 | segue o shell se o submit passar no guard |
| Pedido Woo (linhas/total) | preço de catálogo do produto no `add_product` | **não** reusa `set_price` do carrinho nem `totalamount` |

Isto explica o pedido **#48504**: linha Woo **5.00** (tabela do SKU teste) mesmo com Store API/hiddens Esquenta a **2.00**. O total Woo pós-Accesstage **não prova** o valor cobrado no cartão — o cartão usa `totalamount`.

## Estado live OT (restudo)

- Snippet **#6** `pm-home`: ativo; enfileira `checkout-shell-c24.js?v=c37`; propaga `__PM_BLACK_PHASE__` se `PM_BLACK_NOV_FORCE`.
- Snippet **#24** `pm-black-nov-pricing`: ativo; `set_price` + `pm_catalog`; `define('PM_BLACK_NOV_FORCE', 'esquenta')` ainda ativo (smoke OT).
- CF7 **#1831**: tem `totalamount`, `fullvalue`, `cart`, `cartqtd`, `cupom`, `unit`, `easyunit`, `cart-number`, `securityCode`.
- `black-nov-campaign.json` no disco OT: `blackWeekStart` **2026-11-23**; taxas Esquenta laser 60/65, cera+esf 15/20.
- Shell em disco OT aponta `base` para `loja.pellomenos.com.br/.../pm-home/` (CDN da loja) — assets JSON/JS de campanha podem vir da loja, não do OT.
- SKUs `pm-teste-esquenta-*` e pedidos recentes com meta Accesstage confirmados via WC REST.

## GO / próximos passos (código Accesstage)

Para o pedido Woo bater com o charge (e com a UI):

- Após `calculate_totals()`, forçar total/linhas a partir de `totalamount` (e/ou aplicar o mesmo preço Esquenta ao `add_product`), **ou**
- Gravar meta `totalamount` cobrado e reconciliar no backoffice.

Sem essa alteração no `functions.php` do child, a garantia Esquenta até o **cartão** depende de `totalamount` correto; a garantia até o **recibo Woo** continua incompleta.

## Segurança

- API keys Accesstage por unidade estão em texto claro no child theme OT (e tipicamente no mesmo ficheiro da loja). Tratar dumps Hostinger como segredo; rodar com cuidado se for editar o ficheiro em produção.
