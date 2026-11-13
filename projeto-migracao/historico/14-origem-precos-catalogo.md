# Origem dos preços do catálogo (e-commerce)

**Data:** 26/10/2026

## Legenda das fontes

| Código | Significado |
|--------|-------------|
| `loja-store` | Espelhado da loja (`loja.pellomenos.com.br` / bridge Woo feminino legado) |
| `rafael-cera-esfol-planos` | E-mail Supervisão → Rafael (já e-commerce; `skipDiscount`) |
| `laser-masc-tabela-2026-10` | Tabela laser masc cheia; Esquenta/Black % sobre a tabela |
| `legado-catalogo` | Seed Next pré-existente (fora do e-mail Rafael) |
| `twin-chrome` | Twin `*-masc` de gift/splash/planos compartilhados |

Fora da campanha: preço exibido = `skipDiscount` ? original : `round(original × 0,95)`. Na Esquenta laser: `round(original × 0,40)` (60% OFF) / multi 65%. Checkout de teste ainda usa `TEST_CHARGE_CENTS` = R$ 1,00.

## Feminino

### Cera

| ID | Nome | Original | Exibido no site | Fonte |
|----|------|----------|-----------------|-------|
| `abdomen-cera` | Abdômen – Cera | R$ 58,00 | R$ 55,10 (de R$ 58,00) | `loja-store` |
| `antebraco-cera` | Antebraço – Cera | R$ 49,90 | R$ 47,41 (de R$ 49,90) | `loja-store` |
| `axila-cera` | Axila – Cera | R$ 33,00 | R$ 31,35 (de R$ 33,00) | `loja-store` |
| `bracos-cera` | Braços – Cera | R$ 69,90 | R$ 66,41 (de R$ 69,90) | `loja-store` |
| `buco-cera` | Buço – Cera | R$ 26,90 | R$ 25,56 (de R$ 26,90) | `loja-store` |
| `costas-cera` | Costas – Cera | R$ 55,00 | R$ 52,25 (de R$ 55,00) | `loja-store` |
| `coxa-cera` | Coxa – Cera | R$ 49,90 | R$ 47,41 (de R$ 49,90) | `loja-store` |
| `design-sobrancelha` | Design de Sobrancelha – Cera | R$ 58,50 | R$ 55,58 (de R$ 58,50) | `loja-store` |
| `design-sobrancelha-realce` | Design de Sobrancelha + Realce – Cera | R$ 78,50 | R$ 74,58 (de R$ 78,50) | `loja-store` |
| `faixa-cera` | Faixa – Cera | R$ 26,00 | R$ 24,70 (de R$ 26,00) | `loja-store` |
| `henna` | Henna | R$ 41,00 | R$ 38,95 (de R$ 41,00) | `loja-store` |
| `intergluteos-cera` | Interglúteos – Cera | R$ 32,50 | R$ 30,88 (de R$ 32,50) | `loja-store` |
| `labios-genitais-cera` | Lábios Genitais – Cera | R$ 38,50 | R$ 36,58 (de R$ 38,50) | `loja-store` |
| `meia-nadega-cera` | Meia Nádega – Cera | R$ 24,99 | R$ 23,74 (de R$ 24,99) | `loja-store` |
| `meia-perna-cera` | Meia Perna – Cera | R$ 49,90 | R$ 47,41 (de R$ 49,90) | `loja-store` |
| `nadegas-cera` | Nádegas Completas – Cera | R$ 49,90 | R$ 47,41 (de R$ 49,90) | `loja-store` |
| `nariz-cera` | Nariz – Cera | R$ 28,90 | R$ 27,46 (de R$ 28,90) | `loja-store` |
| `perna-cera` | Perna Inteira – Cera | R$ 85,90 | R$ 81,61 (de R$ 85,90) | `loja-store` |
| `queixo-cera` | Queixo – Cera | R$ 26,90 | R$ 25,56 (de R$ 26,90) | `loja-store` |
| `realce` | Realce | R$ 32,00 | R$ 30,40 (de R$ 32,00) | `loja-store` |
| `seios-cera` | Seios – Cera | R$ 27,90 | R$ 26,51 (de R$ 27,90) | `loja-store` |
| `sobrancelha-cera` | Sobrancelha – Cera | R$ 47,99 | R$ 45,59 (de R$ 47,99) | `loja-store` |
| `sobrancelha-henna` | Design de Sobrancelha + Henna Feminino | R$ 86,50 | R$ 82,18 (de R$ 86,50) | `loja-store` |
| `sobrancelha-henna-simples` | Sobrancelha Simples + Henna | R$ 83,90 | R$ 79,71 (de R$ 83,90) | `loja-store` |
| `sobrancelha-realce-cera` | Sobrancelha + Realce – Cera | R$ 75,90 | R$ 72,11 (de R$ 75,90) | `loja-store` |
| `tintura-pelos-pubianos` | Tintura de Pelos Pubianos | R$ 32,00 | R$ 30,40 (de R$ 32,00) | `loja-store` |
| `virilha-cavada-cera` | Virilha Cavada – Cera | R$ 71,00 | R$ 67,45 (de R$ 71,00) | `loja-store` |
| `virilha-cavada-faixa-cera` | Virilha Cavada + Faixa – Cera | R$ 84,00 | R$ 79,80 (de R$ 84,00) | `loja-store` |
| `virilha-cera` | Virilha Total – Cera | R$ 85,00 | R$ 80,75 (de R$ 85,00) | `loja-store` |
| `virilha-comum-cera` | Virilha Comum – Cera | R$ 38,50 | R$ 36,58 (de R$ 38,50) | `loja-store` |
| `virilha-comum-faixa-cera` | Virilha Comum + Faixa – Cera | R$ 51,50 | R$ 48,93 (de R$ 51,50) | `loja-store` |
| `virilha-modelada-cera` | Virilha Modelada – Cera | R$ 83,90 | R$ 79,71 (de R$ 83,90) | `loja-store` |

