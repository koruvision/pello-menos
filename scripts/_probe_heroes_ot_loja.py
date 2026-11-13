# -*- coding: utf-8 -*-
import re
import urllib.request
from pathlib import Path

UA = {"User-Agent": "pm-hero-probe"}


def fetch(url: str) -> bytes:
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=90
    ).read()


def hero_srcs(html: str) -> list[str]:
    return sorted(
        set(
            re.findall(
                r"/wp-content/uploads/pm-home[^\"']+(?:hero|banner)[^\"']+",
                html,
                flags=re.I,
            )
        )
    )


def main() -> None:
    out = Path("projeto-migracao/.secrets/hero-compare")
    out.mkdir(parents=True, exist_ok=True)
    for label, base in (
        ("ot", "https://pellomenosoficialteste.companygenesis.com.br"),
        ("loja", "https://loja.pellomenos.com.br"),
    ):
        html = fetch(base + "/?v=herocmp1").decode("utf-8", "replace")
        srcs = hero_srcs(html)
        print(label, "count", len(srcs))
        for s in srcs:
            print(" ", s)
            if not s.lower().endswith((".jpg", ".jpeg", ".webp", ".png")):
                continue
            name = s.split("/")[-1].split("?")[0]
            try:
                data = fetch(base + s.split("?")[0] + "?v=herocmp1")
                dest = out / f"{label}-{name}"
                dest.write_bytes(data)
                print("   saved", dest.name, len(data))
            except Exception as err:
                print("   fail", err)


if __name__ == "__main__":
    main()
