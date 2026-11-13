# -*- coding: utf-8 -*-
"""Probe + reversible test of WooCommerce new-order additional_content on oficialteste."""
import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
MARKER = "<!--PM_EMAIL_TEST_OK-->"


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
        "User-Agent": "pm-email-test/1.0",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body.strip().startswith(("{", "[")) else body
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw[:500]
        return e.code, parsed


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "probe"
    # Woo REST settings group for new order email
    group = "/wp-json/wc/v3/settings/email_new_order"
    status, data = call("GET", group)
    print("GET", group, status)
    if status != 200:
        # try listing email settings
        st2, data2 = call("GET", "/wp-json/wc/v3/settings/email")
        print("GET email", st2, data2 if not isinstance(data2, list) else f"{len(data2)} items")
        if isinstance(data2, list):
            for row in data2[:20]:
                print(" -", row.get("id"), row.get("label"))
        sys.exit(1)

    by_id = {row.get("id"): row for row in data} if isinstance(data, list) else {}
    add = by_id.get("woocommerce_new_order_settings[additional_content]") or by_id.get(
        "additional_content"
    )
    if not add:
        print("ids:", sorted(by_id.keys()))
        # print all for discovery
        for row in data:
            print(row.get("id"), "=", (row.get("value") or "")[:80])
        sys.exit(1)

    setting_id = add["id"]
    original = add.get("value") or ""
    print("setting", setting_id)
    print("original_len", len(original))
    print("original_preview", original[:120].replace("\n", " "))

    if mode == "probe":
        return

    put_path = f"/wp-json/wc/v3/settings/email_new_order/{setting_id}"

    if mode == "set":
        if MARKER in original:
            print("marker already present; skip set")
            return
        next_val = original.rstrip() + f"\n\n<p>{MARKER} Teste PM — frase temporária.</p>\n"
        st, saved = call("PUT", put_path, {"value": next_val})
        print("PUT set", st)
        if isinstance(saved, dict):
            print("saved_has_marker", MARKER in str(saved.get("value", "")))
        return

    if mode == "verify":
        st, cur = call("GET", put_path)
        print("GET one", st)
        val = cur.get("value") if isinstance(cur, dict) else ""
        print("has_marker", MARKER in str(val))
        print("preview", str(val)[-200:].replace("\n", " "))
        return

    if mode == "revert":
        st, cur = call("GET", put_path)
        val = cur.get("value") if isinstance(cur, dict) else original
        if MARKER not in str(val):
            print("no marker; nothing to revert")
            return
        # remove our test paragraph
        cleaned = str(val)
        cleaned = cleaned.replace(f"\n\n<p>{MARKER} Teste PM — frase temporária.</p>\n", "")
        cleaned = cleaned.replace(f"<p>{MARKER} Teste PM — frase temporária.</p>", "")
        cleaned = cleaned.replace(MARKER + " Teste PM — frase temporária.", "")
        cleaned = cleaned.replace(MARKER, "")
        st2, saved = call("PUT", put_path, {"value": cleaned.strip() + ("\n" if cleaned.strip() else "")})
        print("PUT revert", st2)
        if isinstance(saved, dict):
            print("marker_gone", MARKER not in str(saved.get("value", "")))
            print("preview", str(saved.get("value", ""))[:120].replace("\n", " "))
        return

    print("usage: probe|set|verify|revert")
    sys.exit(2)


if __name__ == "__main__":
    main()
