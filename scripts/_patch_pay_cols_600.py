# -*- coding: utf-8 -*-
from pathlib import Path

path = Path("wordpress-loja/pm-home/checkout-brand.css")
text = path.read_text(encoding="utf-8")

block = """
/* Pagamento: inputs em coluna abaixo de 600px */
@media (max-width: 600px) {
  body.pm-checkout-brand #pills-pagamento .row {
    flex-direction: column !important;
    flex-wrap: nowrap !important;
    gap: 0;
  }

  body.pm-checkout-brand #pills-pagamento .row > [class*="col"],
  body.pm-checkout-brand #pills-pagamento .row > .col,
  body.pm-checkout-brand #pills-pagamento .row > .col-6,
  body.pm-checkout-brand #pills-pagamento .row > .col-md-6,
  body.pm-checkout-brand #pills-pagamento .row > .col-sm-6 {
    flex: 0 0 100% !important;
    max-width: 100% !important;
    width: 100% !important;
  }

  body.pm-checkout-brand #pills-dados .row {
    flex-direction: column !important;
  }

  body.pm-checkout-brand #pills-dados .row > [class*="col"] {
    flex: 0 0 100% !important;
    max-width: 100% !important;
    width: 100% !important;
  }
}

"""

if "inputs em coluna abaixo de 600px" in text:
    print("already present")
else:
    path.write_text(text.rstrip() + "\n" + block, encoding="utf-8")
    print("appended")
