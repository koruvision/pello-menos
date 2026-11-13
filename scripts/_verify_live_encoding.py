# -*- coding: utf-8 -*-
import urllib.request

urls = [
    "https://loja.pellomenos.com.br/produto/axila-cera/",
    "https://loja.pellomenos.com.br/",
    "https://loja.pellomenos.com.br/carrinho/",
]
for url in urls:
    raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "pm-enc"}), timeout=60).read()
    text = raw.decode("utf-8", "replace")
    score = text.count("Ã") + text.count("â€")
    print(
        url,
        {
            "score": score,
            "Inicio": "Início" in text,
            "bad_Inicio": "InÃ­cio" in text,
            "Servicos": "Serviços" in text,
            "Axila": "Axila" in text and "Cera" in text,
        },
    )
