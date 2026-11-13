# -*- coding: utf-8 -*-
"""Adiciona ao mapa label->slug do snippet 13 os rotulos exatos das unidades que faltam.

Motivo (pedido 49674): o mapa so tinha 'RJ - Nova Iguaçu' => 'novaiguacu', mas o
select envia o rotulo longo. Sem correspondencia, o valor chegava cru ao
payment_CF7 e o update_post_meta('Unidade') gravava a unidade errada.

Regra do projeto (.cursor/rules/accesstage-unidades.mdc): so mapear slug que JA tem
par de chaves no tema. Este script recusa qualquer slug fora dessa lista.

Uso: python scripts/_patch_snippet13_units.py [--write] [--target loja|ot]
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNIPPET_NAME = "pm-accesstage-normalize-test"

# Slugs com par API/APIKey no child theme (verificado no dump).
KNOWN_SLUGS = {
    "largobicao", "bangu", "botafogo", "humaita", "augusta", "saojosecampos", "ipanema",
    "flamengo", "olegario", "ilhagovernador2", "uruguai", "madureira", "nilopolis",
    "camposgoytacazes", "freguesia", "largomachado", "copacabana1", "copacabana2",
    "saogoncalo", "paulista", "niteroi", "saojose", "icarai", "campogrande", "petropolis",
    "goncalvesdias", "meier", "bonsucesso", "asasul", "asanorte", "recreio", "cabofrio",
    "caxias", "jundiai", "saojoaomeriti", "leblon2", "parkshopping", "estradabandeirantes",
    "afonsopena", "trezemaio", "novaiguacu", "novaiguacu2", "saenspena",
}

ADDITIONS = {
    "RJ - Nova Iguaçu I - Rua Otávio Tarquino": "novaiguacu",
    "RJ - Nova Iguaçu II - Ao lado TOP Shopping Nova Iguaçu": "novaiguacu2",
    "RJ - Nova Iguaçu": "novaiguacu",
}


def config(target: str) -> tuple[str, str, str]:
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
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--target", choices=("loja", "ot"), default="loja")
    args = ap.parse_args()

    base, user, pwd = config(args.target)
    tok = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    auth = {"Authorization": "Basic " + tok, "User-Agent": "pm-snippet13"}

    rows_req = urllib.request.Request(base + "/wp-json/code-snippets/v1/snippets?per_page=100", headers=auth)
    with urllib.request.urlopen(rows_req, timeout=90) as r:
        rows = json.load(r)
    snip = next((s for s in rows if s.get("name") == SNIPPET_NAME), None)
    if not snip:
        raise SystemExit(f"snippet '{SNIPPET_NAME}' nao encontrado em {base}")

    with urllib.request.urlopen(
        urllib.request.Request(base + f"/wp-json/code-snippets/v1/snippets/{snip['id']}", headers=auth),
        timeout=90,
    ) as r:
        code = json.load(r)["code"]

    print(f"snippet #{snip['id']} ({SNIPPET_NAME}) em {base} | ativo={snip.get('active')} | {len(code)} bytes")

    for label, slug in ADDITIONS.items():
        if slug not in KNOWN_SLUGS:
            raise SystemExit(f"ABORTADO: slug '{slug}' nao tem par de chaves no tema")

    pending = {l: s for l, s in ADDITIONS.items() if f"'{l}' =>" not in code}
    print("entradas a adicionar:", len(pending), list(pending))
    if not pending:
        print("nada a fazer")
        return

    anchor = re.search(r"('RJ - Nova Iguaçu' => '[a-z0-9]+',)", code)
    if not anchor:
        raise SystemExit("ABORTADO: ancora 'RJ - Nova Iguaçu' nao encontrada no mapa")
    block = "".join(f"\n        '{l}' => '{s}'," for l, s in pending.items())
    new_code = code.replace(anchor.group(1), anchor.group(1) + block, 1)

    for l, s in pending.items():
        if f"'{l}' => '{s}'" not in new_code:
            raise SystemExit(f"ABORTADO: insercao de {l} nao confirmada")

    print("novo tamanho:", len(new_code))
    if not args.write:
        print("(dry-run; use --write)")
        return

    payload = {
        "name": snip.get("name"),
        "code": new_code,
        "scope": snip.get("scope") or "global",
        "active": snip.get("active", True),
    }
    put = urllib.request.Request(
        base + f"/wp-json/code-snippets/v1/snippets/{snip['id']}",
        data=json.dumps(payload).encode(),
        method="PUT",
        headers={**auth, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(put, timeout=90) as r:
        saved = json.load(r)
    ok = all(f"'{l}' => '{s}'" in (saved.get("code") or "") for l, s in pending.items())
    print("publicado | ativo", saved.get("active"), "| entradas confirmadas:", ok)


if __name__ == "__main__":
    main()