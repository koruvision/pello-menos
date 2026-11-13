# Diário do treino de migração

Ensaio de 17 de outubro de 2026. O destino `https://pellomenosoficialteste.companygenesis.com.br` faz o papel da loja oficial. A origem do front é o projeto Next exportado em `wordpress-loja/pm-home` mais o snippet `scripts/pm_home_snippet.php`, hoje publicados em `https://pellomenos.companygenesis.com.br`.

`https://loja.pellomenos.com.br` recebe só GET de leitura. Nenhum pedido é enviado em site nenhum. O PHP do destino fica em 7.4. O plugin de CPF fica ativo. DNS fica como está.

Senhas: só em `projeto-migracao/.secrets/oficialteste.env`, ignorado pelo git. O token da Hostinger segue no `.env` do projeto `stack`.

Os documentos que valiam antes deste ensaio estão em [historico/](historico/). O cronograma de segunda-feira é [historico/12-cronograma-loja-oficial.md](historico/12-cronograma-loja-oficial.md); este diário registra o que o ensaio confirmou ou mudou nele. Os testes Playwright de cada fase estão em [testes/](testes/) e as capturas em [capturas/](capturas/).

Resumo: as cinco fases passaram no destino. Dois defeitos antigos do front apareceram e foram corrigidos (número do header na página do carrinho; cores e fontes do header do checkout). Três coisas mudam no cronograma: o Code Snippets precisa ser ativado (já está instalado e inativo), o bundle precisa ser reescrito para a base da loja antes de subir, e as fases 1 e 2 vão juntas.

## Fase 0 — leitura do destino

Hora: 17/10/2026, manhã. Só GET. Credencial: senha de aplicativo lida do `.env`.

### Primeiro susto: a página pública mostrava "Hello world!"

O primeiro GET `/` devolveu o tema Twenty Twenty-Five, título igual ao domínio e o post "Hello world!", com `X-Powered-By: PHP/8.3.35`. Era cache do servidor da Hostinger guardado antes da migração e antes da troca de PHP. O mesmo GET com `?pm=fase0` na URL devolveu a loja Shopwise, título "Desconto Depilação Cera e Laser - E-commerce Pello Menos", `PHP/7.4.33`. O `/wp-admin/` também responde 200 em 7.4.33.

Lição para segunda: toda verificação depois de publicar algo usa um parâmetro novo na URL ou espera o cache do servidor expirar. Uma página "antiga" logo depois da publicação não quer dizer que o snippet falhou.

### Senha de aplicativo

"curoisrrrteste" é o nome que a senha recebeu no painel. O usuário dono dela é `company-genesis` (administrador, id 10182). Com `curoisrrrteste` como usuário o WordPress devolve `invalid_username`. O `.env` já aponta para o usuário certo.

### O que o destino é

| Sinal | Destino `pellomenosoficialteste` | Loja no ar (leitura de 17/10) |
| --- | --- | --- |
| PHP | 7.4.33 | 7.4.33 |
| WordPress | 7.1.3 | 7.1.3 |
| WooCommerce | 10.1.4 | presente |
| Tema ativo | `shopwise-child` sobre `shopwise` | igual |
| Produtos na Store API | 64 | não contado |
| Último pedido | 48214, `processing`, 17/10/2026 12:02 | — |
| `/finalizar-pagamento/` | `wpcf7-f1831` sim, `input name="cpf"` sim, `[cpf` não, `cart-number` 3, `jquery.mask` 2, `wpcf7cf` 15, reCAPTCHA sim | mesmos números |
| `/masculino/` | 404 | 404 |
| `/carrinho/`, `/minha-conta/`, `/loja/`, `/produto/axila-cera/` | 200, tema | 200, tema |
| `uploads/pm-home/` | 404 | 404 |
| `wc/store/v1/cart` | 200, carrinho vazio | existe |
| `code-snippets/v1` | 404 mesmo autenticado | 404 público |
| Plugin Code Snippets | instalado, 3.9.1, **inativo** | a confirmar no painel |
| Plugin `cpf-e-cnpj-para-contact-form-7-old` | ativo, 1.0.2 | ativo |
| Cache | plugin nenhum; há cache do servidor | LiteSpeed |

