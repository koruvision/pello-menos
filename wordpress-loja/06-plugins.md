# Como ver plugins (esta conta)

Esta conta **não é administradora** (`is_administrator: false`).  
**Plugins** e **Saúde do site** dão 403. Por isso a barra não mostra “Plugins”.

Há **Adminimize** ativo — é comum ele esconder exatamente esse menu.

## Onde olhar sem instalar nada

**WooCommerce → Status** (não é Pagamentos). Lá o WooCommerce lista tema e plugins. Não clicar nas ferramentas de sistema (logs, transients, etc.) sem necessidade.

Não instalar plugin novo em produção para “ver o site”.

## O que está ativo (leitura em 15/09/2026)

Tema: **Shopwise Child 1.4.8** (pai Shopwise 1.4.8)  
WordPress 7.1 · WooCommerce 10.1.4 · PHP 7.4.33  
34 plugins ativos, 1 inativo.

Os que importam para o visual:

- Elementor 3.5.6 (sem Pro na lista)
- Shopwise Core, Kirki, Meta Box
- Smart Slider 3, Slider Revolution, Mega Main Menu
- Variation Swatches, TI Wishlist, YITH Compare
- Code Snippets + WPCode Lite (CSS/JS extra — olhar só leitura)
- Kadence WooCommerce Email Designer (e-mail de pedido — **não mexer**)

Outros: CF7, Mailchimp, Yoast, Redirection, Loco, Classic Editor, Google for WooCommerce, File Manager, SMTP, Really Simple Security, otimizadores de imagem, WebToffee import/export.

Inativo: Advanced Dynamic Pricing Pro.

## “Ver arquivos do tema”

Existe **WP File Manager**. Ele enxerga arquivos, mas em produção é perigoso (editar/apagar). Para o visual, use **Aparência** / CSS do child, não o File Manager.

Checkout / Pagamentos: continua fora.