### Laser (pacote 10 sessões)

| ID | Nome | Original | Exibido no site | Fonte |
|----|------|----------|-----------------|-------|
| `abdomen-laser` | Abdômen Laser | R$ 1020,00 | R$ 969,00 (de R$ 1020,00) | `loja-store` |
| `antebraco-laser` | Antebraço Laser | R$ 1080,00 | R$ 1026,00 (de R$ 1080,00) | `loja-store` |
| `areola-laser` | Aréola Laser | R$ 380,90 | R$ 361,86 (de R$ 380,90) | `loja-store` |
| `axilas-laser` | Axilas Laser | R$ 899,90 | R$ 854,91 (de R$ 899,90) | `loja-store` |
| `bracos-laser` | Braços Inteiros Laser | R$ 1440,00 | R$ 1368,00 (de R$ 1440,00) | `loja-store` |
| `buco-laser` | Buço Laser | R$ 425,90 | R$ 404,61 (de R$ 425,90) | `loja-store` |
| `costas-laser` | Costas Laser | R$ 1495,00 | R$ 1420,25 (de R$ 1495,00) | `loja-store` |
| `coxas-laser` | Coxas Inteiras Laser | R$ 2199,90 | R$ 2089,91 (de R$ 2199,90) | `loja-store` |
| `intergluteos-laser` | Interglúteos Laser | R$ 470,00 | R$ 446,50 (de R$ 470,00) | `loja-store` |
| `meia-nadega-laser` | Meia Nádega Laser | R$ 703,00 | R$ 667,85 (de R$ 703,00) | `loja-store` |
| `meia-perna-laser` | Meia Perna Laser | R$ 2030,00 | R$ 1928,50 (de R$ 2030,00) | `loja-store` |
| `nadegas-laser` | Nádegas Laser | R$ 1230,90 | R$ 1169,36 (de R$ 1230,90) | `loja-store` |
| `nariz-laser` | Nariz Laser | R$ 340,00 | R$ 323,00 (de R$ 340,00) | `loja-store` |
| `orelhas-laser` | Orelhas Laser | R$ 439,90 | R$ 417,91 (de R$ 439,90) | `loja-store` |
| `perna-laser` | Perna Inteira Laser | R$ 4235,00 | R$ 4023,25 (de R$ 4235,00) | `loja-store` |
| `pescoco-laser` | Pescoço Laser | R$ 703,00 | R$ 667,85 (de R$ 703,00) | `loja-store` |
| `psd-g-laser` | PSD G Laser (a partir de 21 cm) | R$ 769,00 | R$ 730,55 (de R$ 769,00) | `loja-store` |
| `psd-m-laser` | PSD M Laser (até 20 cm) | R$ 495,00 | R$ 470,25 (de R$ 495,00) | `loja-store` |
| `psd-p-laser` | PSD P Laser (até 10 cm) | R$ 430,00 | R$ 408,50 (de R$ 430,00) | `loja-store` |
| `queixo-laser` | Queixo Laser | R$ 733,00 | R$ 696,35 (de R$ 733,00) | `loja-store` |
| `rosto-inteiro-laser` | Rosto Inteiro Laser (BU+QU+NZ+PSD P) | R$ 1445,00 | R$ 1372,75 (de R$ 1445,00) | `loja-store` |
| `virilha-cavada-faixa-laser` | Virilha Cavada c/ Faixa Laser | R$ 2035,00 | R$ 1933,25 (de R$ 2035,00) | `loja-store` |
| `virilha-cavada-laser` | Virilha Cavada Laser | R$ 1790,00 | R$ 1700,50 (de R$ 1790,00) | `loja-store` |
| `virilha-comum-laser` | Virilha Comum Laser | R$ 1320,00 | R$ 1254,00 (de R$ 1320,00) | `loja-store` |
| `virilha-faixa-laser` | Virilha Comum + Faixa Laser | R$ 1560,00 | R$ 1482,00 (de R$ 1560,00) | `loja-store` |
| `virilha-laser` | Virilha Total Laser | R$ 2090,00 | R$ 1985,50 (de R$ 2090,00) | `loja-store` |

