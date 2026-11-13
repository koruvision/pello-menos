# -*- coding: utf-8 -*-
from pathlib import Path

path = Path("wordpress-loja/pm-home/checkout-brand.css")
text = path.read_text(encoding="utf-8")

# Replace always-hidden response-output with visual-only hide
start = text.find("/* Banner CF7 sempre oculto")
if start < 0:
    start = text.find("body.pm-checkout-brand .wpcf7-response-output,")
end = text.find("/*", start + 5) if start >= 0 else -1
# find end of the rule block after start - look for next major comment after the closing brace of hide rules
if start >= 0:
    # find closing of the big hide block
    brace = text.find("}", text.find("{", start))
    # may be one rule - find last } of consecutive response-output rules
    chunk_end = brace + 1
    while True:
        nxt = text.find("body.pm-checkout-brand .wpcf7", chunk_end)
        if nxt < 0 or nxt > chunk_end + 40:
            # also allow blank lines then more response rules
            peek = text[chunk_end : chunk_end + 80]
            if "wpcf7-response-output" in text[chunk_end : chunk_end + 200]:
                brace2 = text.find("}", text.find("{", chunk_end))
                if brace2 > 0:
                    chunk_end = brace2 + 1
                    continue
            break
        brace2 = text.find("}", text.find("{", nxt))
        chunk_end = brace2 + 1

    new_block = """/* CF7 response: sem faixa azul / check; texto de mensagem continua visivel */
body.pm-checkout-brand .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form .wpcf7-response-output {
  display: block !important;
  position: relative !important;
  border: 0 !important;
  border-color: transparent !important;
  background: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  outline: none !important;
  margin: 0.65rem 0 0 !important;
  padding: 0 !important;
  min-height: 0 !important;
  height: auto !important;
  color: var(--pm-ck-on) !important;
  font-size: 0.875rem !important;
  font-weight: 600 !important;
  line-height: 1.4 !important;
  text-align: left !important;
}

body.pm-checkout-brand .wpcf7-response-output::before,
body.pm-checkout-brand .wpcf7-response-output::after,
body.pm-checkout-brand .wpcf7-form.sent .wpcf7-response-output::before,
body.pm-checkout-brand .wpcf7-form.failed .wpcf7-response-output::before,
body.pm-checkout-brand .wpcf7-form.invalid .wpcf7-response-output::before {
  content: none !important;
  display: none !important;
  background: none !important;
  border: 0 !important;
  width: 0 !important;
  height: 0 !important;
}

body.pm-checkout-brand .wpcf7-form.invalid .wpcf7-response-output {
  color: #b71c1c !important;
}

body.pm-checkout-brand .wpcf7-form.sent .wpcf7-response-output {
  color: #1b5e20 !important;
}

body.pm-checkout-brand .wpcf7-form.failed .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form.aborted .wpcf7-response-output,
body.pm-checkout-brand .wpcf7-form.spam .wpcf7-response-output {
  color: #b71c1c !important;
}

"""
    text = text[:start] + new_block + text[chunk_end:]
    print("response-output visual chrome stripped")
else:
    print("WARN: response block start not found")

# Brighter submit button - find pm-checkout-submit block background-image
old_grad = """  --pm-ck-shine-a: rgba(255, 244, 214, 0.32);
  --pm-ck-shine-b: rgba(232, 184, 109, 0.9);
  color: #fff !important;
  background-color: #700053 !important;
  background-image: linear-gradient(
    120deg,
    #3d0a38 0%,
    #700053 26%,
    #a12680 50%,
    #700053 74%,
    #4a1848 100%
  ) !important;
  background-size: 220% 220% !important;
  box-shadow: 0 10px 24px rgba(112, 0, 83, 0.32) !important;
  cursor: pointer;
  overflow: hidden;
  animation: btn-gradient 9s ease infinite;
}"""

new_grad = """  --pm-ck-shine-a: rgba(255, 255, 255, 0.55);
  --pm-ck-shine-b: rgba(255, 244, 214, 0.95);
  color: #fff !important;
  background-color: #8a0070 !important;
  background-image: linear-gradient(
    115deg,
    #4a0a42 0%,
    #700053 18%,
    #b1007a 42%,
    #e25ab8 58%,
    #9b006f 78%,
    #5c0a4a 100%
  ) !important;
  background-size: 240% 240% !important;
  box-shadow: 0 12px 28px rgba(112, 0, 83, 0.4) !important;
  cursor: pointer;
  overflow: hidden;
  animation: btn-gradient 5.5s ease infinite;
}"""

if old_grad in text:
    text = text.replace(old_grad, new_grad)
    print("submit gradient brightened")
else:
    print("WARN: submit gradient block not exact match")

# Faster shine on submit ::before if present
text = text.replace(
    "animation: btn-shine 6.4s ease-in-out infinite;\n  pointer-events: none;\n}\n\n.pm-checkout-brand .wpcf7-form input.wpcf7-submit:hover",
    "animation: btn-shine 3.6s ease-in-out infinite;\n  pointer-events: none;\n}\n\n.pm-checkout-brand .wpcf7-form input.wpcf7-submit:hover",
)

path.write_text(text, encoding="utf-8")
print("css done")
