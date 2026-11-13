# WordPress da loja — só visual

Pasta para falar **somente** da loja em produção [loja.pellomenos.com.br](https://loja.pellomenos.com.br/) e de como aproximar home, catálogo, produto e busca do que já existe neste projeto Next.js.

Nada daqui é um GO para alterar o site. Qualquer mudança futura precisa de autorização explícita, em staging se possível, e **nunca** em checkout, pagamento, contratos ou dados.

## Regras

Leia `00-regras.md` antes de qualquer ideia de alteração.

## O que já foi lido (15/09/2026)

- Login somente leitura na conta `company genesis`
- Painel, temas, páginas, modelos Elementor, produtos, menus e widgets
- HTML público da home, categorias WooCommerce, busca e uma página de produto
- **Não** abri Pagamentos, configurações de checkout, nem cliquei em salvar/ativar/atualizar

## Arquivos

| Arquivo | Conteúdo |
| --- | --- |
| `00-regras.md` | O que nunca mexer |
| `01-mapa-leitura.md` | Tema, plugins, Elementor, páginas, categorias |
| `02-viabilidade-visual.md` | Como ficar parecido com o projeto com poucas mudanças |
| `03-masculino-feminino.md` | O que já existe na loja vs o que construímos aqui |
| `04-onde-mexer.md` | O que dá para fazer e em qual item do admin mexer |
| `05-pagina-produto.md` | Por que o produto parece padrão e onde mudar |
| `06-plugins.md` | Como ver plugins com esta conta (sem menu Plugins) |
| `07-diagnostico-migracao.md` | Histórico app/clone vs produção após WP-Vivid; spam e usuário `lsb` |
| `08-historico-acoes-e-risco.md` | Tudo que fizemos em produção vs clone; senha no chat vs instalação |

## Próximo passo (quando você pedir)

Escolher um recorte visual pequeno — por exemplo só a home feminina — e descrever o plano no Elementor/CSS **sem aplicar nada** até você autorizar.
