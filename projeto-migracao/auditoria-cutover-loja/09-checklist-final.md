# 09 — Checklist final (gate antes do GO de execução)

Marcar só quando verificado. **Nada abaixo foi executado nesta entrega de auditoria.**

## Documentação

- [x] Pasta `auditoria-cutover-loja/` com 00–09  
- [x] Zero escrita na loja / OficialTeste nesta etapa  
- [ ] Diretoria leu o [00-resumo-executivo.md](00-resumo-executivo.md)  
- [ ] Dúvida Argobot × Accesstage respondida  
- [ ] Meio de pagamento do teste R$ 1,99 definido  

## Credenciais

- [x] `loja.env` autentica como admin (probe 30/10)  
- [x] `oficialteste.env` autentica completo  
- [ ] `loja-readonly.env` descartado ou regenerado  
- [ ] App passwords revogadas se houver suspeita de abuso (doc 21)  

## Pré-cutover técnico

- [ ] Backup arquivos + BD da loja armazenado fora do ensaio  
- [ ] Modo manutenção combinado  
- [ ] Snapshot HTML `/` e `/finalizar-pagamento/`  
- [ ] PHP 7.4 confirmado  
- [ ] CPF = `input`, form `wpcf7-f1831`  
- [ ] Code Snippets instalado (ativar no GO)  
- [ ] Produto teste R$ 1,99 existe ou criação autorizada  
- [ ] GTM ID confirmado  
- [ ] Cupom `PRIMEIRACOMPRA5` planejado  

## Durante o GO (ordem)

- [ ] Ativar Code Snippets (`plugin`)  
- [ ] Snippet rotas vazias + `bundle`  
- [ ] Rotas por fase **ou** `--all` conforme janela  
- [ ] Snippets e-mail + WCAR + plugin CA  
- [ ] Cupom Woo  
- [ ] Sync featured images (`--allow-prod`)  
- [ ] Hardening spam (sem apagar clientes)  
- [ ] Purge cache  
- [ ] Smoke GET checkout (CPF)  

## Pós-cutover

- [ ] Compra real R$ 1,99 ([07](07-plano-testes.md))  
- [ ] E-mails (disparo + inbox ou e-mail informado)  
- [ ] Carrinho qty/cupom  
- [ ] Conta login/cadastro  
- [ ] Limpeza BD/mídia só depois ([historico/18](../historico/18-limpeza-bd-pos-migracao.md))  

## Proibições (sempre)

- [ ] Não restore BD OficialTeste na loja  
- [ ] Não subir PHP para 8  
- [ ] Não editar Accesstage/CF7 miolo  
- [ ] Não apagar users com pedidos  
- [ ] Não pagar em produção sem GO de teste  

---

**Status desta entrega (30/10/2026):** documentação e plano prontos; execução **aguardando aprovação**.
