# -*- coding: utf-8 -*-
"""Fix mojibake titles + inject Woo favicons into all pm-home HTML."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PM = ROOT / "wordpress-loja" / "pm-home"

FAVICON_BLOCK = """
<link rel="icon" href="https://loja.pellomenos.com.br/wp-content/uploads/2021/04/cropped-favicon-50x50.png" sizes="32x32">
<link rel="icon" href="https://loja.pellomenos.com.br/wp-content/uploads/2021/04/cropped-favicon-300x300.png" sizes="192x192">
<link rel="apple-touch-icon" href="https://loja.pellomenos.com.br/wp-content/uploads/2021/04/cropped-favicon-300x300.png">
""".strip()

# Common mojibake fixes in titles (UTF-8 interpreted as Latin-1)
MOJIBAKE = {
    "DepilaÃ§Ã£o": "Depilação",
    "DepilaÃ§Ã£o a Cera": "Depilação a Cera",
    "DepilaÃ§Ã£o a Laser": "Depilação a Laser",
    "EsfoliaÃ§Ã£o": "Esfoliação",
    "Privacidade": "Privacidade",
    "PromoÃ§Ãµes": "Promoções",
    "ServiÃ§os": "Serviços",
    "CartÃ£o": "Cartão",
    "Presente": "Presente",
}


def fix_title(title: str) -> str:
    out = title
    for bad, good in MOJIBAKE.items():
        out = out.replace(bad, good)
    # generic: if still looks mojibaked, try latin1->utf8 roundtrip
    if "Ã" in out or "Â" in out:
        try:
            repaired = out.encode("latin-1").decode("utf-8")
            if "Ã" not in repaired:
                out = repaired
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return out


def ensure_favicon(html: str) -> str:
    if "cropped-favicon-50x50.png" in html:
        return html
    # remove old brand logo favicons if present
    html = re.sub(
        r'<link[^>]+rel=["\'][^"\']*icon[^"\']*["\'][^>]*>\s*',
        "",
        html,
        flags=re.I,
    )
    html = re.sub(
        r'<link[^>]+rel=["\']apple-touch-icon["\'][^>]*>\s*',
        "",
        html,
        flags=re.I,
    )
    if "<meta charset=" in html.lower():
        html = re.sub(
            r'(<meta charset=["\']?utf-8["\']?\s*/?>)',
            r"\1\n" + FAVICON_BLOCK,
            html,
            count=1,
            flags=re.I,
        )
    elif "</title>" in html.lower():
        html = re.sub(
            r"(</title>)",
            r"\1\n" + FAVICON_BLOCK,
            html,
            count=1,
            flags=re.I,
        )
    else:
        html = html.replace("<head>", "<head>\n" + FAVICON_BLOCK, 1)
    return html


def process_file(path: Path):
    text = path.read_text(encoding="utf-8")
    original = text
    m = re.search(r"<title>(.*?)</title>", text, flags=re.I | re.S)
    if m:
        fixed = fix_title(m.group(1))
        if fixed != m.group(1):
            text = text[: m.start(1)] + fixed + text[m.end(1) :]
    text = ensure_favicon(text)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main():
    changed = 0
    for path in sorted(PM.rglob("*.html")):
        if process_file(path):
            changed += 1
            title = re.search(
                r"<title>(.*?)</title>",
                path.read_text(encoding="utf-8"),
                flags=re.I | re.S,
            )
            print("updated", path.relative_to(PM), "->", title.group(1) if title else "?")
    print("changed", changed)


if __name__ == "__main__":
    main()
