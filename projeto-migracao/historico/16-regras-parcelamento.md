# 16 — Regras de parcelamento (vitrine × checkout)

Auditoria read-only inicial em **27 de outubro de 2026**.  
**Alinhamento da vitrine à loja** aplicado no mesmo dia (oficialteste): ficha segue os tetos do CF7 #1831 de `loja.pellomenos.com.br`.

Script de prova CF7: [`scripts/_peek_install_loja_oficial.py`](../../scripts/_peek_install_loja_oficial.py).  
KB geral: [`../conhecimento-checkout.md`](../conhecimento-checkout.md).

---

## Veredito

**Oficialteste = loja** no miolo de parcelas do CF7 #1831 (mesmas opções e 13 condições Conditional Fields).

**Fonte da verdade de pagamento:** selects do CF7 da loja.  
**Vitrine (desde o alinhamento):** mesma regra numérica — não promete Nx que o cartão da loja não oferece.

O **carrinho não calcula parcela** do total do pedido.

```text
Ficha (Nx = teto CF7 da loja) → Carrinho (só total) → CF7 selects → Accesstage (fora do repo)
```

---

## Camada 1 — Display (por produto) — alinhada à loja

### Fontes

| Arquivo | Função |
|---------|--------|
| [`src/lib/data.ts`](../../src/lib/data.ts) | `MIN_INSTALLMENT_CENTS`, `CHECKOUT_CERA_MAX_TIMES`, `CHECKOUT_DEFAULT_MAX_TIMES`, `getInstallment`, `installmentHint` |
| [`wordpress-loja/pm-home/product.js`](../../wordpress-loja/pm-home/product.js) | `installment()` (espelho) |
| [`src/components/ProductPageView.tsx`](../../src/components/ProductPageView.tsx) | exibe Nx na ficha |

**Não** usam essa fórmula: carrinho (`CartView` / `cart.js`).

### Constantes

| Constante | Valor | Significado |
|-----------|-------|-------------|
| `MIN_INSTALLMENT_CENTS` | `5000` | Parcela mínima **R$ 50,00** (piso da ficha) |
| `CHECKOUT_CERA_MAX_TIMES` | `3` | Teto CF7 `cerainstallments` (cera / esfoliação) |
| `CHECKOUT_DEFAULT_MAX_TIMES` | `10` | Teto CF7 `allinstallments` |

### Fórmula (`getInstallment`) — pós-alinhamento

```text
se method === "plano" ou "presente":
  times = 1, parcela = preço cheio

maxTimes = 3 se cera ou esfoliacao; senão 10
byFloor = max(1, floor(preço / 5000))
times = min(maxTimes, byFloor)
parcela = ceil(preço / times)
```

### Por `method` na vitrine (= checkout loja)

| Method | Máx. na ficha | Select CF7 correspondente |
|--------|---------------|---------------------------|
| laser / linha / produto | até 10x (piso R$ 50) | `allinstallments` |
| cera | até **3x** (piso R$ 50) | `cerainstallments` |
| esfoliacao | até **3x** (piso R$ 50) | `cerainstallments` (grupo `productcera`) |
| plano | **1x** | `installments` |
| presente | **1x** | fluxo à vista / subscribe |

---

## Camada 2 — Checkout (inalterado; = loja)

| Campo CF7 | Opções | Quando |
|-----------|--------|--------|
| `allinstallments` | 1x–**10x** | `nosubscribe` + não-cera-feminino |
| `cerainstallments` | 1x–**3x** | `productcera` (cera feminino / esfoliação / clareamento + `fullvalue=1`) |
| `installments` | só **1x** | `subscribe` / `siteinstallment=0` |
| `siteinstallment` | forçado `1` pelo shell | liga parcelamento e-commerce |

`checkout-shell` **não** recalcula teto; só UI.  
`fullvalue` / `totalamount` = totais Woo, não Nx.

**Prova oficialteste = loja:** `CONDITIONS_EQUAL True` (`_peek_install_loja_oficial.py`).

---

## O que ainda depende da diretoria

Itens que a loja **não** deixa 100% claros só pelo HTML (não alterados neste alinhamento):

1. Cera masculina: a condição CF7 cita categoria *“Cera Feminino”* — masculino pode cair em 10x. Confirmar teto desejado.
2. Esfoliação/clareamento a 3x: é intencional?
3. Piso R$ 50: a ficha aplica; o select da loja **não** remove opções “impossíveis”. Filtrar no shell?
4. Mix cera+laser no mesmo carrinho: qual select/teto vale?
5. Accesstage: teto real do adquirente?

---

## Histórico da mudança de display (27/10/2026)

| Antes (vitrine) | Depois (alinhado à loja) |
|-----------------|--------------------------|
| Cera até 10x se ≥ R$ 180 | Cera até **3x** |
| Esfoliação até 10x | Esfoliação até **3x** |
| Presente podia Nx no Next | Presente **1x** |
| Hint “10x só acima de R$ 180” | Hint “até 3x” (cera/esfoliação) |

CF7 e Accesstage **não** foram alterados.

---

## Referências

- `src/lib/data.ts` — fórmula e hints  
- `wordpress-loja/pm-home/product.js` — espelho WP  
- `wordpress-loja/pm-home/checkout-shell.js` — `ensureInstallmentsUi`  
- [`../conhecimento-checkout.md`](../conhecimento-checkout.md)  
- [`10-checkout-loja-vs-clone.md`](10-checkout-loja-vs-clone.md)

*Última atualização: 27/10/2026 — vitrine alinhada aos tetos CF7 da loja; dúvidas de negócio listadas para diretoria.*
