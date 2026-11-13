# 26 — Tintura de pelos pubianos (Black Nov)

Busca Woo (31/10/2026) em **loja** e **OficialTeste**:

- `search=tintura` → só **Realce** (sobrancelha), sem SKU de pubianos.
- `pubian` / `púbico` / `pubico` / `pelos pub` → sem produto correspondente.

**Ação no catálogo do projeto:** criado id `tintura-pelos-pubianos` em [`src/lib/data.ts`](../../src/lib/data.ts) com preço **provisório R$ 32,00** (= Realce), faixa Black Week **M (30%)**, method `cera`.

**Pendente com a Pello:** confirmar preço de tabela e criar/reativar o produto no Woo + `woo-bridge.json` (`productId` / variations). Até lá o item aparece no front do projeto, mas não sincroniza cobrança real na loja.
