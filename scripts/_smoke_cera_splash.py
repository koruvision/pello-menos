# -*- coding: utf-8 -*-
import http.client
import re
import socket
import ssl

HOST = "pellomenosoficialteste.companygenesis.com.br"
IP = socket.getaddrinfo(HOST, 443, socket.AF_INET)[0][4][0]
CTX = ssl.create_default_context()


class C(http.client.HTTPSConnection):
    def connect(self):
        self.sock = CTX.wrap_socket(
            socket.create_connection((IP, 443), 60), server_hostname=HOST
        )


def get(path: str) -> bytes:
    c = C(HOST, timeout=60, context=CTX)
    c.request("GET", path, headers={"User-Agent": "pm", "Cache-Control": "no-cache"})
    r = c.getresponse()
    b = r.read()
    c.close()
    print(path, r.status, len(b))
    return b


home = get("/?v=cera1")
i = home.find(b"Cera em destaque")
art1 = home.find(b"<article data-carousel-card", i)
art2 = home.find(b"<article data-carousel-card", art1 + 10)
card = home[art1:art2].decode("utf-8", "replace")
print(
    "1real card divs",
    card.count("<div"),
    card.count("</div>"),
    "href",
    "produto-1-real" in card,
    "balanced",
    card.count("<div") == card.count("</div>"),
)
print("home divs", home.count(b"<div"), home.count(b"</div>"))

cartjs = get("/wp-content/uploads/pm-home/cart.js?v=cart17").decode("utf-8", "replace")
m = re.search(r"priceCents:\s*(\d+)", cartjs)
print("splash priceCents", m.group(1) if m else None, "cart17 file ok", "priceCents: 199" in cartjs)
