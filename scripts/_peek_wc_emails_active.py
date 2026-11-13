# -*- coding: utf-8 -*-
"""List WooCommerce email settings and which are enabled (oficialteste)."""
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/oficialteste.env")


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
            return e.code, body[:500]


def main():
    # Top-level email group
    st, top = call("/wp-json/wc/v3/settings/email")
    print("TOP", st, "rows", len(top) if isinstance(top, list) else top)

    # Discover email groups via settings groups
    st, groups = call("/wp-json/wc/v3/settings")
    email_groups = []
    if isinstance(groups, list):
        for g in groups:
            gid = g.get("id") or ""
            if "email" in gid.lower():
                email_groups.append(gid)
                print("GROUP", gid, "|", g.get("label"))

    # Also try common WC email setting IDs
    candidates = list(
        dict.fromkeys(
            email_groups
            + [
                "email",
                "email_new_order",
                "email_cancelled_order",
                "email_failed_order",
                "email_customer_on_hold_order",
                "email_customer_processing_order",
                "email_customer_completed_order",
                "email_customer_refunded_order",
                "email_customer_invoice",
                "email_customer_note",
                "email_customer_reset_password",
                "email_customer_new_account",
            ]
        )
    )

    results = []
    for gid in candidates:
        st, rows = call(f"/wp-json/wc/v3/settings/{gid}")
        if st != 200 or not isinstance(rows, list):
            continue
        enabled = None
        subject = None
        recipient = None
        title = gid
        for row in rows:
            rid = row.get("id") or ""
            if rid.endswith("_enabled") or rid == "enabled":
                enabled = row.get("value")
            if rid.endswith("_subject") or rid == "subject":
                subject = row.get("value")
            if rid.endswith("_recipient") or rid == "recipient":
                recipient = row.get("value")
            if rid.endswith("_title") or rid == "title":
                title = row.get("value") or title
        results.append(
            {
                "group": gid,
                "title": title,
                "enabled": enabled,
                "subject": subject,
                "recipient": recipient,
            }
        )

    print("\n=== EMAILS ===")
    for r in results:
        if r["group"] == "email":
            continue
        print(
            f"{r['enabled']!s:>5} | {r['group']:<40} | {r['title']}"
            + (f" | subj={r['subject']}" if r["subject"] else "")
            + (f" | to={r['recipient']}" if r["recipient"] else "")
        )

    active = [r for r in results if str(r.get("enabled")).lower() in ("yes", "true", "1")]
    inactive = [
        r
        for r in results
        if r["group"] != "email" and str(r.get("enabled")).lower() in ("no", "false", "0")
    ]
    print("\nACTIVE_COUNT", len(active))
    print("INACTIVE_COUNT", len(inactive))


if __name__ == "__main__":
    main()
