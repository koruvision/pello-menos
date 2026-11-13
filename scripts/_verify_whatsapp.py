# -*- coding: utf-8 -*-
import urllib.request

base = "https://pellomenosoficialteste.companygenesis.com.br"
html = urllib.request.urlopen(base + "/?t=wa", timeout=60).read().decode("utf-8", "replace")
js = urllib.request.urlopen(
    base + "/wp-content/uploads/pm-home/whatsapp-float.js?v=wa6", timeout=60
).read().decode("utf-8", "replace")
print("footer label", "(21) 2549-4265" in html)
print("footer wa.me", "wa.me/552125494265" in html)
print("float js", "wa.me/552125494265" in js)
print("old empty wa.me/?", "wa.me/?text=" in js)
