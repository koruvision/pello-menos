# 37 — Inventário unidades × AccesStage

Data: 2026-11-03. Fontes: `storeUnits` (data.ts), `shopwise-child/functions.php` no OficialTeste (Hostinger), CF7 #1831 loja+OT.

## Resumo

- **Unidades no catálogo front (`storeUnits`)**: 36
- **Slugs com token AccesStage (OT `$api`+`$apikey`)**: 44 — todos com o par completo
- **CF7 `unit` loja**: 38 opções | **`easyunit` (laser) loja**: 15
- **CF7 `unit` OT**: 38 | **`easyunit` OT**: 15
- **storeUnits sem token AccesStage**: 0
- **Slugs AccesStage fora do storeUnits**: 8

### Tokens na loja vs OT

A conta Hostinger `u956483026` só serve o **OficialTeste** (`pellomenosoficialteste.companygenesis.com.br`). Tentativas em `loja.pellomenos.com.br` / `pellomenos.com.br` retornam 404 — a loja **não** está nessa conta Files API.

Tokens AccesStage (`$api` + `$apikey`, 44 slugs) foram lidos do child theme OT. Na prática o checkout da loja usa o mesmo padrão `payment_CF7` + CF7 **#1831**: nesta data os selects **`unit` e `easyunit` da loja e do OT são idênticos** (38 + 15 opções; diff vazio). Todos os 38 slugs do CF7 `unit` da loja existem no mapa de tokens do OT.

**Atenção (checkout):** SJM (`saojoaomeriti`) está no front (`storeUnits`) e tem token, mas **não** aparece no select CF7 `unit` — pagamento dessa unidade pode falhar ou cair em outro slug se o shell não preencher `easyunit`/`unit` corretamente.

## storeUnits × AccesStage × CF7

