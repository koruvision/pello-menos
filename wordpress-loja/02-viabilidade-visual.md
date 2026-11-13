# Viabilidade: parecer com o projeto, com pouca alteração

Objetivo: levar home, listagem, produto e busca para perto do Next.js **sem reescrever a loja** e **sem tocar em checkout**.

O Shopwise + Elementor já é uma vitrine WooCommerce. O nosso projeto é outra casca (GSAP, `data-audience`, carrosséis próprios). Dá para chegar perto no visual; animação 1:1 do GSAP na home WordPress seria a parte mais cara e a que menos vale como “pouca alteração”.

## O que já coincide

- Cor primária da loja = `#700053` (feminino deste repo)
- Hero em slider (nós: `HeroBanner`; eles: Smart Slider)
- Trilhos de produto (nós: `ProductGrid`; eles: `shopwise-product-carousel`)
- Página de produto com escolha de **unidade** (atributo WooCommerce)
- Banner masculino **já está no slider da home**, mesmo a vitrine ainda sendo feminina

## Caminho de menor risco (quando autorizar)

Trabalhar de fora para dentro. Cada camada é desfazível.

### 1. CSS do child theme (menor risco)

O `shopwise-child/style.css` está vazio. É o lugar certo para:

- Fundo `#f7f1ec`, cards arredondados, sombra igual à nossa
- Fonte Manrope + display (Cormorant) via Customizer / Fontes
- Cards da listagem e da página de produto
- Busca e arquivo `/loja/`
- **Não** estilizar `#order_review`, `form.checkout`, `.woocommerce-checkout`

Isso muda a cara sem editar HTML de página.

### 2. Home no Elementor (página 571)

Poucas seções, na ordem do `HomeExperience`:

1. Hero (já existe — Smart Slider)
2. Círculos de categoria (hoje não tem; um bloco de imagens/ícones no Elementor)
3. Filtros Cera / Laser / Linha / Esfoliação (hoje não tem; botões âncora para os carrosséis)
4. Carrosséis que já existem
5. Faixas tipo `SplitOffer` (imagem + texto + botão — Elementor já faz)
6. Busca (já tem; dá para estilizar e, depois, trocar o comportamento)

Não precisa plugin novo para essa etapa.

### 3. Listagem e produto

- Arquivo e categorias: CSS Shopwise + eventual header Elementor
- Single product: CSS no template Shopwise; **não** trocar o formulário de add to cart além de aparência
- Unidade já existe; só visual do seletor

### 4. Busca

Hoje o `?s=` é ruim (mistura contrato). Caminho leve:

1. CSS da página de resultados
2. Forçar busca só em produtos (configuração de busca / plugin já instalado, **sem** instalar nada sem pedido)
3. Overlay parecido com `SearchPanel` exigiria JS no child — só depois das etapas 1–3

## O que NÃO fazer para “parecer o Next”

- Substituir o tema Shopwise
- Embutir o Next.js na loja
- Mexer em WooCommerce Blocks de checkout
- Atualizar Elementor 3.5.6 “para ficar moderno” em produção sem staging (risco alto)

## Animação

O reveal GSAP da home (`js-reveal`) não existe no WordPress. Equivalente barato: animações nativas do Elementor / Animate.css que o Shopwise já carrega. GSAP igual ao projeto = escopo extra.

## Ordem sugerida (ainda só plano)

1. Tokens CSS no child (feminino)
2. Home 571 no Elementor
3. Cards + página de produto
4. Busca só de produtos
5. Só então masculino (`03-masculino-feminino.md`)
