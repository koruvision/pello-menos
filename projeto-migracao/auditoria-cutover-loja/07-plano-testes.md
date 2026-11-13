# 07 — Plano de testes (pós-migração)

Executar **somente após** o cutover aprovado. Nesta etapa de auditoria **não** há compra nem pagamento.

## Critérios gerais de aprovação

- Fluxo completo até thank-you sem erro de front.  
- CPF continua `input` no checkout.  
- Totais do carrinho batem com qty/cupom.  
- Pedido aparece em Woo admin.  
- E-mail disparado (e, se possível, recebido).

---

## 7.1 Compra real — produto R$ 1,99

**Produto de referência no OficialTeste:** slug `produto-r-1` (id 48216), nome “Produto R$ 1,99”, price `1.99`.  
**Na loja:** confirmar existência do mesmo slug/SKU de teste **antes** de cobrar; criar só se autorizado, sem alterar preços dos demais.

### Passos

1. Acessar `https://loja.pellomenos.com.br/` (front novo).  
2. Abrir o produto R$ 1,99.  
3. Adicionar ao carrinho (unidade válida).  
4. Ver subtotal/total.  
5. Se primeira compra do e-mail de teste: aplicar `PRIMEIRACOMPRA5` (5% no carrinho).  
6. Ir a `/finalizar-pagamento/`.  
7. Preencher dados (CPF máscara OK).  
8. Pagar **somente** com meio autorizado para teste (Accesstage/sandbox conforme operação).  
9. Redirecionamento → pedido recebido (HTML projeto).  
10. Woo admin: pedido criado, status coerente, total correto.  
11. Pagamento aprovado (meta Accesstage se aplicável).  
12. E-mails (abaixo).

**Não** simular só no Store API — a compra precisa ser concluída de verdade.

---

## 7.2 E-mails

| Checagem | Critério |
|----------|----------|
| Confirmação de pedido | Disparado |
| Pagamento | Se o fluxo Woo envia |
| Conteúdo | Produto, valores, dados cliente |
| Identidade | Logo/cores do snippet e-mail |
| Entrega inbox | Se o agente não tiver acesso à caixa: informar **e-mail destinatário usado** para a diretoria conferir |

Canal: wp_mail / SMTP já da loja (não migrar SMTP do OT).

---

## 7.3 Complementares

| Área | Teste |
|------|-------|
| Conta | Cadastro (nome+telefone+e-mail+senha), login, logout |
| Senha | Lost-password Woo |
| Pedidos | Lista + detalhe (incl. guest antigo mesmo e-mail, se houver) |
| Carrinho | +qty, −qty, remove, persistência, mixed unit bloqueia pagar |
| Cupom | 5% primeira compra; recusa se já comprou; remove cupom |
| Parcelamento | Ficha × CF7 ([historico/16](../historico/16-regras-parcelamento.md)) |
| Mobile | Home, PDP, carrinho, checkout chrome |
| WCAR | Abandonar com e-mail de teste (aguardar cron; não exige no smoke imediato) |
| Pop-up | Home, 1× sessão, copy cupom |
| Imagens | Featured alinhada após sync |

---

## 7.4 Smoke técnico (sem pagar)

Antes da compra real:

1. `GET /` — header projeto.  
2. Store API `add-item`.  
3. `/carrinho/` — linha visível.  
4. `GET /finalizar-pagamento/` — `wpcf7-f1831`, `input[name=cpf]`, `cart-number`.  
5. Nenhum submit de pagamento neste smoke.
