# Páginas, checkout e conta no clone

Leitura feita em 16 de outubro de 2026 em `https://pellomenos.companygenesis.com.br`. A loja de produção não entra neste mapa. Nenhum pedido foi enviado.

## O que já é o projeto

Estas URLs saem do HTML do projeto. O tema do WordPress não desenha a página.

- `/` e a busca `/?s=`
- `/masculino/`
- `/carrinho/`
- `/produto/{slug}/`

## O que ainda abre o tema

O corpo destas páginas é o do WordPress. O cabeçalho `header.header_wrap` e o rodapé `footer.footer_dark` são o que o visual do projeto passa a cobrir. O HTML e os scripts continuam na página.

- `/finalizar-pagamento/` — formulário de pagamento. O corpo fica como está.
- `/minha-conta/` — login e cadastro. A versão do projeto substitui este miolo. As subpáginas abaixo, menos a senha perdida, também abrem essa versão.
- `/minha-conta/lost-password/` — formulário original de senha perdida. O corpo permanece; só o chrome muda.
- `/minha-conta/downloads/`, `/minha-conta/edit-address/`, `/minha-conta/edit-account/` — sem sessão, o WordPress devolve a tela de entrar. Com sessão, são Downloads, Endereços e Detalhes da conta.
- `/termos-e-condicoes/`
- `/politica-de-privacidade/`
- `/loja/`
- Menu do tema, ainda no HTML do checkout e da conta: `/depilacao-a-cera/`, `/depilacao-a-laser/`, `/assinante-vip/`, `/promocoes/`, `/yith-compare/`

`/termos/`, `/privacidade/`, `/desejos/` e `/finalizar-compra/` respondem erro no clone. O rodapé publicado aponta para `/termos-e-condicoes/` e `/politica-de-privacidade/`.

`/wp-login.php` fica fora do chrome. É a tela de acesso do WordPress, sem o header da loja.

## Scripts que o finalizar pagamento precisa

Eles ficam no `<head>` e antes do `</body>`. Esconder o header e o footer não remove esses arquivos.

O formulário depende de:

- jQuery, jQuery Migrate e jQuery Mask (`cart-number` e os outros campos mascarados)
- WooCommerce (`woocommerce.min.js`, cookie, blockUI, order attribution)
- Contact Form 7 (`contact-form-7/includes/js/index.js` e SWV)
- Conditional Fields (`cf7-conditional-fields/js/scripts.js`), que desenha os grupos de unidade
- reCAPTCHA do CF7
- O script inline da página que chama `.mask()` em `cart-number` e conduz o passo do pagamento

Também carregam, e permanecem, os scripts do tema Shopwise, Elementor, menu, comentários e o RDSDK. O `checkout-shell.js` só monta o cabeçalho e o rodapé do projeto. Não lê o formulário.

## Minha Conta, como está hoje

Visitante sem sessão vê dois formulários no corpo:

- Entrar: nome de usuário ou e-mail, senha, lembre-me, botão Acessar, link Perdeu sua senha? para `/minha-conta/lost-password/`
- Cadastre-se: e-mail, senha, botão Cadastre-se

Não há botão de excluir conta. O cabeçalho não escreve o nome de quem entrou: busca, conta e carrinho ficam iguais com ou sem sessão.

A tela nova cobre:

- entrar e sair com o usuário real da loja
- cadastrar com e-mail e senha
- pedidos e endereço de cobrança depois do login
- senha perdida continua no formulário original, com o chrome do projeto

A conferência de 17 de outubro de 2026 está em `09-testes-clone.md`. A diferença do pagamento entre a loja e o clone está em `10-checkout-loja-vs-clone.md`. A ordem da troca oficial está em `11-migracao-em-fases.md`.
