# -*- coding: utf-8 -*-
from pathlib import Path

path = Path("wordpress-loja/pm-home/checkout-brand.css")
text = path.read_text(encoding="utf-8")

# 1) Always hide response-output banner
old_resp = """body.pm-checkout-brand .wpcf7-form.invalid .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form.unaccepted .wpcf7-response-output {
  display: none !important;
}

body.pm-checkout-brand .wpcf7-form.sent .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form.failed .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form.aborted .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form.spam .wpcf7-response-output {
  display: block !important;
  margin-top: 1rem;
  padding: 0.85rem 1rem;
  border-radius: 0.85rem;
  text-align: center;
  font-size: 0.875rem;
  font-weight: 600;
}"""

new_resp = """/* Banner CF7 sempre oculto no checkout (status via bordas / fluxo do gateway) */
body.pm-checkout-brand .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form.invalid .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form.unaccepted .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form.sent .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form.failed .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form.aborted .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form.spam .wpcf7-response-output {
  display: none !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  overflow: hidden !important;
}"""

if old_resp in text:
    text = text.replace(old_resp, new_resp)
    print("response-output: replaced conditional hide")
elif "Banner CF7 sempre oculto" in text:
    print("response-output: already always hidden")
else:
    # fallback: append strong hide
    text += "\n" + new_resp + "\n"
    print("response-output: appended")

# 2) column-gap 0 on rows
old_row = """.pm-checkout-brand .wpcf7-form .row {
  display: flex;
  flex-wrap: wrap;
  margin-left: 0 !important;
  margin-right: 0 !important;
  margin-bottom: 0.35rem;
  column-gap: 0.85rem;
  row-gap: 0.35rem;
}"""

new_row = """.pm-checkout-brand .wpcf7-form .row {
  display: flex;
  flex-wrap: wrap;
  margin-left: 0 !important;
  margin-right: 0 !important;
  margin-bottom: 0.35rem;
  column-gap: 0 !important;
  row-gap: 0.35rem;
}"""

if old_row in text:
    text = text.replace(old_row, new_row)
    print("row gap: updated")
elif "column-gap: 0 !important" in text:
    print("row gap: already 0")
else:
    text = text.replace("column-gap: 0.85rem;", "column-gap: 0 !important;")
    text = text.replace("column-gap: 0px;", "column-gap: 0 !important;")
    print("row gap: regex-ish replace")

# 3) payment columns padding 5px instead of 15px (Bootstrap col default)
pay_pad = """
/* Dados de Pagamento: padding lateral das colunas 5px */
body.pm-checkout-brand #pills-pagamento .row > [class*="col"],
body.pm-checkout-brand #pills-pagamento .row > .col {
  padding-left: 5px !important;
  padding-right: 5px !important;
}
"""

if "padding lateral das colunas 5px" in text:
    print("pay pad: already present")
else:
    text = text.rstrip() + "\n" + pay_pad + "\n"
    print("pay pad: appended")

path.write_text(text, encoding="utf-8")
print("done")
