# -*- coding: utf-8 -*-
"""Force-set email logo option via Code Snippet + WP JSON bootstrap (not pm-home HTML)."""
import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
SNAP = ROOT / "projeto-migracao" / ".secrets" / "email-brand-snapshot-oficialteste.json"
LOGO = "https://pellomenosoficialteste.companygenesis.com.br/wp-content/uploads/2026/10/pello-menos-email-logo.jpg"
NAME = "pm-email-logo-once"


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
        "User-Agent": "pm-email-logo/1.1",
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


def find_snippet():
    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets")
    if st != 200 or not isinstance(rows, list):
        raise SystemExit(f"snippets {st}")
    for row in rows:
        if row.get("name") == NAME:
            return row.get("id")
    return None


def save(active: bool):
    code = f"""// {NAME}
$dir = wp_upload_dir();
$dump = $dir['basedir'] . '/pm-home/email-logo-dump.json';
update_option('woocommerce_email_header_image', '{LOGO}');
update_option('woocommerce_email_header_image_width', '200');
update_option('woocommerce_email_header_alignment', 'center');
@file_put_contents($dump, wp_json_encode(array(
  'header' => get_option('woocommerce_email_header_image'),
  'width' => get_option('woocommerce_email_header_image_width'),
  'align' => get_option('woocommerce_email_header_alignment'),
  'base' => get_option('woocommerce_email_base_color'),
  'bg' => get_option('woocommerce_email_background_color'),
  'body_bg' => get_option('woocommerce_email_body_background_color'),
  'text' => get_option('woocommerce_email_text_color'),
  'footer_color' => get_option('woocommerce_email_footer_text_color'),
  'footer_text' => get_option('woocommerce_email_footer_text'),
  'ts' => time(),
)));
"""
    payload = {"name": NAME, "code": code, "scope": "global", "active": active}
    sid = find_snippet()
    if sid is None:
        st, saved = call("POST", "/wp-json/code-snippets/v1/snippets", payload)
    else:
        st, saved = call("PUT", f"/wp-json/code-snippets/v1/snippets/{sid}", payload)
    print("save", active, st, saved.get("id") if isinstance(saved, dict) else saved)
    if st not in (200, 201) or not isinstance(saved, dict):
        raise SystemExit("snippet save failed")
    return saved.get("id")


def bootstrap_wp():
    """Hit authenticated REST so plugins/snippets run (not static pm-home HTML)."""
    st, data = call("GET", "/wp-json/wp/v2/users/me")
    print("bootstrap", st, data.get("slug") if isinstance(data, dict) else data)


def fetch_dump():
    cfg = env()
    url = cfg["PM_OFICIALTESTE_URL"].rstrip("/") + f"/wp-content/uploads/pm-home/email-logo-dump.json?t={int(time.time())}"
    req = urllib.request.Request(url, headers={"User-Agent": "pm-email-logo/1.1", "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]


def main():
    sid = save(True)
    bootstrap_wp()
    time.sleep(1)
    st, dump = fetch_dump()
    print("dump", st, dump)
    # deactivate
    save(False)
    if st != 200 or not isinstance(dump, dict):
        raise SystemExit("dump missing — logo option not confirmed")
    if dump.get("header") != LOGO:
        raise SystemExit(f"header mismatch: {dump.get('header')}")
    if dump.get("base") != "#B3196F":
        print("WARN base color", dump.get("base"))
    if dump.get("footer_text") != "{site_title}":
        print("WARN footer_text changed", dump.get("footer_text"))

    # Guard new-order additional_content only (subject/heading empty = Woo defaults)
    st2, rows = call("GET", "/wp-json/wc/v3/settings/email_new_order")
    add = ""
    for row in rows if isinstance(rows, list) else []:
        if row.get("id") == "additional_content":
            add = row.get("value") or ""
    snap = json.loads(SNAP.read_text(encoding="utf-8")) if SNAP.is_file() else {}
    before_add = (snap.get("new_order_texts_before") or {}).get("additional_content") or ""
    # Normalize whitespace for compare
    def norm(s):
        return " ".join(str(s).split())

    same = norm(before_add) == norm(add) or (before_add and before_add[:80] in add)
    print("additional_content_ok", same, "len", len(add))
    if before_add and not same:
        # Still ok if only whitespace; hard fail if marker/test crept in
        if "PM_EMAIL_TEST" in add:
            raise SystemExit("test marker in additional_content")
    snap["logo_confirmed"] = dump
    SNAP.write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("DONE", LOGO)


if __name__ == "__main__":
    main()
