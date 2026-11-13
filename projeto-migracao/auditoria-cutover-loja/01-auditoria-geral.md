# 01 — Auditoria geral

## Situação dos dois ambientes (30/10/2026)

| Sinal | OficialTeste | Loja oficial |
|-------|--------------|--------------|
| URL | `https://pellomenosoficialteste.companygenesis.com.br` | `https://loja.pellomenos.com.br` |
| Nome WP | Pello Menos | Pello Menos |
| PHP (docs) | 7.4.33 (ensaio) | 7.4.33 — **não subir para 8** |
| Front `pm-home` | Presente em `uploads/pm-home/` | Ausente (`/wp-json/pm-home/v1` 404) |
| Code Snippets | **Ativo** + REST OK | **Instalado, inativo** + REST 404 |
| WCAR / `pm-wcar` | Plugin + snippet ativos | Ausente |
| Plugins (REST) | 42 | 39 |
| Produtos Woo (`X-WP-Total`) | ~80 | ~66 |
| Checkout | CF7 #1831 + shell do projeto | CF7 #1831 tema Shopwise (sem shell pm-home) |
| Auth app password admin | Completa | Completa (WP/Woo/plugins); sem rotas de publicação ainda |

Clone (`pellomenos.companygenesis.com.br`): PHP 8.x; **não** é modelo para a loja (CPF-old quebra).

## Comparação original × atualizado

### Loja “original” (antes do projeto)

- Home Elementor + Smart Slider / RevSlider + Shopwise.
- Carrinho e Minha Conta do tema Woo.
- Fichas de produto do Woo/tema.
- Pagamento: `/finalizar-pagamento/` CF7 #1831 + Accesstage (inalterado no ensaio).
- Sem `/masculino/` de catálogo do app (404 histórico).
- Sem bundle estático do Next exportado.

### OficialTeste “atualizado”

- Home/masculino/PDP/carrinho/conta = HTML estático do repositório.
- Store API + `localStorage` (`pm-cart-v1`) + identidade (`pm-identity-v1`).
- Shell de checkout (header/footer + painel) **sem** reescrever POST/CF7.
- Conta: card único Entrar|Cadastre-se; nome+telefone; pedidos guest por e-mail.
- Cupom `PRIMEIRACOMPRA5`, pop-up, WCAR (6 e-mails), CSS de e-mail, sync de featured images.
- PSI home mobile melhorado no ensaio; checkout PSI **não** otimizado de propósito.

## Diagnóstico técnico

1. A loja **já tem** o plugin Code Snippets — só precisa **ativar** (não instalar “do zero” para contornar 404 público).
2. Gap de infraestrutura na loja = exatamente o que o cutover instala: snippet `pm-home` (REST bundle), bundle zip, snippets e-mail/WCAR, plugin WCAR.
3. Gap de catálogo (80 vs 66) **não** se resolve copiando o OficialTeste inteiro: risco de preços de ensaio e SKUs de teste. Alinhar só itens aprovados (ex.: Body Splash quando P1 liberar).
4. Gateway e Accesstage estão **fora do git**; migração de front não os toca.
5. Ferramenta: `scripts/pm_publicar_destino.py` com `--prefix PM_LOJA --permitir-loja`.

## O que a auditoria **não** fez

- Não alterou loja nem OficialTeste.
- Não abriu menu Pagamentos / Accesstage no painel.
- Não enviou pedido de pagamento.
- Não validou caixa de entrada de e-mail real na loja (só planejado no doc 07).
