# 27 — Checkout anim + imagens Drive → loja (auth)

Data: 01/11/2026.

## Feito no repo

- Overlay Finalizar Pagamento: wiring `pmCheckoutLoading` restaurado em `checkout-shell.js` / `c24`; polish (sem pulseHolding); bump `c35` / `load3` no `pm_home_snippet.php`.
- Drive pasta pai `1UMmUhjwJmyYfz8O6O-g0DpNB1Wp6GC29` (FEMININO/MASCULINO): sync 135/135; sobrancelha dedicada (cera, realce, henna, design+realce); `data.ts` aponta imagens próprias.
- Media espelhada em `wordpress-loja/pm-home/media/images/products/`.
- Script publish pronto: `scripts/_publish_loja_black_and_checkout.py` (bundle + snippet rotas + `pm-black-nov-pricing` **sem FORCE**).

## Bloqueio loja (atualizado 01/11)

- `company-genesis` / `325g` → REST **401 `invalid_username`** (user removido pós-spam; cutover 30/10 usava esse user).
- Públicos na REST: `lsb` (id 1), `gerencia-admin` (id 8). `pellomenos` responde `incorrect_password` (existe, não é author público).
- Todas as senhas conhecidas (`loja.env`, readonly, OT app×2, OT wp-admin, clone `lsb`) falham em REST e em `wp-login.php`.
- Live: `code-snippets` pasta no servidor (**403**), REST snippets/**pm-home** **404** (plugin inativo); `/uploads/pm-home/` **404** (bundle fora do ar). Home/carrinho voltaram ao tema antigo.
- Sem token Hostinger/FTP no repo → sem upload fora da REST.

Sem app password admin válida **não dá** para POST `pm-home/v1/bundle` nem PUT snippets / Black Nov (sem FORCE) em `loja.pellomenos.com.br`.

### Quando tiver senha nova

1. Atualizar `loja.env` (`PM_LOJA_USER` = `lsb` ou `gerencia-admin` + `PM_LOJA_APP_PASSWORD`).
2. Rodar:

```powershell
python scripts/_publish_loja_black_and_checkout.py
```

Reativa Code Snippets se necessário (`plugin` no `pm_publicar_destino`) antes do bundle.

## Pagamento / Genesis (read-only OT)

Relatório: `.secrets/_audit_payment_ot_blacknov.json`.

- API OT OK (`company-genesis`).
- Snippet `pm-black-nov-pricing` (#24) ativo (com FORCE no OT).
- Pedidos têm meta `Pedido Accesstage`; plugin Accesstage **não** aparece na lista WP plugins (provável mu-plugin/tema/fora da API).
- Conta Hostinger nomeada (`PM_HOSTINGER_ACCOUNT`); **sem** token API Hostinger no repo — sem FTP/API files para a loja.
- Código Accesstage/CF7 #1831 **não está no git**; charge real depende do dev do gateway + totais Woo/hiddens.
