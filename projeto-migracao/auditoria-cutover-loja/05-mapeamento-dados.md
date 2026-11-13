# 05 — Mapeamento de dados

## Preservar obrigatoriamente (loja oficial)

| Dado | Motivo |
|------|--------|
| Usuários WP (clientes + admins, incl. Genesis) | Contas reais; “Argobot”/admin não recriar |
| Pedidos Woo + itens + notas + **meta Accesstage/gateway** | Histórico comercial e conciliação |
| Endereços / billing usermeta | Conta e checkout |
| Produtos, variações, categorias, atributos (comerciais) | Catálogo vivo |
| Cupons já existentes | Promoções atuais |
| CF7 #1831 + Conditional Fields + CPF-old + reCAPTCHA keys | Pagamento |
| Settings Woo (gateway, e-mails, moeda) | Operação |
| Action Scheduler **pendente** | Filas de e-mail/jobs |
| Conteúdo Elementor no BD | Volta se snippet desligar |

## Pode atualizar / substituir (superfície)

| Elemento | Como |
|----------|------|
| HTML/CSS/JS em `uploads/pm-home/` | Bundle overlay |
| Featured images Woo alinhadas ao catálogo do projeto | `_sync_woo_featured_images.py --allow-prod` |
| Imagens antigas órfãs / mídia lixo | Só **após** cutover + backup (doc 18); não no GO cego |
| Layout home Elementor (só o que o público vê) | Substituído pelo GET do `home.html` enquanto snippet ativo |
| UI login/conta/carrinho | HTML do projeto |
| CSS de e-mail | Snippet e-mail |
| Config WCAR / templates abandonados | Snippet + plugin |

## Não trazer do OficialTeste

| Item | Motivo |
|------|--------|
| Banco completo / dump OT | Apagaria clientes e pedidos da loja |
| Pedidos e users de ensaio | Irrelevantes e poluem |
| Preços R$ 1,00 / produtos só de teste em massa | Distortion comercial |
| Plugins Hostinger do ensaio | Hosting diferente |
| `loja-readonly.env` | Credencial inválida |

## Identidades (conta / leads) — ver também `historico/22`

| Armazém | Na loja | Ação |
|---------|---------|------|
| `wp_users` + billing | Existe | Preservar; cadastro novo grava nome/telefone via `account.php` |
| Pedidos guest por e-mail | Já possíveis | Lista/detalhe alinhados no código atual |
| `wp_pm_checkout_leads` | Criada pelo WCAR snippet | Nova na loja ao ativar WCAR |
| CartFlows abandon table | Com plugin | Nova/uso do plugin |
| `pm-identity-v1` / cookie | Só browser | Nada a migrar |

## Riscos de sobrescrita

1. **Restore BD OT → loja** = perda total de histórico oficial. Proibido.  
2. Sync de produtos/preços OT → loja sem filtro = preços de ensaio.  
3. Apagar users “fake” sem checar pedidos = risco de apagar cliente. Critério: só spam óbvio **sem** pedidos (doc 21).  
4. Truncar metas Accesstage = quebra conciliação.  
5. Bundle zip **não** apaga o BD; só arquivos sob `uploads/pm-home/` (+ extract). Pedidos/users intactos.
