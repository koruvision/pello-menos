# -*- coding: utf-8 -*-
import re
import urllib.request
from pathlib import Path

BASE = "https://loja.pellomenos.com.br"
PAGES = [
    "/produto/plano-de-assinatura-vip-silver/",
    "/produto/plano-de-assinatura-vip-gold/",
    "/produto/clube-do-laser/",
    "/produto/pre-pago-pello-menos/",
]
OUT = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "plan-html"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 pm-audit"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", "replace")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in PAGES:
        html = fetch(BASE + path)
        slug = path.strip("/").split("/")[-1]
        (OUT / f"{slug}.html").write_text(html, encoding="utf-8")
        print("===", path, "len", len(html))
        for needle in [
            "pdf",
            "contrato",
            "termo",
            "acordo",
            "consentimento",
            "download",
            "wp-content/uploads",
            "saiba mais",
            "attachment",
        ]:
            print(f"  count {needle}:", html.lower().count(needle.lower()))
        # extract upload URLs
        ups = sorted(
            set(
                re.findall(
                    r"https?://loja\.pellomenos\.com\.br/wp-content/uploads/[^\s\"'<>]+",
                    html,
                    re.I,
                )
            )
        )
        print("  uploads", len(ups))
        for u in ups:
            if any(
                x in u.lower()
                for x in (".pdf", "termo", "contrat", "acordo", "consent", "anexo")
            ):
                print("   *", u)
        # also relative
        rel = sorted(
            set(
                re.findall(
                    r"/wp-content/uploads/[^\s\"'<>]+",
                    html,
                    re.I,
                )
            )
        )
        for u in rel:
            if any(
                x in u.lower()
                for x in (".pdf", "termo", "contrat", "acordo", "consent", "anexo")
            ):
                print("   R", u)
        # look near 'CONSULTA' / 'Contrato'
        for m in re.finditer(
            r".{0,80}(Contrato|Termo de Consentimento|saiba mais|anexo).{0,120}",
            html,
            re.I | re.S,
        ):
            snippet = re.sub(r"\s+", " ", m.group(0))[:200]
            print("  CTX", snippet)


if __name__ == "__main__":
    main()
