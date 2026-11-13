# -*- coding: utf-8 -*-
import re
import urllib.request

ORIGIN = "http://127.0.0.1:3456"
UA = {"User-Agent": "pm-smoke"}
PATHS = [
    "/produto/axilas-laser",
    "/produto/perna-cera",
    "/produto/virilha-laser",
    "/produto/bracos-laser",
    "/produto/axila-cera",
]


def main() -> None:
    for path in PATHS:
        html = urllib.request.urlopen(
            urllib.request.Request(ORIGIN + path, headers=UA), timeout=120
        ).read().decode("utf-8", "replace")
        sale = re.search(r'data-rj-sale="(\d+)"', html)
        reg = re.search(r'data-rj-regular="(\d+)"', html)
        print(
            path,
            "sale",
            sale.group(1) if sale else None,
            "reg",
            reg.group(1) if reg else None,
        )


if __name__ == "__main__":
    main()
