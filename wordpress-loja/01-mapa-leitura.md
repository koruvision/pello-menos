# Mapa da loja (somente leitura)

Site: https://loja.pellomenos.com.br/

## Stack

| Camada | O que é |
| --- | --- |
| CMS | WordPress 7.1 |
| Loja | WooCommerce 10.1.4, arquivo em `/loja/` |
| Tema pai | **Shopwise** (KlbTheme) |
| Tema filho | **Shopwise Child 1.4.8** — `style.css` praticamente vazio |
| Páginas | **Elementor 3.5.6** (kit global id 11) |
| Home | Página 571 `e-commerce-pello-menos`, classe `elementor-page-571` |
| Hero | **Smart Slider 3** (slider id 1), shortcode no Elementor |
| Menu | **Mega Main Menu** |
| Busca da home | widget nativo `woocommerce_product_search` |
| SEO | Yoast |
| Extra vitrine | TI Wishlist, YITH Compare, variation swatches, Revolution Slider (plugin presente; o hero atual é Smart Slider) |

Personalização de cor do Shopwise **já usa `#700053`**, a mesma do feminino deste projeto.

Caminho de aparência no admin: **Aparência → Temas / Personalizar / Menus / Widgets**. Não apareceu painel extra “Theme Options” para esta conta.

## Plugins vistos no HTML público (não abri a tela de Plugins)

WooCommerce, Elementor, shopwise-core, Smart Slider 3, RevSlider, Mega Main Menu, Contact Form 7 + conditional fields, Mailchimp, TI Wishlist, YITH Compare, variation swatches, Jetpack, Redirection, Yoast, Code Snippets (namespace na API), Google for WooCommerce.

## Home Elementor (estrutura)

1. Shortcode do Smart Slider (slides **banner feminino** e **banner masculino**, imagens em `/wp-content/uploads/2026/09/`)
2. Título “Por tempo limitado!” + botão de laser
3. Carrossel Shopwise de produtos (laser)
4. Imagem + outro carrossel
5. Campo de busca WooCommerce (“Pesquise por outros serviços”)
6. Carrossel de cera
7. Botão de cera + imagens/CTA (“Vitrine de Serviços”, “Fale conosco”)

Widgets Elementor usados: `shortcode`, `heading`, `button`, `image`, `shopwise-product-carousel`, `wp-widget-woocommerce_product_search`.

Modelos Elementor na biblioteca: só kits padrão (3 itens). A home **não** é um template da biblioteca; é a própria página 571.

## Páginas relevantes

Públicas de vitrine: Home, Depilação a Cera, Depilação a Laser, Promoções, Planos de Assinatura, Loja, Contato, FAQ.

Rascunhos: **Depilação Cera Masculino** (id 17544, slug `depilacao-cera-masculino`, Elementor, última edição em 2022) e Assinante Vip Silver.

**Proibidas nesta conversa:** Finaliza Compra, Finalizar Pagamento, Carrinho, Minha Conta, contratos e política de privacidade.

## Catálogo

- 66 produtos visíveis no admin
- Produtos variáveis com atributo **Unidade** (`pa_unidade`) — o mesmo papel do seletor de loja do nosso `ProductPageView`
- Categorias:

| Categoria | Produtos |
| --- | --- |
| Serviços de Depilação a Cera Feminino | 32 |
| Tratamentos Avulsos Laser | 26 |
| Serviços de depilação a Linha | 3 |
| Assinante Vip | 2 |
| Clube do Laser | 1 |
| Promoções | 1 |
| Serviços de Depilação a Cera Masculino | **0** |
| Serviços de Depilação a Laser Masculino | **0** |
| Esfoliação | **0** |

## Busca hoje

`https://loja.pellomenos.com.br/?s=cera` mistura produto, página e até texto de contrato. Não é o overlay do nosso `SearchPanel`.

## Conta

Login ok no painel. Display name: **company genesis**. Sem acesso a Plugins (403). Menus visíveis incluem WooCommerce, Produtos, Páginas, Modelos Elementor, Aparência, Smart Slider, Mega Main Menu. Menu Pagamentos existe — **não foi aberto**.
