# -*- coding: utf-8 -*-
import re
import urllib.error
import urllib.request

BASE = "https://loja.pellomenos.com.br"

html = urllib.request.urlopen(
    urllib.request.Request(
        BASE + "/?v=bake5",
        headers={"User-Agent": "x", "Cache-Control": "no-cache"},
    ),
    timeout=60,
).read().decode("utf-8", "replace")

urls = sorted(set(re.findall(r"https?://[^\"']+banner-exemplo[^\"']+", html)))
print("in home", len(urls))
for u in urls:
    print("HOME_REF", u)

# also relative paths
rels = sorted(set(re.findall(r"[^\"']+banner-exemplo[^\"'\s]+", html)))
print("rel hits", len(rels))
for u in rels[:20]:
    print("REL", u[:200])

candidates = [
    "/wp-content/uploads/pm-home/media/images/hero/examples/banner-exemplo-avatar-esquerda-desktop.jpg",
    "/wp-content/uploads/pm-home/media/images/hero/examples/banner-exemplo-avatar-direita-desktop.jpg",
    "/wp-content/uploads/pm-home/media/images/hero/examples/banner-exemplo-avatar-esquerda.jpg",
    "/wp-content/uploads/pm-home/media/images/hero/examples/banner-exemplo-avatar-direita.jpg",
    "/wp-content/uploads/pm-home/images/hero/examples/banner-exemplo-avatar-esquerda-desktop.jpg",
    "/wp-content/uploads/pm-home/images/hero/examples/banner-exemplo-avatar-direita-desktop.jpg",
]

for path in candidates:
    url = BASE + path + "?v=direct2"
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "x"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read(32)
            print(
                "OK",
                resp.status,
                url,
                resp.headers.get("Content-Type"),
                resp.headers.get("Content-Length"),
                data[:8],
            )
    except urllib.error.HTTPError as e:
        print("FAIL", e.code, url)
    except Exception as e:
        print("ERR", url, e)
