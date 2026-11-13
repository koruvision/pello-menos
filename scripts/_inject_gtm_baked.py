# -*- coding: utf-8 -*-
"""Inject GTM-52G8XVQ8 into existing pm-home HTML without full re-export."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "wordpress-loja" / "pm-home"
GTM_ID = "GTM-52G8XVQ8"

GTM_HEAD = f"""<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{GTM_ID}');</script>
<!-- End Google Tag Manager -->
"""

GTM_BODY = f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
"""


def inject(html: str) -> str:
    if GTM_ID in html:
        return html
    if re.search(r"<head\b", html, re.I):
        html = re.sub(r"(<head\b[^>]*>)", r"\1\n" + GTM_HEAD, html, count=1, flags=re.I)
    m = re.search(r"(<body\b[^>]*>)", html, flags=re.I)
    if m:
        pos = m.end()
        html = html[:pos] + "\n" + GTM_BODY + html[pos:]
    return html


def main():
    n = 0
    for path in list(OUT.rglob("*.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        next_text = inject(text)
        if next_text != text:
            path.write_text(next_text, encoding="utf-8")
            n += 1
    print("patched", n, "html files with", GTM_ID)


if __name__ == "__main__":
    main()
