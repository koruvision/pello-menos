# -*- coding: utf-8 -*-
"""Publica regra Accesstage pago → completed + account.php filtrado + backfill."""
from __future__ import annotations

import base64
import io
import json
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
SNIPPET = ROOT / "scripts" / "pm_order_paid_completed_snippet.php"
ACCOUNT = ROOT / "wordpress-loja" / "pm-home" / "account.php"
NAME = "pm-order-paid-completed"


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def main():
    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()

    def call(method, path, payload=None, raw=None, content_type="application/json", timeout=120):
        data = raw
        if payload is not None:
            data = json.dumps(payload).encode()
        req = urllib.request.Request(
            base + path,
            data=data,
            method=method,
            headers={
                "Authorization": "Basic " + auth,
                "Content-Type": content_type,
                "Accept": "application/json",
                "User-Agent": "pm-order-status",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
                return r.status, (json.loads(body) if body.strip()[:1] in "{[" else body)
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            return err.code, body

    code = SNIPPET.read_text(encoding="utf-8")
    if code.startswith("<?php"):
        code = code[5:].lstrip()

    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    if st != 200 or not isinstance(rows, list):
        raise SystemExit(f"snippets list {st} {rows}")
    sn = next((x for x in rows if x.get("name") == NAME), None)
    payload = {"name": NAME, "code": code, "scope": "global", "active": True}
    if sn:
        st, saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{sn['id']}", payload)
    else:
        st, saved = call("POST", "/wp-json/code-snippets/v1/snippets", payload)
    print("snippet", st, isinstance(saved, dict) and saved.get("id"), isinstance(saved, dict) and saved.get("active"))

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("account.php", ACCOUNT.read_bytes())
    st, resp = call(
        "POST",
        "/wp-json/pm-home/v1/bundle",
        raw=buf.getvalue(),
        content_type="application/zip",
        timeout=180,
    )
    print("account_bundle", st, str(resp)[:160])

    # Dispara backfill em lotes (80/request no init do snippet).
    for i in range(80):
        st_c, orders = call(
            "GET",
            "/wp-json/wc/v3/orders?status=processing&per_page=1&orderby=date&order=desc",
        )
        left = 0
        if st_c == 200 and isinstance(orders, list):
            # total via headers — refetch with a HEAD-like full page count
            req = urllib.request.Request(
                base + "/wp-json/wc/v3/orders?status=processing&per_page=1",
                headers={
                    "Authorization": "Basic " + auth,
                    "Accept": "application/json",
                    "User-Agent": "pm-order-status",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                left = int(r.headers.get("X-WP-Total") or "0")
        print(f"backfill_tick {i} processing_left={left}")
        if left == 0:
            break
        # Hit frontend to run init backfill
        try:
            urllib.request.urlopen(
                urllib.request.Request(base + "/?pm_status_backfill=" + str(i), headers={"User-Agent": "pm"}),
                timeout=90,
            ).read(64)
        except Exception as err:
            print("hit_home", type(err).__name__, err)
        time.sleep(0.4)

    # Sample recent
    st, recent = call("GET", "/wp-json/wc/v3/orders?per_page=8&orderby=date&order=desc")
    if isinstance(recent, list):
        for o in recent:
            email = (o.get("billing") or {}).get("email") or ""
            print("order", o.get("id"), o.get("status"), o.get("total"), email[:50])


if __name__ == "__main__":
    main()
