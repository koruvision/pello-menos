# -*- coding: utf-8 -*-
"""Audita/apaga media em pm-home/media que nao e referenciada pelo front.

Por defeito e --dry (so reporta). Use --delete para apagar localmente.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sync_drive_product_images as sync  # noqa: E402

PM = ROOT / "wordpress-loja" / "pm-home"
MEDIA = PM / "media"
PUBLIC = ROOT / "public"
REPORT = ROOT / "scripts" / "_orphan_media_report.json"

WHITELIST_PREFIXES = (
    "brand/",
    "trust/",
    "docs/",
    "images/docs/",
    "fonts/",
)

WHITELIST_NAMES = {
    "cliente-1.png",
    "cliente-2.png",
    "cliente-3.png",
    "cliente-4.png",
    "cliente-5.png",
    "body-splash.png",
    "body-splash.webp",
    "body-splash-livre.webp",
    "body-splash-marcante.webp",
    "body-splash-autentica.webp",
    "plano-silver.webp",
    "plano-gold.webp",
    "plano-prepago.webp",
    "plano-clube-laser.webp",
    "plano-silver.png",
    "plano-gold.png",
    "plano-prepago.png",
    "plano-clube-laser.png",
}

WHITELIST_STEMS = {
    "plano-silver",
    "plano-gold",
    "plano-prepago",
    "plano-clube-laser",
    "body-splash",
    "body-splash-livre",
    "body-splash-marcante",
    "body-splash-autentica",
    "contrato-planos-assinaturas-vip",
    "contrato-clube-do-laser",
    "contrato-laser-servico-avulso",
    "pacote-servicos-cera-pagamento-antecipado",
    "termo-consentimento-dados-pessoais",
    "termo-termos-e-condicoes-de-uso-pello-menos",
    "contratos-indice",
    "termo-consentimento-pagina",
}


def collect_refs() -> set[str]:
    refs: set[str] = set()
    patterns = [
        re.compile(r"/wp-content/uploads/pm-home/media/([^\s\"'?#]+)", re.I),
        re.compile(r"media/([^\s\"'?#]+)", re.I),
        re.compile(r"/images/([^\s\"'?#]+)", re.I),
        re.compile(r"(?<![A-Za-z0-9_/])images/([^\s\"'?#]+)", re.I),
        re.compile(r"/brand/([^\s\"'?#]+)", re.I),
        re.compile(r"(?<![A-Za-z0-9_/])brand/([^\s\"'?#]+)", re.I),
        re.compile(r"/docs/([^\s\"'?#]+)", re.I),
    ]
    roots = [PM, ROOT / "src", PUBLIC]
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            # Skip media binary tree itself
            try:
                path.relative_to(MEDIA)
                continue
            except ValueError:
                pass
            if path.suffix.lower() not in {
                ".html",
                ".js",
                ".css",
                ".ts",
                ".tsx",
                ".json",
                ".md",
                ".php",
            }:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pat in patterns:
                for m in pat.findall(text):
                    cleaned = m.replace("\\", "/").lstrip("/").split("?", 1)[0]
                    if cleaned:
                        refs.add(cleaned)
    bare = {Path(r).name for r in refs}
    refs |= bare
    return refs


def catalog_used_paths() -> set[str]:
    """Paths that catalog / gift / splash imply even if HTML not re-exported."""
    used: set[str] = set()
    ids = sync.product_ids()
    for pid, audience in ids.items():
        if audience == "masculino":
            for ext in (".webp", ".png", ".jpg", ".jpeg"):
                used.add(f"images/products/male/{pid}{ext}")
                used.add(f"products/male/{pid}{ext}")
                used.add(f"{pid}{ext}")
        else:
            for ext in (".webp", ".png", ".jpg", ".jpeg"):
                used.add(f"images/products/{pid}{ext}")
                used.add(f"products/{pid}{ext}")
                used.add(f"{pid}{ext}")
    extras = [
        "body-splash",
        "body-splash-livre",
        "body-splash-marcante",
        "body-splash-autentica",
        "cartao-presente-80",
        "plano-silver",
        "plano-gold",
        "plano-prepago",
        "plano-clube-laser",
    ]
    for stem in extras:
        for ext in (".webp", ".png", ".jpg", ".jpeg"):
            used.add(f"images/products/{stem}{ext}")
            used.add(f"{stem}{ext}")
    return used


def protected(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    if any(rel.startswith(p) for p in WHITELIST_PREFIXES):
        return True
    if "/docs/" in f"/{rel}" or rel.startswith("docs/"):
        return True
    name = Path(rel).name
    stem = Path(rel).stem
    if name in WHITELIST_NAMES or stem in WHITELIST_STEMS:
        return True
    if name.lower().endswith((".pdf", ".docx")):
        return True
    if stem.startswith("contrato-") or stem.startswith("termo-") or stem.startswith("pacote-servicos"):
        return True
    if stem.startswith("plano-"):
        return True
    return False


def is_referenced(rel: str, name: str, refs: set[str]) -> bool:
    candidates = {
        rel,
        name,
        f"images/{rel}" if not rel.startswith("images/") else rel,
        rel[7:] if rel.startswith("images/") else f"images/{rel}",
    }
    # products/male/foo.webp also as images/products/male/foo.webp
    if rel.startswith("images/"):
        candidates.add(rel[len("images/") :])
    else:
        candidates.add(f"images/{rel}")
    return any(c in refs for c in candidates)


def find_orphans(refs: set[str]) -> tuple[list[Path], int]:
    orphans: list[Path] = []
    kept = 0
    for path in MEDIA.rglob("*"):
        if not path.is_file():
            continue
        # skip non-media junk
        if path.name in {"bundle.zip", ".DS_Store", "Thumbs.db"}:
            orphans.append(path)
            continue
        rel = path.relative_to(MEDIA).as_posix()
        name = path.name
        if protected(rel):
            kept += 1
            continue
        if is_referenced(rel, name, refs):
            kept += 1
            continue
        orphans.append(path)
    return orphans, kept


def main() -> None:
    delete = "--delete" in sys.argv
    dry = not delete
    refs = collect_refs()
    refs |= catalog_used_paths()
    print("refs", len(refs), "mode", "delete" if delete else "dry")
    orphans, kept = find_orphans(refs)
    freed = sum(p.stat().st_size for p in orphans)
    rows = []
    for path in sorted(orphans, key=lambda p: p.relative_to(MEDIA).as_posix()):
        rel = path.relative_to(MEDIA).as_posix()
        size = path.stat().st_size
        rows.append({"rel": rel, "bytes": size})
        print(("DEL" if delete else "ORPHAN"), rel, size)
        if delete:
            path.unlink()
    report = {
        "mode": "delete" if delete else "dry",
        "kept": kept,
        "orphan_count": len(orphans),
        "freed_bytes": freed,
        "orphans": rows,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("kept", kept, "orphans", len(orphans), "freed_bytes", freed)
    print("report", REPORT.relative_to(ROOT))


if __name__ == "__main__":
    main()
