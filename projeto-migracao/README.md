# Projeto de migração

Pasta do ensaio feito em 17 de outubro de 2026 e do roteiro que saiu dele. O destino do ensaio foi `https://pellomenosoficialteste.companygenesis.com.br`. A loja `https://loja.pellomenos.com.br` não recebeu o front do projeto até o cutover autorizado.

## Cutover loja (auditoria 30/10/2026)

Documentação completa (somente planejamento — sem escrita na loja nesta etapa):

**[auditoria-cutover-loja/](auditoria-cutover-loja/)** — comece pelo [00-resumo-executivo.md](auditoria-cutover-loja/00-resumo-executivo.md). Relatório do cutover 30/10: [10-relatorio-execucao.md](auditoria-cutover-loja/10-relatorio-execucao.md).

## O que ler

| Arquivo | Para quê |
| --- | --- |
| [auditoria-cutover-loja/](auditoria-cutover-loja/) | Auditoria OT × loja, inventários, plano de migração e testes |
| [como-publicar.md](como-publicar.md) | O roteiro que passou: ordem dos comandos, o que cada fase prova, a loja com filtros e as duas correções do front |
| [diario.md](diario.md) | O que aconteceu em cada microfase do ensaio, com os números dos testes |
| [historico/](historico/) | Os documentos anteriores, copiados de `wordpress-loja/`. O cronograma de segunda é [historico/12-cronograma-loja-oficial.md](historico/12-cronograma-loja-oficial.md) |
| [testes/](testes/) | Playwright de cada fase. O site vem de `PM_BASE`; a saída vai para `testes/saida/` |
| [capturas/](capturas/) | Telas do ensaio, inclusive o header do checkout antes e depois da correção |

## O que não entra no git

`.secrets/` guarda as senhas de aplicativo. `fase0-finalizar-pagamento.html` é o HTML cru do pagamento, referência da fase 5. Os dois estão no `.gitignore`.
