# Como publicar o front

Roteiro que passou no ensaio de 17 de outubro de 2026, no site `https://pellomenosoficialteste.companygenesis.com.br`, no papel da loja oficial. A ferramenta é [scripts/pm_publicar_destino.py](../scripts/pm_publicar_destino.py). O diário com os números de cada teste é [diario.md](diario.md).

O script lê um `.env` ignorado pelo git e recusa `loja.pellomenos.com.br` sem `--permitir-loja`. As chaves são `{PREFIX}_URL`, `{PREFIX}_USER` e `{PREFIX}_APP_PASSWORD`. O prefixo padrão é `PM_OFICIALTESTE`.

```powershell
python scripts/pm_publicar_destino.py --env projeto-migracao/.secrets/oficialteste.env plugin
python scripts/pm_publicar_destino.py --env projeto-migracao/.secrets/oficialteste.env snippet --routes=none
python scripts/pm_publicar_destino.py --env projeto-migracao/.secrets/oficialteste.env bundle
python scripts/pm_publicar_destino.py --env projeto-migracao/.secrets/oficialteste.env snippet --routes=home,masculino,produto,carrinho,conta,shell
```

`plugin` ativa o Code Snippets que já está instalado. `snippet --routes=none` publica o PHP sem servir nenhuma página do projeto: só abre `POST /wp-json/pm-home/v1/bundle`. `bundle` zipa `wordpress-loja/pm-home`, troca a base `pellomenos.companygenesis.com.br/wp-content/uploads/pm-home` pela base do destino e envia o zip. O último comando liga todas as rotas de uma vez. No ensaio elas entraram uma por uma; o resultado final é o mesmo conjunto.

A constante `PM_HOME_ROUTES` no começo do snippet escolhe os ramos: `home`, `masculino`, `produto`, `carrinho`, `conta`, `shell`. Sem a constante, tudo liga. `--all` publica assim. `--off` desativa o snippet e o tema volta; no ensaio isso levou cerca de 1 segundo. `--id N` atualiza um snippet que já existe em vez de criar outro.

POST, `admin-ajax`, `wc-ajax`, `/wp-login.php` e `/wp-admin` ficam fora do snippet em qualquer rota. `/minha-conta/lost-password/` continua o WooCommerce. O HTML, os scripts e o POST de `/finalizar-pagamento/` não são reescritos: com `shell`, a página só ganha o header e o footer do projeto e esconde os do tema.

Cada conferência usa `?pm=` com um valor novo na URL. O cache do servidor da Hostinger segurou a home antiga por alguns minutos depois de uma troca de PHP; uma página velha logo depois de publicar não significa que o snippet falhou.

## O que cada fase prova

Os testes estão em [testes/](testes/). Rodam com `python projeto-migracao/testes/fase1_home.py`. Nenhum envia o formulário de pagamento. O da conta apaga o usuário que cria.

| Fase | Rotas | O teste confirma |
| --- | --- | --- |
| 0 | nenhuma | PHP 7.4, tema Shopwise, WooCommerce, `input name="cpf"`, formulário `wpcf7-f1831` |
| 1 | `home` | Header do projeto, links `/produto/`, pagamento cru igual ao HTML da fase 0 |
| 2 | `+ masculino, produto` | Incluir grava a mesma linha na Store API; recarregar mantém; outra unidade é recusada; quantidade 2 entra na API |
| 3 | `+ carrinho` | A mesma linha na página e na API, número fora do círculo, quantidade 2 sem link de pagamento, remover zera a API |
| 4 | `+ conta` | Entrar, pedidos, endereço, sair, header sem nome, senha perdida no WooCommerce |
| 5 | `+ shell` | Só se o CPF continuar `input`. Campos iguais aos da fase 0. Máscara do CPF funciona. Nenhum POST |

A home sozinha deixa em 404 os slugs que existem no projeto e não existem com o mesmo nome no WooCommerce: 55 de 85 no ensaio. Por isso `produto` entra logo depois de `home`.

## Correções que o ensaio achou

As duas já estão no repositório e foram publicadas no destino do ensaio e no clone `pellomenos.companygenesis.com.br`.

1. Número do carrinho no header. `cart.js` gravava o `localStorage` e redesenhava a lista, e o número só era pintado pelo `product.js`. Na mesma aba ele ficava parado depois de remover ou somar. `writeCart` agora também pinta o número. A página pede `cart.js?v=cart3`.
2. Cores e fontes do header no checkout. O `checkout-shell.js` monta header e footer numa shadow root. As variáveis `--brand-*` estão em `:root`, que não existe ali, e o `@font-face` de dentro da shadow root não baixa arquivo. O script passou a declarar as variáveis em `:host` e a copiar os `@font-face` para o documento. O snippet pede `checkout-shell.js?v=shell7`. As capturas estão em [capturas/](capturas/).

## Clone

O clone já tem o snippet 9, "Home fiel: documento HTML", com todas as rotas ligadas. A atualização dele é:

```powershell
python scripts/pm_publicar_destino.py --env projeto-migracao/.secrets/clone.env --prefix PM_CLONE bundle
python scripts/pm_publicar_destino.py --env projeto-migracao/.secrets/clone.env --prefix PM_CLONE snippet --all --id 9
```

`--all` não acrescenta `PM_HOME_ROUTES`, então o clone continua servindo home, ficha, masculino, carrinho, conta e o chrome do checkout. O nome do snippet 9 é mantido.

Isso foi feito em 18 de outubro de 2026. O snippet 9 seguiu ativo com o nome "Home fiel: documento HTML" e passou a pedir `checkout-shell.js?v=shell7`. O carrinho passou a pedir `cart.js?v=cart3`. Na conferência, remover o item zerou o número do header e a Store API, e a faixa do checkout saiu na cor da marca (`rgb(112, 0, 83)`), com a Manrope carregada.

## Loja no visual do projeto (18/10)

`/loja/` deixou de ser a grade do tema. A página nova do app, [src/app/loja/page.tsx](../src/app/loja/page.tsx), lista o catálogo inteiro com os filtros que a home já usava (Todos, Cera, Laser, Linha, Esfoliação) mais Produtos, Cartão Presente e Planos, e com o par Feminino/Masculino. O `home.js?v=conta4` esconde os cards pelos atributos `data-home-panel` e `data-audience`. Serviços, áreas, planos, produtos, cartão presente, desejos, termos e privacidade passam a ser as páginas do app, servidas pelo mapa `pages.json` quando a rota `loja` está ligada. `/depilacao-a-cera/` e `/depilacao-a-laser/` (e as mesmas em `/produto-categoria/`) abrem o catálogo do método. Checkout, contato, FAQ, contratos e sobre continuam o tema com o chrome.

Publicado no clone (snippet 9, todas as rotas) e no oficial de teste (rotas anteriores mais `loja`). Nos dois: filtro Laser zera a cera e deixa o laser; Masculino esconde o feminino e mostra os 54 cards masculinos mais os itens compartilhados; Linha no masculino mostra o aviso de vazio; um card de cera inclui na unidade e o carrinho mostra o número; remover zera o número. A loja oficial não entrou.
