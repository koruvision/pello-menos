# 02 — Documentação das páginas

Convenção: **Original** = loja tema Shopwise/Elementor antes do overlay. **OT** = OficialTeste com `pm-home`. Rotas controladas por `PM_HOME_ROUTES` em `scripts/pm_home_snippet.php`.

POST, `admin-ajax`, `wc-ajax`, `/wp-login.php`, `/wp-admin` **nunca** são interceptados pelo snippet.

---

## Rotas principais do projeto

### `/` — Home feminina

| | |
|--|--|
| **Original** | Elementor + sliders Shopwise |
| **OT** | `home.html` + `home.js` + `home.css`; pop-up `promo-popup.js` |
| **Códigos** | Snippet `pm-home` rota `home`; GTM no snippet |
| **Migrar** | Bundle + ativar rota `home` (ou `--all`) |
| **Cuidado** | Sem rota `produto` na sequência, ~55 links da home 404; cache Hostinger |

### `/masculino/` — Home masculina

| | |
|--|--|
| **Original** | 404 ou página fraca |
| **OT** | `masculino.html`; pop-up também |
| **Migrar** | Rota `masculino` |
| **Cuidado** | Preços/imagens masculino já alinhados no OT — sync featured na loja no cutover |

### `/produto/{slug}/` — Ficha

| | |
|--|--|
| **Original** | Template Woo/tema |
| **OT** | `products/{slug}.html` via `routes.json`; `product.js` (carrinho, cupom %, WCAR) |
| **Migrar** | Bundle completo de `products/` + `routes.json` + `woo-bridge.json` |
| **Cuidado** | Preços na UI vêm do JSON/catálogo; Woo na loja deve ter preços **reais**, não R$1 de ensaio |

### `/carrinho/`

| | |
|--|--|
| **Original** | Carrinho Woo tema |
| **OT** | `carrinho.html` + `cart.js` (qty, cupom 5%, sync preço, mixed unit block) |
| **Migrar** | Rota `carrinho` |
| **Cuidado** | `pm-cart-v1` no browser; Store API no servidor; cupom `PRIMEIRACOMPRA5` precisa existir no Woo da loja |

### `/minha-conta/` (+ subrotas exceto lost-password)

| | |
|--|--|
| **Original** | Woo My Account tema |
| **OT** | `conta.html` + `account.js` + `account.php` (AJAX `pm_account`); switch Entrar/Cadastro; nome+telefone; pedidos por `customer_id` + `billing_email`; detalhe também por e-mail |
| **Migrar** | Rota `conta` + include `account.php` do uploads |
| **Cuidado** | `conta.html` **não** é gerada por `export_wp_home.py` — vai no bundle manual; lost-password fica Woo |

### `/minha-conta/lost-password/`

| | |
|--|--|
| **Original / OT** | Formulário Woo; chrome do projeto se `shell` on |
| **Migrar** | Nada de HTML próprio |
| **Cuidado** | Não substituir o miolo |

### `/finalizar-pagamento/` — Checkout

| | |
|--|--|
| **Original** | CF7 `#1831` + Conditional Fields + CPF-old + Accesstage |
| **OT** | **Mesmo miolo**; `checkout-shell-c24.js` + `checkout-brand.css` só chrome/painel |
| **Migrar** | Rota `shell` (enqueue); **não** copiar form |
| **Cuidado** | Trava: `input name="cpf"`, `cart-number`×3, `wpcf7-f1831`. Sem POST de teste sem GO. PHP 7.4 |

### Order received (`…/order-received/{id}/?key=`)

| | |
|--|--|
| **Original** | Thank-you Woo/tema |
| **OT** | `pedido-recebido.html` + corpo via `pm_home_order_body` |
| **Migrar** | Com `shell` / conta |
| **Cuidado** | Precisa `key` do pedido |

---

## Páginas do mapa `pages.json` (rota `loja`)

Todas: original = tema/Elementor ou 404; OT = HTML em `wordpress-loja/pm-home/pages/`.

| Path | Arquivo |
|------|---------|
| `/loja` | `pages/loja.html` |
| `/servicos`, `/servicos/cera|laser|linha|esfoliacao` | `servicos*.html` |
| `/masculino/servicos` (+ cera/laser/esfoliacao) | `masculino-servicos*.html` |
| `/area/virilha|pernas|axilas|rosto|corpo` | `area-*.html` |
| `/masculino/area/torax|axilas|pernas|rosto|corpo` | `masculino-area-*.html` |
| `/planos`, `/masculino/planos` | `*planos.html` |
| `/produtos`, `/masculino/produtos` | `*produtos.html` |
| `/cartao-presente`, `/masculino/cartao-presente` | `*cartao-presente.html` |
| `/desejos` | `desejos.html` |
| `/termos`, `/privacidade` | termos/privacidade |
| Aliases `/depilacao-a-cera`, `/depilacao-a-laser`, categorias | reutilizam servicos-cera/laser |

**Migrar:** rota `loja` + pasta `pages/`.  
**Cuidado:** conteúdo institucional pode diferir do Elementor antigo; conteúdo Elementor permanece no BD e volta se o snippet desligar.

---

## Fora do overlay (permanecem tema / WP)

- Contato, FAQ, contratos, sobre (chrome só, se `shell`).
- `/wp-login.php`, `/wp-admin/`.
- WhatsApp float **não** em carrinho/checkout (regra do front).

## Mock Next (não é produção)

- `src/app/checkout` — preview local; link real aponta para `/finalizar-pagamento/`.
