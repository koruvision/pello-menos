# -*- coding: utf-8 -*-
import urllib.request
from pathlib import Path

UA = {"User-Agent": "pm-hero-dl"}
OUT = Path("projeto-migracao/.secrets/hero-compare")
OUT.mkdir(parents=True, exist_ok=True)

FILES = [
    "banner-perna-desktop-fw.jpg",
    "banner-axilas-desktop-fw.jpg",
    "banner-virilha-desktop-fw.jpg",
    "banner-bracos-desktop-fw.jpg",
]


def dl(url: str, dest: Path) -> None:
    data = urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=120
    ).read()
    dest.write_bytes(data)
    print(dest.name, len(data))


def main() -> None:
    for name in FILES:
        for label, base in (
            ("loja", "https://loja.pellomenos.com.br"),
            ("ot", "https://pellomenosoficialteste.companygenesis.com.br"),
        ):
            url = (
                f"{base}/wp-content/uploads/pm-home/media/images/hero/examples/{name}?v=ref2"
            )
            dl(url, OUT / f"{label}-{name}")


if __name__ == "__main__":
    main()
