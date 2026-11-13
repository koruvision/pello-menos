# -*- coding: utf-8 -*-
"""Set woocommerce_email_header_image on oficialteste (REST v3 hides this field)."""
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
SNAP = ROOT / "projeto-migracao" / ".secrets" / "email-brand-snapshot-oficialteste.json"
LOGO = "https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/2026/10/pello-menos-email-logo.jpg"


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def call(method, path, payload=None):
    cfg = env()
    base = cfg["PM_OFICIALTESTE_URL"].rstrip("/")
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    data = None if payload is None else json.dumps(payload).encode()
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
        "User-Agent": "pm-email-logo/1.0",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body.strip()[:1] in "{[" else body
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:800]


def via_v4():
    for path in (
        "/wp-json/wc/v4/settings/email",
        "/wp-json/wc/v3/settings/email",
    ):
        st, data = call("GET", path)
        print("GET", path, st, type(data).__name__, (list(data)[:8] if isinstance(data, dict) else ""))
        if st == 200 and isinstance(data, dict):
            print("keys", list(data.keys())[:20])
    # Try PUT v4
    payloads = [
        {"values": {"woocommerce_email_header_image": LOGO}},
        {"woocommerce_email_header_image": LOGO},
        {"id": "woocommerce_email_header_image", "value": LOGO},
    ]
    for payload in payloads:
        st, data = call("PUT", "/wp-json/wc/v4/settings/email", payload)
        print("PUT v4", st, str(data)[:200])
        if st in (200, 201):
            return True
    return False


def via_snippet():
    """One-shot: temp snippet updates option then we deactivate it."""
    # Code Snippets: no opening <?php tag
    code = (
        "// pm-email-logo-once — auto\n"
        f"update_option('woocommerce_email_header_image', '{LOGO}');\n"
        "update_option('woocommerce_email_header_image_width', '200');\n"
        "update_option('woocommerce_email_header_alignment', 'center');\n"
    )
    # List snippets
    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets")
    print("snippets", st, len(rows) if isinstance(rows, list) else rows)
    existing = None
    if isinstance(rows, list):
        for row in rows:
            if row.get("name") == "pm-email-logo-once":
                existing = row.get("id")
    payload = {
        "name": "pm-email-logo-once",
        "code": code,
        "scope": "global",
        "active": True,
    }
    if existing:
        st, saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{existing}", payload)
    else:
        st, saved = call("POST", "/wp-json/code-snippets/v1/snippets", payload)
    print("snippet save", st, saved.get("id") if isinstance(saved, dict) else saved)
    if st not in (200, 201) or not isinstance(saved, dict):
        return False
    sid = saved.get("id")
    # Hit front page to execute global snippet
    cfg = env()
    urllib.request.urlopen(
        urllib.request.Request(
            cfg["PM_OFICIALTESTE_URL"].rstrip("/") + "/?pm=email-logo",
            headers={"User-Agent": "pm-email-logo/1.0"},
        ),
        timeout=60,
    ).read(200)
    # Deactivate snippet so it does not keep running
    st2, off = call(
        "PUT",
        f"/wp-json/code-snippets/v1/snippets/{sid}",
        {"name": "pm-email-logo-once", "code": code, "scope": "global", "active": False},
    )
    print("snippet off", st2, off.get("active") if isinstance(off, dict) else off)
    return True


def verify_via_snippet_read():
    """Read option back with a tiny inactive→active probe snippet that writes to a transient — skip.
    Instead check email preview HTML if available."""
    cfg = env()
    base = cfg["PM_OFICIALTESTE_URL"].rstrip("/")
    # Woo email preview endpoint (admin) may need cookies; try public-ish
    for path in (
        "/?preview_woocommerce_mail=true&type=new_order",
        "/wp-admin/admin-ajax.php?action=woocommerce_email_preview",
    ):
        try:
            req = urllib.request.Request(base + path, headers={"User-Agent": "pm"})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8", "replace")
                print("preview", path, r.status, "logo" in body.lower(), LOGO in body, len(body))
        except Exception as e:
            print("preview", path, "ERR", e)


def main():
    snap = {}
    if SNAP.is_file():
        snap = json.loads(SNAP.read_text(encoding="utf-8"))
    snap["logo_url"] = LOGO
    # Remember we need to store previous header image; unknown via REST — leave blank
    snap.setdefault("previous_header_image", None)
    SNAP.write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if via_v4():
        print("logo set via wc/v4")
    else:
        print("falling back to code snippet option update")
        if not via_snippet():
            raise SystemExit("failed to set logo")

    # Also set width/alignment via known REST ids
    for sid, value in (
        ("woocommerce_email_header_image_width", "200"),
        ("woocommerce_email_header_alignment", "center"),
    ):
        st, saved = call("PUT", f"/wp-json/wc/v3/settings/email/{sid}", {"value": value})
        print("PUT", sid, st, saved.get("value") if isinstance(saved, dict) else saved)

    # Verify new order texts still intact
    st, rows = call("GET", "/wp-json/wc/v3/settings/email_new_order")
    texts = {}
    if isinstance(rows, list):
        for row in rows:
            if row.get("id") in ("subject", "heading", "additional_content", "recipient"):
                texts[row["id"]] = row.get("value")
    before = snap.get("new_order_texts_before") or {}
    print("texts_same", before == texts if before else "no_before")
    print("texts_now", {k: str(v)[:60] for k, v in texts.items()})
    if before and before != texts:
        raise SystemExit("TEXT CHANGED — abort")
    print("DONE logo", LOGO)


if __name__ == "__main__":
    main()
