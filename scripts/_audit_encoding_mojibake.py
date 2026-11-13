# -*- coding: utf-8 -*-
"""Audita mojibake UTF-8 em arquivos locais e na página ao vivo."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
MARKERS = ("Ã", "â€", "Â ", "Â ")


def score(text: str) -> dict:
    return {m: text.count(m) for m in MARKERS}


def main():
    # live
    url = "https://loja.pellomenos.com.br/produto/axila-cera/"
    raw = urllib.request.urlopen(url, timeout=60).read()
    live = raw.decode("utf-8", "replace")
    print("LIVE", url)
    print("  scores", score(live))
    for needle in ("Início", "InÃ­cio", "Serviços", "ServiÃ§os", "região", "regiÃ£o"):
        print(" ", needle, live.find(needle))

    # local product
    local = (PM / "products" / "axila-cera.html").read_text(encoding="utf-8", errors="replace")
    print("LOCAL products/axila-cera.html")
    print("  scores", score(local))
    for needle in ("Início", "InÃ­cio", "Serviços", "ServiÃ§os", "região", "regiÃ£o"):
        print(" ", needle, local.find(needle))

    # scan pm-home text files
    bad = []
    for path in sorted(PM.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".html", ".js", ".css", ".json", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        s = score(text)
        total = sum(s.values())
        if total >= 5:  # meaningful
            bad.append((total, str(path.relative_to(PM)), s))
    bad.sort(reverse=True)
    print("LOCAL files with mojibake markers (>=5):", len(bad))
    for total, rel, s in bad[:30]:
        print(f"  {total:5d} {rel} {s}")
    out = ROOT / "scripts" / "_audit_encoding_mojibake_result.json"
    out.write_text(json.dumps({"live": score(live), "top": bad[:80]}, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
