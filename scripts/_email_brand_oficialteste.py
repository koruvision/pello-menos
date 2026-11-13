# -*- coding: utf-8 -*-
"""Upload email logo + apply Woo email brand colors on oficialteste (texts untouched)."""
from __future__ import annotations

import base64
import json
import mimetypes
import shutil
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
SNAP = ROOT / "projeto-migracao" / ".secrets" / "email-brand-snapshot-oficialteste.json"
SRC_LOGO = Path(
    r"C:\Users\GC1\.cursor\projects\c-Users-GC1-Desktop-pello-menos\assets"
    r"\c__Users_GC1_AppData_Roaming_Cursor_User_workspaceStorage_5fbd0f4a155bce6742dfd1809ecf2a22_images_6a738a99ac7d7ffc645fc909-05f345ed-5ba2-4771-b631-3792838b5ff1.png"
)
LOCAL_LOGO = ROOT / "wordpress-loja" / "pm-home" / "media" / "brand" / "pello-menos-email-logo.png"

# Brand palette from plan
BASE_COLOR = "#B3196F"
BG_COLOR = "#F5F0F2"
BODY_BG = "#FFFFFF"
TEXT_COLOR = "#1A1A1A"
FOOTER_TEXT_COLOR = "#6A1043"

# Settings we may change (brand only)
BRAND_IDS = {
    "woocommerce_email_header_image",
    "header_image",
    "woocommerce_email_base_color",
    "base_color",
    "woocommerce_email_background_color",
    "background_color",
    "woocommerce_email_body_background_color",
    "body_background_color",
    "woocommerce_email_text_color",
    "text_color",
    "woocommerce_email_footer_text_color",
    "footer_text_color",
}

# Must remain identical
TEXT_GUARD_IDS = {
    "woocommerce_email_footer_text",
    "footer_text",
}


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def site():
    cfg = env()
    return {
        "base": cfg["PM_OFICIALTESTE_URL"].rstrip("/"),
        "auth": base64.b64encode(
            f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
        ).decode(),
    }


def call(method, path, payload=None, raw=None, content_type=None, headers_extra=None):
    s = site()
    data = raw if raw is not None else (None if payload is None else json.dumps(payload).encode())
    headers = {
        "Authorization": "Basic " + s["auth"],
        "Accept": "application/json",
        "User-Agent": "pm-email-brand/1.0",
    }
    if headers_extra:
        headers.update(headers_extra)
    if content_type:
        headers["Content-Type"] = content_type
    elif payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(s["base"] + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read().decode("utf-8", "replace")
            if not body:
                return r.status, {}
            if body.strip().startswith(("{", "[")):
                return r.status, json.loads(body)
            return r.status, body
    except urllib.error.HTTPError as e:
        raw_body = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw_body)
        except Exception:
            parsed = raw_body[:800]
        return e.code, parsed


def list_email_settings():
    st, data = call("GET", "/wp-json/wc/v3/settings/email")
    if st != 200 or not isinstance(data, list):
        raise SystemExit(f"email settings failed: {st} {data}")
    return data


def setting_map(rows):
    return {row.get("id"): row for row in rows if isinstance(row, dict) and row.get("id")}


def put_setting(setting_id, value):
    st, saved = call(
        "PUT",
        f"/wp-json/wc/v3/settings/email/{setting_id}",
        {"value": value},
    )
    return st, saved


