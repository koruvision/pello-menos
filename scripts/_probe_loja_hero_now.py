# -*- coding: utf-8 -*-
import re
import urllib.request

UA = {"User-Agent": "pm"}
html = urllib.request.urlopen(
    urllib.request.Request("https://loja.pellomenos.com.br/", headers=UA),
    timeout=60,
).read().decode("utf-8", "replace")

keys = [
    "bakedText",
    "hero-campaign",
    "desktop-fw",
    "banner-perna",
    "banner-axilas",
    "pm-hero-copy",
    "hero-copy",
]
for k in keys:
    print(k, html.count(k))

imgs = sorted(set(re.findall(r"/pm-home/media/images/hero/[^\"'?#]+", html)))
print("hero imgs", len(imgs))
for i in imgs:
    print(i)
