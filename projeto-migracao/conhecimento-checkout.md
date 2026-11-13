# Base de conhecimento — Checkout / pagamento Pello Menos

Documento **somente leitura**. Não autoriza mudança de formulário, POST, gateway, preço, estoque nem pedido. Consolida o que o repositório e a leitura pública (outubro de 2026 + revalidação em oficialteste) já sabem.

**Segredos:** este arquivo lista **nomes** de variáveis e caminhos. Valores ficam em `.secrets/` (gitignored) ou no painel. Nunca versionar senhas, app passwords, tokens, nonces ou `order key`.

---

## 1. Escopo e regras

### O que é o checkout real

O pagamento em produção / ensaio WordPress **não** passa pelo protótipo Next.js:

| Camada | Rota / arquivo | Papel |
|--------|----------------|--------|
| **Real (WP)** | `/finalizar-pagamento/` + CF7 **#1831** | Formulário de cartão, CPF, unidade, reCAPTCHA; POST do CF7 |
| **Chrome do projeto** | `checkout-shell.js` (rota `shell`) | Só header/footer do projeto; **não** lê o formulário |
| **Mock Next** | `src/app/checkout`, `CheckoutView.tsx` | UI local; não é o checkout da loja |

Link do carrinho do projeto e do Next aponta para **`/finalizar-pagamento`** (WP), não para o mock.

### Nunca mexer (produção)

Fonte: [wordpress-loja/00-regras.md](../wordpress-loja/00-regras.md)

- `/finaliza-compra/`, `/finalizar-pagamento/`, menu **Pagamentos**, WooCommerce → Checkout
- Gateway, preço real, cupom de pagamento, estoque, pedido
- POST do formulário, HTML do miolo CF7, contratos/termos
- Ativar/desativar plugin, atualizar WP, trocar tema (sem autorização)

### Pode (só com autorização)

- Chrome visual: `checkout-shell.js`, CSS que esconde `header.header_wrap` / `footer.footer_dark`
- Front pré-pagamento: home, ficha, carrinho via Store API + `pm-home`
- Thank-you visual: `pedido-recebido.html` + corpo gerado por PHP quando `shell` está ligada

---

## 2. Mapa de rotas

| Rota | O que acontece com `PM_HOME_ROUTES` incluindo `shell` |
|------|------------------------------------------------------|
| `/finalizar-pagamento/` | HTML/scripts do **tema + CF7 intactos**; snippet **não** troca o corpo; enfileira `checkout-shell-c13.js?v=c13` + `checkout-brand.css?v=brand4`; shell monta painel Store API (`#pm-checkout-cart`: qty/remove; só na etapa Pagamento) e preenche `cupom`/`cupomamount`/`fullvalue`/`totalamount` (cupom só via `/carrinho/`) |
| `/finaliza-compra/`, `/checkout/` | Em geral iguais ao tema; usados como prefixo de `order-received` |
| `/(finalizar-pagamento\|finaliza-compra\|checkout)/order-received/{id}` | Serve `uploads/pm-home/pedido-recebido.html` e injeta `<!--PM_ORDER_BODY-->` via `pm_home_order_body($id)` (exige `?key=` do Woo para detalhe) |
| `/carrinho/` | HTML estático do projeto (`carrinho.html` + `cart.js`) |
| `/produto/{slug}/` | HTML estático + `product.js` (`pmWoo`) |
| POST, `admin-ajax`, `wc-ajax`, `/wp-admin`, `/wp-login.php` | **Fora** do `template_redirect` do snippet |

Implementação: [scripts/pm_home_snippet.php](../scripts/pm_home_snippet.php). Constante opcional `PM_HOME_ROUTES` (ex.: `home,masculino,produto,carrinho,conta,shell,loja`). Sem a constante, todos os ramos ligam.

WhatsApp flutuante (`whatsapp-float.js`) **não** aparece em `/carrinho`, `/finalizar-pagamento`, `/finaliza-compra`, `/checkout`.

