# -*- coding: utf-8 -*-
"""Reordena os carrosseis de produto da home feminina pelo ranking de vendas.

O carrossel e HTML estatico gerado pelo Next; o re-export completo regride
ajustes feitos a mao (banners e link do SAC), entao aqui so os blocos
<article data-carousel-card> sao movidos, nada mais e tocado.

Cada card aparece 3x no HTML (clones do loop infinito); os clones sao movidos
junto, preservando o triplete.

Uso: python scripts/_reorder_home_rails.py [--write]
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "wordpress-loja" / "pm-home" / "home.html"

# Ranking real de unidades vendidas (pedidos de 01/08 a 13/11/2026).
CERA_SALES = [
    "virilha-cera",  # 174 un. — Virilha Total
    "perna-cera",  # 54 — Perna Inteira
    "buco-cera",  # 51 — Buço
    "axila-cera",  # 51 — Axila
    "meia-nadega-cera",  # 45 — Meia Nádega
    "virilha-cavada-cera",  # 41
    "meia-perna-cera",  # 35
    "virilha-cavada-faixa-cera",  # 28
    "coxa-cera",  # 24
    "sobrancelha-cera",  # 20
    "virilha-comum-cera",  # 19
    "faixa-cera",  # 15
    "nariz-cera",  # 13
    "virilha-comum-faixa-cera",  # 12
]

LASER_SALES = [
    "axilas-laser",  # 38 un. no trimestre
    "virilha-comum-laser",  # 8
    "buco-laser",  # 3
    "rosto-inteiro-laser",  # 2
    "virilha-laser",
    "virilha-cavada-laser",
    "pescoco-laser",
    "perna-laser",
    "orelhas-laser",
    "intergluteos-laser",
]

CERA_AREAS_IDS = [
    "virilha-cavada-cera",
    "meia-perna-cera",
    "virilha-cavada-faixa-cera",
    "coxa-cera",
    "design-sobrancelha",
    "bracos-cera",
    "virilha-comum-cera",
    "nadegas-cera",
    "queixo-cera",
    "costas-cera",
]

ART = re.compile(r'<article data-carousel-card="true"[\s\S]*?</article>')
SLUG = re.compile(r'href="/produto/([a-z0-9\-]+)')


def sort_rank(ranking, slug):
    return ranking.index(slug) if slug in ranking else len(ranking)


def panel_bounds(html: str, start_needle: str, nth: int = 0):
    """Retorna [inicio, fim) do painel que contem start_needle."""
    i = -1
    for _ in range(nth + 1):
        i = html.find(start_needle, i + 1)
        if i < 0:
            raise SystemExit(f"ancora nao encontrada: {start_needle!r}")
    # recua ate o <section do painel
    begin = html.rfind("<section ", 0, i)
    end = html.find("<section ", i)
    return begin, end if end > 0 else len(html)


def read_cards(fragment: str):
    cards = []
    for m in ART.finditer(fragment):
        s = SLUG.search(m.group(0))
        if not s:
            raise SystemExit("card sem slug")
        cards.append({"slug": s.group(1), "texto": m.group(0), "ini": m.start(), "fim": m.end()})
    if not cards:
        raise SystemExit("nenhum card no painel")
    # contiguidade: nada relevante entre os cards
    for a, b in zip(cards, cards[1:]):
        if fragment[a["fim"]:b["ini"]].strip():
            raise SystemExit(f"markup entre cards: {fragment[a['fim']:b['ini']][:80]!r}")
    return cards


def apply_order(fragment: str, cards, order):
    """Reescreve o trecho com os cards na ordem dada (por slug, todos os clones)."""
    por_slug: dict[str, list] = {}
    for c in cards:
        por_slug.setdefault(c["slug"], []).append(c)
    novos = []
    for slug in order:
        if slug not in por_slug:
            raise SystemExit(f"slug ausente no painel: {slug}")
        novos.extend(por_slug.pop(slug))
    # slugs nao citados mantem a ordem atual, no fim
    restantes = [c for c in cards if c["slug"] in por_slug]
    novos.extend(restantes)
    return (
        fragment[: cards[0]["ini"]]
        + "".join(c["texto"] for c in novos)
        + fragment[cards[-1]["fim"] :]
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    html = HOME.read_text(encoding="utf-8")
    original = html

    # 1) Cera em destaque — os 5 mais vendidos primeiro, resto pelo ranking
    b, e = panel_bounds(html, "Cera em destaque")
    frag = html[b:e]
    cards = read_cards(frag)
    novo = apply_order(frag, cards, CERA_SALES)
    html = html[:b] + novo + html[e:]
    print("cera destaque :", len(cards), "cards ->", [c["slug"] for c in read_cards(novo)][:6], "...")

    # 2) Cera por região — abre com os 4 seguintes; tira os 5 do primeiro carrossel
    b, e = panel_bounds(html, "Cera por região")
    frag = html[b:e]
    cards = read_cards(frag)
    # guarda um card de fora para incluir (virilha-cavada-faixa-cera)
    extra_card = None
    for c in read_cards(html[panel_bounds(html, "Cera em destaque")[0]:panel_bounds(html, "Cera em destaque")[1]]):
        if c["slug"] == "virilha-cavada-faixa-cera":
            extra_card = c["texto"]
            break
    if extra_card is None:
        raise SystemExit("card virilha-cavada-faixa-cera nao encontrado")
    mantidos = [c for c in cards if c["slug"] not in CERA_SALES[:5]]
    removidos = len(cards) - len(mantidos)
    # insere o card extra (clones) no lugar do primeiro card, antes de reordenar
    if "virilha-cavada-faixa-cera" not in {c["slug"] for c in mantidos}:
        clones = sum(1 for c in cards if c["slug"] == cards[0]["slug"])
        base = mantidos[0]
        injetados = [{"slug": "virilha-cavada-faixa-cera", "texto": extra_card,
                      "ini": base["ini"], "fim": base["fim"]} for _ in range(clones)]
        mantidos = mantidos + injetados
    frag2 = frag[: cards[0]["ini"]] + "".join(c["texto"] for c in mantidos) + frag[cards[-1]["fim"]:]
    cards2 = read_cards(frag2)
    novo = apply_order(frag2, cards2, CERA_AREAS_IDS)
    html = html[:b] + novo + html[e:]
    print(f"cera regiao   : {len(cards)} -> {len(cards2)} cards (removidos {removidos}), top:", [c["slug"] for c in read_cards(novo)][:4])

    # 3) Laser no rosto / no corpo
    for needle, rank in (("Laser no rosto", LASER_SALES), ("Laser no corpo", LASER_SALES)):
        b, e = panel_bounds(html, needle)
        frag = html[b:e]
        cards = read_cards(frag)
        atual = list(dict.fromkeys(c["slug"] for c in cards))
        order = sorted(atual, key=lambda s: sort_rank(rank, s))
        novo = apply_order(frag, cards, order)
        html = html[:b] + novo + html[e:]
        print(f"{needle:14s}:", len(cards), "cards, top:", order[:4])

    # 4) Esfoliação — sem venda registrada, mantem a ordem do catalogo
    print("esfoliacao    : sem vendas no periodo, ordem mantida")

    if html == original:
        print("\nnada a mudar")
        return
    print(f"\ntamanho: {len(original)} -> {len(html)} bytes")
    if not args.write:
        print("(dry-run; use --write)")
        return
    bak = HOME.with_suffix(".html.bak-rail")
    if not bak.exists():
        shutil.copy2(HOME, bak)
    HOME.write_text(html, encoding="utf-8")
    print("gravado. backup:", bak.name)


if __name__ == "__main__":
    main()
