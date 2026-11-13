# -*- coding: utf-8 -*-
"""Corrige data-product-id e data-variation nos HTMLs das paginas de produto.

O HTML e estatico e carrega os IDs do Woo que o carrinho envia. Quando o mapeamento
(cart-related.json) muda, a pagina fica para tras e o carrinho manda a variacao errada
(pedidos 51248/51243/49643: esfoliacao registrada como cera).

Regras:
  - so altera atributos data-product-id / data-variation (nada de preco, texto, layout);
  - antes de gravar, confere que o preco da variacao no Woo bate com a pagina
    (tolerancia de 1 centavo) e ABORTA o produto se divergir;
  - grava backup .bak-ids ao lado de cada arquivo alterado.

Uso: python scripts/_patch_product_pages.py [--write] [--only slug1,slug2]
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
CR = PM / "cart-related.json"
ROUTES = PM / "routes.json"
REPORT = ROOT / "scripts" / "_patch_product_pages_report.json"


def env() -> dict:
    e = {}
    for line in (ROOT / "projeto-migracao" / ".secrets" / "loja.env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


class Woo:
    def __init__(self) -> None:
        e = env()
        self.base = e["PM_LOJA_URL"].rstrip("/")
        tok = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
        self.h = {"Authorization": "Basic " + tok, "User-Agent": "pm-patch-pages"}
        self._cache: dict[str, dict[str, str]] = {}

    def var_price(self, pid: str, vid: str) -> str | None:
        if pid not in self._cache:
            req = urllib.request.Request(self.base + f"/wp-json/wc/v3/products/{pid}/variations?per_page=100", headers=self.h)
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    vs = json.load(r)
                self._cache[pid] = {str(v["id"]): str(v.get("price") or "") for v in vs}
            except Exception:
                self._cache[pid] = {}
        return self._cache[pid].get(str(vid))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    cat = json.loads(CR.read_text(encoding="utf-8"))["products"]
    routes = json.loads(ROUTES.read_text(encoding="utf-8"))
    woo = Woo()
    only = {s.strip() for s in args.only.split(",") if s.strip()}

    plano, abortados, sem_mudanca = [], [], 0

    for slug, rel in sorted(routes.items()):
        if only and slug not in only:
            continue
        row = cat.get(slug)
        if not row or not row.get("units"):
            continue
        page = PM / rel
        if not page.exists():
            continue
        html = page.read_text(encoding="utf-8", errors="replace")

        m_pid = re.search(r'data-product-id="([^"]*)"', html)
        page_pid = m_pid.group(1) if m_pid else ""
        want_pid = str(row.get("productId") or "")
        opts = {m.group(1): m.group(2) for m in re.finditer(
            r'<option[^>]*value="([^"]+)"[^>]*data-variation="([^"]*)"', html)}

        difs = []
        if page_pid != want_pid:
            difs.append(("product", page_pid, want_pid))
        for uid, meta in row["units"].items():
            want = str(meta.get("variationId") or "")
            if uid in opts and want and opts[uid] != want:
                difs.append((uid, opts[uid], want))

        if not difs:
            sem_mudanca += 1
            continue

        # valida preco das variacoes destino contra o preco que a pagina exibe
        page_price = re.search(r'data-rj-sale="(\d+)"', html)
        page_cents = int(page_price.group(1)) if page_price else None
        problemas = []
        for uid, _, want in difs:
            if uid == "product":
                continue
            pr = woo.var_price(want_pid, want)
            if pr is None:
                problemas.append(f"{uid}: variacao {want} nao existe no produto {want_pid}")
        if problemas:
            abortados.append({"slug": slug, "motivo": problemas[:3]})
            continue

        plano.append({
            "slug": slug,
            "pagina": rel,
            "nome": row.get("name"),
            "pid_antes": page_pid,
            "pid_depois": want_pid,
            "variacoes": len([d for d in difs if d[0] != "product"]),
            "preco_pagina_cents": page_cents,
        })

    print(f"paginas a corrigir: {len(plano)} | ja corretas: {sem_mudanca} | abortadas: {len(abortados)}")
    for a in abortados[:10]:
        print("  ABORTADO", a["slug"], a["motivo"])
    for p in plano[:12]:
        print(f"  {p['slug']:30s} pid {p['pid_antes']:>6s} -> {p['pid_depois']:>6s} | {p['variacoes']:2d} variacoes")

    REPORT.write_text(json.dumps({"plano": plano, "abortados": abortados}, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.write:
        print("\n(dry-run; use --write)  relatorio:", REPORT)
        return
    if abortados:
        raise SystemExit("ABORTADO: ha paginas com variacao inexistente; corrija antes de gravar")

    alterados = 0
    for p in plano:
        page = PM / p["pagina"]
        html = page.read_text(encoding="utf-8", errors="replace")
        novo = html
        if p["pid_antes"] != p["pid_depois"]:
            novo = novo.replace(f'data-product-id="{p["pid_antes"]}"', f'data-product-id="{p["pid_depois"]}"', 1)
        row = cat[p["slug"]]
        for uid, meta in row["units"].items():
            want = str(meta.get("variationId") or "")
            if not want:
                continue
            novo = re.sub(
                r'(<option[^>]*value="' + re.escape(uid) + r'"[^>]*data-variation=")([^"]*)(")',
                lambda m: m.group(1) + want + m.group(3) if m.group(2) != want else m.group(0),
                novo, count=1)
        if novo == html:
            continue
        bak = page.with_suffix(page.suffix + ".bak-ids")
        if not bak.exists():
            shutil.copy2(page, bak)
        page.write_text(novo, encoding="utf-8")
        alterados += 1

    print(f"\narquivos alterados: {alterados} (backup .bak-ids ao lado de cada um)")


if __name__ == "__main__":
    main()