# 08 — Riscos e pendências

## Problemas encontrados na auditoria

| ID | Problema | Impacto | Mitigação |
|----|----------|---------|-----------|
| R1 | Loja sem `pm-home` / snippets ativos | Front antigo até o cutover | Plano 06 |
| R2 | Code Snippets inativo na loja | REST 404 | Ativar plugin (já instalado) |
| R3 | WCAR ausente na loja | Sem e-mails de abandono do projeto | Instalar plugin + snippet |
| R4 | Catálogo 80 (OT) vs 66 (loja) | Divergência de SKUs | Não importar OT cego; alinhar itens aprovados |
| R5 | Spam/posts fake + possível abuso de credenciais (doc 21) | SEO/segurança | Hardening no cutover; não apagar clientes |
| R6 | Cache Hostinger/CDN 7d em assets pm-home | Front “antigo” após publish | Purge + `?v=` |
| R7 | Accesstage/CF7 fora do git | Não versionado | Não alterar no overlay |
| R8 | Clone PHP 8 vs loja 7.4 | CPF-old | Nunca copiar estado do clone |
| R9 | Detecção R$1 / preços ensaio no OT | Confusão comercial | Não sync preços ensaio |
| R10 | `loja-readonly.env` inválido | Confusão operacional | Não usar; preferir `loja.env` |

## Possíveis gambiarras (ver 04)

- Shells c10–c21 no disco (inertes).  
- Hardcodes GTM e `SPLASH_CENTS`.  
- Rewrite de URL só no `bundle` do script.  
- IDs de snippet do OT não servem na loja.

## Adaptações necessárias no GO

1. Scripts `_publish_email_styles.py` / WCAR que hardcodam OficialTeste → apontar `loja.env` ou PUT manual.  
2. Confirmar/criar produto teste `produto-r-1` (ou equivalente) **na loja**.  
3. Confirmar ID GTM da loja.  
4. Logo de e-mail na mídia da loja.  
5. Novo `loja.state.json` para ids de snippet.

## Credenciais

| Item | Status |
|------|--------|
| `PM_OFICIALTESTE_*` | OK completo |
| `PM_LOJA_*` (`loja.env`) | Auth admin OK |
| `loja-readonly.env` | Falha — regenerar ou apagar |
| Accesstage / gateway keys | No painel da loja (não no git) — **não** documentar valores aqui |
| SMTP | No painel da loja |
| PageSpeed key | Só OT — opcional |

**Ausente no repo (confirmar com humanos):**

1. Nome **“Argobot”** — não encontrado; processador documentado = **Accesstage**. É o mesmo? Há outra ferramenta administrativa a preservar?  
2. Meio de pagamento **autorizado** para a compra R$ 1,99 (cartão real vs ambiente de teste Accesstage).  
3. Horário de lançamento 03/11 (9h vs 3h — doc 21).  
4. Se Body Splash / itens extras entram no mesmo cutover ou depois.

## Dependências pendentes (não bloqueiam documentar, bloqueiam GO)

- Backup fresco da loja.  
- Janela de manutenção.  
- GO escrito para `--permitir-loja` e `--allow-prod` nas imagens.  
- Produto R$ 1,99 na loja.  
- Resposta sobre Argobot vs Accesstage.
