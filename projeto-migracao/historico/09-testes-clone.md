# Testes do clone em 17 de outubro de 2026

Alvo: `https://pellomenos.companygenesis.com.br`. A loja `https://loja.pellomenos.com.br` não foi escrita. Nenhum pedido foi enviado. O botão de pagar do formulário não foi clicado (`pay_submitted 0`).

A conta criada para o login, `pm.fluxo.1792209536@example.com`, foi apagada em seguida pela API de administrador do clone. A busca depois da exclusão voltou vazia.

## Carrinho

O gesto na ficha grava o `localStorage` `pm-cart-v1` e a Store API `/wp-json/wc/store/v1/cart`.

| Passo | Resultado |
| --- | --- |
| Incluir Axila – Cera, unidade Asa Norte (`df-ano`) | A tela avisou o acréscimo. A API devolveu o item `12941`, quantidade 1, chave `90b542d37eff341c71ec98736551cb62` |
| Abrir `/carrinho/` | A linha Axila estava na página. O link Ir para o pagamento apareceu (quantidade 1, uma unidade) |
| Número do ícone | Texto `1`. O selo começa acima do círculo (93 contra 102) e termina à direita dele (1269 contra 1260) |
| Recarregar `/carrinho/` | A linha continuou. A API devolveu o mesmo item e a mesma chave |
| Remover a linha | A página ficou no estado vazio. A API devolveu `items: []` |
| Segunda unidade | Com Asa Norte no carrinho, Sobrancelha – Cera em São José dos Campos (`sp-sjc`) foi recusada: “O carrinho é da unidade Asa Norte”. A API continuou só com o item 12941 |
| Esvaziar de novo | Remover a linha deixou a API vazia |
| Quantidade 2 | A API gravou quantidade 2. O link de pagamento sumiu e a página pediu para ajustar a quantidade para 1 |
| Pagamento com 1 item válido | O formulário original abriu (CF7, `cart-number`, máscara, grupos condicionais, shortcode de CPF). O header do tema ficou `display: none`. A API ainda tinha o item. Nada foi enviado |
| Limpeza | A última remoção deixou a API vazia |

O botão “Esvaziar carrinho” só é desenhado quando já existem duas unidades no mesmo carrinho. A ficha impede esse estado antes de chamar a loja. O esvaziamento que o cliente faz, e que este teste conferiu, é o botão de remover cada linha. Esse caminho zera a sessão do WooCommerce.

## Login

| Passo | Resultado |
| --- | --- |
| Visitante em `/minha-conta/` | Título Entrar e o cadastro Cadastre-se |
| Cadastro | Entrou na hora. A saudação foi `pm.fluxo.1792209536` |
| Pedidos | “Nenhum pedido nesta conta.” |
| Endereço | Salvou e, depois de recarregar, o nome continuou `Teste` |
| Cabeçalho | Nenhum nome ao lado dos ícones, na conta e na home, com a sessão aberta |
| Excluir conta | O bloco não está na página |
| Sair | Voltou a tela Entrar |
| `/minha-conta/lost-password/` | Formulário original do WooCommerce. Header do tema oculto. O menu Serviços do projeto visível |

## O que isso autoriza

No clone, o que se faz na ficha e no carrinho chega e sai da sessão WooCommerce. Entrar, cadastrar, ver pedidos, salvar endereço e sair usam o usuário real do WordPress.

Isso não autoriza a fase do checkout na loja. A leitura do formulário de pagamento está em `10-checkout-loja-vs-clone.md`.
