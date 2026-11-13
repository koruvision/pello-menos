# 10 — Relatório de execução do cutover

**Data:** 30/10/2026  
**Destino:** `https://loja.pellomenos.com.br`  
**Modo:** overlay (sem restore de BD do OficialTeste)

## Resumo

O front do projeto, snippets, WCAR, cupom e produto de teste estão **no ar** na loja. Clientes/pedidos/admins/CF7/Accesstage **não** foram apagados. A compra automática de R$ 1,99 **não** concluiu por **reCAPTCHA** no CF7 (bloqueio esperado em automação); o fluxo até o checkout com carrinho R$ 1,99 e unidade DF - Asa Sul foi preenchido com sucesso.

## A — Backup

| Item | Resultado |
|------|-----------|
| WP-Vivid | Plugin **ativo**, mas **sem** REST pública simples (`/wp-json/wpvivid/*` 404) |
| Tentativa | 1× — **pulada** conforme plano |
| Backup humano | Confirmado previamente pelo Rafael |

## B — Gates (pré)

| Gate | Resultado |
|------|-----------|
| PHP | `PHP/7.4.33` |
| CPF `input` | sim |
| `wpcf7-f1831` | sim |
| `cart-number` ×3 | sim |
| Snapshots | `%TEMP%\shotbanner\loja-*-pre.html` |

## C — Front publicado

Comandos com `loja.env` + `--prefix PM_LOJA --permitir-loja`:

1. `plugin` → Code Snippets **active**  
2. `snippet --routes=none` → snippet **id 6** `pm-home (front do projeto)`  
3. `bundle` → 200 OK (`home.html` ~473 KB)  
4. `snippet --routes=home,masculino,produto,carrinho,conta,shell,loja`

**Pós-rotas:** home pm-home; checkout ainda com CPF + shell; masculino/conta OK.

## D — Automações / catálogo

| Item | Resultado |
|------|-----------|
| Plugin WCAR | Instalado + **active** |
| Snippet `pm-email-styles` | id **7** active |
| Snippet `pm-wcar` | id **8** active |
| Cupom `PRIMEIRACOMPRA5` | id **48408**, 5% |
| Produto `produto-r-1` | id **48409**, R$ 1,99, `catalog_visibility=hidden` |
| Sync featured images | Maioria já alinhada; 1 atualizado; SKUs só do OT (masculino novos / Body Splash) **ausentes** na loja — pulados |

## E — Smoke

| Teste | Resultado |
|-------|-----------|
| Store API add-item `48409` | 201, total `199` centavos |
| `/carrinho/` | 200 + `cart.js` |
| `/finalizar-pagamento/` | CPF + 1831 + shell |
| `/masculino/`, `/minha-conta/` | 200 pm-home |

## F — Compra R$ 1,99

| Etapa | Resultado |
|-------|-----------|
| Add carrinho | OK (R$ 1,99) |
| Checkout preenchido | Nome, e-mail `rafaelrangel@companygenesis.com.br`, endereço, unidade **DF - Asa Sul**, cartão (só em memória) |
| Submit CF7 | **Falhou** — `likely_recaptcha_block` (reCAPTCHA impede bot) |
| Pedido Woo criado | **Não** (0 pedidos com esse e-mail na busca imediata) |

**Ação humana necessária:** abrir a loja, colocar `produto-r-1` no carrinho, pagar uma vez no checkout (reCAPTCHA manual). Depois conferir e-mail em `rafaelrangel@companygenesis.com.br` e o pedido no admin.

**Não** foram gravados PAN/CVV em git, Markdown nem `.env`.

## O que NÃO foi feito / NÃO foi apagado

- Sem restore de BD do OficialTeste  
- Sem alteração Accesstage / miolo CF7  
- Sem apagar users/pedidos  
- Sem limpeza massiva de mídia (doc 18 — depois, se quiser)  
- Produtos masculino/Body Splash que só existem no OT **não** foram criados na loja  

## G — Alinhamento pós-cutover (sem resíduos OT na loja)

| Item | Resultado |
|------|-----------|
| `cart-related.json` `produto-1-real` | **48216 → 48409** (igual ao bridge) |
| HTML `products/produto-1-real.html` | `data-product-id="48409"` |
| IDs OT-only (Body Splash + cera masc novas: `48219`, `48390`, `48391`, `48244`…`48370`) | `productId` / `variationId` **zerados** em bridge/cart/HTML; `forSale: false`; `SPLASH.wooId` vazio |
| Base de assets no repo `pm-home/` | `companygenesis` → `loja.pellomenos.com.br` (~214 ficheiros) |
| Bundle republicado | 200 OK; rewrite na fonte já alinhado (0 rewrites no publish) |
| Gate live | **0** `companygenesis` / **0** host `oficialteste` em `home.html`, `cart-related`, `woo-bridge`, `cart.js`, shells, PDP |
| Store API | add-item **48409 → 201**; **48216 → 400** (produto inexistente) |

