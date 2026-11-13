# Onde mexer (e o que dá para fazer)

Menu do admin da loja. Abrir para **entender**. Não clicar em Atualizar / Publicar / Salvar.

## Resposta curta

Dá para fazer **a cara** do projeto na home, nos cards e na página de produto.  
Não dá para colar o Next.js inteiro (GSAP, overlay de busca, dois mundos masculino/feminino completos) sem catálogo masculino e sem um pouco mais de trabalho.

Você já está no primeiro lugar certo: **Páginas**.

## O que você quer × o que dá × onde

| Você quer | Dá? | Onde mexer neste menu |
| --- | --- | --- |
| Home parecer com o projeto | **Sim**, a maior parte | **Páginas → Home** (Elementor) + **Smart Slider** (hero) |
| Cores, fundo, fonte, card | **Sim**, e é o mais seguro | **Aparência → Personalizar** e CSS do tema filho (Aparência → Temas) |
| Animação da home (GSAP) | **Parcial** | Elementor na Home. Igual ao projeto = não é “pouca alteração” |
| Página de produto | **Sim**, visual | **Produtos** (conteúdo já existe; unidade já existe). Visual = CSS / Shopwise |
| Busca de produto tipo o projeto | **Parcial** | Widget na Home (Elementor). A busca `?s=` hoje é ruim |
| Feminino / masculino | **Metade** | Slider já tem os dois banners. Categorias masculinas existem **sem produto**. Página masculina é rascunho |
| Checkout / pagamento | **Não mexemos** | **Pagamentos** — nem abrir |

## Ordem para só olhar (sem salvar)

1. **Páginas** — abra a **Home** (`e-commerce-pello-menos`). É a página 571, feita no Elementor. Aqui mora o miolo da vitrine (títulos, botões, carrosséis, busca da home). Se abrir “Editar com Elementor”, só olhe e saia **sem** Atualizar.
2. **Smart Slider** (final da barra) — hero. Já tem slide feminino e masculino. Aqui não se mexe em produto nem pagamento.
3. **Aparência → Personalizar** — cores do Shopwise (já `#700053`). Tem “CSS adicional”. Não clique em Publicar.
4. **Produtos → Categorias** — vê feminino cheio e masculino/esfoliação zerados. Isso explica o limite do masculino.
5. **Mega Main Menu** — cabeçalho / toggle Ele-Ela no futuro.

## Não abrir para este assunto

- **Pagamentos**
- **WooCommerce → Configurações** (checkout mora aí)
- **WebToffee Import Export**
- **Usuários**
- Contratos, termos, privacidade (também em Páginas — não abrir para editar)

## O que cada item do seu print controla

- **Páginas** — Home, Cera, Laser, rascunho masculino. É o palco.
- **Modelos** — kits Elementor (quase vazio; a home não é um modelo, é página).
- **Produtos** — serviços da vitrine, categorias, atributo Unidade.
- **Aparência** — tema Shopwise + child, Personalizar, menus, widgets.
- **Mega Main Menu** — menu do topo.
- **Smart Slider** — banners da home.
- **WooCommerce / Análises / Marketing / TI Wishlist** — operação da loja, não o visual da home.
- **Pagamentos** — fora de escopo.

## Conclusão prática

O “tudo que você quer” de **aparência da home feminina** cabe em 3 gavetas: Páginas (Home), Smart Slider, Aparência.  
O masculino **não** cabe só nisso: falta produto nas categorias.  
A busca igual ao app é o quarto item, depois.  
Checkout não entra.
