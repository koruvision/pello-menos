# -*- coding: utf-8 -*-
"""Dump WooCommerce email template fields (oficialteste)."""
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/oficialteste.env")

GROUPS = [
    "email_new_order",
    "email_cancelled_order",
    "email_customer_cancelled_order",
    "email_failed_order",
    "email_customer_failed_order",
    "email_customer_on_hold_order",
    "email_customer_processing_order",
    "email_customer_completed_order",
    "email_customer_refunded_order",
    "email_customer_invoice",
    "email_customer_note",
    "email_customer_reset_password",
    "email_customer_new_account",
]


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    return values


def call(path):
    cfg = env()
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    req = urllib.request.Request(
        cfg["PM_OFICIALTESTE_URL"].rstrip("/") + path,
        headers={"Authorization": "Basic " + token, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body[:400]


def main():
    interesting = (
        "enabled",
        "recipient",
        "subject",
        "heading",
        "additional_content",
        "email_type",
        "body",
        "content",
        "title",
    )
    for gid in GROUPS:
        st, rows = call(f"/wp-json/wc/v3/settings/{gid}")
        print("\n========", gid, st)
        if st != 200 or not isinstance(rows, list):
            print(rows)
            continue
        for row in rows:
            rid = row.get("id") or ""
            short = rid.split(gid + "_")[-1] if gid in rid else rid
            label = row.get("label") or short
            val = row.get("value")
            # skip huge unrelated
            if short not in interesting and not any(k in rid for k in interesting):
                # still show if label looks content-like
                if not any(
                    k in (label or "").lower()
                    for k in ("assunto", "título", "titulo", "conteúdo", "conteudo", "corpo", "habilitar", "destinat")
                ):
                    continue
            text = "" if val is None else str(val)
            if len(text) > 600:
                text = text[:600] + "…"
            print(f"  [{short}] {label}: {text!r}")


if __name__ == "__main__":
    main()
