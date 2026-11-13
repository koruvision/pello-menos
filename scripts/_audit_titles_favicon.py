# -*- coding: utf-8 -*-
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PM = ROOT / "wordpress-loja" / "pm-home"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 pm-audit"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", "replace")


def main():
    html = fetch("https://loja.pellomenos.com.br/finalizar-pagamento/")
    icons = re.findall(r"<link[^>]+>", html, flags=re.I)
    for tag in icons:
        if re.search(r"icon|shortcut|apple", tag, flags=re.I):
            print("CHECKOUT_LINK", tag)

    bad = []
    for path in [PM / "home.html", PM / "masculino.html", PM / "carrinho.html", PM / "busca.html"]:
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            m = re.search(r"<title>(.*?)</title>", text)
            title = m.group(1) if m else ""
            print("TITLE", path.name, title)
            if "Ã" in title:
                bad.append(path.name)
            fav = re.findall(r"<link[^>]+rel=[\"'][^\"']*icon[^\"']*[\"'][^>]*>", text, flags=re.I)
            print("  favicons", len(fav), fav[:2])
    for path in sorted((PM / "pages").glob("*.html"))[:15]:
        text = path.read_text(encoding="utf-8")
        m = re.search(r"<title>(.*?)</title>", text)
        title = m.group(1) if m else ""
        if "Ã" in title:
            bad.append(str(path.relative_to(PM)))
            print("BAD", path.name, title)
    print("bad_count", len(bad), bad)


if __name__ == "__main__":
    main()
