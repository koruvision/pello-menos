# -*- coding: utf-8 -*-
"""Troca o dominio base das imagens dentro dos HTMLs publicados.

home.html e masculino.html foram exportados apontando para o clone
(pellomenos.companygenesis.com.br), onde faltam arquivos em media/ — resultado:
imagens quebradas na home feminina e masculina. As mesmas imagens existem na loja.

Uso: python scripts/_fix_image_hosts.py [--write] [--host loja.pellomenos.com.br]
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
CLONES = ("pellomenos.companygenesis.com.br", "pellomenosoficialteste.companygenesis.com.br")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--host", default="loja.pellomenos.com.br")
    args = ap.parse_args()

    alvos = sorted(PM.glob("*.html")) + sorted(PM.glob("products/*.html")) + sorted(PM.glob("pages/*.html"))
    afetados = []
    for f in alvos:
        try:
            s = f.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError:
            s = f.read_text(encoding="utf-8", errors="replace")
        conta = {c: s.count(c) for c in CLONES if c in s}
        if conta:
            afetados.append((f, conta))

    print("arquivos com dominio de clone:", len(afetados))
    total = 0
    for f, conta in afetados:
        n = sum(conta.values())
        total += n
        if len(afetados) <= 15:
            print(f"  {f.relative_to(PM)!s:34s} {conta}")
    print("ocorrencias a trocar:", total)

    if not args.write:
        print("\n(dry-run; use --write)")
        return

    alterados = 0
    for f, _ in afetados:
        s = f.read_text(encoding="utf-8", errors="replace")
        novo = s
        for c in CLONES:
            novo = novo.replace(c, args.host)
        if novo == s:
            continue
        bak = f.with_suffix(f.suffix + ".bak-host")
        if not bak.exists():
            shutil.copy2(f, bak)
        f.write_text(novo, encoding="utf-8")
        alterados += 1
    print("arquivos gravados:", alterados)


if __name__ == "__main__":
    main()