| Código | Nome | UF | Capacidade | Slug AccesStage | Token | CF7 unit loja | CF7 easyunit loja |
|---|---|---|---|---|---|---|---|
| APE | Tijuca — Afonso Pena | RJ | cera♀ | `afonsopena` | sim | sim | não |
| BON | Bonsucesso | RJ | cera♀ | `bonsucesso` | sim | sim | não |
| CAX | Duque de Caxias | RJ | cera♀ | `caxias` | sim | sim | não |
| CGR2 | Campo Grande | RJ | cera♀ | `campogrande` | sim | sim | não |
| DF-ASU | Asa Sul | DF | cera♀ | `asasul` | sim | sim | não |
| DF-ANO | Asa Norte | DF | cera♀ | `asanorte` | sim | sim | não |
| LEB2 | Leblon | RJ | cera♀ | `leblon2` | sim | sim | não |
| MAD | Madureira | RJ | cera♀ | `madureira` | sim | sim | não |
| MEI | Méier | RJ | cera♀ | `meier` | sim | sim | não |
| SNP | Tijuca — Saens Peña | RJ | cera♀ | `saenspena` | sim | sim | não |
| SJM | São João de Meriti | RJ | cera♀ | `saojoaomeriti` | sim | não | não |
| SJO | Centro — Rua São José | RJ | cera♀ | `saojose` | sim | sim | não |
| TON | Copacabana I — Barata Ribeiro | RJ | cera♀ | `copacabana1` | sim | sim | não |
| IPA | Ipanema | RJ | cera♀ | `ipanema` | sim | sim | não |
| NIG | Nova Iguaçu I | RJ | cera♀ | `novaiguacu` | sim | sim | não |
| 13M | Centro — Treze de Maio | RJ | cera♀ | `trezemaio` | sim | sim | não |
| REC | Recreio dos Bandeirantes | RJ | cera♀, laser♀, cera♂ | `recreio` | sim | sim | não |
| SP-AUG | Rua Augusta | SP | cera♀, cera♂ | `augusta` | sim | sim | não |
| SP-AVP | Avenida Paulista | SP | cera♀, cera♂ | `paulista` | sim | sim | não |
| CEN | Centro — Gonçalves Dias | RJ | cera♀, laser♀ | `goncalvesdias` | sim | sim | sim |
| NIL | Nilópolis | RJ | cera♀, laser♀ | `nilopolis` | sim | sim | não |
| LMA | Largo do Machado | RJ | cera♀, laser♀ | `largomachado` | sim | sim | sim |
| SP-SJC | São José dos Campos | SP | cera♀, laser♀ | `saojosecampos` | sim | sim | sim |
| PET | Petrópolis | RJ | cera♀, laser♀ | `petropolis` | sim | sim | sim |
| IG02 | Ilha do Governador II | RJ | cera♀, laser♀ | `ilhagovernador2` | sim | sim | sim |
| HUT | Humaitá | RJ | cera♀, laser♀ | `humaita` | sim | sim | sim |
| URG | Tijuca — Uruguai | RJ | cera♀, laser♀, cera♂, laser♂ | `uruguai` | sim | sim | sim |
| BAN | Bangu | RJ | cera♀, laser♀, cera♂, laser♂ | `bangu` | sim | sim | sim |
| BOT | Botafogo | RJ | cera♀, laser♀, cera♂, laser♂ | `botafogo` | sim | sim | sim |
| COPA-2 | Copacabana II | RJ | cera♀, laser♀, cera♂, laser♂ | `copacabana2` | sim | sim | sim |
| EBA | Estrada dos Bandeirantes | RJ | cera♀, laser♀, cera♂, laser♂ | `estradabandeirantes` | sim | sim | sim |
| FLA | Flamengo | RJ | cera♀, laser♀, cera♂, laser♂ | `flamengo` | sim | sim | não |
| FRE | Jacarepaguá — Freguesia | RJ | cera♀, laser♀, cera♂, laser♂ | `freguesia` | sim | sim | sim |
| ICA | Icaraí | RJ | cera♀, laser♀, cera♂, laser♂ | `icarai` | sim | sim | sim |
| LBI | Largo do Bicão | RJ | cera♀, laser♀, cera♂, laser♂ | `largobicao` | sim | sim | sim |
| NIG2 | Nova Iguaçu II | RJ | cera♀, laser♀, cera♂, laser♂ | `novaiguacu2` | sim | sim | sim |

## Gaps

### AccesStage com token, mas fora do `storeUnits` (front não vende)

- `cabofrio` — CF7 loja: unit
- `camposgoytacazes` — CF7 loja: unit
- `jundiai` — CF7 loja: não aparece no CF7 loja
- `niteroi` — CF7 loja: não aparece no CF7 loja
- `olegario` — CF7 loja: unit
- `parkshopping` — CF7 loja: não aparece no CF7 loja
- `rjsaojose` — CF7 loja: não aparece no CF7 loja
- `saogoncalo` — CF7 loja: não aparece no CF7 loja

### storeUnits sem token

- (nenhum — todos os códigos do catálogo têm par api+apikey no OT)

### storeUnits ausentes do select CF7 `unit` da loja

- SJM → `saojoaomeriti`

### Diff CF7 unit loja vs OT

- Só loja: (vazio)
- Só OT: (vazio)

### Diff CF7 easyunit loja vs OT

- Só loja: (vazio)
- Só OT: (vazio)

## CF7 `unit` (loja) — lista completa