**SKUs ainda sem Woo na loja (indisponíveis para compra até GO comercial):** Body Splash e linhas masculinas novas que só existiam no OficialTeste — não criados em massa neste cutover.

DEV LOCK (snippet **9**) permanece ativo.

## I — “Processando” vs “Concluído” (Minha Conta / thank-you)

**Não é bug do overlay.** `account.php` / thank-you só espelham `wc_get_order_status_name($order->get_status())` — sem mapa PT próprio.

| O que o cliente vê | Significado real |
|--------------------|------------------|
| Copy do gateway (“compra concluída” / pedido recebido) | Fim do checkout Accesstage + redirect `order-received` |
| Situação **Processando** (`processing`) | Status Woo **padrão** pós-pagamento para produtos/serviços não tratados como virtual/downloadable no overlay |
| **Concluído** (`completed`) | Slug Woo separado; o repo **não** chama `update_status('completed')` |

Evidência: pedidos com meta `Pedido Accesstage` (ex. **#48475**, **#48480**) ficam em `processing` com nota “Pagamento pendente → Processando”. Thank-you já fala em uso **24h após confirmação do pagamento** — coerente com pago em processamento. WCAR trata `processing` e `completed` como pedido pago.

**Fora de escopo sem GO:** auto-completar em massa, marcar produtos virtual, ou regra Accesstage → `completed`.

## H — Cupom PRIMEIRACOMPRA5 no pedido #48475 (30/10/2026)

Relato: cupom no carrinho → checkout → e-mail a **R$ 1,99** sem desconto; 2ª tentativa no carrinho → *"Este cupom vale só para a primeira compra…"*.

| Prova REST (loja) | Valor |
|-------------------|--------|
| Pedido | **#48475** `processing`, produto **48409**, e-mail `genesiscompanyoficial@gmail.com`, customer **10182** |
| `total` / `discount_total` | **1.99** / **0.00** |
| Line item subtotal/total | **1.99** / **1.99** (sem desconto na linha) |
| `coupon_lines` | **presente**: código `primeiracompra5`, campo `discount` **"0.10"**, `discount_type` reportado como `fixed_cart` (anomalia) |
| Meta | `Pedido Accesstage` = `17933876271668` |
| Cupom Woo **48408** | `percent` **5%**, `usage_limit_per_user` **1**, `usage_count` **1** |

**Leitura:** o cupom **entrou no pedido** (há `coupon_lines` e uso consumido no Woo), mas os **totais cobrados/gravados ficaram cheios** (1,99). O e-mail Woo usa `discount_total` / total do pedido → aparece sem desconto. Isso **não** é falha do painel de vitrine do shell (`displayDiscount` sobre catálogo); o caminho de cobrança é CF7 #1831 + **Accesstage** (fora do git).

**2ª aplicação no carrinho:** comportamento **esperado** — `usage_limit_per_user=1` + pedido já existente; [`cart.js`](../../wordpress-loja/pm-home/cart.js) remapeia a rejeição Woo para a mensagem de primeira compra.

**Ação de código neste overlay (30/10 noite):** reforço no `checkout-shell-c24.js?v=c31` — `ensureCouponsOnCart` reaplica `pm-coupon-v1` no boot e no submit; se Woo listar desconto mas `total_price` vier cheio, `totalamount` CF7 força líquido (`items − discount`). **Não** altera Accesstage. Reteste com e-mail/cliente novo (cupom já consumido no #48475).

**Operação (fora do repo):** se hiddens forem 1,89 e a cobrança continuar 1,99 — Accesstage/CF7 precisa aplicar o desconto no total do pedido.

## Rollback


```text
python scripts/pm_publicar_destino.py --env projeto-migracao/.secrets/loja.env --prefix PM_LOJA --permitir-loja snippet --off
```

## Veredito

**Cutover de superfície: concluído.**  
**Alinhamento hosts/IDs à loja: concluído** (zero hosts OT no overlay live; teste R$1,99 no ID 48409).  
**Compra real ponta a ponta: pendente de 1 clique humano (reCAPTCHA).**
