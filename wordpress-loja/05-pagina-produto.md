# Página de produto (quando clica no item)

Parece padrão porque **é padrão**. Não é a Home no Elementor.

Ao clicar, o WooCommerce abre `/produto/...` com o template do tema Shopwise (`product-template-default`). O Elementor só aplica o kit global de cor; **não monta o layout** dessa tela.

## Onde NÃO está

- **Páginas** — a Home é página; o produto não
- **Modelos** Elementor — não há template de produto na biblioteca
- Editar o produto em **Produtos** — muda nome, foto, texto e preço, **não** a casca da página

## Onde mexer (do mais seguro ao mais fundo)

| Onde | O que muda | Risco |
| --- | --- | --- |
| **Produtos → o item** | Foto, título, descrição, preço, atributo Unidade | Baixo, mas não muda o visual da página |
| **Aparência → Personalizar → CSS adicional** (ou `shopwise-child/style.css`) | Cara: imagem, título, botão, abas, relacionados | Baixo, desfazível |
| **Aparência → Personalizar** (WooCommerce / Shopwise, se aparecer) | Galeria, abas, produtos relacionados | Médio — não publicar sem olhar |
| Copiar template WooCommerce no child theme | Layout igual ao nosso `ProductPageView` | Alto em produção; só com autorização e staging |
| Elementor Pro “Theme Builder → Single Product” | Redesign visual completo | **Não vimos Elementor Pro** nesta loja |

Checkout / botão de pagamento / `form.checkout`: **não mexer**. Estilizar o bloco “Unidade + Adicionar ao carrinho” na página do produto é visual; o fluxo depois do carrinho continua proibido.

## O que a tela tem hoje

- Foto + título + preço Shopwise
- Formulário de variação **Unidade** (`pa_unidade`) — o mesmo papel do seletor do nosso projeto
- Abas WooCommerce (Descrição, Informação adicional, Avaliações)
- Relacionados padrão
- Wishlist / compare (plugins)

## Equivalente no nosso projeto

`ProductPageView`: foto grande, título display, preço, seletor de unidade, quantidade, adicionar ao carrinho, “outros serviços”.

Na loja dá para chegar perto com **CSS** (e, se um dia autorizar, um override no child). Não é abrir a Home no Elementor e arrastar blocos.

## Primeiro passo desta tela (quando autorizar)

Só CSS no child: card da foto, tipografia, botão vinho, esconder ruído (compare, abas vazias) se fizer sentido. Sem PHP, sem checkout, sem publicar rascunho.