---

## 3. Fluxo ponta a ponta

```text
[Ficha product.js]
    |-- localStorage "pm-cart-v1"
    |-- POST /wp-json/wc/store/v1/cart/add-item|update-item|remove-item
    |      (header Nonce; cookies sessão Woo)
    |-- IDs Woo vêm do mapa woo-bridge.json (não cria produtos no admin)
    v
[/carrinho/ cart.js]
    |-- espelha qty/remove no Store API
    |-- cupom: apply-coupon / remove-coupon + totals Woo
    |-- link "Ir para o pagamento" se !mixed (uma unidade)
    |-- no clique: reconcile itens + reaplicar cupons, depois GET
    v
[GET /finalizar-pagamento/]
    |-- mesma sessão Woo (cookies)
    |-- CF7 #1831 + plugins + script inline da página WP
    |-- checkout-shell preenche cupom/cupomamount/fullvalue/totalamount via GET cart
    v
[POST CF7 feedback]  ← fora do repositório; testes NÃO enviam
    v
[…/order-received/{id}/?key=…]
    |-- pedido-recebido.html + pm_home_order_body
```

### Bridge ≠ criação de produto

O catálogo do projeto (`src/lib/data.ts`) aponta para produtos **já existentes** no WooCommerce via `woo-bridge.json` (`productId` / `variationId` por unidade). Scripts como `build_woo_bridge.py` só **clonam entradas do mapa** (ex. esfoliação → SKU de cera equivalente); não cadastram produtos novos no admin Woo. Cupons também são só os cadastrados em Woo → Marketing → Cupons.

### Regras de negócio no front do projeto (carrinho)

- **Uma unidade por carrinho:** itens de outra unidade → aviso “mixed”; link de pagamento some (`canPay = !mixed` em `cart.js`).
- Divergência com roteiros antigos de teste: alguns docs/testes falavam em **qty 2** esconder o link e pedir “Ajuste a quantidade”. No `cart.js` atual **não** há checagem `totalQty === 1` — só bloqueio por unidades misturadas. Ver §10.

### Preço R$ 1 no ensaio

- Next / bridge: `TEST_CHARGE_CENTS = 100` em `src/lib/data.ts` e `woo-bridge.ts` — só protótipo/catálogo do projeto.
- Isso **não** altera sozinho o gateway WP; no teste, produtos Woo também podem estar a R$ 1 por configuração da loja de ensaio.

---

## 4. Formulário Contact Form 7 #1831

### Identidade

- ID: **1831**
- Classes típicas: `wpcf7-f1831`, action `/finalizar-pagamento/#wpcf7-f1831-o1`
- Página título (oficialteste): “Finalizar Pagamento - Pello Menos”

### Campos do miolo (pagamento)

Consolidados de [wordpress-loja/10-checkout-loja-vs-clone.md](../wordpress-loja/10-checkout-loja-vs-clone.md) e fase 5 (`diario.md`):

**Pessoa / contato**

- `your-name`, `your-email`, `your-phone`
- `cpf` — `<input name="cpf">` na loja e no oficialteste (PHP 7.4); no clone PHP 8 o shortcode `[cpf` pode aparecer cru

**Endereço**

- `cep`, `endereco`, `numero`, `complemento`, `bairro`, `cidade`, `estado`

**Pedido / unidade**

- `unit`, `category`, `cart`, `cartqtd`, `cupom`, `cupomamount`, `fullvalue`, `totalamount`, `subscribemode`, `declaracao`, `easyunit`

**Cartão**

- `cart-number` (3 ocorrências no HTML), `holder`, `expiration`, `securityCode`
- `installments`, `allinstallments`, `cerainstallments`, `siteinstallment`

