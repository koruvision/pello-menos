# -*- coding: utf-8 -*-
import base64
import io
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"
PATH = PM / "pages" / "loja.html"


def env():
    vals = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip()
    return vals


def main():
    t = PATH.read_text(encoding="utf-8")
    print("before", t.count("produto-1-real"), t.count("1,99"))
    pat = re.compile(
        r"<article[^>]*>[\s\S]*?(?:produto-1-real|Produto R\$ 1,99|Produto de teste)[\s\S]*?</article>",
        re.I,
    )
    new, n = pat.subn("", t)
    print("articles removed", n)
    for s in (
        "produto-1-real",
        "produto-r-199",
        "Produto R$ 1,99",
        "Produto de teste de R$ 1,99",
        "Produto de teste",
    ):
        new = new.replace(s, "")
    # wipe leftover bare 1,99 only inside loja page if still tied to empty title
    new = new.replace("R$ 1,99", "")
    new = new.replace("1,99", "")
    PATH.write_text(new, encoding="utf-8")
    print("after", new.count("produto-1-real"), new.count("1,99"))

    vals = env()
    base = vals["PM_LOJA_URL"].rstrip("/")
    dest = base + "/wp-content/uploads/pm-home"
    token = base64.b64encode(
        f"{vals['PM_LOJA_USER']}:{vals['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()
    html = PATH.read_text(encoding="utf-8").replace(CLONE, dest)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pages/loja.html", html.encode("utf-8"))
        # also re-send black-nov cleaned earlier
        bn = PM / "black-nov-campaign.json"
        if bn.is_file():
            z.write(bn, "black-nov-campaign.json")
    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + token,
            "Content-Type": "application/zip",
            "User-Agent": "pm-scrub-loja-199",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        print("bundle", r.status, r.read()[:120])

    live = (
        urllib.request.urlopen(
            urllib.request.Request(
                base + "/loja/?v=rm199d",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode("utf-8", "replace")
    )
    print(
        "live loja",
        "produto-1-real" in live,
        "1,99" in live,
        "Produto R$" in live,
        "Teste" in live and "Produto" in live,
    )


if __name__ == "__main__":
    main()