Plugins ativos no destino: Adminimize, CF7 Conditional Fields 2.6.3, Classic Editor, Contact Form 7 6.1.1, CPF e CNPJ para CF7 (old) 1.0.2, Elementor 3.5.6, Envato Market, Google Listings and Ads, Kirki, Loco Translate, Mailchimp for WP, Mega Main Menu, Meta Box, Order Import Export, Really Simple SSL, Redirection, RevSlider 6.4.6, Shopwise Core, Smart Slider 3, TI Wishlist, Variation Swatches, WooCommerce 10.1.4, Yoast 26.0, wp-analytics, WP File Manager, WP Mail SMTP, CF7 reCAPTCHA, WPForms Lite, WPvivid Backup, YITH Compare.

Inativos que importam: `code-snippets` 3.9.1, `insert-headers-and-footers`, os três da Hostinger, Akismet.

O HTML do pagamento desta leitura está em `projeto-migracao/fase0-finalizar-pagamento.html` (ignorado pelo git). É a referência da fase 5. A leitura completa em JSON está em `.secrets/fase0-leitura.json`.

### A loja no ar

`GET https://loja.pellomenos.com.br/` → 200. Nada foi enviado para lá.

### O que a fase 0 muda no cronograma

1. O cronograma dizia "No painel, ver se Code Snippets está ativo". No destino ele está instalado e inativo. A loja no ar provavelmente está igual, porque a rota pública é 404 nos dois. Na segunda, o primeiro passo depois do backup é ativar o plugin que já existe. Não é instalar plugin novo.
2. O bundle exportado hoje aponta CSS, JS e mídia para `https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home/`. No destino isso carregaria o front a partir do clone. Para o ensaio valer como treino, o bundle precisa ser reescrito com a base do destino antes de subir. Na segunda, com a base `https://loja.pellomenos.com.br/wp-content/uploads/pm-home/`.
3. O snippet do repositório faz tudo de uma vez. Para publicar um recorte por fase sem manter cinco arquivos, o snippet passa a aceitar a constante `PM_HOME_ROUTES`. Sem a constante ele se comporta como sempre; com ela, só os ramos listados ligam.

Fase 0 passou. A loja está debaixo do cache, o checkout tem o CPF como input e o WooCommerce responde.

## Preparo — plugin, snippet vazio e bundle

Ferramenta: [scripts/pm_publicar_destino.py](../scripts/pm_publicar_destino.py). Ela lê o `.env`, recusa `loja.pellomenos.com.br` sem `--permitir-loja`, e tem três comandos: `plugin` (ativa o Code Snippets que já existe), `snippet --routes=...` (cria ou atualiza o snippet `pm-home (front do projeto)` com `define('PM_HOME_ROUTES', ...)` na frente do arquivo do repositório; `--off` desativa; `--all` publica igual ao clone) e `bundle` (zipa `wordpress-loja/pm-home` trocando a base do clone pela base do destino e faz POST em `pm-home/v1/bundle`). O id do snippet fica em `.secrets/oficialteste.state.json`.

1. `plugin`: Code Snippets saiu de inativo para ativo. A rota `code-snippets/v1` passou a responder 200. O banco migrado já trazia cinco snippets da loja: quatro inativos (nomes de arquivo em minúsculas, barra de administração, smilies, ano atual) e um ativo de escopo `content`, "FAQ Schema Depilação a laser", que só roda onde o shortcode dele é usado. Ativar o plugin não ligou nada que estivesse desligado. Na segunda, confirmar os mesmos cinco na loja antes de ativar.
2. `snippet --routes=none`: snippet id 6 ativo, 5.528 caracteres, nenhuma rota ligada. Depois disso: `/` continua Shopwise, `/finalizar-pagamento/` continua com `wpcf7-f1831` e `input name="cpf"`, `pm-home/v1` aparece nos namespaces e um POST vazio em `pm-home/v1/bundle` devolve `400 pm_empty`. O snippet novo não muda página nenhuma por si só.
3. `bundle`: zip de 116,5 MB, 2.099 referências reescritas de `pellomenos.companygenesis.com.br/wp-content/uploads/pm-home` para a base do destino. Resposta `{"ok":true,"html":true,"css":true}` em 48 segundos. `uploads/pm-home/home.html` e `home.css` respondem 200.

## Fase 1 — home

Publicado: `snippet --routes=home`. Teste Playwright (`treino_fase1.py`, desktop 1280 e mobile 390) com `?pm=<timestamp>` para furar o cache.

