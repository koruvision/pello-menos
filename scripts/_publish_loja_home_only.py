# -*- coding: utf-8 -*-
import base64
import io
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def main():
    vals = env()
    base = vals["PM_LOJA_URL"].rstrip("/")
    dest = base + "/wp-content/uploads/pm-home"
    clone = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"
    token = base64.b64encode(
        f"{vals['PM_LOJA_USER']}:{vals['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        text = (PM / "home.html").read_text(encoding="utf-8").replace(clone, dest)
        z.writestr("home.html", text.encode("utf-8"))
    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + token,
            "Content-Type": "application/zip",
            "User-Agent": "pm-home-fix",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        print("bundle", resp.status, resp.read()[:200])
    html = urllib.request.urlopen(
        urllib.request.Request(
            base + "/?v=cleanhome2",
            headers={"User-Agent": "x", "Cache-Control": "no-cache"},
        ),
        timeout=60,
    ).read().decode("utf-8", "replace")
    print(
        "live",
        "1,99",
        html.count("1,99"),
        "Produto R",
        html.count("Produto R"),
        "Cera destaque",
        "Cera em destaque" in html,
    )
    if "Produto R$ 1,99" in html or "produto-1-real" in html:
        raise SystemExit("still present")
    print("HOME_CLEAN_OK")


if __name__ == "__main__":
    main()
