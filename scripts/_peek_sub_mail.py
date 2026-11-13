# -*- coding: utf-8 -*-
"""Read-only: CF7 #1831 mail + subscription-related plugins/settings."""
import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/oficialteste.env")
BASE_HTML = "https://pellomenosoficialteste.companygenesis.com.br"


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
    st, form = call("/wp-json/contact-form-7/v1/contact-forms/1831")
    print("cf7", st)
    props = (form.get("properties") if isinstance(form, dict) else {}) or {}
    for key in ("mail", "mail_2"):
        m = props.get(key) or {}
        print("---", key)
        print("  active:", m.get("active"))
        print("  recipient:", m.get("recipient"))
        print("  subject:", m.get("subject"))
        print("  attachments:", m.get("attachments"))
        body = m.get("body") or ""
        print("  body:", repr(body[:500]))

    add = props.get("additional_settings") or ""
    print("additional_settings:", repr(add[:500]) if isinstance(add, str) else add)

    st, plugs = call("/wp-json/wp/v2/plugins")
    if isinstance(plugs, list):
        for p in plugs:
            blob = ((p.get("plugin") or "") + " " + (p.get("name") or "")).lower()
            if any(
                k in blob
                for k in (
                    "subscri",
                    "assinat",
                    "contrato",
                    "pdf",
                    "mail",
                    "smtp",
                    "membership",
                    "yith",
                    "woocommerce",
                )
            ):
                print("plugin", p.get("status"), p.get("plugin"), "|", (p.get("name") or "")[:70])

    # Woo email settings list (ids only)
    st, emails = call("/wp-json/wc/v3/settings/email")
    if isinstance(emails, list):
        print("woo_email_settings", len(emails))
        for row in emails[:20]:
            print(" ", row.get("id"), "=", str(row.get("value"))[:80])

    # HTML page: any mention of contrato/pdf in checkout scripts
    html = urllib.request.urlopen(
        BASE_HTML + "/finalizar-pagamento/?pm=submail", timeout=60
    ).read().decode("utf-8", "replace")
    for pat in ("contrato", "assinatura", "attachment", ".pdf", "subscribemode"):
        print("html_hit", pat, html.lower().count(pat.lower()))


if __name__ == "__main__":
    main()