**Parcelas (mapa completo):** vitrine (`getInstallment`) × selects CF7 × paridade oficialteste/loja — ver [historico/16-regras-parcelamento.md](historico/16-regras-parcelamento.md). Resumo CF7: `allinstallments` 1–10x; `cerainstallments` 1–3x; `installments` só 1x. **Desde 27/10/2026** a vitrine do projeto segue esses tetos (cera/esfoliação 3x, presente/plano 1x); carrinho não calcula Nx do total.

**Conditional Fields (grupos de unidade)**

- `_wpcf7cf_hidden_group_fields`, `_wpcf7cf_hidden_groups`, `_wpcf7cf_options`, `_wpcf7cf_repeaters`, `_wpcf7cf_steps`, `_wpcf7cf_visible_groups`

**reCAPTCHA**

- `g-recaptcha-response`, `_wpcf7_recaptcha_response` (e scripts `recaptcha`)

**CF7 internos**

- `_wpcf7`, `_wpcf7_version`, `_wpcf7_locale`, `_wpcf7_unit_tag`, `_wpcf7_container_post`, `_wpcf7_posted_data_hash`, …

### Marcadores HTML (revalidação oficialteste, GET `?pm=kb-checkout-1`)

| Marcador | Valor observado |
|----------|-----------------|
| `wpcf7-f1831` | sim |
| `input name="cpf"` | sim |
| shortcode `[cpf` cru | não |
| `cart-number` | 3 |
| `jquery.mask` | 2 |
| chamadas `.mask(` | 5 |
| `wpcf7cf` | 15 |
| `checkout-shell` | sim |
| honeypot `_wpcf7_ak_hp_textarea` | não (presente no clone, não na loja/oficialteste) |
| PHP | 7.4.33 (`X-Powered-By`) |
| CDN | hcdn, status DYNAMIC nesta leitura |

Lista de inputs na página inteira (inclui busca, meta, Mailchimp): inventário em leitura local; o **miolo 1831** é o subconjunto acima (~38 nomes no formulário normalizado da fase 5).

### CPF (ponto crítico loja vs clone)

- Plugin: **`cpf-e-cnpj-para-contact-form-7-old`** (docs: 1.0.2)
- Loja / oficialteste (PHP **7.4**): plugin ativo → campo `cpf` renderizado + `main.js` / `mask.min.js`
- Clone (PHP **8.x**): plugin quebra → shortcode cru; **não** copiar esse estado para a loja
- Subir PHP da loja para 8 **com** esse plugin ativo é risco de quebrar CPF no pagamento

---

## 5. Scripts e plugins

### Dependências que o pagamento precisa (não remover ao esconder o tema)

Fonte: [wordpress-loja/01-paginas-e-conta.md](../wordpress-loja/01-paginas-e-conta.md)

- jQuery, jQuery Migrate, **jQuery Mask 1.14.16**
- WooCommerce front (`woocommerce.min.js`, cookie, blockUI, order attribution, sourcebuster; loja também pode ter `cart-fragments`)
- Contact Form 7 (`includes/js/index.js` + SWV)
- **CF7 Conditional Fields** (`cf7-conditional-fields/js/scripts.js`)
- **CF7 reCAPTCHA** + `recaptcha/api.js`
- **cpf-e-cnpj-para-contact-form-7-old** (`main.js`, `mask.min.js`) quando PHP 7.4
- **Script inline da página WP** (máscara de cartão + condução do passo / preenchimento de hidden fields) — **não versionado neste repo**

Também permanecem no DOM (tema): Shopwise, Elementor, Mega Menu, RevSlider, Mailchimp, RDSDK, etc. Não fazem parte do miolo 1831, mas não devem ser “limpos” às cegas.

### `checkout-shell.js`