### Linha

| ID | Nome | Original | Exibido no site | Fonte |
|----|------|----------|-----------------|-------|
| `buco-linha` | Buço – Linha | R$ 20,92 | R$ 19,87 (de R$ 20,92) | `loja-store` |
| `faixa-linha` | Faixa – Linha | R$ 25,50 | R$ 24,23 (de R$ 25,50) | `loja-store` |
| `queixo-linha` | Queixo – Linha | R$ 27,90 | R$ 26,51 (de R$ 27,90) | `loja-store` |

### Esfoliação

| ID | Nome | Original | Exibido no site | Fonte |
|----|------|----------|-----------------|-------|
| `esfoliacao-abdomen` | Esfoliação de abdômen | R$ 29,00 | R$ 27,55 (de R$ 29,00) | `loja-store` |
| `esfoliacao-axilas` | Esfoliação de axilas | R$ 16,50 | R$ 15,68 (de R$ 16,50) | `loja-store` |
| `esfoliacao-braco` | Esfoliação de braço | R$ 34,95 | R$ 33,20 (de R$ 34,95) | `loja-store` |
| `esfoliacao-costas` | Esfoliação de costas | R$ 27,50 | R$ 26,13 (de R$ 27,50) | `loja-store` |
| `esfoliacao-coxa` | Esfoliação de coxa | R$ 24,95 | R$ 23,70 (de R$ 24,95) | `loja-store` |
| `esfoliacao-faixa` | Esfoliação Faixa 01 | R$ 13,00 | R$ 12,35 (de R$ 13,00) | `loja-store` |
| `esfoliacao-meia-nadega` | Esfoliação de meia nádega | R$ 12,50 | R$ 11,88 (de R$ 12,50) | `loja-store` |
| `esfoliacao-meia-perna` | Esfoliação de meia perna | R$ 24,95 | R$ 23,70 (de R$ 24,95) | `loja-store` |
| `esfoliacao-meio-braco` | Esfoliação de meio braço | R$ 24,95 | R$ 23,70 (de R$ 24,95) | `loja-store` |
| `esfoliacao-nadegas` | Esfoliação de nádegas | R$ 24,95 | R$ 23,70 (de R$ 24,95) | `loja-store` |
| `esfoliacao-perna` | Esfoliação de perna inteira | R$ 42,95 | R$ 40,80 (de R$ 42,95) | `loja-store` |
| `esfoliacao-seios` | Esfoliação de seios | R$ 13,95 | R$ 13,25 (de R$ 13,95) | `loja-store` |
| `esfoliacao-virilha` | Esfoliação de virilha | R$ 19,25 | R$ 18,29 (de R$ 19,25) | `loja-store` |
| `esfoliacao-virilha-faixa` | Esfoliação de virilha + faixa | R$ 25,75 | R$ 24,46 (de R$ 25,75) | `loja-store` |

