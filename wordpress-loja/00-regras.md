# Regras desta pasta

A loja está em **produção**. Há milhares de pedidos em processamento. Qualquer clique errado pode quebrar venda.

## Nunca mexer

- Checkout e pagamento (`/finaliza-compra/`, `/finalizar-pagamento/`, menu **Pagamentos**, WooCommerce → Configurações → Checkout)
- Carrinho e Minha Conta, salvo se no futuro pedirem **só CSS** e ainda assim com plano escrito
- Contratos, termos, privacidade, consentimento de dados
- Preço, gateway, cupom de pagamento, estoque, pedido
- Ativar/desativar plugin, atualizar WordPress, trocar tema ativo
- Publicar rascunho sem autorização
- Apertar botão de salvar, atualizar, publicar, lixeira, importar, exportar

## Pode (só quando autorizado, e ainda assim com cuidado)

- Aparência: CSS do child theme, Customizer (cores/fontes), Elementor da **Home** e páginas de vitrine
- Smart Slider da home (já tem banner feminino e masculino)
- Mega Main Menu (visual)
- Cards de produto, arquivo `/loja/`, busca **visual**
- Página rascunho de masculino (id 17544) — hoje **não está pública**

## Conta usada na leitura

A conta entra no painel e vê temas, páginas, produtos e Elementor. `plugins.php` retornou 403 (sem acesso a Plugins). Mesmo com menu de Pagamentos visível, **não abrimos**.
