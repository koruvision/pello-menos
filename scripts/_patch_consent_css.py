# -*- coding: utf-8 -*-
from pathlib import Path

path = Path("wordpress-loja/pm-home/checkout-brand.css")
text = path.read_text(encoding="utf-8")
start = text.find("/* Consentimento logo acima do bot")
end = text.find("/* Parcelas sempre leg", start)
if start < 0 or end < 0:
    raise SystemExit(f"markers not found start={start} end={end}")

replacement = """/* Consentimento logo acima do botao — checkbox + texto na mesma linha */
.pm-checkout-consent {
  margin: 1rem 0 0.85rem !important;
  text-align: left;
  padding: 0.85rem 1rem;
  border-radius: 0.85rem;
  background: var(--pm-ck-surface-soft);
  border: 1px solid var(--pm-ck-line);
}

.pm-checkout-consent .wpcf7-acceptance,
.pm-checkout-consent .wpcf7-list-item,
.pm-checkout-consent .wpcf7-list-item label {
  display: flex !important;
  flex-direction: row !important;
  align-items: flex-start !important;
  gap: 0.65rem;
  margin: 0 !important;
  width: 100%;
}

.pm-checkout-consent input[type="checkbox"] {
  flex: 0 0 auto;
  width: 1.15rem;
  height: 1.15rem;
  margin: 0.15rem 0 0 !important;
  float: none !important;
}

.pm-checkout-consent .wpcf7-list-item-label {
  display: inline !important;
  margin: 0 !important;
  font-size: 0.8125rem !important;
  line-height: 1.45;
  color: var(--pm-ck-on);
  font-weight: 500 !important;
  text-align: left;
}

/* Label acima do select de parcelas */
.pm-checkout-installments-label {
  display: block;
  margin: 0 0 0.45rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--pm-ck-on);
  text-align: left;
}

"""

path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")
print("patched", path)
