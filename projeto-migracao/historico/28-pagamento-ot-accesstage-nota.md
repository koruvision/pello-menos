# 28 — Nota pagamento / Accesstage (OficialTeste, só leitura)

Data: 01/11/2026. Fonte: `.secrets/_audit_payment_ot_blacknov.json` via `scripts/_audit_payment_ot_readonly.py`.

## O que a API OT mostra

- Auth Genesis (`company-genesis`) OK; conta Hostinger **nomeada** no env (`PM_HOSTINGER_ACCOUNT`), **sem** token API/FTP no repo.
- Snippet `pm-black-nov-pricing` ativo (com `FORCE` no OT — calendário forçado para ensaio).
- Pedidos recentes trazem meta **`Pedido Accesstage`**; totais Woo na amostra são de teste (ex. `1.00`), sem cupom nas linhas.
- Plugins listáveis: Woo + CF7/CPF/reCAPTCHA; **nenhum plugin com nome Accesstage** na lista REST.

## O que só o hosting / Accesstage muda

- Miolo CF7 **#1831** e charge Accesstage **não estão no git**.
- Se o gateway ignora `total`/`cupom` Woo ou hiddens do form, o desconto da vitrine (Black Nov / labels no cart) **não** altera a cobrança — isso é alteração Accesstage + alinhamento Woo, não front.
- Overlay `pmCheckoutLoading` / shell no repo só cobrem UX até o re-submit CF7.

## Loja (contexto publish)

Sem app password admin válida na loja (`company-genesis` → `invalid_username`; `lsb` / `gerencia-admin` / `pellomenos` → senhas conhecidas falham). Bundle/snippet Black Nov **sem FORCE** ficam bloqueados até nova credencial em `loja.env`.
