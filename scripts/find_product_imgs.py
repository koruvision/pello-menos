import re
import urllib.request

urls = [
    "https://loja.pellomenos.com.br/produto/axilas-laser/",
    "https://loja.pellomenos.com.br/produto/buco-laser/",
    "https://loja.pellomenos.com.br/produto/perna-inteira-laser/",
    "https://loja.pellomenos.com.br/produto/virilha-total-laser/",
]
found = []
for url in urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    imgs = re.findall(r"https://loja\.pellomenos\.com\.br/wp-content/uploads/[^\s\"']+\.(?:webp|jpg|jpeg|png)", html)
    print("PAGE", url)
    for img in dict.fromkeys(imgs):
        if "Logo" in img or "banner" in img.lower() or "woocommerce" in img:
            continue
        print(" ", img)
        found.append(img)
