# -*- coding: utf-8 -*-
import json
import re
import urllib.request
from pathlib import Path

BASE = "https://loja.pellomenos.com.br"
OUT = Path(__file__).resolve().parents[1] / "wordpress-loja" / "pm-home" / "media" / "docs"
PUBLIC = Path(__file__).resolve().parents[1] / "public" / "docs"

PAGES = {
    "contrato-planos-assinaturas-vip": "/contrato-planos-assinaturas-vip/",
    "contrato-clube-do-laser": "/contrato-clube-do-laser/",
    "contrato-laser-servico-avulso": "/contrato-laser-servico-avulso/",
    "pacote-servicos-cera-pagamento-antecipado": "/pacote-de-servicos-cera-pagamento-antecipado/",
    "termo-consentimento-pagina": "/termo-de-consentimento-para-tratamento-de-dados-pessoais-e-o-contrato/",
    "contratos-indice": "/contratos-pello-menos/",
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 pm-audit"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    manifest = {}
    if (OUT / "_manifest.json").exists():
        manifest = json.loads((OUT / "_manifest.json").read_text(encoding="utf-8"))

    for name, path in PAGES.items():
        url = BASE + path
        data = fetch(url)
        html = data.decode("utf-8", "replace")
        dest = OUT / f"{name}.html"
        dest.write_bytes(data)
        (PUBLIC / f"{name}.html").write_bytes(data)
        print("page", name, len(data))
        manifest[dest.name] = {"url": url, "kind": "html"}
        # files linked
        for m in re.findall(r"https?://loja\.pellomenos\.com\.br/wp-content/uploads/[^\s\"'<>]+", html, re.I):
            lower = m.lower()
            if not any(lower.endswith(ext) for ext in (".pdf", ".docx", ".doc")):
                continue
            fname = Path(m.split("?")[0]).name
            # normalize
            if "consentimento" in lower:
                fname = "termo-consentimento-dados-pessoais.pdf"
            elif "clube" in lower and lower.endswith(".docx"):
                fname = "contrato-clube-do-laser.docx"
            elif "avulso" in lower:
                fname = "contrato-laser-servico-avulso" + Path(m).suffix.lower()
            elif "vip" in lower or "assinatura" in lower:
                fname = "contrato-planos-assinaturas-vip" + Path(m).suffix.lower()
            elif "pre" in lower or "antecipado" in lower or "pacote" in lower:
                fname = "contrato-prepago-pacote-cera" + Path(m).suffix.lower()
            blob = fetch(m)
            (OUT / fname).write_bytes(blob)
            (PUBLIC / fname).write_bytes(blob)
            manifest[fname] = {"url": m, "kind": "file"}
            print(" file", fname, len(blob))

    # also known media from earlier REST
    extra = [
        (
            "https://loja.pellomenos.com.br/wp-content/uploads/2022/03/ctto-clube-do-laser-p-1-a-8-printadas.docx",
            "contrato-clube-do-laser.docx",
        ),
    ]
    for url, fname in extra:
        if (OUT / fname).exists():
            continue
        try:
            blob = fetch(url)
            (OUT / fname).write_bytes(blob)
            (PUBLIC / fname).write_bytes(blob)
            manifest[fname] = {"url": url, "kind": "file"}
            print("extra", fname, len(blob))
        except Exception as exc:
            print("extra ERR", fname, exc)

    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("docs", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
