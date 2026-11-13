# Relatório — Cera / Esfoliação / Planos Masculino (tabela Rafael)

**Data:** 26/10/2026  
**Fonte:** e-mail Supervisão Franquia → Rafael (tabela e-commerce já com desconto)  
**Escopo:** oficialteste + catálogo Next. **Loja oficial = só leitura** (não alterada).  
**Regra de preço:** valor do e-mail = preço final no site (`skipDiscount: true`; não aplicar 5% de novo).

---

## Resumo executivo

| Ação | Qtd | O quê |
|------|-----|--------|
| **Preço atualizado** | 27 | SKUs masc que já existiam no Next (cera/esfol/planos da tabela) |
| **Criados (Woo + catálogo)** | 10 | Linhas da tabela sem SKU masculino próprio |
| **Mantidos fora do e-mail (ativos)** | 2 | Antebraço e meia-nádega masc — restaurados com preço anterior |
| **Excluídos do catálogo** | 2 | Esfoliação Faixa 02 fem + masc (não existe mais no e-commerce) |
| **Fora deste escopo / intacto** | — | Laser masculino (~26 SKUs), gift cards, body splash |

Correção pós-e-mail (26/10): antebraço e meia-nádega **voltam**; Faixa 02 **sai** (fem e masc). Laser **não foi alterado**.

---

## 1. Preços aplicados (já existiam → atualizados)

Valores em R$ (e-commerce). Seed + `woo-bridge` `*-masc` (rj/spdf).

### Cera

| Tabela (e-mail) | ID catálogo | Preço |
|-----------------|-------------|-------|
| ABDOMEN | `abdomen-cera-masc` | 57,90 |
| INTERGLÚTEOS | `intergluteos-cera-masc` | 48,50 |
| AXILA | `axila-cera-masc` | 38,90 |
| BRAÇO | `bracos-cera-masc` | 74,00 |
| COSTAS | `costas-cera-masc` | 59,90 |
| COXA | `coxa-cera-masc` | 61,90 |
| FAIXA | `faixa-cera-masc` | 34,00 |
| NADEGAS | `nadegas-cera-masc` | 52,50 |
| NARIZ | `nariz-cera-masc` | 32,90 |
| 1/2 PERNA | `meia-perna-cera-masc` | 61,90 |
| PERNA INTEIRA | `perna-cera-masc` | 115,00 |
| QUEIXO | `queixo-cera-masc` | 32,90 |
| TÓRAX | `peito-cera-masc` | 49,90 |
| VIRILHA TOTAL | `virilha-cera-masc` | 88,90 |
| VIRILHA | `virilha-comum-cera-masc` | 58,90 |

### Esfoliação

| Tabela | ID | Preço |
|--------|-----|-------|
| FAIXA | `esfoliacao-faixa-masc` | 17,00 |
| BRAÇO | `esfoliacao-braco-masc` | 37,00 |
| MEIA PERNA | `esfoliacao-meia-perna-masc` | 30,95 |
| ABDOMEN | `esfoliacao-abdomen-masc` | 28,95 |
| AXILA | `esfoliacao-axilas-masc` | 19,45 |
| NADEGAS | `esfoliacao-nadegas-masc` | 26,25 |
| COXA | `esfoliacao-coxa-masc` | 30,95 |
| COSTAS | `esfoliacao-costas-masc` | 29,95 |
| PERNA INTEIRA | `esfoliacao-perna-masc` | 57,50 |
| VIRILHA | `esfoliacao-virilha-masc` | 29,45 |

### Planos (twins chrome — preço próprio, não herda feminino)

| Tabela | ID | Preço |
|--------|-----|-------|
| PLANO VIP SILVER | `plano-silver-masc` | 124,90 |
| PLANO VIP GOLD | `plano-gold-masc` | 129,90 |

---

## 2. Criados (não existiam como SKU masculino separado)

Produtos **novos** no oficialteste (Woo variável, categoria cera masculino) + seed Next + bridge.  
Woo variação = R$ 1,00 (checkout de teste); seed/bridge = preço da tabela.

