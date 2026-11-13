# -*- coding: utf-8 -*-
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "oficialteste.env"


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def call(path, method="GET", payload=None):
    cfg = env()
    base = cfg["PM_OFICIALTESTE_URL"].rstrip("/")
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    data = None if payload is None else json.dumps(payload).encode()
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
        "User-Agent": "pm-probe",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body.strip()[:1] in "{[" else body
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:500]


def main():
    st, groups = call("/wp-json/wc/v3/settings")
    print("groups", st)
    if isinstance(groups, list):
        for g in groups:
            print(" ", g.get("id"), g.get("label"))

    st, rows = call("/wp-json/wc/v3/settings/email")
    print("\nemail settings", st)
    if isinstance(rows, list):
        for row in rows:
            print(" ", row.get("id"), "=", repr(row.get("value"))[:100], "type", row.get("type"))

    # Try options endpoint (needs manage_options)
    for key in (
        "woocommerce_email_header_image",
        "woocommerce_email_header_image_width",
        "woocommerce_email_header_alignment",
    ):
        st, opt = call(f"/wp-json/wp/v2/settings")  # once
        break
    st, settings = call("/wp-json/wp/v2/settings")
    print("\nwp settings", st, type(settings).__name__)
    if isinstance(settings, dict):
        for k, v in settings.items():
            if "email" in k.lower() or "woo" in k.lower() or "header" in k.lower():
                print(" ", k, "=", str(v)[:80])

    # Direct option via custom? try wc batch update with header_image id
    for sid in (
        "woocommerce_email_header_image",
        "header_image",
        "email_header_image",
    ):
        st, one = call(f"/wp-json/wc/v3/settings/email/{sid}")
        print("GET", sid, st, one if not isinstance(one, dict) else one.get("id", one))

    # Update option via undocumented REST - try PUT option through WC
    # Use /wp-json/wc/v3/settings/email with batch
    logo = "https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/2026/10/pello-menos-email-logo.jpg"
    st, put = call(
        "/wp-json/wc/v3/settings/email/woocommerce_email_header_image",
        method="PUT",
        payload={"value": logo},
    )
    print("PUT header_image", st, put if not isinstance(put, dict) else {k: put.get(k) for k in ("id", "value", "code", "message")})


if __name__ == "__main__":
    main()
