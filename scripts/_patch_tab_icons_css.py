# -*- coding: utf-8 -*-
from pathlib import Path

path = Path("wordpress-loja/pm-home/checkout-brand.css")
text = path.read_text(encoding="utf-8")
marker = "/* Abas = mesmo lux da home"
if ".pm-ck-tab-icon" in text:
    print("icons css already present")
else:
    inject = """
.pm-checkout-brand .nav-pills .nav-link,
.pm-checkout-brand .pm-checkout-buy-now {
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
}

.pm-ck-tab-icon {
  flex: 0 0 auto;
  display: block;
  position: relative;
  z-index: 1;
}

.pm-checkout-brand .nav-pills .nav-link > span,
.pm-checkout-brand .pm-checkout-buy-now > span {
  position: relative;
  z-index: 1;
}

"""
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("marker missing")
    path.write_text(text[:idx] + inject + text[idx:], encoding="utf-8")
    print("injected")
