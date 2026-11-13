# -*- coding: utf-8 -*-
"""Smoke: docs/planos/produtos ainda 200; órfãos apagados 404."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
REPORT = ROOT / "scripts" / "_orphan_media_report.json"


def base_url() -> str:
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e["PM_LOJA_URL"].rstrip("/")


def probe(url: str) -> int:
    req = urllib.request.Request(
        url, headers={"User-Agent": "pm-smoke-media", "Cache-Control": "no-cache"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            r.read(64)
            return r.status
    except urllib.error.HTTPError as err:
        return err.code


def main() -> None:
    base = base_url()
    media = base + "/wp-content/uploads/pm-home/media"
    must_200 = [
        f"{media}/images/docs/contrato-planos-assinaturas-vip.html",
        f"{media}/images/docs/contrato-clube-do-laser.html",
        f"{media}/images/docs/contrato-laser-servico-avulso.html",
        f"{media}/images/docs/pacote-servicos-cera-pagamento-antecipado.html",
        f"{media}/images/docs/termo-consentimento-dados-pessoais.pdf",
        f"{media}/images/docs/termo-termos-e-condicoes-de-uso-pello-menos.pdf",
        f"{media}/images/products/plano-silver.webp",
        f"{media}/images/products/plano-gold.webp",
        f"{media}/images/products/axila-cera.webp",
        f"{media}/images/products/male/axila-cera-masc.webp",
        f"{media}/images/hero/hero-campaign-center.jpg",
        f"{media}/brand/logo-footer.png",
    ]
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    must_404 = [
        f"{media}/{row['rel']}"
        for row in (report.get("orphans") or [])[:8]
    ]
    failed = []
    for url in must_200:
        st = probe(url)
        print("KEEP", st, url.split("/pm-home/")[-1])
        if st != 200:
            failed.append(("want200", st, url))
    for url in must_404:
        st = probe(url)
        print("GONE", st, url.split("/pm-home/")[-1])
        if st != 404:
            failed.append(("want404", st, url))
    if failed:
        print("FAIL", failed)
        raise SystemExit(1)
    print("SMOKE_MEDIA_PURGE_OK")


if __name__ == "__main__":
    main()
