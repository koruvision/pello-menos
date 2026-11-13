# Masculino e feminino

No Next.js isso já está resolvido: `HomeExperience` com `audience`, tokens em `[data-audience="masculino"]` (`#1f2456` + dourado) e rotas `/` vs `/masculino`.

Na loja WordPress o feminino é o site inteiro. O masculino está **preparado pela metade** e **sem catálogo**.

## O que a loja já tem

- Smart Slider da home com slide **banner feminino** e **banner masculino** (upload 09/2026)
- Categorias WooCommerce masculinas criadas, mas com **zero produtos**
- Página Elementor rascunho **Depilação Cera Masculino** (id 17544), parada desde 2022, **não pública**
- Esfoliação também com 0 produtos

## O que falta para igualar o projeto

Visual de paleta azul dá para fazer com CSS (`body.masculino` ou página própria), copiando as variáveis de `globals.css`.

O bloqueio real não é CSS: **não há serviços masculinos publicados**. Sem atribuir/criar produtos nas categorias masculinas, qualquer home masculina fica vazia.

Isso é catálogo, não checkout — mas também **não é “só um CSS”**. Só faremos se você pedir, e nunca misturando com pagamento.

## Duas formas viáveis (depois)

**A — Duas homes (mais simples no Shopwise)**  
Home atual = feminino. Publicar/atualizar a 17544 (ou uma `/masculino/`) com os mesmos blocos Elementor, paleta azul, carrosséis das categorias masculinas. Toggle no Mega Main Menu (Ele / Ela), como o nosso header.

**B — Um site com classe no `body`**  
Um seletor muda cor e filtra vitrine. Mais perto do Next, mais frágil no Shopwise/Elementor antigo.

Recomendação: **A**, quando houver produtos masculinos na loja.

## O que não fazer

- Não publicar o rascunho 17544 agora
- Não inventar produtos masculinos sem as tabelas oficiais
- Não ligar o banner masculino a um checkout diferente
- Não usar a busca global `?s=masculino` como “departamento masculino” — hoje ela nem lista um catálogo masculino
