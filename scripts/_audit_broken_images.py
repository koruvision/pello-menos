# -*- coding: utf-8 -*-
"""Verifica quais imagens referenciadas nas paginas da home estao quebradas.

Compara as URLs do HTML com o que existe em uploads/pm-home/media da loja.
"""
from __future__ import annotations

import re
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["/", "/masculino", "/servicos/cera/", "/servicos/laser/", "/planos/"]
OUT = ROOT / "scripts" / "_broken_images.json"
UA = {"User-Agent": "Mozilla/5.0 (pm-img-audit)"}


def head(url: str) -> int:
    try:
        req = urllib.request.Request(url, headers=UA, method="HEAD")
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def main() -> None:
    relatorio = {}
    for page in PAGES:
        try:
            req = urllib.request.Request("https://loja.pellomenos.com.br" + page, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                html = r.read().decode("utf-8", "replace")
        except Exception as exc:
            print(page, "erro", exc)
            continue

        srcs = re.findall(r'<img[^>]*src="([^"]+)"', html)
        srcs += re.findall(r'url\((["\']?)(/wp-content[^)"\']+)\1\)', html) and [] or []
        bg = re.findall(r'background-image:\s*url\(["\']?(/wp-content[^)"\']+)', html)
        srcs += bg
        unicos = sorted({s.split("?")[0] for s in srcs if s.startswith(("http", "/"))})

        host = Counter()
        quebradas = []
        for s in unicos:
            full = s if s.startswith("http") else "https://loja.pellomenos.com.br" + s
            m = re.match(r"https://([^/]+)/", full)
            if m:
                host[m.group(1)] += 1
            code = head(full)
            if code != 200:
                quebradas.append({"url": full, "status": code})
        relatorio[page] = {"total": len(unicos), "hosts": dict(host), "quebradas": quebradas}
        print(f"{page}: {len(unicos)} imagens | hosts={dict(host)} | quebradas={len(quebradas)}")
        for q in quebradas[:8]:
            print("   ", q["status"], q["url"][:110])

    import json
    OUT.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nrelatorio:", OUT)


if __name__ == "__main__":
    main()