def upload_logo():
    LOCAL_LOGO.parent.mkdir(parents=True, exist_ok=True)
    if not SRC_LOGO.is_file():
        raise SystemExit(f"missing source logo: {SRC_LOGO}")
    shutil.copyfile(SRC_LOGO, LOCAL_LOGO)
    print("local_logo", LOCAL_LOGO, LOCAL_LOGO.stat().st_size)

    blob = LOCAL_LOGO.read_bytes()
    filename = "pello-menos-email-logo.png"
    ctype = mimetypes.guess_type(filename)[0] or "image/png"
    # WP REST media upload: binary body + Content-Disposition
    st, media = call(
        "POST",
        "/wp-json/wp/v2/media",
        raw=blob,
        content_type=ctype,
        headers_extra={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
    print("media_upload", st)
    if st not in (200, 201) or not isinstance(media, dict):
        raise SystemExit(f"media upload failed: {st} {media}")
    url = media.get("source_url") or media.get("guid", {}).get("rendered")
    print("media_id", media.get("id"), "url", url)
    if not url:
        raise SystemExit("no source_url on media")
    return url, media.get("id")


def snapshot_new_order_texts():
    st, rows = call("GET", "/wp-json/wc/v3/settings/email_new_order")
    if st != 200 or not isinstance(rows, list):
        return {}
    out = {}
    for row in rows:
        sid = row.get("id")
        if sid in ("subject", "heading", "additional_content", "recipient", "enabled"):
            out[sid] = row.get("value")
    return out


def main():
    # 1) Upload
    logo_url, media_id = upload_logo()

    # 2) Backup
    rows = list_email_settings()
    by_id = setting_map(rows)
    print("email_setting_ids", sorted(by_id.keys()))
    before_texts = snapshot_new_order_texts()
    snap = {
        "logo_url": logo_url,
        "media_id": media_id,
        "email_settings": {k: v.get("value") for k, v in by_id.items()},
        "new_order_texts_before": before_texts,
    }
    SNAP.write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("snapshot", SNAP)

    # Resolve actual ids present
    def pick(*candidates):
        for c in candidates:
            if c in by_id:
                return c
        return None

    header_id = pick("woocommerce_email_header_image", "header_image")
    base_id = pick("woocommerce_email_base_color", "base_color")
    bg_id = pick("woocommerce_email_background_color", "background_color")
    body_bg_id = pick("woocommerce_email_body_background_color", "body_background_color")
    text_id = pick("woocommerce_email_text_color", "text_color")
    footer_color_id = pick("woocommerce_email_footer_text_color", "footer_text_color")
    footer_text_id = pick("woocommerce_email_footer_text", "footer_text")

    updates = {}
    if header_id:
        updates[header_id] = logo_url
    if base_id:
        updates[base_id] = BASE_COLOR
    if bg_id:
        updates[bg_id] = BG_COLOR
    if body_bg_id:
        updates[body_bg_id] = BODY_BG
    if text_id:
        updates[text_id] = TEXT_COLOR
    if footer_color_id:
        updates[footer_color_id] = FOOTER_TEXT_COLOR

    print("will_update", updates.keys())
    if footer_text_id:
        print("footer_text_untouched", True, "len", len(str(by_id[footer_text_id].get("value") or "")))

    # 3) Apply brand only
    for sid, value in updates.items():
        st, saved = put_setting(sid, value)
        ok = isinstance(saved, dict) and str(saved.get("value", "")) == str(value)
        print("PUT", sid, st, "ok" if ok else saved)

    # 4) Verify
    rows2 = list_email_settings()
    by2 = setting_map(rows2)
    after_texts = snapshot_new_order_texts()

    def val(mid):
        return None if mid is None else (by2.get(mid) or {}).get("value")

    checks = {
        "header_is_new": val(header_id) == logo_url,
        "base_color": val(base_id) == BASE_COLOR if base_id else None,
        "bg_color": val(bg_id) == BG_COLOR if bg_id else None,
        "body_bg": val(body_bg_id) == BODY_BG if body_bg_id else None,
        "text_color": val(text_id) == TEXT_COLOR if text_id else None,
        "new_order_texts_same": before_texts == after_texts,
    }
    print("verify", json.dumps(checks, ensure_ascii=False))
    if before_texts != after_texts:
        print("TEXT DRIFT", before_texts, after_texts)
        raise SystemExit(1)
    if not checks["header_is_new"]:
        raise SystemExit("header image not applied")
    print("DONE", logo_url)


if __name__ == "__main__":
    main()
