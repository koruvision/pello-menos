# -*- coding: utf-8 -*-
"""Espelha no select `installments` do CF7 #1831 a mesma lista de parcelas de
`allinstallments` (1x..10x).

Motivo: o payment_CF7 le `installments` primeiro e esse select so oferecia 1x,
por isso toda compra saia em 1x mesmo com 10x escolhido em `allinstallments`.

Uso: python scripts/_patch_cf7_installments.py --target loja|ot [--write]
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RE_ALL = re.compile(r'\[select\*?\s+allinstallments[^\]]*\]')
RE_INST = re.compile(r'\[select\*?\s+installments([^\]]*)\]')
RE_OPT = re.compile(r'"[^"]*"')


def config(target: str):
    env = ROOT / "projeto-migracao" / ".secrets" / ("loja.env" if target == "loja" else "oficialteste.env")
    prefix = "PM_LOJA" if target == "loja" else "PM_OFICIALTESTE"
    e = {}
    for line in env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e[f"{prefix}_URL"].rstrip("/"), e[f"{prefix}_USER"], e[f"{prefix}_APP_PASSWORD"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=("loja", "ot"), required=True)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    base, user, pwd = config(args.target)
    tok = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    auth = {"Authorization": "Basic " + tok, "User-Agent": "pm-cf7"}
    url = base + "/wp-json/contact-form-7/v1/contact-forms/1831"

    with urllib.request.urlopen(urllib.request.Request(url, headers=auth), timeout=90) as r:
        form = json.load(r)
    props = form["properties"]
    content = props["form"]
    if isinstance(content, dict):
        content = content.get("content", "")

    m_all = RE_ALL.search(content)
    if not m_all:
        raise SystemExit("select allinstallments nao encontrado")

    m_inst = RE_INST.search(content)
    if not m_inst:
        raise SystemExit("select installments nao encontrado")

    opcoes_all = RE_OPT.findall(m_all.group(0))
    opcoes_inst = RE_OPT.findall(m_inst.group(1))

    # mantem o cabecalho (classe/atributos) e a primeira opcao (rotulo)
    cabecalho = RE_OPT.sub("", m_inst.group(1))
    cabecalho = " ".join(cabecalho.split())
    nova_lista = " ".join(opcoes_all[1:])
    novo = "[" + m_inst.group(0)[1:-1]
    for q in opcoes_inst[1:]:
        novo = novo.replace(q, "", 1)
    novo = " ".join(novo.split())
    if not novo.endswith("]"):
        novo += "]"
    novo = novo[:-1].rstrip() + " " + nova_lista + "]"
    novo = novo.replace("[select* installments  ", "[select* installments ")

    print("alvo:", base)
    print("cabecalho:", cabecalho)
    print("opcoes installments antes:", opcoes_inst)
    print("opcoes installments depois:", opcoes_all)
    print("novo shortcode:", novo[:240])

    if opcoes_inst == opcoes_all:
        print("nada a fazer (ja tem a lista completa)")
        return
    if not args.write:
        print("(dry-run; use --write)")
        return

    new_content = content.replace(m_inst.group(0), novo, 1)
    props["form"] = new_content
    put = urllib.request.Request(
        url,
        data=json.dumps({"properties": props}).encode(),
        method="POST",
        headers={**auth, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(put, timeout=120) as r:
        saved = json.load(r)
    sc = saved.get("properties", {}).get("form", "")
    if isinstance(sc, dict):
        sc = sc.get("content", "")
    mi = RE_INST.search(sc)
    ok = bool(mi) and RE_OPT.findall(mi.group(1)) == opcoes_all
    print("salvo | lista aplicada:", ok)


if __name__ == "__main__":
    main()