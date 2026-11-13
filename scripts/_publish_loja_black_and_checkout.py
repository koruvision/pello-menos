# -*- coding: utf-8 -*-
"""Publica checkout overlay + Black Nov (sem FORCE) na loja."""
from __future__ import annotations

import base64
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
SNIPPET_SRC = ROOT / "scripts" / "pm_black_nov_snippet.php"
PUB = ROOT / "scripts" / "pm_publicar_destino.py"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return {
        "url": e["PM_LOJA_URL"].rstrip("/"),
        "user": e["PM_LOJA_USER"],
        "password": e["PM_LOJA_APP_PASSWORD"],
    }


def call(c, method, path, payload=None, timeout=300):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    token = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + token,
            "User-Agent": "pm-loja-publish/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body[:1] in "[{" else body)


def main() -> None:
    c = cfg()
    print("loja", c["url"])
    common = [
        sys.executable,
        str(PUB),
        "--env",
        str(ENV),
        "--prefix",
        "PM_LOJA",
        "--permitir-loja",
    ]
    for args in (
        ["bundle"],
        ["snippet", "--routes", "home,masculino,produto,carrinho,conta,shell,loja"],
    ):
        print(">>", " ".join(args))
        subprocess.check_call(common + args, cwd=str(ROOT))

    # Black Nov PHP — sem FORCE (calendário real)
    code = SNIPPET_SRC.read_text(encoding="utf-8")
    assert "define('PM_BLACK_NOV_FORCE', '');" in code
    st, rows = call(c, "GET", "/wp-json/code-snippets/v1/snippets")
    sn_id = None
    if isinstance(rows, list):
        for row in rows:
            if (row.get("name") or "") == "pm-black-nov-pricing":
                sn_id = row.get("id")
                break
    payload = {
        "name": "pm-black-nov-pricing",
        "code": code,
        "scope": "global",
        "active": True,
    }
    if sn_id:
        st, saved = call(c, "PUT", f"/wp-json/code-snippets/v1/snippets/{sn_id}", payload)
    else:
        st, saved = call(c, "POST", "/wp-json/code-snippets/v1/snippets", payload)
    print(
        "black-nov snippet",
        st,
        saved.get("id") if isinstance(saved, dict) else saved,
        "FORCE empty",
        "PM_BLACK_NOV_FORCE', ''" in code or 'PM_BLACK_NOV_FORCE\', \'\'' in code,
    )

    for probe in (
        "/wp-content/uploads/pm-home/checkout-shell-c24.js?v=c35",
        "/wp-content/uploads/pm-home/checkout-loading.js?v=load3",
        "/wp-content/uploads/pm-home/black-nov-campaign.json",
        "/wp-content/uploads/pm-home/cart.js",
        "/wp-content/uploads/pm-home/media/images/products/axila-cera.webp",
        "/finalizar-pagamento/",
    ):
        try:
            st, body = call(c, "GET", probe)
            text = body if isinstance(body, str) else json.dumps(body)
            flags = []
            if "c24" in probe:
                flags.append(("openCheckoutLoading", "openCheckoutLoading" in text))
            if "loading.js" in probe:
                flags.append(("pmCheckoutLoading", "pmCheckoutLoading" in text))
            if "finalizar" in probe:
                flags.append(("load3", "checkout-loading.js?v=load3" in text))
                flags.append(("c35", "checkout-shell-c24.js?v=c35" in text))
            print(probe, st, flags or len(text))
        except Exception as err:
            print(probe, "ERR", err)


if __name__ == "__main__":
    main()