### Planos

| ID | Nome | Original | Exibido no site | Fonte |
|----|------|----------|-----------------|-------|
| `plano-clube-laser` | Clube do Laser | R$ 249,90 | R$ 249,90 | `loja-store` |
| `plano-gold` | Plano de Assinatura VIP – Gold | R$ 114,90 | R$ 114,90 | `loja-store` |
| `plano-prepago` | Pré-pago Pello Menos | R$ 344,70 | R$ 344,70 | `loja-store` |
| `plano-silver` | Plano de Assinatura VIP – Silver | R$ 109,90 | R$ 109,90 | `loja-store` |

### Cartão presente

| ID | Nome | Original | Exibido no site | Fonte |
|----|------|----------|-----------------|-------|
| `cartao-presente` | Gift Card R$ 79,99 | R$ 79,99 | R$ 79,99 | `twin-chrome` |
| `cartao-presente-160` | Gift Card R$ 160,00 | R$ 160,00 | R$ 160,00 | `twin-chrome` |
| `cartao-presente-215` | Gift Card R$ 215,00 | R$ 215,00 | R$ 215,00 | `twin-chrome` |
| `cartao-presente-290` | Gift Card R$ 290,00 | R$ 290,00 | R$ 290,00 | `twin-chrome` |

### Produtos (retail)

| ID | Nome | Original | Exibido no site | Fonte |
|----|------|----------|-----------------|-------|
| `body-splash-autentica` | Body Splash - Autêntica | R$ 85,90 | R$ 81,61 (de R$ 85,90) | `twin-chrome` |
| `body-splash-livre` | Body Splash - Livre | R$ 85,90 | R$ 81,61 (de R$ 85,90) | `twin-chrome` |
| `body-splash-marcante` | Body Splash - Marcante | R$ 85,90 | R$ 81,61 (de R$ 85,90) | `twin-chrome` |

## Masculino

### Cera

