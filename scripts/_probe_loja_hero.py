# -*- coding: utf-8 -*-
import re
import urllib.request

UA = {"User-Agent": "x", "Cache-Control": "no-cache"}


def fetch(url: str) -> str:
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=60
    ).read().decode("utf-8", "replace")


def probe(label: str, url: str) -> None:
    html = fetch(url)
    print("===", label, len(html))
    keys = [
        "banner-exemplo-avatar",
        "hero-campaign",
        "aspect-ratio:16/9",
        "lg:aspect-[16/9]",
        "height:600px",
        "height:560px",
        "min-width: 1024px",
        "banner-virilha-desktop",
        "banner-exemplo-avatar-esquerda-desktop",
        "banner-exemplo-avatar-esquerda-tablet",
        "object-contain",
    ]
    for k in keys:
        print(f"  {k}: {html.count(k)}")
    srcs = re.findall(r"/wp-content/uploads/pm-home[^\"']+hero[^\"']+", html)
    uniq = []
    for s in srcs:
        if s not in uniq:
            uniq.append(s)
    print("  hero srcs:", uniq[:12])


probe("loja", "https://loja.pellomenos.com.br/?v=bannerchk2")
probe("ot", "https://pellomenosoficialteste.companygenesis.com.br/?v=bannerchk2")