| Tabela (e-mail) | ID | Woo productId | Preço | Unidades |
|-----------------|-----|---------------|-------|----------|
| BARBA | `barba-cera-masc` | 48244 | 56,90 | 13 |
| BARBA (MODELADORA) | `barba-modeladora-cera-masc` | 48258 | 74,90 | 13 |
| BIGODE | `bigode-cera-masc` | 48272 | 38,50 | 13 |
| ORELHA | `orelha-cera-masc` | 48286 | 32,90 | 13 |
| PESCOÇO | `pescoco-cera-masc` | 48300 | 32,90 | 13 |
| MAMILOS | `mamilos-cera-masc` | 48314 | 32,90 | 13 |
| SOBRANCELHA | `sobrancelha-cera-masc` | 48328 | 52,90 | 13 |
| DESIGN DE SOBRANCELHA | `design-sobrancelha-masc` | 48342 | 69,90 | 13 |
| TÓRAX + ABDÔMEN | `torax-abdomen-cera-masc` | 48356 | 89,90 | 13 |
| SACO ESCROTAL | `saco-escrotal-cera-masc` | 48370 | 58,90 | 13 |

---

## 3. Correção: restaurados vs excluídos

### 3.1 Restaurados (ativos de novo — fora do e-mail, mantidos a pedido)

| ID | Nome | Preço seed | Observação |
|----|------|------------|------------|
| `antebraco-cera-masc` | Antebraço – Cera | 38,50 | Nome antebraço (equiv. “meio braço”); bridge Woo `antebraco-cera`; skipDiscount |
| `meia-nadega-cera-masc` | Meia nádega – Cera | 27,95 | Bridge Woo `meia-nadega-cera`; de volta em `ceraAreasMasc` / cross-sell; skipDiscount |

### 3.2 Excluídos do catálogo (Faixa 02 não existe mais)

Removidos de `data.ts`, `product-copy.json`, `woo-bridge.json` (Next + WP) e `routes.json`.  
**Não** se apagou o produto Woo `faixa-cera` (compartilhado). Snapshot: `.secrets/faixa-02-purged-restore.json`.

| ID | Público | Preço seed (antes) |
|----|---------|-------------------|
| `esfoliacao-faixa-02` | feminino | 24,00 |
| `esfoliacao-faixa-02-masc` | masculino | 37,00 |

### 3.3 Laser masculino

**Intacto** — nenhum SKU laser foi removido nem teve preço alterado nesta leva (fora da tabela Rafael deste e-mail).

---

## 4. Inventário cera/esfol/planos masc (pós-correção)

**Cera:** 25 da tabela Rafael **+** antebraço + meia-nádega (= 27 no catálogo).

**Esfoliação masc (10):** faixa 01, braço, meia perna, abdomen, axila, nádegas, coxa, costas, perna inteira, virilha. (**Sem** Faixa 02.)

**Esfoliação fem:** igual, **sem** Faixa 02.

**Planos (2):** Silver 124,90 · Gold 129,90.

---

## 5. Fora do e-mail (não mexido nesta leva)

- **Laser masculino** — existe no Next; sem tabela de preço neste e-mail.
- **Gift cards / body splash** — twins chrome; inventário Woo à parte.
- **TEST_CHARGE** — checkout de teste continua R$ 1,00; seeds/bridge com preço real da tabela.

---

## 6. Arquivos de apoio

| Arquivo | Conteúdo |
|---------|----------|
| `projeto-migracao/.secrets/masc-prices-applied-report.md` | Relatório técnico da aplicação de preços |
| `projeto-migracao/.secrets/masc-cera-created-report.md` | IDs Woo dos 10 criados |
| `projeto-migracao/.secrets/masc-removed-restore.json` | Snapshot histórico (antebraço/meia-nádega já restaurados) |
| `projeto-migracao/.secrets/faixa-02-purged-restore.json` | Snapshot Faixa 02 fem+masc (para reativar se pedirem) |
| `projeto-migracao/.secrets/audit-64-fem-prices.json` | Auditoria 64 loja vs bridge feminino |

---

*Documento para apresentação interna / franquia. Atualizado após correção antebraço / meia-nádega / Faixa 02.*
