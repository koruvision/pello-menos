# Diagnóstico: migração vs app vs clone

Data da checagem (só leitura): 2026-10-07.  
Dump técnico (gitignored): `wordpress-loja/.secrets/diag-migracao.json`.

## Resposta direta

O app Next **não cria usuário WordPress** e **não edita Hostinger**. Em [loja.pellomenos.com.br](https://loja.pellomenos.com.br/) o histórico deste projeto foi **só leitura**. As escritas (home HTML, Code Snippet, `uploads/pm-home/`) foram só no clone [pellomenos.companygenesis.com.br](https://pellomenos.companygenesis.com.br/).

O usuário **`lsb` não foi criado pelo app**. Na loja original ele já aparece na API pública como usuário **id `1`** (conta fundadora típica do WordPress). O clone tem o mesmo `lsb` id `1` porque é cópia do banco. A senha de aplicativo do `lsb` que usamos era do **staging**, colada no chat.

## Comparação rápida

| Sinal | Produção `loja.pellomenos.com.br` | Clone `companygenesis` |
| --- | --- | --- |
| Servidor / PHP | LiteSpeed, PHP **7.4.33** | hcdn, PHP **8.2.33** |
| Home | Shopwise + Elementor + Smart Slider + RevSlider | Documento HTML do projeto (`pm-home`) |
| `uploads/pm-home/` | **404** (não existe) | **200** (home.css / home.html / home.js) |
| Code Snippets API | **404** (rota ausente) | Existe (401 sem auth) |
| Spam de cassino no HTML | **Sim** | Não |
| Página 571 | Publicada, home da loja | Publicada no clone |
| `/masculino/` | API sem página `masculino` pública nessa consulta | Página 46252 publicada |
| Usuário `lsb` | id 1 | id 1 |

Conclusão: a home HTML do clone **não está** na produção. O que a loja original serve ainda é a stack antiga (tema + sliders).

## Achados na produção

### 1. Spam / possível compromisso

No HTML da home pública há blocos escondidos com links de cassino (holandês/polonês), por exemplo:

- `casino50.com`
- `flash-casino-online.nl`
- `westace.pl`
- “casino zonder cruks” / `lievenshof.nl`

Isso **não** veio do app nem do trabalho no clone. Em site migrado, costuma ser malware, widget/footer injetado ou plugin comprometido que veio no backup.

Há também um usuário público com slug `wps_2f7db55245` (id 11167). Nome no padrão de conta suspeita; vale revisar no admin e remover se não for legítima.

### 2. Usuário `lsb`

Presente na produção e no clone com **id 1**. Não indica criação recente pelo Cursor. Indica conta antiga do WordPress (e cópia no staging).

### 3. Página 571

Em produção a home (id 571) mostra `modified` em torno de **2026-10-06**. Isso pode ser edição humana, sync da migração WP-Vivid ou outro processo no host novo. **Não** há `pm-home` nem snippet “Home fiel” na produção, então não foi o deploy da home HTML do clone.

### 4. O que a migração WP-Vivid pode ter feito

Cenários coerentes com o histórico e com o host novo:

1. Backup/restauração no host Hostinger novo (URLs, DNS, arquivos incompletos).
2. Spam que já estava no backup ou entrou no host novo.
3. Contas e ids iguais ao clone porque o staging nasceu de cópia da produção — não o contrário.

## Checklist no admin da loja original (você no painel)

Sem o app. Só no WordPress de [loja.pellomenos.com.br](https://loja.pellomenos.com.br/):

1. **Usuários** — confirmar `lsb` (id 1); auditar `wps_2f7db55245`; trocar senhas de admins após a migração.
2. **Configurações → Geral** — WordPress Address e Site Address = `https://loja.pellomenos.com.br`.
3. **Plugins** — se existir Code Snippets com “Home fiel” ou pasta `wp-content/uploads/pm-home`, aí sim misturou backup do clone (hoje, pela web, **não** há).
4. **Aparência / Widgets / Elementor / rodapé** — achar e apagar o texto/links de cassino.
5. **Segurança** — varredura (Wordfence/malcare ou equivalente Hostinger), revisar File Manager, atualizar o que for seguro fora de janela de Black Friday se possível.
6. **Não confundir** o clone companygenesis com produção ao apontar DNS ou restaurar WP-Vivid.

## Como reexecutar a sonda (só leitura)

```bash
python scripts/diag_migration.py
```

Gera de novo `wordpress-loja/.secrets/diag-migracao.json` (não versionar).