| Verificação | Resultado |
| --- | --- |
| `GET /` | 200, PHP 7.4.33, header do projeto, header do tema ausente |
| Link do carrinho no header | 1 (2 no mobile, header e barra inferior) |
| Links `/produto/` na home | 293 ocorrências, 85 slugs distintos |
| CSS, JS, mídia | 118 referências à base do destino, zero ao clone, logo carregou, fonte Manrope aplicada |
| Erros de JS, requests falhos em `pm-home` | nenhum |
| Mobile 390 | sem rolagem horizontal |
| `/carrinho/`, `/minha-conta/`, `/loja/` | 200, header do tema, sem `pm-home` |
| `/finalizar-pagamento/` HTML cru | igual ao da fase 0 em todos os marcadores (`wpcf7-f1831`, `cpf`, `cart-number` 3, mask 2, `wpcf7cf` 15, reCAPTCHA, lista de inputs) |

Dois aprendizados:

- Comparar o pagamento pelo `page.content()` do navegador dá falso negativo: o JS do Conditional Fields acrescenta classes `wpcf7cf` depois de carregar (19 contra 15). A comparação que vale é do HTML cru, sem executar JS. O script `treino_fase1b.py` faz isso.
- Dos 85 slugs de produto que a home do projeto linka, só 30 existem com o mesmo slug no WooCommerce. Os outros 55 (`abdomen-cera`, `axilas-laser`, `buco-laser`, `plano-silver`...) dão 404 no tema enquanto a rota `produto` está desligada. Na fase 1 isolada, mais da metade dos cliques da home cai em 404. Na segunda, a fase 1 e a fase 2 têm de ser publicadas em sequência imediata, com a fase 1 durando só o tempo do teste dela.

Fase 1 passou.

## Fase 2 — ficha e masculino

Publicado: `snippet --routes=home,masculino,produto`. Carrinho e conta continuam o tema. Teste `treino_fase2.py`.

| Verificação | Resultado |
| --- | --- |
| `/masculino/` | 200, projeto, `data-audience="masculino"`, sem header do tema (antes era 404) |
| `/produto/axila-cera/` | 200, projeto, seletor de unidade e botão incluir |
| `/produto/abdomen-cera/` (slug só do projeto) | 200, projeto (na fase 1 era 404) |
| Incluir Axila – Cera em Asa Norte (`df-ano`) | aviso "adicionado à Asa Norte"; Store API: `id 12941, qty 1`; `localStorage` com `productId 2319, variationId 12941, wooKey` igual à chave da API |
| Recarregar a ficha | API mantém a linha; badge do header mostra 1 |
| `/carrinho/` do tema (fase 3 ainda desligada) | 200, header do tema, mostra a mesma Axila – Cera incluída pelo projeto |
| Remover pela tabela do carrinho do tema | API `items: []`, tema diz carrinho vazio |
| Outra unidade (`sp-sjc`) com carrinho de Asa Norte | recusada: "O carrinho é da unidade Asa Norte. Esvazie ou finalize para comprar em outra loja."; API inalterada |
| Quantidade 2 na ficha | API `qty 2` na mesma chave |
| Erros de JS | nenhum |

Os ids de produto e variação do destino são os mesmos do clone (2319 / 12941), porque os dois nasceram do mesmo banco da loja. Na segunda vale conferir um id na loja antes da fase 2 (`GET /wp-json/wc/store/v1/products/2319`).

Uma observação de comportamento, sem erro: o carrinho do projeto guarda a verdade em `localStorage` e espelha cada escrita na Store API. Ele não relê a API ao abrir. Se alguém remove um item pelo carrinho ou minicarrinho do tema, o projeto continua mostrando o item até o próximo clique nele. Isso só existe enquanto páginas do tema com carrinho ficam acessíveis (fases 2 a 4). O checkout lê o WooCommerce, então o pedido nunca leva item fantasma.

Fase 2 passou.

## Fase 3 — carrinho

Publicado: `snippet --routes=home,masculino,produto,carrinho`. Teste `treino_fase3.py` e `treino_fase3_badge.py`.

| Verificação | Resultado |
| --- | --- |
| `/carrinho/` vazio | 200, projeto, "Seu carrinho está vazio", sem header do tema |
| Incluir na ficha e abrir `/carrinho/` | mostra Axila – Cera, Asa Norte; API com a mesma linha `12941 qty 1`; link de pagamento presente |
| Número no header | fora do círculo: topo 93 < 102, direita 1269 ≥ 1260 (desktop); 89 < 98 e 379 ≥ 370 (mobile 390) |
| Recarregar | página e API mantêm a linha |
| Mais um na página do carrinho | API `qty 2`, link de pagamento some, aviso "Ajuste a quantidade" aparece |
| Menos um | API `qty 1`, link de pagamento volta |
| Remover | página diz vazio, API `items: []` |
| Mobile 390 | sem rolagem horizontal, remover zera a API |
| `/minha-conta/` | ainda o tema |
| `/finalizar-pagamento/` HTML cru | igual ao da fase 0 |
| Erros de JS | nenhum |

