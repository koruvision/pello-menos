# Checkout: loja no ar contra o clone

Leitura pública em 17 de outubro de 2026. Nenhum POST. Nenhum login de escrita. Páginas: `/finalizar-pagamento/` em `https://loja.pellomenos.com.br` e em `https://pellomenos.companygenesis.com.br`.

## Garantia

O pagamento do clone não está igual ao da loja. A fase 4 de `11-migracao-em-fases.md` fica parada até o campo de CPF da loja continuar funcionando no destino. Banner, header e rodapé não entram nessa conta. Campo, plugin e script do cartão entram.

## O que é o mesmo miolo

Os dois HTML têm o mesmo formulário Contact Form 7, id 1831, com action `/finalizar-pagamento/#wpcf7-f1831-o1`.

Campos presentes nos dois:

- pessoa e contato: `your-name`, `your-email`, `your-phone`
- endereço: `cep`, `endereco`, `numero`, `complemento`, `bairro`, `cidade`, `estado`
- pedido: `unit`, `category`, `cart`, `cartqtd`, `cupom`, `cupomamount`, `fullvalue`, `totalamount`, `subscribemode`, `declaracao`, `easyunit`
- cartão: `cart-number`, `holder`, `expiration`, `securityCode`, `installments`, `allinstallments`, `cerainstallments`, `siteinstallment`
- grupos: `_wpcf7cf_hidden_group_fields`, `_wpcf7cf_hidden_groups`, `_wpcf7cf_options`, `_wpcf7cf_repeaters`, `_wpcf7cf_steps`, `_wpcf7cf_visible_groups`
- reCAPTCHA: `g-recaptcha-response`, `_wpcf7_recaptcha_response`

Contagens iguais nos dois: `cart-number` 3, `jquery.mask` 2, chamadas `.mask(` 5, `wpcf7cf` 15, `recaptcha` 23.

Scripts de pagamento presentes nos dois:

- jQuery Mask 1.14.16
- Contact Form 7 (`includes/js/index.js` e SWV)
- Conditional Fields (`cf7-conditional-fields/js/scripts.js`)
- reCAPTCHA do CF7 e `recaptcha/api.js`
- WooCommerce (`woocommerce.min.js`, cookie, blockUI, order attribution, sourcebuster)

`https://loja.pellomenos.com.br/wp-content/uploads/pm-home/home.html` responde 404. No clone a mesma URL responde 200. A home do projeto ainda não está na loja.

Servidor lido no cabeçalho desta mesma requisição:

| | Loja | Clone |
| --- | --- | --- |
| PHP | 7.4.33 | 8.2.34 |
| Servidor | LiteSpeed | hcdn |
| Plataforma | Hostinger | Hostinger |

## O que trava a fase 4

1. CPF. Na loja existe `<input name="cpf">` e carregam `cpf-e-cnpj-para-contact-form-7-old/assets/js/main.js` e `mask.min.js`. No clone o shortcode `[cpf` aparece cru (`cpf_shortcode` 1, `cpf_input` 0) e esses dois scripts não carregam. O plugin antigo quebra no PHP 8 do clone. Na loja, em PHP 7.4, ele está ativo e o campo sai pronto. Copiar o estado do clone para a loja, ou desligar esse plugin, tira o CPF de quem está pagando.

2. Honeypot. O clone tem `_wpcf7_ak_hp_textarea` e `_wpcf7_ak_js`. A loja não tem. É campo extra do CF7 no clone, não um campo de cartão da loja.

## O que a loja tem e não é o cartão

Não muda o formulário 1831, mas mostra que a loja andou depois da cópia:

- newsletter Mailchimp: `EMAIL`, `_mc4wp_form_id`, `_mc4wp_form_element_id`, `_mc4wp_honeypot`, `_mc4wp_timestamp`, e `mailchimp-for-wp/assets/js/forms.js`
- `woocommerce/assets/js/frontend/cart-fragments.min.js`
- lista de desejos TI, variation swatches, RevSlider, módulos extras do Elementor, `wp-analytics`
- o segundo action de formulário da loja é a própria home (`https://loja.pellomenos.com.br/`), o do clone é a home do clone. É a busca ou a newsletter, não o POST do CF7 1831

O único script que só o clone carrega nessa página é `uploads/pm-home/checkout-shell.js`. Ele monta o cabeçalho e o rodapé do projeto. Não lê o formulário.

## O que não fazer na troca

- Não reescrever o HTML do formulário, os contratos nem o POST.
- Não ativar no destino o estado quebrado do CPF do clone.
- Não subir o PHP da loja para 8 enquanto o plugin `cpf-e-cnpj-para-contact-form-7-old` for o que desenha o campo. No clone esse plugin responde HTTP 500 ao ser ativado.
- Não tratar “o chrome está igual” como “o pagamento está igual”.