| ID | Nome | Original | Exibido no site | Fonte |
|----|------|----------|-----------------|-------|
| `abdomen-cera-masc` | Abdômen – Cera | R$ 57,90 | R$ 57,90 | `rafael-cera-esfol-planos` |
| `antebraco-cera-masc` | Antebraço – Cera | R$ 38,50 | R$ 38,50 | `legado-catalogo` |
| `axila-cera-masc` | Axila – Cera | R$ 38,90 | R$ 38,90 | `rafael-cera-esfol-planos` |
| `barba-cera-masc` | Barba – Cera | R$ 56,90 | R$ 56,90 | `rafael-cera-esfol-planos` |
| `barba-modeladora-cera-masc` | Barba Modeladora – Cera | R$ 74,90 | R$ 74,90 | `rafael-cera-esfol-planos` |
| `bigode-cera-masc` | Bigode – Cera | R$ 38,50 | R$ 38,50 | `rafael-cera-esfol-planos` |
| `bracos-cera-masc` | Braços – Cera | R$ 74,00 | R$ 74,00 | `rafael-cera-esfol-planos` |
| `costas-cera-masc` | Costas – Cera | R$ 59,90 | R$ 59,90 | `rafael-cera-esfol-planos` |
| `coxa-cera-masc` | Coxa – Cera | R$ 61,90 | R$ 61,90 | `rafael-cera-esfol-planos` |
| `design-sobrancelha-masc` | Design de Sobrancelha – Cera | R$ 69,90 | R$ 69,90 | `rafael-cera-esfol-planos` |
| `faixa-cera-masc` | Faixa – Cera | R$ 34,00 | R$ 34,00 | `rafael-cera-esfol-planos` |
| `intergluteos-cera-masc` | Interglúteos – Cera | R$ 48,50 | R$ 48,50 | `rafael-cera-esfol-planos` |
| `mamilos-cera-masc` | Mamilos – Cera | R$ 32,90 | R$ 32,90 | `rafael-cera-esfol-planos` |
| `meia-nadega-cera-masc` | Meia nádega – Cera | R$ 27,95 | R$ 27,95 | `legado-catalogo` |
| `meia-perna-cera-masc` | Meia Perna – Cera | R$ 61,90 | R$ 61,90 | `rafael-cera-esfol-planos` |
| `nadegas-cera-masc` | Nádegas – Cera | R$ 52,50 | R$ 52,50 | `rafael-cera-esfol-planos` |
| `nariz-cera-masc` | Nariz – Cera | R$ 32,90 | R$ 32,90 | `rafael-cera-esfol-planos` |
| `orelha-cera-masc` | Orelha – Cera | R$ 32,90 | R$ 32,90 | `rafael-cera-esfol-planos` |
| `peito-cera-masc` | Peito – Cera | R$ 49,90 | R$ 49,90 | `rafael-cera-esfol-planos` |
| `perna-cera-masc` | Perna Inteira – Cera | R$ 115,00 | R$ 115,00 | `rafael-cera-esfol-planos` |
| `pescoco-cera-masc` | Pescoço – Cera | R$ 32,90 | R$ 32,90 | `rafael-cera-esfol-planos` |
| `queixo-cera-masc` | Queixo – Cera | R$ 32,90 | R$ 32,90 | `rafael-cera-esfol-planos` |
| `saco-escrotal-cera-masc` | Saco Escrotal – Cera | R$ 58,90 | R$ 58,90 | `rafael-cera-esfol-planos` |
| `sobrancelha-cera-masc` | Sobrancelha – Cera | R$ 52,90 | R$ 52,90 | `rafael-cera-esfol-planos` |
| `torax-abdomen-cera-masc` | Tórax + Abdômen – Cera | R$ 89,90 | R$ 89,90 | `rafael-cera-esfol-planos` |
| `virilha-cera-masc` | Virilha Total – Cera | R$ 88,90 | R$ 88,90 | `rafael-cera-esfol-planos` |
| `virilha-comum-cera-masc` | Virilha comum – Cera | R$ 58,90 | R$ 58,90 | `rafael-cera-esfol-planos` |

### Laser (pacote 10 sessões)