### O que quebrou e foi corrigido

O número do header na página do carrinho ficava parado: depois de remover o item ele continuava "1", depois de "mais um" continuava "1", e só acertava ao recarregar. Causa: `cart.js` escreve o `localStorage` e redesenha a lista, e quem pinta o número é o `product.js`, que não é avisado (o evento `storage` não dispara na mesma aba). O erro já existia no clone; o ensaio o pegou porque o teste de fase 3 olha o número depois de cada ação.

Correção em `wordpress-loja/pm-home/cart.js`: `writeCart` agora também repinta o número (`paintBadge`, mesma marcação do `product.js`). Versão `cart.js?v=cart3` em `carrinho.html` e em `scripts/export_wp_home.py`. Bundle subido de novo (116,5 MB, 200). Depois da correção: remover → nenhum número; mais um → "2" nos dois lugares (header e barra inferior), API `qty 2`.

O clone `pellomenos.companygenesis.com.br` continua com `cart.js?v=cart2`. Ele recebe a versão nova quando o bundle for publicado lá de novo; não foi feito neste ensaio.

Fase 3 passou.

## Fase 4 — conta

Publicado: `snippet --routes=home,masculino,produto,carrinho,conta`. Com `conta` ligada o snippet também inclui `uploads/pm-home/account.php` no `init` (os handlers `admin-ajax.php?action=pm_account`). Teste `treino_fase4.py`. O usuário de teste foi criado pelo formulário do projeto e apagado pela API de administração no fim; o e-mail está no JSON do teste.

| Verificação | Resultado |
| --- | --- |
| `/minha-conta/` visitante | 200, projeto, "Entrar" e "Cadastre-se", sem "Excluir conta", sem header do tema |
| Login errado | "Usuário ou senha incorretos.", continua na tela de entrar |
| Cadastro | entra na hora, saudação com o usuário, "Nenhum pedido nesta conta.", cookie `wordpress_logged_in` presente |
| Header com usuário logado | sem nome (`[data-pm-user]` = 0) na conta e na home |
| Home logado | `Cache-Control: private, no-store` (o snippet não deixa a página de quem está logado ir para o cache público) |
| Endereço | "Endereço salvo."; depois de recarregar o primeiro nome continua "Treino" |
| Sair | volta para "Entrar", cookie removido |
| Entrar de novo com o usuário criado | saudação e endereço voltam |
| `/minha-conta/lost-password/` | formulário do WooCommerce, header do tema, sem `pm-home` |
| `/wp-login.php` e `/wp-admin/` | 200, formulário do WordPress, sem `pm-home` |
| `/finalizar-pagamento/` HTML cru | igual ao da fase 0 |
| Limpeza | usuário encontrado 1, apagado (200), restantes 0 |
| Erros de JS | nenhum |

Limite deste teste: o usuário criado não tem pedidos, então a lista de pedidos foi vista só no estado vazio. Testar a lista com pedidos exige a senha de um cliente real, que este ensaio não tem, e criar pedido está fora do que se pode fazer. Na segunda, quem tiver uma conta própria com pedidos antigos faz esse clique.

Fase 4 passou.

## Fase 5 — chrome do checkout

Trava da fase conferida antes de publicar: o HTML cru de `/finalizar-pagamento/` continuava com `input name="cpf"`, sem `[cpf`, e com o JS de `cpf-e-cnpj-para-contact-form-7-old` carregando. Publicado: `snippet --routes=home,masculino,produto,carrinho,conta,shell`. Com `shell` ligada, todo GET que não é das rotas do projeto recebe `checkout-shell.js` e o CSS que esconde `header.header_wrap`, `footer.footer_dark` e `.section.bg_default`. Teste `treino_fase5.py`.

