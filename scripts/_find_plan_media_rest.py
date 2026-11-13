# -*- coding: utf-8 -*-
"""Find contract/term PDFs via Woo/WP REST on loja (read-only)."""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://loja.pellomenos.com.br"
OUT = Path(__file__).resolve().parents[1] / "wordpress-loja" / "pm-home" / "media" / "docs"
PUBLIC_DOCS = Path(__file__).resolve().parents[1] / "public" / "docs"


def get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 pm-audit"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def search_media(term: str):
    q = urllib.parse.urlencode(
        {"search": term, "per_page": 20, "media_type": "application"}
    )
    url = f"{BASE}/wp-json/wp/v2/media?{q}"
    try:
        rows = get_json(url)
    except Exception as exc:
        print("media search ERR", term, exc)
        return []
    out = []
    for row in rows:
        src = row.get("source_url") or ""
        title = (row.get("title") or {}).get("rendered") or ""
        mime = row.get("mime_type") or ""
        out.append({"id": row.get("id"), "title": title, "url": src, "mime": mime})
    return out


def search_pages(term: str):
    q = urllib.parse.urlencode({"search": term, "per_page": 10})
    try:
        return get_json(f"{BASE}/wp-json/wp/v2/pages?{q}")
    except Exception as exc:
        print("pages ERR", term, exc)
        return []


def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 pm-audit"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = resp.read()
    dest.write_bytes(data)
    print("saved", dest, len(data))
    return dest


def main() -> None:
    found = []
    for term in [
        "contrato",
        "termo",
        "consentimento",
        "clube do laser",
        "pré-pago",
        "prepago",
        "silver",
        "gold",
        "acordo",
    ]:
        rows = search_media(term)
        print("TERM", term, "hits", len(rows))
        for r in rows:
            print(" ", r["mime"], r["title"][:80], r["url"][-80:])
            found.append(r)
        pages = search_pages(term)
        for p in pages[:5]:
            link = p.get("link")
            title = (p.get("title") or {}).get("rendered")
            print("  PAGE", title, link)

    # unique by url
    by_url = {r["url"]: r for r in found if r.get("url")}
    # prefer pdfs
    pdfs = [r for r in by_url.values() if "pdf" in (r.get("mime") or "").lower() or r["url"].lower().endswith(".pdf")]
    print("unique pdfs", len(pdfs))
    mapping = {}
    for r in pdfs:
        title = re.sub(r"<[^>]+>", "", r["title"]).lower()
        url = r["url"]
        name = None
        if "clube" in title and "laser" in title:
            name = "contrato-clube-laser.pdf"
        elif "consentimento" in title or "dados pessoais" in title:
            name = "termo-consentimento-dados-pessoais.pdf"
        elif "silver" in title:
            name = "contrato-plano-silver.pdf"
        elif "gold" in title:
            name = "contrato-plano-gold.pdf"
        elif "pré" in title or "pre-pago" in title or "prepago" in title or "pré-pago" in title:
            name = "termo-prepago.pdf"
        elif "contrato" in title and "avulso" in title:
            name = "contrato-servico-avulso.pdf"
        elif "contrato" in title:
            name = "contrato-" + re.sub(r"[^a-z0-9]+", "-", title)[:40].strip("-") + ".pdf"
        elif "termo" in title:
            name = "termo-" + re.sub(r"[^a-z0-9]+", "-", title)[:40].strip("-") + ".pdf"
        if not name:
            continue
        dest = OUT / name
        download(url, dest)
        # mirror public
        pub = PUBLIC_DOCS / name
        pub.parent.mkdir(parents=True, exist_ok=True)
        pub.write_bytes(dest.read_bytes())
        mapping[name] = {"url": url, "title": r["title"]}
    (OUT / "_manifest.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("manifest", mapping.keys())


if __name__ == "__main__":
    main()
