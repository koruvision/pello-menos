# Histórico completo: o que fizemos e se isso permitiu o incidente

Documento para responder: “algo que fizemos permitiu isso? instalação, permissão ou vazamento?”  
Senhas **não** são repetidas aqui. Se ainda existirem no histórico do chat Cursor, trate como comprometidas.

## Resposta curta

| Pergunta | Resposta |
| --- | --- |
| Instalamos plugin na loja original? | **Não.** |
| Criamos usuário `lsb` na loja original? | **Não.** (`lsb` já é id 1 no WordPress) |
| Alteramos senha da `company-genesis`? | **Não** no nosso histórico de ações. |
| Escrevemos (POST/PUT) em `loja.pellomenos.com.br`? | **Não.** Só GET / login de leitura. |
| Escrevemos no clone `companygenesis`? | **Sim** (home HTML, snippets, uploads). |
| Algo nosso aumentou risco? | **Sim: senhas coladas no chat** (e scripts temporários). Isso é vazamento de credencial, não instalação de plugin. |

A conta `company-genesis` **não era administrador** (menu Plugins 403). Mesmo logados, **não dava** para instalar plugin pela conta usada.

O spam de cassino e o usuário `wps_*` na produção são sinais clássicos de **site comprometido / migração suja**, não da home HTML do clone (que **não** está na produção).

---

## 1. `loja.pellomenos.com.br` (produção) — só leitura

Conta usada: `company-genesis` (senha de painel colada por você no chat).

### O que foi feito

1. Leitura pública: home HTML, categorias Woo, páginas, produto.
2. Login no wp-admin **só para GET**: dashboard, lista de páginas, status Woo (lista de plugins via system status), modelos Elementor.
3. Tentativas que **falharam** (e paramos): `plugins.php` **403**, instalar tema/plugin **403/500**, REST de plugins sem permissão.
4. Documentação local em `wordpress-loja/00`–`06`.
5. PageSpeed / medição de performance (API key que você colou; só leitura de scores).
6. Diagnóstico pós-migração (2026-10-07): HTML + REST públicos — sem auth de escrita.

### O que **não** foi feito

- Nenhum POST/PUT/DELETE em páginas, usuários, plugins, checkout, pagamentos, pedidos, produtos.
- Nenhuma instalação de plugin.
- Nenhum Code Snippet “Home fiel” / pasta `uploads/pm-home` na produção (confirmado: 404).
- Nenhuma alteração de senha pela nossa sessão.

### Credenciais expostas nesse fluxo

- Senha do painel `company-genesis` entrou no **histórico do chat** e em script temporário em `%TEMP%` (depois apagado no PC, mas o chat pode ainda ter a string).
- Se a senha da `company-genesis` foi **alterada por terceiros**, o caminho mais próximo do nosso trabalho é **vazamento/reuso dessa senha**, não “instalamos um plugin que abriu a porta”.

---

## 2. `pellomenos.companygenesis.com.br` (clone / staging) — com escrita

Conta usada: `lsb` + **application password** “Cursor” (colada por você).

### O que foi feito (resumo)

1. Backup da home Elementor (página 571) via REST.
2. Upload de mídia de campanha; rebuild da home feminina e página `/masculino/` (id 46252) via `_elementor_data`.
3. Limpeza de cache Elementor (`DELETE /wp-json/elementor/v1/cache`).
4. Code Snippets: performance (snippet 6), probes Redis/env (7/8 criados e removidos), depois snippet “Home fiel” + endpoint de upload do zip.
5. Publicação do pacote HTML/CSS/JS/imagens em `wp-content/uploads/pm-home/`.
6. Remoção de animações Elementor que deixavam seções invisíveis; depois substituição da home por documento estático do projeto.
7. Testes de carga leves e add-to-cart via Store API (**sem** checkout/pagamento).

### O que **não** foi feito no clone

- Não mexemos em gateways, pedidos, cupons de pagamento.
- Não instalamos malware de cassino (o clone **não** tem o spam; a produção tem).

### Credenciais expostas nesse fluxo

- Application password do `lsb` no chat e em vários scripts temporários.
- Se alguém tiver o histórico do chat, pode agir no **clone** com o poder do `lsb` até a senha de app ser revogada.

---

## 3. App Next / GitHub

- Commit de cartões presente e push em `gnstecnologia/pello-menos` — **não** altera WordPress.
- O app **não** tem fluxo de criar usuário WP, instalar plugin ou mudar senha Hostinger.

---

## 4. Isso “permitiu” o incidente?

### O que **não** bate com o nosso trabalho

- Spam de cassino na home da **produção** + usuário `wps_2f7db55245` → padrão de invasão/malware, comum após host frágil ou plugin velho; o clone limpo e a ausência de `pm-home` na produção indicam que **não** foi o deploy da home HTML.
- Instalação de plugin pela nossa conta: **impossível** com `company-genesis` (403 em Plugins).

### O que **pode** ter relação indireta

1. **Senha `company-genesis` no chat**  
   Se o chat foi compartilhado, sincronizado, ou o histórico vazou, alguém com a senha antiga podia entrar e **trocar a senha**. Isso é o único elo claro entre “o que fizemos” e “senha alterada”.
2. **Mesma senha em vários lugares** (WP, Hostinger, e-mail) — atacante que pegou uma, muda a outra.
3. **Migração WP-Vivid / host novo** — janela em que o site fica frágil; malware no backup ou no servidor novo.

### O que fazer agora (conta Company Genesis / loja)

1. **Revogar** todas as application passwords do `lsb` no clone e criar outra se ainda precisar.
2. Garantir que a senha nova da `company-genesis` **não** seja a mesma de Hostinger/e-mail; não colar de novo no chat.
3. No admin da produção: apagar spam de cassino; remover usuário `wps_*` se não for de vocês; varredura de malware; revisar File Manager.
4. Tratar o histórico deste chat como **fonte sensível** (contém senhas antigas).

---

## 5. Linha do tempo (ordem)

1. Leitura da produção + docs `wordpress-loja/` (conta `company-genesis`, só GET).  
2. Cartões presente no app Next + push GitHub.  
3. Staging: rebuild Elementor home + `/masculino/`.  
4. Staging: snippets de performance Black Friday.  
5. Staging: home HTML fiel (`pm-home`) + snippet que serve `/` e `/masculino/`.  
6. Diagnóstico migração + este histórico de risco.  

Produção: em nenhum passo houve instalação de plugin nem criação de `lsb`. O risco operacional real do nosso lado foi **credencial no chat**.