- `largobicao` — RJ - Largo do Bicão — token OK
- `bangu` — RJ - Bangu — token OK
- `botafogo` — RJ - Botafogo — token OK
- `humaita` — RJ - Humaitá — token OK
- `saojosecampos` — SP - Interior - São José dos Campos — token OK
- `ipanema` — RJ - Ipanema — token OK
- `olegario` — RJ - Barra da Tijuca - Av. Olegário Maciel — token OK
- `ilhagovernador2` — RJ - Ilha do Governador II - Estrada do Galeão — token OK
- `uruguai` — RJ - Tijuca - Rua Uruguai — token OK
- `nilopolis` — RJ - Nilópolis — token OK
- `freguesia` — RJ - Jacarepaguá - Largo da Freguesia — token OK
- `largomachado` — RJ - Largo do Machado — token OK
- `copacabana1` — RJ - Copacabana I - Av. Barata Ribeiro — token OK
- `copacabana2` — RJ - Copacabana II - Av. N. S. Copacabana — token OK
- `paulista` — SP - Capital - Av. Paulista — token OK
- `saojose` — RJ - Centro - Rua São José — token OK
- `saenspena` — RJ - Tijuca - Praça Saens Pena — token OK
- `campogrande` — RJ - Campo Grande — token OK
- `petropolis` — RJ - Região Serra - Petrópolis — token OK
- `goncalvesdias` — RJ - Centro - Rua Gonçalves Dias — token OK
- `meier` — RJ - Méier — token OK
- `bonsucesso` — RJ - Bonsucesso — token OK
- `asasul` — DF - Asa Sul — token OK
- `asanorte` — DF - Asa Norte — token OK
- `recreio` — RJ - Recreio dos Bandeirantes — token OK
- `novaiguacu2` — RJ - Nova Iguaçu II - Ao lado TOP Shopping Nova Iguaçu — token OK
- `cabofrio` — RJ - Região dos Lagos - Cabo Frio — token OK
- `caxias` — RJ - Duque de Caxias — token OK
- `novaiguacu` — RJ - Nova Iguaçu I - Rua Otávio Tarquino — token OK
- `estradabandeirantes` — RJ - Estrada Bandeirantes - Crystal Mall — token OK
- `icarai` — RJ - Icaraí — token OK
- `madureira` — RJ - Madureira — token OK
- `camposgoytacazes` — RJ - Interior - Campos dos Goytacazes — token OK
- `leblon2` — RJ - Leblon — token OK
- `flamengo` — RJ - Flamengo — token OK
- `trezemaio` — RJ - Centro - Rua Treze de Maio — token OK
- `afonsopena` — RJ - Tijuca - Afonso Pena — token OK
- `augusta` — SP - Capital - Rua Augusta — token OK

## CF7 `easyunit` laser (loja)

- `botafogo` — RJ - Botafogo — token OK
- `uruguai` — RJ - Tijuca - Rua Uruguai — token OK
- `largobicao` — RJ - Largo do Bicão — token OK
- `ilhagovernador2` — RJ - Ilha do Governador II - Estrada do Galeão — token OK
- `petropolis` — RJ - Região Serra - Petrópolis — token OK
- `copacabana2` — RJ - Copacabana II - Av. N. S. Copacabana — token OK
- `bangu` — RJ - Bangu — token OK
- `goncalvesdias` — RJ - Centro - Rua Gonçalves Dias — token OK
- `estradabandeirantes` — RJ - Estrada Bandeirantes - Map Band — token OK
- `humaita` — RJ - Humaitá — token OK
- `icarai` — RJ - Icaraí — token OK
- `freguesia` — RJ - Jacarepaguá - Largo da Freguesia — token OK
- `largomachado` — RJ - Largo do Machado — token OK
- `novaiguacu2` — RJ - Nova Iguaçu II - Ao lado TOP Shopping Nova Iguaçu — token OK
- `saojosecampos` — SP - Interior - São José dos Campos — token OK

## Notas

- Cobrança usa `easyunit` se preenchido, senão `unit` (`payment_CF7`).
- `saojose` e `rjsaojose` existem no AccesStage OT com o **mesmo** par API/APIKey. O CF7 da loja e o inventário mapeiam SJO (Centro — Rua São José) para `saojose`; `rjsaojose` fica como alias órfão do catálogo.
- `niteroi` no AccesStage OT não é o mesmo que `icarai` (Icaraí); `niteroi` fica órfão do catálogo atual.
- JSON detalhado (sem valores de chave): `projeto-migracao/.secrets/_inventory_accesstage_units.json`.
