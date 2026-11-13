# -*- coding: utf-8 -*-
"""Compara os IDs gravados no HTML de cada pagina de produto com o cart-related.json.

O HTML e estatico e carrega data-product-id / data-variation por unidade. Se a pagina
ficou para tras em relacao ao mapeamento, o carrinho envia a variacao ERRADA ao Woo
(foi o que aconteceu no pedido 51248: esfoliacao de coxa entrou como Coxa - Cera).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
CR = PM / "cart-related.json"
ROUTES = PM / "routes.json"


def main() -> None:
    cat = json.loads(CR.read_text(encoding="utf-8"))["products"]
    routes = json.loads(ROUTES.read_text(encoding="utf-8"))

    problemas = []
    ok = 0
    sem_pagina = []
    for slug, rel in sorted(routes.items()):
        row = cat.get(slug)
        if not row or not row.get("units"):
            continue
        page = PM / rel
        if not page.exists():
            sem_pagina.append(slug)
            continue
        html = page.read_text(encoding="utf-8", errors="replace")

        m_pid = re.search(r'data-product-id="([^"]*)"', html)
        page_pid = m_pid.group(1) if m_pid else ""
        want_pid = str(row.get("productId") or "")

        opts = {}
        for m in re.finditer(r'<option[^>]*value="([^"]+)"[^>]*data-variation="([^"]*)"', html):
            opts[m.group(1)] = m.group(2)

        difs = []
        if page_pid != want_pid:
            difs.append(f"productId pagina={page_pid} json={want_pid}")
        for uid, meta in row["units"].items():
            want = str(meta.get("variationId") or "")
            if uid in opts and want and opts[uid] != want:
                difs.append(f"{uid}: pagina={opts[uid]} json={want}")

        if difs:
            problemas.append({"slug": slug, "pagina": rel,
                              "nome": row.get("name"), "difs": difs[:6],
                              "total_difs": len(difs)})
        else:
            ok += 1

    print(f"rotas de produto: {len(routes)} | OK: {ok} | com divergencia: {len(problemas)} | sem pagina: {len(sem_pagina)}")
    print()
    for p in problemas:
        print(f"  {p['slug']:30s} {p['nome'][:34]:34s} {p['total_difs']:3d} difs")
        for d in p["difs"][:3]:
            print(f"      {d}")
    if sem_pagina:
        print("\nsem pagina:", sem_pagina[:10])

    (ROOT / "scripts" / "_product_pages_audit.json").write_text(
        json.dumps({"problemas": problemas, "ok": ok}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()