- Arquivo: [wordpress-loja/pm-home/checkout-shell.js](../wordpress-loja/pm-home/checkout-shell.js)
- Versão enfileirada pelo snippet: `checkout-shell-c13.js?v=c13` + `checkout-brand.css?v=brand4`
- Etapa Dados: só card do formulário (largo). Etapa Pagamento: 2 cards (pedido + formulário). Sem UI de cupom no checkout.
- Painel `#pm-checkout-cart`: mutações via Store API (`update-item` / `remove-item` / cupons); fallback `.removeitem` same-origin
- Monta `#pm-shell-header` / `#pm-shell-footer` (shadow / HTML de upload); lê `localStorage` só para badge do carrinho
- Base de assets no fonte aponta ao clone; o **bundle** (`pm_publicar_destino.py`) reescreve a base do destino
- **Não** preenche nem valida o CF7

### Plugins citados na fase 0 (ensaio)

Lista longa em `projeto-migracao/diario.md` / `.secrets/fase0-leitura.json`. Relevantes ao pagamento:

- WooCommerce
- Contact Form 7
- CF7 Conditional Fields
- cpf-e-cnpj-para-contact-form-7-old
- CF7 reCAPTCHA
- (Code Snippets — usado para publicar o front `pm-home`, não o gateway)

**Gateway de cartão:** nenhum plugin de PagSeguro / Cielo / Stripe / Mercado Pago / Rede / Getnet nomeado neste repositório. O menu WP **Pagamentos** existe nas regras como zona proibida e **não foi aberto** nas leituras documentadas.

---

## 6. APIs e cookies

### Store API (pré-pagamento)

Definida em [wordpress-loja/pm-home/product.js](../wordpress-loja/pm-home/product.js) como `window.pmWoo`:

| Método | Path | Uso |
|--------|------|-----|
| GET | `/wp-json/wc/store/v1/cart` | Lê carrinho; obtém/atualiza **Nonce**; `items`, `coupons`, `totals` |
| POST | `/wp-json/wc/store/v1/cart/add-item` | Incluir |
| POST | `…/update-item` | Quantidade |
| POST | `…/remove-item` | Remover |
| POST | `…/apply-coupon` | Aplicar cupom `{ code }` |
| POST | `…/remove-coupon` | Remover cupom `{ code }` |

- `credentials: "same-origin"`
- Header `Nonce: <wooNonce>`
- Espelho em `localStorage`: chave **`pm-cart-v1`** (itens com `wooId`, `wooKey`, unidade, qty, …)

### Cookies / cache

O snippet marca resposta como privada (sem cache público agressivo) se detectar cookies:

- `wordpress_logged_in*`
- `woocommerce_items_in_cart*`
- `wp_woocommerce_session*`

Pagamento e carrinho Woo dependem dessa sessão: o GET `/finalizar-pagamento/` “vê” o carrinho sem o projeto reescrever o HTML do form.

### Deploy do front

- REST `POST /wp-json/pm-home/v1/bundle` (zip; requer capability `edit_pages`)
- Script: [scripts/pm_publicar_destino.py](../scripts/pm_publicar_destino.py)

---

## 7. Ambientes

| | Loja oficial | Clone | Oficial teste |
|--|--------------|-------|----------------|
| Host | `loja.pellomenos.com.br` | `pellomenos.companygenesis.com.br` | `pellomenosoficialteste.companygenesis.com.br` |
| PHP (leituras out/2026) | 7.4.33 | 8.2.x | 7.4.33 |
| Miolo CF7 1831 | referência | mesmo miolo; CPF pode quebrar | alinhado à loja nos marcadores |
| `checkout-shell.js` | só se `shell` publicado | sim (`--all` / snippet 9) | sim com rotas atuais |
| `uploads/pm-home/` | gradualmente | completo | completo (bundle) |
| Publicação | `--permitir-loja` explícito | prefixo `PM_CLONE_*` | default ensaio `PM_OFICIALTESTE_*` |

Paridade detalhada loja × clone: [wordpress-loja/10-checkout-loja-vs-clone.md](../wordpress-loja/10-checkout-loja-vs-clone.md).

---

## 8. Credenciais e acesso (somente nomes)

**Aviso:** valores **não** entram neste Markdown. Estão em arquivos ignorados pelo git ou no hPanel / WP.

### Arquivos `.env` em `projeto-migracao/.secrets/`