| Verificação | Resultado |
| --- | --- |
| Marcadores do HTML cru | iguais aos da fase 0 (`wpcf7-f1831`, `cpf`, `cart-number` 3, mask 2, `wpcf7cf` 15, reCAPTCHA, JS do plugin de CPF) |
| `<form ... wpcf7-f1831 ... </form>` normalizado (nonces e ids de sessão fora) | igual ao da fase 0; a única linha diferente é o `action`, que carrega o `?pm=` que o próprio teste pôs na URL |
| Inputs do formulário | mesma lista de 38 nomes: `your-name`, `your-email`, `your-phone`, `cpf`, `cep`, `cidade`, `estado`, `endereco`, `bairro`, `numero`, `complemento`, `cart`, `cartqtd`, `cart-number`, `holder`, `expiration`, `securityCode`, `cupom`, `cupomamount`, `fullvalue`, `totalamount`, `siteinstallment`, `subscribemode`, `declaracao`, `category` e os ocultos do CF7 e do Conditional Fields |
| Scripts da página | só um a mais: `uploads/pm-home/checkout-shell.js`; nenhum a menos |
| Chegando pelo carrinho do projeto com um item | header e footer do projeto montados (`#pm-shell-header`, `#pm-shell-footer`), header e footer do tema com `display: none`, formulário visível, campo de cartão presente, número 1 no carrinho do header, item do Woo na página |
| Digitar no CPF | máscara do plugin funciona: `123.456.789-09` |
| Envio | nenhum POST para CF7, formulário sem classe `sent` |
| Mobile 390 | chrome do projeto, sem rolagem horizontal, formulário visível |
| `/loja/` e `/produto-categoria/depilacao-a-cera/` com o chrome | 80 e 20 produtos visíveis; o único `.section.bg_default` escondido é o banner "Quer aproveitar as melhores ofertas", em todas as páginas |
| `/minha-conta/lost-password/` | chrome do projeto em volta do formulário do WooCommerce |
| `/wp-admin/` | 200, sem shell |
| Erros de JS | nenhum |

### O que quebrou e foi corrigido

O header do projeto no checkout saía sem cor: a faixa de benefícios transparente com texto cinza, a pílula "FEMININO" branca sobre branco (invisível), fonte de sistema no lugar da Manrope. Era igual no clone, ou seja, defeito antigo, visível na captura [capturas/fase5-pagamento-antes-shell6.png](capturas/fase5-pagamento-antes-shell6.png). Causa: o `checkout-shell.js` monta header e footer numa shadow root e carrega o `home.css` lá dentro; as variáveis da marca (`--brand-primary` etc.) estão declaradas em `:root`, que não existe dentro de uma shadow root, e as fontes vêm de classes do `<html>` das páginas exportadas, que a página do tema não tem. `@font-face` dentro da shadow root tampouco baixa arquivo.

Correção em `wordpress-loja/pm-home/checkout-shell.js`: um `<style>:host{...}</style>` com as variáveis da marca e das fontes entra antes do link do CSS, e os blocos `@font-face` do `home.css` são copiados para um `<style id="pm-shell-fonts">` no `<head>` do documento. O snippet passou a pedir `checkout-shell.js?v=shell7`. Depois: faixa `rgb(112, 0, 83)`, pílula roxa com texto branco, `document.fonts.check('12px Manrope')` verdadeiro, footer roxo com logo, links e selos — [capturas/fase5-pagamento-depois-shell7.png](capturas/fase5-pagamento-depois-shell7.png) e [capturas/fase5-pagamento-footer.png](capturas/fase5-pagamento-footer.png). O formulário continuou idêntico ao da fase 0 depois da correção (teste repetido).

Fase 5 passou.

## Volta atrás ensaiada

`snippet --off` desativa o snippet 6. Medido: 1,2 s entre o comando e `/`, `/carrinho/`, `/minha-conta/` voltarem ao tema e `/finalizar-pagamento/` ficar sem o shell. Religar com `--routes=...` levou 1,5 s. Os arquivos em `uploads/pm-home/` ficam no servidor nos dois estados; eles não fazem nada sem o snippet.

## Estado final do destino

- Snippet 6 "pm-home (front do projeto)" ativo com `PM_HOME_ROUTES = home,masculino,produto,carrinho,conta,shell`.
- `uploads/pm-home/` com o bundle de 17/10, base reescrita para o destino, `cart.js?v=cart3`, `checkout-shell.js?v=shell7`.
- Code Snippets ativo. PHP 7.4.33. Plugin de CPF ativo. Nenhum pedido criado. Nenhum produto, página ou pedido alterado. O usuário de teste da fase 4 foi apagado.
- `https://loja.pellomenos.com.br/` no fim do ensaio: 200, sem `pm-home`, sem `checkout-shell`.

