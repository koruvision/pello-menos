# -*- coding: utf-8 -*-
"""Remove produto R$ 1,99 dos HTML de páginas (ex.: /servicos/cera) e republica na loja."""
from __future__ import annotations

import base64
import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"

NEEDLES = (
    "produto-1-real",
    "produto-r-1",
    "produto-r-199",
    "Produto R$ 1,99",
    "Produto de teste de R$ 1,99",
    "Produto de teste",
)

CARD_RE = re.compile(
    r"<article[^>]*>[\s\S]*?(?:produto-1-real|produto-r-199|produto-r-1|Produto R\$ 1,99|Produto de teste)[\s\S]*?</article>",
    re.I,
)
LINK_RE = re.compile(
    r'<a[^>]+href="[^"]*(?:produto-1-real|produto-r-199|produto-r-1)[^"]*"[\s\S]*?</a>',
    re.I,
)


def load_env():
    vals = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip()
    return {
        "url": vals["PM_LOJA_URL"].rstrip("/"),
        "user": vals["PM_LOJA_USER"],
        "password": vals["PM_LOJA_APP_PASSWORD"],
    }


def scrub_html(text: str) -> str:
    new = CARD_RE.sub("", text)
    new = LINK_RE.sub("", new)
    for n in NEEDLES:
        new = new.replace(n, "")
    new = new.replace("R$ 1,99", "").replace("1,99", "")
    return new


def main() -> None:
    changed: list[str] = []
    for path in PM.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if not any(n in text for n in NEEDLES):
            continue
        new = scrub_html(text)
        if new == text:
            continue
        path.write_text(new, encoding="utf-8")
        rel = path.relative_to(PM).as_posix()
        changed.append(rel)
        left = sum(new.count(n) for n in NEEDLES)
        print("scrubbed", rel, "left", left)

    pj = PM / "pages.json"
    if pj.is_file() and "produto-1-real" in pj.read_text(encoding="utf-8"):
        data = json.loads(pj.read_text(encoding="utf-8"))

        def drop(obj):
            if isinstance(obj, dict):
                for k in list(obj.keys()):
                    s = str(k) + " " + (obj[k] if isinstance(obj[k], str) else "")
                    if "produto-1-real" in s or "produto-r-1" in s:
                        obj.pop(k, None)
                    else:
                        drop(obj[k])
            elif isinstance(obj, list):
                keep = []
                for item in obj:
                    if "produto-1-real" in str(item) or "produto-r-1" in str(item):
                        continue
                    drop(item)
                    keep.append(item)
                obj[:] = keep

        drop(data)
        pj.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        changed.append("pages.json")
        print("cleaned pages.json")

    if not changed:
        print("nothing to scrub locally")
        return

    c = load_env()
    dest = c["url"] + "/wp-content/uploads/pm-home"
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in changed:
            path = PM / rel
            raw = path.read_bytes()
            if rel.endswith(".html"):
                raw = path.read_text(encoding="utf-8").replace(CLONE, dest).encode("utf-8")
            z.writestr(rel, raw)
            print("zip+", rel)
        if "pages.json" not in changed and (PM / "pages.json").is_file():
            z.write(PM / "pages.json", "pages.json")

    req = urllib.request.Request(
        c["url"] + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-scrub-cera-199",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        print("bundle", r.status, r.read()[:160])

    for path in (
        "/servicos/cera?v=rm199e",
        "/area/corpo?v=rm199e",
        "/produto/produto-1-real/?v=rm199e",
    ):
        try:
            html = (
                urllib.request.urlopen(
                    urllib.request.Request(
                        c["url"] + path,
                        headers={"User-Agent": "x", "Cache-Control": "no-cache"},
                    ),
                    timeout=60,
                )
                .read()
                .decode("utf-8", "replace")
            )
        except Exception as e:
            print("live", path, "ERR", e)
            continue
        hits = [n for n in NEEDLES if n in html] + (["1,99"] if "1,99" in html else [])
        print("live", path, "hits", hits or "none")

    print("OK", c["url"] + "/servicos/cera?v=rm199e")


if __name__ == "__main__":
    main()
