# -*- coding: utf-8 -*-
import http.client
import socket
import ssl

host = "pellomenosoficialteste.companygenesis.com.br"
ip = socket.getaddrinfo(host, 443, socket.AF_INET)[0][4][0]
ctx = ssl.create_default_context()


class C(http.client.HTTPSConnection):
    def connect(self):
        sock = socket.create_connection((ip, 443), 60)
        self.sock = ctx.wrap_socket(sock, server_hostname=host)


def get(path: str):
    c = C(host, timeout=60, context=ctx)
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
    "/wp-content/uploads/pm-home/home.js",
    "/wp-content/uploads/pm-home/cart.js",
    "/wp-content/uploads/pm-home/cart-related.json",
    "/wp-content/uploads/pm-home/media/images/products/cartao-presente.jpg",
    "/wp-content/uploads/pm-home/media/images/products/axilas-laser.png",
    "/",
    "/produto/cartao-presente/",
]
for path in checks:
    status, body = get(path)
    note = ""
    if path.endswith("home.js"):
        note = "ok" if b"/images/products/axilas-laser.png" in body else "missing-prod"
        if b"/images/social/cliente-1.png" in body:
            note += "+still-cliente"
    elif path.endswith("cart.js"):
        note = "ok" if b"data-pm-cart-upsell" in body else "missing-upsell"
    elif path.endswith(".json"):
        note = "ok" if b"axila-cera" in body and b"meia-perna-cera" in body else "bad"
    elif path == "/":
        if b"axilas-laser.png" in body:
            note = "toast-product"
        elif b"cliente-1" in body:
            note = "toast-cliente"
        else:
            note = "no-toast-img"
    elif path.endswith("cartao-presente.jpg"):
        note = f"bytes={len(body)}"
    print(status, len(body), path, note)
