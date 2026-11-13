# 00 — Resumo executivo

**Data da auditoria:** 30/10/2026  
**Escopo desta pasta:** só documentação e planejamento. **Nenhuma** escrita em `loja.pellomenos.com.br` nem republicação no OficialTeste foi feita nesta entrega.

## Em uma frase

Queremos colocar na loja oficial o front, as automações e os códigos que já funcionam no OficialTeste, **sem** apagar clientes, pedidos, usuários administrativos, CF7 #1831 nem Accesstage.

## O que muda (superfície)

- Home, masculino, fichas de produto, carrinho, minha conta e páginas do mapa `pages.json` passam a ser o HTML do projeto (`uploads/pm-home/`), servido pelo snippet `pm-home`.
- Chrome (header/footer) no checkout e em páginas do tema, sem reescrever o formulário de pagamento.
- Estilos de e-mail Woo, recuperação de carrinho (WCAR), cupom `PRIMEIRACOMPRA5`, pop-up de primeira compra, sync de imagens destacadas alinhado ao catálogo do projeto.

## O que fica (base sagrada)

- Banco da loja: clientes, pedidos, metas de gateway/Accesstage, produtos comerciais, cupons existentes, settings Woo.
- Contas admin (incl. Genesis / `company-genesis`), estrutura administrativa.
- Contact Form 7 formulário **#1831**, Conditional Fields, CPF-old, reCAPTCHA, PHP **7.4.33**.
- Pedidos do OficialTeste **não** entram no histórico oficial (não precisam ser migrados).

## Estratégia

**Overlay**, não cópia de banco:

1. Backup da loja.  
2. Ativar Code Snippets (já instalado, hoje inativo).  
3. Publicar bundle `pm-home` + snippets (home, e-mail, WCAR) com `loja.env` + `--permitir-loja`.  
4. Instalar plugin Cart Abandonment Recovery; criar cupom se faltar.  
5. Purge de cache; smoke; só depois compra teste R$ 1,99.

Rollback rápido: desativar o snippet `pm-home` (~1 s). Rollback grave: restore do backup.

## Credenciais (nomes, sem segredos)

| Destino | Arquivo | Status probe 30/10 |
|---------|---------|---------------------|
| OficialTeste | `.secrets/oficialteste.env` (`PM_OFICIALTESTE_*`) | Completo |
| Loja | `.secrets/loja.env` (`PM_LOJA_*`) | Auth admin OK; rotas snippets/pm-home ainda 404 |
| Loja readonly | `.secrets/loja-readonly.env` | **Inválido** — não usar |

## Riscos que não podem ser esquecidos

1. Nunca restaurar o BD do OficialTeste por cima da loja.  
2. Não subir PHP da loja para 8 (quebra CPF-old).  
3. Não alterar Accesstage / miolo do CF7 “para facilitar”.  
4. Spam/posts suspeitos na loja (histórico 21) — tratar no cutover sem apagar clientes.  
5. “Argobot” não está no repositório; o gateway documentado é **Accesstage** — confirmar o nome interno.  
6. Produto de teste no OT: slug **`produto-r-1`** (R$ 1,99), não `produto-1-real`.

## Índice desta pasta

| Arquivo | Conteúdo |
|---------|----------|
| [01-auditoria-geral.md](01-auditoria-geral.md) | Ambientes e diagnóstico |
| [02-documentacao-paginas.md](02-documentacao-paginas.md) | Páginas/rotas |
| [03-inventario-plugins-integracoes.md](03-inventario-plugins-integracoes.md) | Plugins e integrações |
| [04-inventario-codigos.md](04-inventario-codigos.md) | Códigos e gambiarras |
| [05-mapeamento-dados.md](05-mapeamento-dados.md) | O que preservar / substituir |
| [06-plano-migracao.md](06-plano-migracao.md) | Cutover passo a passo |
| [07-plano-testes.md](07-plano-testes.md) | Compra, e-mails, cupom |
| [08-riscos-pendencias.md](08-riscos-pendencias.md) | Pendências e dúvidas |
| [09-checklist-final.md](09-checklist-final.md) | Gate antes do GO |

Fontes: `projeto-migracao/historico/*`, `conhecimento-checkout.md`, `como-publicar.md`, `diario.md`, probe REST 30/10.
