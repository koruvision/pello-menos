# -*- coding: utf-8 -*-
"""Testa resolução de variation + add-item Woo no oficialteste (upsell)."""
from __future__ import annotations

import http.client
import http.cookiejar
import json
import socket
import ssl
import urllib.error
import urllib.request

HOST = "pellomenosoficialteste.companygenesis.com.br"
BASE = f"https://{HOST}"
IP = socket.getaddrinfo(HOST, 443, socket.AF_INET)[0][4][0]
CTX = ssl.create_default_context()


class IPv4HTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("context", CTX)
        super().__init__(IP, *args, **kwargs)

    def connect(self):
        sock = socket.create_connection((IP, 443), self.timeout)
        self.sock = CTX.wrap_socket(sock, server_hostname=HOST)


class IPv4HTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(IPv4HTTPSConnection, req)


def main() -> None:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        IPv4HTTPSHandler(), urllib.request.HTTPCookieProcessor(jar)
    )

    def get(path: str) -> tuple[int, bytes, dict[str, str]]:
        req = urllib.request.Request(
            BASE + path,
            headers={"User-Agent": "pm-upsell-test", "Cache-Control": "no-cache"},
        )
        with opener.open(req, timeout=60) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, resp.read(), headers

    def post_json(path: str, payload: dict, nonce: str) -> tuple[int, object]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            BASE + path,
            data=data,
            method="POST",
            headers={
                "User-Agent": "pm-upsell-test",
                "Content-Type": "application/json",
                "Nonce": nonce,
                "Origin": BASE,
                "Referer": BASE + "/carrinho/",
            },
        )
        try:
            with opener.open(req, timeout=60) as resp:
                body = resp.read().decode("utf-8", "replace")
                return resp.status, json.loads(body)
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            try:
                parsed: object = json.loads(body)
            except json.JSONDecodeError:
                parsed = body[:400]
            return err.code, parsed

    st, cart_js, _ = get("/wp-content/uploads/pm-home/cart.js?v=cart16")
    print("cart.js", st, len(cart_js), "hasFn", b"variationForUnit" in cart_js)

    st, related_raw, _ = get("/wp-content/uploads/pm-home/cart-related.json")
    related = json.loads(related_raw.decode())
    meia = related["products"]["meia-perna-cera"]
    print("meia.units.cen", meia.get("units", {}).get("cen"))
    assert meia.get("units", {}).get("cen", {}).get("variationId"), "missing variation"

    st, cart_body, headers = get("/wp-json/wc/store/v1/cart")
    nonce = (
        headers.get("nonce")
        or headers.get("x-wc-store-api-nonce")
        or headers.get("x-wc-store-api-nonce".lower())
        or ""
    )
    print("cart GET", st, "nonce", bool(nonce), "header_keys_sample", list(headers)[:12])

    parent_id = int(meia.get("productId") or meia.get("wooId"))
    variation_id = int(meia["units"]["cen"]["variationId"])

    if not nonce:
        print("WARN: sem nonce — validando só o mapeamento")
        print("PASS mapping parent", parent_id, "variation", variation_id)
        return

    cart = json.loads(cart_body.decode())
    for item in cart.get("items") or []:
        key = item.get("key")
        if key:
            post_json("/wp-json/wc/store/v1/cart/remove-item", {"key": key}, nonce)

    st_bad, bad = post_json(
        "/wp-json/wc/store/v1/cart/add-item",
        {"id": parent_id, "quantity": 1},
        nonce,
    )
    print("add parent", parent_id, "->", st_bad, str(bad)[:200])

    st_ok, good = post_json(
        "/wp-json/wc/store/v1/cart/add-item",
        {"id": variation_id, "quantity": 1},
        nonce,
    )
    items = good.get("items") if isinstance(good, dict) else None
    print(
        "add variation",
        variation_id,
        "->",
        st_ok,
        "items",
        len(items or []),
        [i.get("id") for i in (items or [])],
    )
    if st_ok in (200, 201) and items:
        print("PASS upsell variation add")
    else:
        raise SystemExit(f"FAIL variation add: {good}")


if __name__ == "__main__":
    main()
