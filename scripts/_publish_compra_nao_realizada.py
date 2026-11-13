# -*- coding: utf-8 -*-
"""Publica compra-nao-realizada.html na loja."""
from __future__ import annotations

import base64
import io
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
HTML = ROOT / "wordpress-loja" / "pm-home" / "compra-nao-realizada.html"


def main() -> None:
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    base = e["PM_LOJA_URL"].rstrip("/")
    assert "loja.pellomenos.com.br" in base
    text = HTML.read_text(encoding="utf-8")
    if "items-center gap-2" not in text or "<svg" not in text:
        raise SystemExit("icons missing in local html")
    dest = base + "/wp-content/uploads/pm-home"
    text = text.replace(
        "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home",
        dest,
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("compra-nao-realizada.html", text.encode("utf-8"))
    tok = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    req = urllib.request.Request(
        base + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-fail-icons",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        print("bundle", r.status, r.read()[:200])
    live = urllib.request.urlopen(
        urllib.request.Request(
            base + "/compra-nao-realizada/?v=icons1",
            headers={"User-Agent": "pm", "Cache-Control": "no-cache"},
        ),
        timeout=60,
    ).read().decode("utf-8", "replace")
    print(
        "live",
        "items-center gap-2" in live,
        live.count("<svg"),
        "Tentar" in live,
        "WhatsApp" in live,
    )
    if "items-center gap-2" not in live or live.count("<svg") < 3:
        raise SystemExit("live missing icons")
    print("FAIL_PAGE_ICONS_OK")


if __name__ == "__main__":
    main()
