# 03 — Inventário de plugins e integrações

Comparação REST autenticada 30/10/2026 (OficialTeste × Loja). Sem segredos.

## Diff de plugins

### Só no OficialTeste

| Plugin (slug) | Status OT | Ação na loja |
|---------------|-----------|--------------|
| `woo-cart-abandonment-recovery` | active | **Instalar e ativar** no cutover (WCAR) |
| `hostinger`, `hostinger-easy-onboarding`, `hostinger-reach` | inactive | Irrelevante (hosting do ensaio) |
| `litespeed-cache` | inactive | Loja já tem LiteSpeed no servidor Hostinger; não copiar estado OT |

### Só na Loja

| Plugin (slug) | Status | Ação |
|---------------|--------|------|
| `lb-fpl-102tsm`, `lb-fpl-zfm3gv` | inactive | Manter como estão; não apagar no cutover de front |

### Mesmo plugin, status diferente

| Plugin | OT | Loja | Ação |
|--------|----|------|------|
| `code-snippets` | **active** | **inactive** | **Ativar** na loja (já instalado) |

### Em comum (~37)

Incluem (lista não exaustiva documentada no histórico): WooCommerce, Contact Form 7, Conditional Fields, CPF-old, reCAPTCHA CF7, Elementor, Shopwise / Shopwise Core, RevSlider, Smart Slider, Yoast, Mega Main Menu, Mailchimp, TI Wishlist, variation swatches, YITH Compare, etc.

**Não remover** CF7, Conditional Fields, CPF-old, Woo no cutover.

## Integrações externas

| Integração | Onde vive | Migrar? |
|------------|-----------|---------|
| **Accesstage** (pagamento) | Config + metas de pedido na **loja**; fora do git | **Não tocar** — preservar |
| **CF7 #1831** | Página `/finalizar-pagamento/` | Preservar formulário e scripts |
| **WCAR / CartFlows CA** | Plugin + snippet `pm_wcar_snippet.php` + tabela leads | Instalar plugin + publicar snippet |
| **SMTP / wp_mail** | Settings da loja | Preservar; validar no teste de e-mail |
| **GTM** | Hardcoded no `pm_home_snippet.php` (`GTM-52G8XVQ8`) | Confirmar se o ID da loja é o mesmo antes do GO |
| **reCAPTCHA CF7** | Plugin + keys no WP | Preservar |
| **Store API** (`wc/store/v1`) | Woo nativo | Já existe na loja — carrinho do projeto depende dela |
| **PageSpeed API** | Chave só em `oficialteste.env` | Opcional / ensaio PSI — não necessário no cutover |

## Configurações a recriar na loja (não vêm no bundle)

1. Cupom WooCommerce `PRIMEIRACOMPRA5` (5% no total, 1 uso/cliente, primeira compra) — se ainda não existir.  
2. Templates/sequência WCAR (o snippet tenta setup versionado `PM_WCAR_SETUP_VERSION`).  
3. Logo de e-mail (ensaio usou `_email_round_logo.py` no OT — reaplicar na loja se a mídia diferir).  
4. Featured images via `_sync_woo_featured_images.py --allow-prod` (só após GO).

## Namespaces REST

| Namespace | OT | Loja (hoje) |
|-----------|----|-------------|
| `code-snippets/v1` | sim | não (plugin inativo) |
| `pm-home/v1` | sim (bundle POST) | não |
| `pm-wcar/v1` | sim | não |
| `wc/v3`, `wc/store/v1` | sim | sim |