| ID | Nome | Original | Exibido no site | Fonte |
|----|------|----------|-----------------|-------|
| `abdomen-laser-masc` | Abdômen Laser | R$ 1090,00 | R$ 1035,50 (de R$ 1090,00) | `laser-masc-tabela-2026-10` |
| `antebraco-laser-masc` | Antebraço Laser | R$ 1155,00 | R$ 1097,25 (de R$ 1155,00) | `laser-masc-tabela-2026-10` |
| `axilas-laser-masc` | Axila Laser | R$ 980,00 | R$ 931,00 (de R$ 980,00) | `laser-masc-tabela-2026-10` |
| `barba-laser-masc` | Barba Laser | R$ 1070,00 | R$ 1016,50 (de R$ 1070,00) | `laser-masc-tabela-2026-10` |
| `bigode-laser-masc` | Bigode Laser | R$ 505,00 | R$ 479,75 (de R$ 505,00) | `laser-masc-tabela-2026-10` |
| `bracos-laser-masc` | Braço Laser | R$ 1460,00 | R$ 1387,00 (de R$ 1460,00) | `laser-masc-tabela-2026-10` |
| `costas-laser-masc` | Costas Laser | R$ 1580,00 | R$ 1501,00 (de R$ 1580,00) | `laser-masc-tabela-2026-10` |
| `coxa-laser-masc` | Coxa Laser | R$ 2280,00 | R$ 2166,00 (de R$ 2280,00) | `laser-masc-tabela-2026-10` |
| `intergluteos-laser-masc` | Interglúteos Laser | R$ 550,00 | R$ 522,50 (de R$ 550,00) | `laser-masc-tabela-2026-10` |
| `mamilo-laser-masc` | Mamilo Laser | R$ 460,00 | R$ 437,00 (de R$ 460,00) | `laser-masc-tabela-2026-10` |
| `meia-nadega-laser-masc` | Meia Nádega Laser | R$ 780,00 | R$ 741,00 (de R$ 780,00) | `laser-masc-tabela-2026-10` |
| `meia-perna-laser-masc` | Meia Perna Laser | R$ 2115,00 | R$ 2009,25 (de R$ 2115,00) | `laser-masc-tabela-2026-10` |
| `nadegas-laser-masc` | Nádegas Laser | R$ 1310,00 | R$ 1244,50 (de R$ 1310,00) | `laser-masc-tabela-2026-10` |
| `nariz-laser-masc` | Nariz Laser | R$ 415,00 | R$ 394,25 (de R$ 415,00) | `laser-masc-tabela-2026-10` |
| `orelhas-laser-masc` | Orelhas Laser | R$ 520,00 | R$ 494,00 (de R$ 520,00) | `laser-masc-tabela-2026-10` |
| `peito-laser-masc` | Tórax Laser | R$ 1420,00 | R$ 1349,00 (de R$ 1420,00) | `laser-masc-tabela-2026-10` |
| `perna-laser-masc` | Perna Inteira Laser | R$ 4320,00 | R$ 4104,00 (de R$ 4320,00) | `laser-masc-tabela-2026-10` |
| `pescoco-laser-masc` | Pescoço Laser | R$ 780,00 | R$ 741,00 (de R$ 780,00) | `laser-masc-tabela-2026-10` |
| `psd-g-laser-masc` | PSD G Laser (a partir de 21 cm) | R$ 850,00 | R$ 807,50 (de R$ 850,00) | `laser-masc-tabela-2026-10` |
| `psd-m-laser-masc` | PSD M Laser (até 20 cm) | R$ 580,00 | R$ 551,00 (de R$ 580,00) | `laser-masc-tabela-2026-10` |
| `psd-p-laser-masc` | PSD P Laser (até 10 cm) | R$ 505,00 | R$ 479,75 (de R$ 505,00) | `laser-masc-tabela-2026-10` |
| `queixo-laser-masc` | Queixo Laser | R$ 810,00 | R$ 769,50 (de R$ 810,00) | `laser-masc-tabela-2026-10` |
| `rosto-inteiro-laser-masc` | Rosto Inteiro Laser (Barba + NZ + PSD P) | R$ 1595,00 | R$ 1515,25 (de R$ 1595,00) | `laser-masc-tabela-2026-10` |
| `torax-abdomen-laser-masc` | Tórax + Abdômen Laser | R$ 2365,00 | R$ 2246,75 (de R$ 2365,00) | `laser-masc-tabela-2026-10` |
| `virilha-laser-masc` | Virilha Laser | R$ 1399,00 | R$ 1329,05 (de R$ 1399,00) | `laser-masc-tabela-2026-10` |
| `virilha-total-laser-masc` | Virilha Total Laser | R$ 2170,00 | R$ 2061,50 (de R$ 2170,00) | `laser-masc-tabela-2026-10` |

