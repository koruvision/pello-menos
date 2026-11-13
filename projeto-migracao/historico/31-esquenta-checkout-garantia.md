# 31 — Esquenta: tabela + desconto até Woo/CF7 (OT)

## Spec travada
- Esquenta 03–21/11: laser 60%/65% (≥3); cera+esf 15%/20% (≥3); % sobre tabela.
- `blackWeekStart` corrigido para **2026-11-23**.

## O que foi garantido no OficialTeste
- Snippet PHP `pm-black-nov-pricing` com `FORCE=esquenta`: Store API aplica `set_price` sobre tabela (incl. `skipDiscount` ÷0,95 via cart-related).
- SKUs ensaio R$ 5,00 (`pm-teste-esquenta-laser*`, `pm-teste-esquenta-cera*`, visibility hidden): smoke OK
  - 1 laser → **R$ 2,00** (60%)
  - 3 lasers → **R$ 5,25** (65%)
  - 1 cera → **R$ 4,25** (15%)
  - 3 ceras → **R$ 12,00** (20%)
- Shell `checkout-shell-c24.js?v=c37`: painel mostra tabela riscada + sale Esquenta; hiddens `fullvalue`/`totalamount` = **2.00** alinhados à UI (**200** centavos) no checkout.
- Guard de submit: bloqueia se UI ↔ Woo divergirem >1 centavo.

## Accesstage / CF7 #1831
- Form tem hiddens `totalamount`/`fullvalue` (preenchidos pelo shell).
- REST CF7 reportou `demo_mode: true` no feedback durante automação.
- Tentativa de charge Playwright com cartão de ensaio: validação CF7 / demo mode impediu concluir `mail_sent` de forma fiável (campo `unit` + fluxo multi-step).
- Pedidos recentes OT continuam em totais de teste (R$1 / R$1,99) com meta `Pedido Accesstage`.
- Pedido **#48504** (após ensaio): linha `PM Teste Esquenta Laser A` com total Woo **5.00** (tabela) + meta Accesstage — sugere path que **não** persistiu o `set_price` Esquenta no pedido (ou charge em fase/FORCE inconsistente). Contrasta com Store API smoke em que o mesmo SKU fica **2.00**.
- **Conclusão:** paridade UI↔Woo Store API↔hiddens `totalamount=2.00` está no ar no checkout; persistência no pedido Accesstage/`demo_mode` CF7 ainda exige GO no gateway (fora do git — [28](28-pagamento-ot-accesstage-nota.md)).

## Publish
- OT: bundle + shell c37 + black-nov FORCE esquenta (ensaio).
- Ao fechar a leva: `FORCE` vazio (calendário real a partir de 03/11).
- Loja: manutenção intacta; assets/snippet **sem** FORCE; sem compra de cartão.
