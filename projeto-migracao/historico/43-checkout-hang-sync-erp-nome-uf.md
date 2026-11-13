# 43 — Checkout travado (Nilópolis/LMA) + sync ERP (nome/UF)

Data: 2026-11-06.

## Diagnóstico spinner

| Hipótese | Resultado |
|----------|-----------|
| Keys Accesstage Nilópolis/LMA | **OK** — cobrança direta Rede `returnCode=00` (probes repetidos) |
| Label→slug normalize | Já ativo; mapa inclui Nilópolis / Largo do Machado |
| Overlay em falha Accesstage | **Bug UX** — `payment_CF7` em erro ainda dispara `wpcf7mailsent` com texto “Compra não realizada.”; shell tratava como **confirmado** |
| Laser em Nilópolis | **Gap CF7** — catálogo vende laser♀ em NIL, mas `easyunit` **não** listava Nilópolis (só `unit`/cera). Cliente laser não conseguia escolher a unidade certa |

Evidência UI pós-fix: submit Nilópolis → resposta CF7 `sent` + “Compra não realizada.” + overlay **idle** (sem hang). Falha pontual Accesstage também retornou `Insufficient funds` em uma janela (merchant), depois voltou a autorizar.

## Correções publicadas

1. **Shell `checkout-shell-c24.js?v=c45`**
   - Failsafe overlay **35s** (antes 90s) + mensagem se timeout
   - `wpcf7mailsent` com “Compra não realizada” / curl / recusa → **fecha overlay**, não marca confirmado; cookie de redirect aponta para a mesma URL (`#pm-pay-fail`) para não ir a `location=undefined`
   - Bloqueio front: `your-name` com `@` antes do submit
   - `ensureAccesstageUnitFromCart()`: se a unidade do carrinho não está no `easyunit`, **injeta** a option (ex. Nilópolis laser)

2. **Snippet `pm-accesstage-normalize-test`**
   - UF: nomes (`Rio de Janeiro`…) → `RJ` no `wpcf7_posted_data` e em `woocommerce_order_status_*`
   - CF7 validate: rejeita `your-name` com `@`
   - Se `billing_first_name` parece e-mail → limpa (não inventa nome)
   - Injeta option Nilópolis no `easyunit` (`wpcf7_form_tag` + `wpcf7_form_elements`) — REST do CF7 **não** persistiu edição do form #1831

3. **Backfill**
   - `#49500`: `billing/shipping.state` `Rio de Janeiro` → **`RJ`**
   - `#49488` / `#49541`: `first_name` era e-mail → **limpo** (ERP precisa correção manual do Nome; Woo não inventa)

## Causa nome = e-mail (ERP)

`payment_CF7` grava `first_name = your-name` e cria user com `user_login = email` sem `display_name`. Autofill coloca e-mail em Nome → JSON da sync leva e-mail em **Nome**. Bloqueios front+CF7 impedem novos; pedidos antigos: limpar campo, corrigir no ERP à mão.

## Status ERP vs Woo

Pedidos Accesstage na loja seguem fluxo `processing` → snippet paid-completed → `completed`. ERP em “process” costuma ser **re-pull** atrasado, não falha de pagamento.

## Smoke

- Accesstage API Nilópolis/LMA: Success (com janela de `Insufficient funds` intermediária)
- Overlay: falha Accesstage **não** fica em confirmed
- Pedidos API ensaio (nome real + `state=RJ`) — ver `_smoke_nil_lma_api_orders_result.json`
- reCAPTCHA plugin **reativado** após bateria (snippet bypass off)

## Nilópolis — o que foi / o que **não** foi

| Item | Feito? |
|------|--------|
| Criar unidade nova Accesstage | **Não** |
| Criar / alterar token `API` / `APIKey` | **Não** |
| Token `nilopolis` já existia no tema | **Sim** (dump `shopwise-child` + inventário §37; probe Rede `00`) |
| Nilópolis no CF7 `unit` (cera) | Já existia |
| Nilópolis no CF7 `easyunit` (laser) | **Faltava** — só injetamos a **option no select** apontando para o slug `nilopolis` já existente |
| Shell: injetar option a partir do carrinho | Sim (mesmo slug) |

Regra permanente: agente **não cria unidade nem token** sem a chave informada pelo time — ver `.cursor/rules/accesstage-unidades.mdc`.

## Não mexido

- Valores das keys Accesstage (só leitura/prova; **nenhuma key criada**)
- Limpeza cega do tema `payment_CF7`