### Esfoliação

| ID | Nome | Original | Exibido no site | Fonte |
|----|------|----------|-----------------|-------|
| `esfoliacao-abdomen-masc` | Esfoliação de abdômen | R$ 28,95 | R$ 28,95 | `rafael-cera-esfol-planos` |
| `esfoliacao-axilas-masc` | Esfoliação de axilas | R$ 19,45 | R$ 19,45 | `rafael-cera-esfol-planos` |
| `esfoliacao-braco-masc` | Esfoliação de braço | R$ 37,00 | R$ 37,00 | `rafael-cera-esfol-planos` |
| `esfoliacao-costas-masc` | Esfoliação de costas | R$ 29,95 | R$ 29,95 | `rafael-cera-esfol-planos` |
| `esfoliacao-coxa-masc` | Esfoliação de coxa | R$ 30,95 | R$ 30,95 | `rafael-cera-esfol-planos` |
| `esfoliacao-faixa-masc` | Esfoliação Faixa 01 | R$ 17,00 | R$ 17,00 | `rafael-cera-esfol-planos` |
| `esfoliacao-meia-perna-masc` | Esfoliação de meia perna | R$ 30,95 | R$ 30,95 | `rafael-cera-esfol-planos` |
| `esfoliacao-nadegas-masc` | Esfoliação de nádegas | R$ 26,25 | R$ 26,25 | `rafael-cera-esfol-planos` |
| `esfoliacao-perna-masc` | Esfoliação de perna inteira | R$ 57,50 | R$ 57,50 | `rafael-cera-esfol-planos` |
| `esfoliacao-virilha-masc` | Esfoliação de virilha | R$ 29,45 | R$ 29,45 | `rafael-cera-esfol-planos` |

### Planos

| ID | Nome | Original | Exibido no site | Fonte |
|----|------|----------|-----------------|-------|
| `plano-gold-masc` | Plano de Assinatura VIP – Gold (masc) | R$ 129,90 | R$ 129,90 | `rafael-cera-esfol-planos` |
| `plano-prepago-masc` | Pré-pago Pello Menos (masc) | R$ 344,70 | R$ 344,70 | `loja-store` |
| `plano-silver-masc` | Plano de Assinatura VIP – Silver (masc) | R$ 124,90 | R$ 124,90 | `rafael-cera-esfol-planos` |

### Cartão presente

| ID | Nome | Original | Exibido no site | Fonte |
|----|------|----------|-----------------|-------|
| `cartao-presente-160-masc` | Gift Card R$ 160,00 (masc) | R$ 160,00 | R$ 160,00 | `twin-chrome` |
| `cartao-presente-215-masc` | Gift Card R$ 215,00 (masc) | R$ 215,00 | R$ 215,00 | `twin-chrome` |
| `cartao-presente-290-masc` | Gift Card R$ 290,00 (masc) | R$ 290,00 | R$ 290,00 | `twin-chrome` |
| `cartao-presente-masc` | Gift Card R$ 79,99 (masc) | R$ 79,99 | R$ 79,99 | `twin-chrome` |

## Nota laser masculino

Base = tabela oficial (até 10 sessões). Na Esquenta: 60% OFF (1 área) / 65% (≥3). Ex.: Axila R$ 980 → R$ 392.
