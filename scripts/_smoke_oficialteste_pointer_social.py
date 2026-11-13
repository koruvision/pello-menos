# -*- coding: utf-8 -*-
import http.client
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


def get(path: str) -> tuple[int, bytes]:
    c = C(HOST, timeout=60, context=CTX)
    c.request(
        "GET",
        path,
        headers={"User-Agent": "pm-smoke", "Cache-Control": "no-cache"},
    )
    r = c.getresponse()
    b = r.read()
    c.close()
    return r.status, b


checks = [
    ("/", None),
    ("/wp-content/uploads/pm-home/home.js?v=premium6", None),
    ("/wp-content/uploads/pm-home/home.css?v=premium4", None),
    ("/wp-content/uploads/pm-home/cart.js?v=cart16", None),
    ("/carrinho/", None),
]
for path, _ in checks:
    st, body = get(path)
    notes = []
    if path == "/":
        notes.append("toast-product" if b"axilas-laser.png" in body else "no-product-toast")
        notes.append("cliente" if b"cliente-1.png" in body else "no-cliente")
        notes.append("css4" if b"home.css?v=premium4" in body else "css-old")
        notes.append("js6" if b"home.js?v=premium6" in body else "js-old")
    elif "home.js" in path:
        notes.append("prod" if b"axilas-laser.png" in body else "miss")
        notes.append("cliente" if b"cliente-1.png" in body else "ok-no-cliente")
    elif "home.css" in path:
        notes.append("pointer" if b"pm-cursor-pointer" in body else "no-pointer")
        notes.append(f"bytes={len(body)}")
    elif "cart.js" in path:
        notes.append("variation" if b"variationForUnit" in body else "no-var")
        notes.append("upsell" if b"data-pm-cart-upsell" in body else "no-upsell")
    elif path.startswith("/carrinho"):
        notes.append("cart16" if b"cart.js?v=cart16" in body else "cart-old")
        notes.append("css4" if b"home.css?v=premium4" in body else "css-old")
    print(st, path, " | ".join(notes))