## O que mudou no repositório

- `scripts/pm_home_snippet.php`: função `pm_home_route_on()` e constante opcional `PM_HOME_ROUTES`; include do `account.php` só com `conta`; shell só com `shell`; `checkout-shell.js?v=shell7`.
- `scripts/pm_publicar_destino.py`: novo, publica plugin, snippet por recorte e bundle com a base reescrita.
- `wordpress-loja/pm-home/cart.js`: repinta o número do header ao escrever o carrinho. `carrinho.html` e `scripts/export_wp_home.py` pedem `cart.js?v=cart3`.
- `wordpress-loja/pm-home/checkout-shell.js`: variáveis da marca no `:host` e `@font-face` no documento.
- `.gitignore`: `projeto-migracao/.secrets/` e `projeto-migracao/*.html`.
- O índice da pasta é [README.md](README.md). O roteiro fechado, com os comandos, é [como-publicar.md](como-publicar.md).

## Loja no visual do projeto

Em 18/10, `/loja/` nos dois sites de teste passou a ser o catálogo do app, com os filtros da home (método e feminino/masculino) e as páginas de serviços, áreas, planos, produtos, cartão presente, desejos, termos e privacidade. O detalhe está em [como-publicar.md](como-publicar.md).

## Clone atualizado em 18/10

O mesmo bundle e o mesmo `checkout-shell.js?v=shell7` foram para `https://pellomenos.companygenesis.com.br`. O snippet que já existia lá, id 9, "Home fiel: documento HTML", foi atualizado com `--all --id 9`: continua com todas as rotas ligadas e o nome antigo. Conferido na hora: `/carrinho/` pede `cart.js?v=cart3` e o número do header some ao remover (API fica vazia); `/finalizar-pagamento/` pede `shell7`, a faixa e a pílula "FEMININO" saem `rgb(112, 0, 83)` e a Manrope carrega. A loja oficial não entrou nisso.

## O que a segunda-feira ainda depende

1. Backup de arquivos e banco da loja, e modo manutenção, antes de qualquer escrita. O ensaio não cobre isso.
2. Confirmar na loja, autenticado, o que a fase 0 confirmou aqui: PHP 7.4.33, `shopwise-child`, Code Snippets instalado e inativo com os mesmos cinco snippets, o pagamento com `input name="cpf"`. O destino veio de uma cópia da loja tirada em 17/10 de manhã; qualquer mudança feita na loja depois disso não está no ensaio.
3. Uma senha de aplicativo de administrador da loja, guardada num `.env` só dela (`PM_LOJA_URL`, `PM_LOJA_USER`, `PM_LOJA_APP_PASSWORD`) e passada ao script com `--prefix PM_LOJA --permitir-loja`. Sem o `--permitir-loja` o script recusa a loja.
4. Ordem que o ensaio validou: `plugin` → `snippet --routes=none` → `bundle` → `snippet --routes=home` → teste → `--routes=home,masculino,produto` logo em seguida (fase 1 isolada deixa 55 links da home em 404) → teste → `+carrinho` → teste → `+conta` → teste → `+shell` só se o CPF continuar input → teste. Cada teste com `?pm=<novo valor>` na URL por causa do cache do servidor.
5. Os testes de cada fase estão em [testes/](testes/): `fase0_leitura.py`, `fase1_home.py`, `fase1_home_links_e_pagamento_cru.py` (vale para as fases 1 a 4; na 5 ele acusa o shell, como deve), `fase2_ficha_masculino.py`, `fase3_carrinho.py`, `fase3_carrinho_numero_header.py`, `fase4_conta.py`, `fase5_chrome_checkout.py`, `volta_atras.py`. O site testado vem de `PM_BASE` (padrão: o destino de ensaio); as saídas vão para `testes/saida/`, ignorada pelo git. Eles não enviam formulário e apagam o usuário que criam. Rodar: `python projeto-migracao/testes/fase1_home.py`.
6. Lista de pedidos da conta com pedidos reais: só alguém com conta própria na loja consegue olhar. O ensaio viu só o estado vazio.
7. Cache: a Hostinger serviu por alguns minutos a home antiga depois da troca de PHP. Depois de ligar cada rota na loja, conferir com parâmetro novo na URL e, se houver painel de cache da Hostinger ou do LiteSpeed, limpar.
8. Se qualquer teste falhar: `snippet --off` (1 segundo) e a loja volta ao tema inteira. A fase seguinte não começa.
