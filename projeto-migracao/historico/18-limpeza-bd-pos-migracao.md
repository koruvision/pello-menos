# 18 — Limpeza de BD pós-migração (loja oficial)

Checklist **programado para depois do cutover** em `loja.pellomenos.com.br`.  
**Não executar agora** neste passo. Oficialteste pode ser usado só para ensaiar comandos equivalentes, com backup.

Contexto Black Friday: migração do front → limpeza leve de sessão/cache → pico de tráfego (~2×). Clientes e pedidos **permanecem**.

## Pré-requisitos (obrigatório)

1. Backup completo **arquivos + banco** da loja.
2. Janela curta de manutenção (fora do pico).
3. Confirmar versão WooCommerce no painel (Status) antes de qualquer WP-CLI.
4. **Não** restaurar o banco do clone/oficialteste por cima da loja.

## Limpar (seguro, após backup)

| Item | O quê | Como (orientação) | Não fazer |
|------|--------|-------------------|-----------|
| Sessões Woo / carrinhos abandonados | Linhas expiradas em sessões Woo (`woocommerce_sessions` e equivalentes da versão) | WooCommerce → Status → ferramentas de sessões expiradas **ou** WP-CLI documentado para a versão instalada | Truncar tabela inteira sem filtro de expiração; apagar pedidos |
| Transients expirados | `_transient_*` / `_site_transient_*` vencidos | Ferramenta nativa Woo/WP ou WP-CLI de transients expirados | Apagar todos os transients “na mão” sem saber o que é plugin ativo |
| Cache de página | LiteSpeed / Hostinger | Purge no painel do cache após o GO do front (`?pm=` novo no bundle) | Desligar cache no meio da Black Friday sem plano |
| Lixo de ensaio | Usuários fake / spam (`wps_*` etc.) | Revisão manual no admin; só contas claramente de teste | Apagar clientes Woo com pedidos |
| Logs Woo antigos | Arquivos de log em disco | Remover logs velhos no Status → Logs | Confundir log com pedido/meta de pagamento |

## Manter (não truncar / não “otimizar” em massa)

- Clientes Woo e endereços
- Pedidos, itens, notas, meta Accesstage / gateway
- Produtos, variações, categorias, atributos
- Cupons
- CF7 **#1831** e plugins de pagamento / CPF / Conditional Fields
- Settings Woo, e-mails (Kadence), redirects
- Action Scheduler: só limpar **completadas antigas** após backup; **não** limpar fila pendente

## Ordem sugerida no dia do cutover

1. Backup arquivos + BD  
2. Manutenção breve  
3. Publicar front (bundle + snippet) com bust de cache  
4. Purge LiteSpeed/Hostinger  
5. Limpar sessões Woo **expiradas** + transients **expirados**  
6. Smoke: Store API carrinho vazio → add item → `/finalizar-pagamento/` mostra o item (sem pagamento de teste em produção sem GO)  
7. Tirar manutenção  

## Nota sobre `pm-cart-v1`

Espelho de carrinho no `localStorage` do browser. Limpar BD de sessões **não** limpa browsers dos clientes — irrelevante para integridade de pedidos; não exige ação no dia do GO.

## Fora de escopo desta limpeza

- Refator de performance de front (ver `17-psi-oficialteste-baseline.md`)
- Qualquer alteração de checkout/CF7/Accesstage
- Purge de catálogo ou preços
