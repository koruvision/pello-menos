# Troca oficial em fases

A loja no ar é `https://loja.pellomenos.com.br`. O ensaio é `https://pellomenos.companygenesis.com.br`. Este arquivo não autoriza a escrita na loja. A fase 0 já foi feita em 17 de outubro de 2026. As fases 1 a 4 só começam numa janela em que as vendas estejam pausadas, e cada uma para se o teste dela falhar.

O arquivo [scripts/pm_home_snippet.php](../scripts/pm_home_snippet.php) hoje faz as três trocas de uma vez: serve o HTML do projeto em home, masculino, carrinho, produto e Minha Conta, e em qualquer outro GET enfileira o chrome do checkout. Na loja isso não entra inteiro. Cada fase publica um recorte. POST, `admin-ajax`, `wc-ajax` e `/wp-admin` já ficam de fora do snippet, e isso se mantém.

## Fase 0 — feita, só leitura e clone

- Carrinho e login do clone: `09-testes-clone.md`. Os dois espelham o WooCommerce. Nenhum pedido foi enviado.
- Pagamento da loja contra o clone: `10-checkout-loja-vs-clone.md`. O miolo do formulário 1831 coincide. O CPF não. A fase 4 está travada.
- `uploads/pm-home/` segue ausente na loja (404).

## Fase 1 — pré-requisito, ainda sem trocar a vitrine

Na janela de manutenção, antes de copiar arquivo:

1. Backup completo do arquivo e do banco da loja, fora do clone.
2. Modo manutenção. O público não compra durante o ensaio.
3. Anotar de novo o PHP. Em 17 de outubro a loja estava em PHP 7.4.33 e o clone em PHP 8.2.34.
4. Confirmar que Code Snippets existe na loja. No diagnóstico de 7 de outubro a rota da API não existia na loja. Se continuar ausente, a fase 2 não tem onde pendurar o snippet.
5. Confirmar Conditional Fields ativo, porque os grupos do formulário 1831 dependem dele. Na loja, em 17 de outubro, `wpcf7cf` já aparecia 15 vezes. Não reinstalar por cima.
6. Confirmar que `cpf-e-cnpj-para-contact-form-7-old` continua ativo e que `/finalizar-pagamento/` ainda tem `input name="cpf"`. Não desativar esse plugin. Não subir o PHP para 8 nesta janela.
7. Abrir o finalizar pagamento uma vez e guardar o HTML. Se o campo CPF sumir, a janela para e o backup volta.

Nesta fase a home da loja continua o tema.

## Fase 2 — vitrine

Copiar para `wp-content/uploads/pm-home/` o conteúdo de [wordpress-loja/pm-home](pm-home). Publicar um snippet que só faz o `readfile` de:

- `/` → `home.html`
- `/masculino/` → `masculino.html`
- `/carrinho/` → `carrinho.html`
- `/produto/{slug}/` → `routes.json` ou `products/{slug}.html`

`/minha-conta/` e `/finalizar-pagamento/` não entram. O `else` que chama `pm_home_enqueue_shell` fica de fora desta versão.

Com a manutenção ainda fechada ao público, repetir no domínio da loja o roteiro de `09-testes-clone.md` para o carrinho: incluir, recarregar, remover, quantidade 2 sem link de pagamento, unidade diferente recusada, Store API vazia no fim. Se a API não espelhar a tela, desativar o snippet. A loja volta ao tema. A pasta pode ficar no disco.

## Fase 3 — conta

Incluir no snippet o ramo de `/minha-conta/` para `conta.html`, exceto `/minha-conta/lost-password/`. O `init` passa a incluir `uploads/pm-home/account.php`.

Testar entrar, cadastrar, pedidos, salvar endereço e sair. A senha perdida tem de continuar o formulário do WooCommerce. O cabeçalho não mostra o nome. Não existe bloco de excluir conta.

Conta de teste se apaga pelo administrador, não por um botão na loja. Se o login não criar sessão WordPress, desativar o snippet.

## Fase 4 — chrome do checkout, travada

Só abre quando uma leitura nova de `/finalizar-pagamento/` na loja, depois das fases 2 e 3, ainda tiver:

- `input name="cpf"`
- os scripts `cpf-e-cnpj-para-contact-form-7-old`
- `cart-number`, jQuery Mask, Contact Form 7, Conditional Fields e reCAPTCHA
- o action `#wpcf7-f1831-o1`

Aí o snippet ganha o `else` de `pm_home_enqueue_shell`: esconde `header.header_wrap`, `footer.footer_dark` e `.section.bg_default`, e carrega `checkout-shell.js`. O HTML do formulário, os scripts de pagamento e o POST não são reescritos.

O pagamento em si é testado à mão nessa janela, por uma pessoa, com a manutenção ainda no ar. Este roteiro não envia pedido. Se o CPF, o cartão ou o grupo de unidade mudarem em relação ao HTML guardado na fase 1, o snippet perde o shell e a página volta a ser só o tema.

## Volta atrás

Desativar o snippet. A loja volta a servir o tema em todas as URLs. `uploads/pm-home/` sem o snippet não é lido pelo tema. Se a fase 1 ou a 4 tiver estragado o plugin de CPF ou o PHP, a volta é o backup, não só desligar o snippet.

## O que não copiar da experiência do clone

- Não publicar o snippet inteiro de uma vez.
- Não levar o CPF cru do clone no lugar do campo que a loja já desenha.
- Não usar o id 9 do snippet do clone como se fosse o id da loja. Na loja o snippet, se passar a existir, ganha o id de lá.
- Não apontar DNS nem restaurar o banco do clone por cima da loja. O clone é cópia anterior e o PHP dele é outro.
