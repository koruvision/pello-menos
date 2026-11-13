# Cronograma da loja oficial

Leitura pública em 17 de outubro de 2026. Nenhum arquivo foi publicado em `https://loja.pellomenos.com.br`. Este documento é o plano de segunda-feira. A escrita na loja só começa com três coisas ao mesmo tempo: backup, modo manutenção e um GO explícito. Cada fase publica um recorte de [scripts/pm_home_snippet.php](../scripts/pm_home_snippet.php). Se o teste da fase falha, o snippet volta à versão anterior e a fase seguinte não começa.

O arquivo [11-migracao-em-fases.md](11-migracao-em-fases.md) numerava as fases de outro jeito. Na segunda, vale este arquivo.

O snippet do repositório, hoje, faz tudo de uma vez: home, masculino, carrinho, ficha, Minha Conta e o chrome das outras páginas. Na loja ele não entra inteiro. POST, `admin-ajax`, `wc-ajax`, `/wp-login.php` e `/wp-admin` ficam de fora em todas as versões.

## O que a loja é hoje

Pedido GET, sem login de escrita.

| Sinal | Loja `loja.pellomenos.com.br` |
| --- | --- |
| PHP | 7.4.33 |
| Servidor | LiteSpeed, Hostinger |
| WordPress | 7.1.3 |
| Tema na home | `shopwise-child` sobre `shopwise` |
| Home | Elementor, Smart Slider 3, RevSlider, Shopwise Core |
| `uploads/pm-home/home.html` | 404 |
| `checkout-shell.js` | ausente |
| `/wp-json/code-snippets/v1` | 404. No clone, com o plugin presente, a mesma rota pede login (401) |
| `/wp-json/wc/store/v1` | existe. É a API que o carrinho do projeto usa |
| `/wp-json/pm-home/v1` | não existe |
| `/masculino/` | 404 |
| `/carrinho/` | 200, tema, sem `pm-home` |
| `/minha-conta/` | 200, tema |
| `/finalizar-pagamento/` | formulário Contact Form 7 `wpcf7-f1831` |

Plugins que a home ou o pagamento carregam hoje: Contact Form 7, Conditional Fields, `cpf-e-cnpj-para-contact-form-7-old`, reCAPTCHA do CF7, WooCommerce, Elementor, Mailchimp, Mega Main Menu, RevSlider, Smart Slider 3, Shopwise Core, TI Wishlist, variation swatches, YITH Compare, wp-analytics.

O clone está em PHP 8.2.34. A loja não sobe de PHP nesta janela. No PHP 8 o plugin antigo de CPF quebra. No PHP 7.4 da loja ele está desenhando o campo.

No finalizar pagamento, hoje:

- existe `input name="cpf"`
- o shortcode `[cpf` não aparece
- `cart-number` aparece 3 vezes
- jQuery Mask aparece 2 vezes
- `wpcf7cf` aparece 15 vezes
- há reCAPTCHA

Esse campo de CPF é a trava da fase 5. O estado cru do clone não é copiado para a loja.

Namespaces públicos úteis: `wc/store/v1`, `contact-form-7/v1`, `wp/v2`. Não há namespace `code-snippets`.

## Antes da fase 1

1. Backup do arquivo e do banco da loja, guardado fora do clone.
2. Modo manutenção. O público não compra durante o ensaio.
3. Guardar o HTML de `/` e de `/finalizar-pagamento/`. O da manhã é a referência da fase 5.
4. Confirmar de novo o cabeçalho `X-Powered-By: PHP/7.4.33`.
5. Confirmar que `/finalizar-pagamento/` ainda tem `input name="cpf"`, `cart-number` e `wpcf7-f1831`.
6. No painel, ver se Code Snippets está ativo. A rota pública hoje é 404, então o plugin não está expondo a API. Com a conta de administrador, a rota autenticada tem de deixar de ser 404. Sem isso, nenhuma fase publica snippet. Não instalo plugin novo para contornar.

Carrinho, conta, ficha Woo e pagamento continuam o tema até a fase que os cita.

## Fase 1 — home

Muda só o GET `/`. O snippet faz `readfile` de `wp-content/uploads/pm-home/home.html`. O resto das URLs não entra nesse recorte: não há ramo de masculino, carrinho, produto, conta, nem `pm_home_enqueue_shell`.

O que deixa de aparecer na home: Elementor, Smart Slider 3 e RevSlider, inclusive banner novo que esteja só nessa página. O conteúdo continua no banco. Desativar o snippet devolve a home atual.

O que não muda: pedido, preço, gateway, CPF, POST do formulário, `/carrinho/`, `/minha-conta/`, ficha Woo e `/finalizar-pagamento/`.

Teste com Playwright, antes da fase 2:

- `/` abre o header do projeto: Serviços, busca, conta e carrinho.
- Um link de produto abre a ficha que ainda é do WooCommerce.
- `/finalizar-pagamento/` segue com `input name="cpf"`, `cart-number` e o formulário 1831. Nenhum botão de enviar é clicado.
- `/carrinho/` segue o carrinho do tema, sem o HTML do projeto.