| Arquivo | Variáveis (nomes) |
|---------|-------------------|
| `oficialteste.env` | `PM_OFICIALTESTE_URL`, `PM_OFICIALTESTE_USER`, `PM_OFICIALTESTE_APP_PASSWORD`, `PM_OFICIALTESTE_WP_ADMIN_USER`, `PM_OFICIALTESTE_WP_ADMIN_PASSWORD`, `PM_HOSTINGER_ACCOUNT` |
| `clone.env` | `PM_CLONE_URL`, `PM_CLONE_USER`, `PM_CLONE_APP_PASSWORD` |

Documentadas em guias (podem não existir no disco):

- `PM_LOJA_URL`, `PM_LOJA_USER`, `PM_LOJA_APP_PASSWORD` — loja oficial + flag `--permitir-loja`

### Outros nomes usados por scripts / testes

| Nome | Uso |
|------|-----|
| `PM_BASE` | URL alvo dos testes Playwright (`_comum.py`) |
| `PM_ENV_FILE` | Caminho do `.env` nos testes |
| `PM_HOME_ROUTES` | Constante PHP no snippet Code Snippets |
| `PM_HOME_ORIGIN` | Origem Next no export (`export_wp_home.py`) |
| `PM_ASSET_BASE` | Base de assets no HTML exportado |
| `PM_WOO_USER` / `PM_WOO_PASS` | Opcional para listar slugs Woo no export |
| Prefixo genérico | `{PREFIX}_URL`, `{PREFIX}_USER`, `{PREFIX}_APP_PASSWORD` em `pm_publicar_destino.py` |

### Estado (não são senhas)

- `oficialteste.state.json` / `clone.state.json` — id do snippet Code Snippets, rotas ativas
- `.secrets/fase0-leitura.json` — snapshot fase 0 (plugins, marcadores)
- `fase0-finalizar-pagamento.html` — HTML cru de referência (gitignored)

### Painel WordPress

- App password / usuário de leitura: variáveis `*_USER` / `*_APP_PASSWORD`
- Menu **Pagamentos** / gateways: **não documentados por inspeção** neste projeto (regra de não abrir)

### Hostinger

- Conta: nome `PM_HOSTINGER_ACCOUNT` (ex. formato `u…`)
- Token de API (quando usado em outros repos): **não** versionado aqui; não colar valor neste arquivo

---

## 9. Lacunas explícitas (o que o repo não sabe)

1. **Nome do gateway / processador de cartão** — ausente do código e docs; processamento após CF7 vive em WP/plugins/hooks fora deste git.
2. **Pós-submit CF7** — templates de mail, criação/atualização de pedido Woo, redirecionamento para `order-received`, tratamento de falha: **zero implementação no repo**.
3. **JS inline da página `/finalizar-pagamento/`** — citado como quem chama `.mask()` e preenche `cart` / `cartqtd` / `unit` / totais; **não** está em `wordpress-loja/pm-home/`.
4. **Assets só no servidor** (podem faltar no working tree): `pedido-recebido.html`, `checkout-header.html`, `checkout-footer.html` sob `uploads/pm-home/`.
5. **Endpoint exato de feedback CF7** — testes monitoram URLs com `wpcf7`/`feedback`, mas não há especificação de payload/resposta de sucesso neste repo.
6. **Divergência qty** — ver §10.

Qualquer “completar” essas lacunas exige leitura autorizada no WP (sem POST de pagamento) ou engenharia fora do escopo deste KB.

---

## 10. Testes e o que não se faz

| Artefato | Função |
|----------|--------|
| `testes/fase0_leitura.py` | GET pagamento + plugins; grava referência |
| `testes/fase3_carrinho.py` | Carrinho → link pagamento; qty (roteiro legado) |
| `testes/fase5_chrome_checkout.py` | Paridade form 1831, shell, CPF máscara; **nenhum submit** |
| `testes/_comum.py` | `PM_BASE`, helpers Store API; política: não enviar pagamento |

