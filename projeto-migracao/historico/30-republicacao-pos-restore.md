# 30 — Republicação pós-restore (OT + loja) com manutenção

Data: 02/11/2026.

## Contexto

Backup/restore humano devolveu `loja.pellomenos.com.br` ao tema Shopwise. Nova app password do `company-genesis` gravada em `.secrets/loja.env` (não versionada). Auth validada (`/users/me` admin).

## O que subiu

### OficialTeste (aberto ao público)

- Bundle `pm-home` completo + snippet rotas `home,masculino,produto,carrinho,conta,shell,loja`
- Black Nov pricing **com FORCE esquenta** (smoke)
- `pm-email-styles`, `pm-wcar`, plugin WCAR ativo
- Smoke: home ~474 KB `pm-home`; `/masculino/` 200; shell + `black-nov-campaign.json` 200

### Loja (manutenção pública)

| Snippet | Id | Notas |
|---------|----|-------|
| `pm-ecommerce-maintenance` | 6 | Público: “E-commerce em Manutenção” + link `/wp-admin`; admin `manage_options` bypass; REST/ajax/login liberados |
| `pm-email-styles` | 7 | |
| `pm-wcar (carrinho abandonado)` | 8 | |
| `pm-home (front do projeto)` | 9 | Rotas full; enqueue `c35` / `load3` / black-nov |
| `pm-black-nov-pricing` | 10 | **sem FORCE** (calendário 03–30/11) |

- Bundle full 200 (`home.html` ~473 KB); overlay `openCheckoutLoading` no shell; WCAR plugin instalado+ativo
- Estado: `.secrets/loja.state.json` → `snippet_id` **9** (não misturar com manutenção)

## Smoke

| Check | Resultado |
|-------|-----------|
| Anónimo `/`, `/carrinho/`, `/masculino/` | **503** + texto manutenção + link wp-admin |
| Anónimo `/wp-admin/` | **200** (login/admin) |
| Assets auth `pm-home` | 200 (home, shell, loading, black-nov, cart) |
| OT `/` | 200 front novo, sem manutenção |

## Cuidados

- Manutenção e `pm-home` são snippets **separados** (6 vs 9). Não reutilizar o id da manutenção no `loja.state.json`.
- Tirar manutenção: desativar snippet 6 (`pm-ecommerce-maintenance`) só com GO explícito.
- Accesstage/CF7 #1831 não foram alterados.

## Scripts usados

- `scripts/pm_maintenance_snippet.php` + `_publish_loja_maintenance.py`
- `scripts/pm_publicar_destino.py` (OT e loja `--permitir-loja`)
- `_publish_black_nov_ot.py` / `_publish_black_nov_loja.py`
- `_publish_email_styles.py`, `_publish_wcar_snippet.py`, `_install_wcar_plugin.py`
- `_smoke_pos_restore.py`
