/**
 * Estilo visual dos e-mails WooCommerce (loja / oficialteste).
 * Logo circular com anel dourado na imagem; CSS força border-radius 50% + 180px.
 * Não altera textos, assuntos, placeholders nem templates PHP.
 * Code Snippets: colar SEM a tag <?php de abertura.
 */

add_filter('woocommerce_email_styles', 'pm_email_brand_styles', 40, 2);

function pm_email_brand_styles($css, $email = null) {
    $extra = <<<'CSS'

/* Pello Menos — tipografia alinhada ao site (Manrope + Cormorant) */
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Manrope:wght@400;500;600;700&display=swap');

body, #body_content_inner, .td, td, th, p, li, address {
  font-family: Manrope, "Helvetica Neue", Helvetica, Arial, sans-serif !important;
  color: #1A1A1A !important;
}

h1, h2, h3, #header_wrapper h1, .email-heading {
  font-family: "Cormorant Garamond", Georgia, "Times New Roman", serif !important;
  font-weight: 600 !important;
  letter-spacing: -0.02em !important;
  color: #B3196F !important;
}

a { color: #B3196F !important; }

#wrapper {
  /* Parte de fora: degradê roxo/rosa do footer do site */
  background-color: #700053 !important;
  background-image: linear-gradient(165deg, #5a0a4a 0%, #700053 42%, #3a0628 100%) !important;
  padding: 28px 12px !important;
}

body {
  background-color: #700053 !important;
  background-image: linear-gradient(165deg, #5a0a4a 0%, #700053 42%, #3a0628 100%) !important;
}

#template_container,
#template_header,
#template_body,
#template_footer {
  border: 0 !important;
  box-shadow: none !important;
}

#template_container {
  border: 1px solid #FFBB3A !important;
  border-radius: 16px !important;
  overflow: hidden !important;
  background-color: #FFFFFF !important;
  box-shadow: 0 10px 28px rgba(106, 16, 67, 0.08) !important;
}

#template_header {
  background-color: #FFFFFF !important;
  border-radius: 16px 16px 0 0 !important;
  border-bottom: 1px solid #F0E4EA !important;
  padding: 20px 24px 8px !important;
}

#template_header h1,
#header_wrapper h1 {
  color: #B3196F !important;
  font-size: 26px !important;
  line-height: 1.25 !important;
  margin: 8px 0 0 !important;
}

#template_header_image img,
#template_header_image p img {
  margin: 0 auto !important;
  border-radius: 50% !important;
  /* Círculo com anel dourado já na imagem */
  width: 180px !important;
  max-width: 180px !important;
  height: auto !important;
}

#template_body {
  background-color: #FFFFFF !important;
}

#body_content {
  background-color: #FFFFFF !important;
}

#body_content_inner {
  color: #1A1A1A !important;
  font-size: 15px !important;
  line-height: 1.55 !important;
}

#body_content_inner p {
  margin: 0 0 14px !important;
}

/* Tabelas de pedido — mais suaves, cantos arredondados (clientes modernos) */
table.td,
#body_content_inner table.td,
.email-order-details,
.order_item,
table.order_details {
  border: 1px solid #F0E4EA !important;
  border-collapse: separate !important;
  border-spacing: 0 !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  background: #FFFFFF !important;
}

table.td th,
table.td td,
#body_content_inner table.td th,
#body_content_inner table.td td {
  border-color: #F5EBF0 !important;
  border-top-color: #F5EBF0 !important;
  border-bottom-color: #F5EBF0 !important;
  border-left-color: #F5EBF0 !important;
  border-right-color: #F5EBF0 !important;
  color: #1A1A1A !important;
  font-family: Manrope, "Helvetica Neue", Helvetica, Arial, sans-serif !important;
}

table.td th,
#body_content_inner table.td th {
  background-color: #FFF8FB !important;
  color: #6A1043 !important;
  font-weight: 600 !important;
  font-size: 12px !important;
  letter-spacing: 0.04em !important;
  text-transform: uppercase !important;
}

table.td tfoot tr:last-child td,
table.td tfoot tr:last-child th {
  color: #B3196F !important;
  font-weight: 700 !important;
  border-top: 2px solid #FFBB3A !important;
}

#template_footer {
  background-color: #FFFFFF !important;
  border-top: 1px solid #F0E4EA !important;
  border-radius: 0 0 16px 16px !important;
}

#template_footer #credit,
#template_footer td {
  color: #6A1043 !important;
  font-family: Manrope, "Helvetica Neue", Helvetica, Arial, sans-serif !important;
  font-size: 12px !important;
}

/*
 * Cards de cobrança/entrega: mesma altura.
 * O visual do card fica no <td> (a linha da tabela já equaliza altura);
 * o <address> só carrega o texto, sem caixa própria menor.
 */
#addresses {
  width: 100% !important;
  border-collapse: separate !important;
  border-spacing: 10px 0 !important;
  margin: 8px 0 16px !important;
}

#addresses td {
  width: 50% !important;
  vertical-align: top !important;
  border: 1px solid #F0E4EA !important;
  border-radius: 12px !important;
  background-color: #FFF8FB !important;
  padding: 14px 16px !important;
}

#addresses .address-title,
#addresses h2 {
  display: block !important;
  margin: 0 0 10px !important;
  color: #6A1043 !important;
  font-family: Manrope, "Helvetica Neue", Helvetica, Arial, sans-serif !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
}

#addresses .address,
#addresses address {
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  padding: 0 !important;
  margin: 0 !important;
  color: #1A1A1A !important;
  font-style: normal !important;
  line-height: 1.5 !important;
  font-size: 14px !important;
}

CSS;
    return $css . "\n" . $extra;
}