### Divergência documentada: quantidade vs `cart.js`

- Roteiros / `fase3` / histórico: qty **2** → some link “Ir para o pagamento” + aviso “Ajuste a quantidade”.
- Código atual (`cart.js`): `canPay = !mixed` (só unidades misturadas). Quantidade > 1 **na mesma unidade** ainda pode mostrar o link.

Quem for alterar comportamento do carrinho deve alinhar teste e código de propósito; não assumir que o roteiro antigo ainda vale.

---

## 11. Índice de arquivos

| Path | Papel |
|------|--------|
| `wordpress-loja/pm-home/product.js` | `pmWoo` + add to cart |
| `wordpress-loja/pm-home/cart.js` | UI carrinho + link `/finalizar-pagamento/` |
| `wordpress-loja/pm-home/checkout-shell.js` | Chrome do checkout |
| `wordpress-loja/pm-home/whatsapp-float.js` | Esconde WA no pagamento |
| `wordpress-loja/pm-home/account.php` | Conta + possible intercept order-received |
| `scripts/pm_home_snippet.php` | Rotas, shell, order-received, bundle REST |
| `scripts/pm_publicar_destino.py` | Publica snippet/bundle |
| `src/components/CartView.tsx` | Link Next → `/finalizar-pagamento` |
| `src/lib/data.ts` | `TEST_CHARGE_CENTS` |
| `wordpress-loja/00-regras.md` | Limites produção |
| `wordpress-loja/01-paginas-e-conta.md` | Mapa páginas + scripts pagamento |
| `wordpress-loja/10-checkout-loja-vs-clone.md` | Diff loja × clone |
| `projeto-migracao/diario.md` | Ensaio fases 0–5 |
| `projeto-migracao/como-publicar.md` | Como publicar rotas |
| `projeto-migracao/testes/fase5_chrome_checkout.py` | Aceite chrome + form |
| `projeto-migracao/historico/16-regras-parcelamento.md` | Parcelas: ficha × CF7; oficialteste = loja |

Espelhos em `projeto-migracao/historico/` e `wordpress-loja/` (cópias numeradas).

---

## 12. Checklist read-only (revalidar sem POST)

1. `GET /finalizar-pagamento/?pm=<novo>` no destino
2. Confirmar marcadores: `wpcf7-f1831`, `name="cpf"`, `cart-number`×3, `jquery.mask`, `wpcf7cf`, reCAPTCHA, (se shell) `checkout-shell.js`
3. Confirmar **ausência** de `[cpf` cru e, se PHP 7.4, presença de script `cpf-e-cnpj-para-contact-form-7-old`
4. Com item na Store API, abrir pagamento e ver se o conteúdo da página reflete o serviço (evidência indireta do JS inline)
5. `GET …/order-received/{id}?key=…` só com pedido próprio / ambiente de teste
6. **Não** clicar enviar no formulário de cartão em automação
7. **Não** abrir menu Pagamentos sem pedido explícito e plano

---

## Docs legados (não apagar)

Este KB **consolida**; os originais continuam válidos como histórico:

- [wordpress-loja/10-checkout-loja-vs-clone.md](../wordpress-loja/10-checkout-loja-vs-clone.md)
- [wordpress-loja/01-paginas-e-conta.md](../wordpress-loja/01-paginas-e-conta.md)
- [projeto-migracao/historico/10-checkout-loja-vs-clone.md](historico/10-checkout-loja-vs-clone.md)
- [projeto-migracao/historico/01-paginas-e-conta.md](historico/01-paginas-e-conta.md)
- [projeto-migracao/historico/16-regras-parcelamento.md](historico/16-regras-parcelamento.md) — vitrine × CF7 × oficialteste=loja
- [projeto-migracao/diario.md](diario.md)

---

*Última consolidação: leitura de código + GET público oficialteste (`pm=kb-checkout-1`), alinhada às regras de não alterar checkout.*
