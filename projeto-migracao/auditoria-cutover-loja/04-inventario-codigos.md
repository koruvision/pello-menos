# 04 — Inventário de códigos personalizados

## Snippets Code Snippets (fontes no git)

| Fonte | Nome típico no OT | Finalidade | Dependências | Adaptar na loja? |
|-------|-------------------|------------|--------------|------------------|
| [`scripts/pm_home_snippet.php`](../../scripts/pm_home_snippet.php) | `pm-home (front do projeto)` (id 6 no OT) | Rotas HTML, shell checkout, REST `pm-home/v1/bundle`, include `account.php`, GTM | Code Snippets ativo; pasta `uploads/pm-home/` | Sim: publicar via `pm_publicar_destino.py`; IDs de snippet na loja serão **novos** |
| [`scripts/pm_email_styles_snippet.php`](../../scripts/pm_email_styles_snippet.php) | `pm-email-styles` (id 12) | CSS e-mails Woo (tipografia/cores/logo) | Woo e-mail templates | Publicar (script `_publish_email_styles.py` hoje hardcode OT — no GO usar loja ou PUT manual) |
| [`scripts/pm_wcar_snippet.php`](../../scripts/pm_wcar_snippet.php) | `pm-wcar` (id 13) | Setup CartFlows CA, 6 e-mails, leads `pm_checkout_leads`, `pmWcar`, janela 8h–21h | Plugin `woo-cart-abandonment-recovery` | Publicar após instalar plugin |

## Front estático `wordpress-loja/pm-home/`

| Artefato | Finalidade |
|----------|------------|
| `home.html`, `masculino.html`, `home.css`, `home.js` | Homes |
| `carrinho.html`, `cart.js` | Carrinho + cupom + sync |
| `conta.html`, `account.js`, `account.php` | Conta (conta.html **manual**, fora do export) |
| `products/*.html`, `routes.json`, `product.js` | PDPs |
| `pages/*.html`, `pages.json` | Institucionais / serviços |
| `pedido-recebido.html` | Thank-you |
| `checkout-shell.js` / `checkout-shell-c24.js` | Shell ativo (snippet aponta c24 `?v=c29`) |
| `checkout-brand.css`, header/footer HTML | Marca no checkout |
| `promo-popup.js`, `whatsapp-float.js` | Pop-up e WhatsApp |
| `woo-bridge.json`, `cart-related.json`, `product-copy.json`, `woo-slugs.json` | Ponte catálogo ↔ Woo |

Publicação: zip via `pm_publicar_destino.py bundle` (reescreve URLs do clone → destino).

## Next.js (preview local — não é o runtime da loja)

- `src/components/AuthModal.tsx`, `StoreProvider.tsx` — auth mock localStorage.  
- Espelham UX da conta WP; **não** substituem `account.php` na produção.

## Gambiarras / soluções provisórias (documentar risco)

| Item | O que é | Risco se migrar mal | Migração |
|------|---------|---------------------|----------|
| Shells `c10`–`c21` | Snapshots antigos de cache-bust | Confusão; arquivos inertes | Podem ir no zip; **ativo** é c24 |
| Detecção preço R$ 1,00 / `produto-1-real` | UI ignora Store API total quando cents===100 | Na loja com preços reais quase não dispara; **não** trazer catálogo a R$1 | Manter lógica defensiva; não sync preços ensaio |
| `SPLASH_CENTS` / ingest catalog no shell | Preço Body Splash hardcoded no ensaio | Valor errado se catálogo mudar | Conferir no GO com preço real da loja |
| Base URL clone no JS fonte | Bundle reescreve no publish | Se subir zip “na mão” sem rewrite, assets apontam clone | Sempre publicar pelo script |
| GTM fixo no snippet | `GTM-52G8XVQ8` | Tag errada na loja | Confirmar ID |
| IDs snippet 6/12/13 | Só válidos no OficialTeste | PUT no id errado na loja | Criar/atualizar por **nome** ou state novo `loja.state.json` |
| Accesstage / JS inline checkout | Fora do repo | “Corrigir” no escuro quebra pagamento | Não alterar |

## Códigos que **não** precisam migrar

- Scripts `_bump_*`, `_peek_*`, `_smoke_*`, `_audit_accesstage*` (operação/ensaio).  
- PSI dumps em `.secrets/psi-*`.  
- Pedidos/users criados só no OficialTeste.

## Conflitos possíveis

1. Tema Elementor na home **coexiste** no BD mas deixa de ser servido enquanto `pm-home` estiver ativo na rota `home` — não é conflito de plugin, é substituição de GET.  
2. Dois carrinhos (tema vs projeto): com rota `carrinho` ligada, só o do projeto deve aparecer.  
3. WCAR + e-mails Kadence: snippet de estilo só CSS; textos WCAR vêm do setup do snippet 13.
