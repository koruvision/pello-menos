# -*- coding: utf-8 -*-
import http.client
import re
import socket
import ssl

host = "pellomenosoficialteste.companygenesis.com.br"
ip = socket.getaddrinfo(host, 443, socket.AF_INET)[0][4][0]
ctx = ssl.create_default_context()


class C(http.client.HTTPSConnection):
    def connect(self):
        self.sock = ctx.wrap_socket(
            socket.create_connection((ip, 443), 60), server_hostname=host
        )


c = C(host, timeout=60, context=ctx)
c.request(
    "GET",
    "/carrinho/?nocache=1",
    headers={"User-Agent": "x", "Cache-Control": "no-cache"},
)
r = c.getresponse()
b = r.read()
c.close()
print("status", r.status, "len", len(b))
print("cart14", b"cart.js?v=cart14" in b)
print("cart13", b"cart.js?v=cart13" in b)
m = re.search(br"cart\.js\?v=[^\s\"']+", b)
print("ref", m.group(0).decode() if m else None)