Se a home nova não abrir, ou se o CPF deixar de ser input, o snippet dessa fase é desativado.

## Fase 2 — ficha e masculino

Entram `/masculino/` e `/produto/{slug}/`, por `masculino.html`, `routes.json` e `products/{slug}.html`. A URL `/masculino/`, que hoje responde 404, passa a existir.

O que muda: a ficha deixa de ser a página WooCommerce e passa a ser a do projeto. Incluir um serviço grava `localStorage` (`pm-cart-v1`) e a Store API (`add-item`, `update-item`, `remove-item`).

O que não muda: `/carrinho/` ainda é o tema. O pagamento continua o formulário 1831. O CPF continua o input da loja.

Teste, sem enviar pedido:

- Escolher unidade e incluir. A Store API, na mesma sessão, devolve essa linha.
- Recarregar a ficha ou o carrinho do tema e a linha continua na API.
- Remover pela tela do projeto, quando a fase 3 já existir, ou pela API nesta fase, até `items` vazio.
- Quantidade 2 não libera o caminho de pagamento da tela do projeto.
- Com uma unidade no carrinho, outra unidade é recusada e a API fica com a primeira.

Se a API não espelhar a tela, a fase para e o snippet volta a servir só a home.

## Fase 3 — carrinho

Entra o GET `/carrinho/`, servido por `carrinho.html`. O número do ícone fica no canto do círculo, por fora, com o brilho preso ao botão.

O que muda: a página de carrinho do tema sai da frente. Tirar um item chama `remove-item` na Store API.

O que não muda: o botão de pagamento da página só leva a `/finalizar-pagamento/`. O formulário dessa URL continua o original. Quantidade maior que 1, ou duas unidades, não mostram o link.

Teste:

- A linha incluída na fase 2 aparece na página e na Store API.
- O selo do ícone mostra a quantidade e fica fora do círculo.
- Remover a linha deixa a página vazia e a API com `items: []`.
- Quantidade 2 esconde o link Ir para o pagamento.
- Não clicar em pagar.

Se a página e a API divergirem, o ramo `/carrinho/` sai do snippet. A home e a ficha podem ficar.

## Fase 4 — conta

Entra `/minha-conta/` por `conta.html`, e o `init` inclui `uploads/pm-home/account.php`. A exceção é `/minha-conta/lost-password/`: o corpo continua o formulário do WooCommerce.

O que a tela faz: entrar, cadastrar, listar pedidos, salvar endereço de cobrança e sair, pela sessão real do WordPress (`wp_signon`, `wc_create_new_customer`). O cabeçalho não escreve o nome. Não há bloco de excluir conta.

O que não muda: a senha perdida, o pagamento e o CPF.

Teste:

- Visitante vê Entrar e Cadastre-se.
- Um cadastro de teste entra na hora, vê pedidos e salva o endereço.
- O header da conta e da home não ganha o nome.
- Sair volta à tela de visitante.
- `/minha-conta/lost-password/` continua o formulário original, com o chrome do projeto.
- A conta de teste é apagada pelo administrador. O botão de excluir não volta para a loja.

Se o cadastro não criar sessão, o ramo de conta sai do snippet.

## Fase 5 — layout do checkout

Só abre depois de reler `/finalizar-pagamento/` e ver, ainda, `input name="cpf"`, os scripts `cpf-e-cnpj-para-contact-form-7-old`, jQuery Mask, Contact Form 7, Conditional Fields e `wpcf7-f1831`.

Aí o `else` do snippet chama `pm_home_enqueue_shell`: esconde `header.header_wrap`, `footer.footer_dark` e `.section.bg_default`, e carrega `checkout-shell.js`. O HTML do formulário, os scripts de pagamento e o POST não são reescritos. O shortcode cru do clone não substitui o campo.

O que muda: o cabeçalho e o rodapé visíveis passam a ser os do projeto. A newsletter do tema some da frente.

O que não muda: campos de pessoa, endereço, cupom, cartão (`cart-number`, `holder`, `expiration`, `securityCode`, parcelas), CPF, reCAPTCHA e o action `#wpcf7-f1831-o1`.

Teste, sem clicar em enviar:

- Os nomes desses campos continuam iguais ao HTML guardado de manhã.
- O header visível é o do projeto (Serviços).
- `header.header_wrap` fica `display: none`.
- O CPF continua um input, não um shortcode.
- Se o CPF virar `[cpf`, o shell sai na hora.

O pagamento com cartão fica para uma pessoa, à mão, ainda na manutenção. Este cronograma não envia pedido.

## Volta atrás

Desativar o snippet devolve o tema em todas as URLs. A pasta `pm-home` sem o snippet não é lida pelo tema. Se o CPF ou o PHP mudarem, a volta é o backup, não só desligar o snippet.

## O que não entra na segunda

- Subir o PHP da loja para 8.
- Desativar `cpf-e-cnpj-para-contact-form-7-old`.
- Reescrever o formulário, o contrato ou o POST.
- Instalar plugin novo porque a rota de Code Snippets não apareceu.
- Apontar DNS ou restaurar o banco do clone por cima da loja.
- Usar o id 9 do snippet do clone como se fosse o id da loja.
