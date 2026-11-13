# -*- coding: utf-8 -*-
"""Inventario read-only de links/botoes de WhatsApp em loja.pellomenos.com.br.

Rastreia paginas do site (sitemap + links internos), o HTML servido por cada uma e os
arquivos JS/PHP proprios, procurando wa.me / api.whatsapp.com / web.whatsapp.com,
com o numero formatado ou nao. NAO altera nada.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

BASE = "https://loja.pellomenos.com.br"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "scripts" / "_whatsapp_audit.json"
UA = {"User-Agent": "Mozilla/5.0 (pm-audit)"}
TARGET = "552125494265"
PAT = re.compile(r"(wa\.me/|api\.whatsapp\.com/send|web\.whatsapp\.com/send)[^\s\"'<>)]*", re.I)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return ""


def seeds() -> list[str]:
    html = fetch(BASE + "/")
    links = set(re.findall(r'href="(?:' + re.escape(BASE) + r')?([^"#?]+)', html))
    pages = {"/"}
    for l in links:
        if l.startswith("/") and not l.startswith("//"):
            if re.search(r"\.(jpg|jpeg|png|webp|svg|css|js|pdf)$", l, re.I):
                continue
            pages.add(l)
    for extra in ("/servicos", "/servicos/cera", "/servicos/laser", "/servicos/esfoliacao",
                  "/planos", "/produtos", "/carrinho", "/finalizar-pagamento/",
                  "/masculino/servicos", "/masculino/servicos/cera", "/masculino/servicos/laser",
                  "/compra-nao-realizada/", "/termos", "/privacidade"):
        pages.add(extra)
    return sorted(pages)


def numbers_in(url: str) -> list[str]:
    return re.findall(r"\d{10,15}", urllib.parse.unquote(url))


def main() -> None:
    rows = []
    pages = seeds()
    print("paginas a varrer:", len(pages))

    # assets JS proprios carregados no site
    js_assets = set()
    for p in pages:
        h = fetch(BASE + p)
        for m in re.findall(r'src="([^"]+\.js[^"]*)"', h):
            if "pm-home" in m or "wp-content" in m:
                js_assets.add(m if m.startswith("http") else BASE + m)
        for m in PAT.findall(h):
            pass
        for m in re.finditer(r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=|web\.whatsapp\.com/send\?phone=)([^\s\"'<>)]*)", h, re.I):
            full = m.group(0)
            nums = numbers_in(full)
            rows.append({
                "page": p,
                "where": "html",
                "url": full if full.startswith("http") else "https://" + full,
                "numbers": nums,
                "is_target": TARGET in (nums[0][-13:] if nums else ""),
                "snippet": h[max(0, m.start() - 90): m.end() + 40].replace("\n", " ")[:220],
            })

    print("assets js:", len(js_assets))
    for a in sorted(js_assets):
        body = fetch(a)
        if not body:
            continue
        for m in re.finditer(r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=|web\.whatsapp\.com/send\?phone=)([^\s\"'<>)]*)", body, re.I):
            full = m.group(0)
            nums = numbers_in(full)
            rows.append({
                "page": "(asset)",
                "where": a,
                "url": "https://" + full if not full.startswith("http") else full,
                "numbers": nums,
                "is_target": TARGET in (nums[0][-13:] if nums else ""),
                "snippet": body[max(0, m.start() - 90): m.end() + 40].replace("\n", " ")[:220],
            })

    # numeros soltos (sem link) tambem interessam
    raw_hits = []
    for p in pages:
        h = fetch(BASE + p)
        for pat, label in ((r"\(?21\)?\s*2549[\s\-]?4265", "21 2549-4265"),
                           (r"55212549426 5?".replace(" ", ""), "552125494265")):
            for m in re.finditer(pat, h):
                raw_hits.append({"page": p, "match": label,
                                 "snippet": h[max(0, m.start() - 80): m.end() + 60].replace("\n", " ")[:200]})

    by_target = [r for r in rows if r["is_target"]]
    others = [r for r in rows if not r["is_target"]]
    print()
    print("ocorrencias de link whatsapp:", len(rows))
    print("  -> numero alvo (552125494265):", len(by_target))
    print("  -> outros numeros:", len(others))
    print("  -> textos com o numero (sem link):", len(raw_hits))

    OUT.write_text(json.dumps({
        "target": TARGET,
        "pages_scanned": pages,
        "assets_scanned": sorted(js_assets),
        "links": rows,
        "text_hits": raw_hits,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("relatorio:", OUT)

    for r in by_target[:25]:
        print(f"  [{r['page']}] {r['where']} -> {r['url'][:90]} | nums={r['numbers'][:2]}")
    if others:
        print("\noutros numeros:")
        for r in others[:15]:
            print(f"  [{r['page']}] {r['url'][:90]} | nums={r['numbers'][:2]}")


if __name__ == "__main__":
    main()