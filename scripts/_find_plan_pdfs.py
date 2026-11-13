# -*- coding: utf-8 -*-
import re
import urllib.request
from pathlib import Path

BASE = "https://loja.pellomenos.com.br"
SLUGS = [
    "plano-silver",
    "plano-de-assinatura-vip-silver",
    "assinatura-vip-silver",
    "plano-gold",
    "plano-de-assinatura-vip-gold",
    "assinatura-vip-gold",
    "plano-clube-laser",
    "clube-de-laser",
    "clube-do-laser",
    "pre-pago-pello-menos",
    "pre-pago",
    "plano-prepago",
]


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 pm-audit"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def main() -> None:
    for slug in SLUGS:
        for path in (f"/produto/{slug}/", f"/product/{slug}/"):
            url = BASE + path
            try:
                status, html = fetch(url)
            except Exception as exc:
                print(path, "ERR", exc)
                continue
            pdfs = sorted(set(re.findall(r"https?://[^\s\"'<>]+\.pdf", html, re.I)))
            # also relative uploads
            rel = sorted(
                set(
                    re.findall(
                        r"(?:href|src)=[\"']([^\"']+\.pdf)[\"']", html, re.I
                    )
                )
            )
            print(path, status, "html", len(html), "abs_pdf", len(pdfs), "rel", len(rel))
            for p in pdfs[:12]:
                print("  ABS", p)
            for p in rel[:12]:
                print("  REL", p)
            # title hint
            m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
            if m:
                print("  TITLE", re.sub(r"\s+", " ", m.group(1))[:120])


if __name__ == "__main__":
    main()
