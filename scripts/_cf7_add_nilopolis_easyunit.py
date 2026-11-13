# -*- coding: utf-8 -*-
"""Adiciona Nilópolis ao select easyunit (laser) do CF7 #1831 na loja."""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/loja.env")
OUT = Path("scripts/_cf7_add_nilopolis_easyunit_result.json")
FORM_ID = 1831
OPTION = '"RJ - Nilópolis|nilopolis"'


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def call(method, path, payload=None):
    e = env()
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    base = e["PM_LOJA_URL"].rstrip("/")
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        base + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + auth,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "User-Agent": "pm-cf7-nil",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode()
            return r.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")


def get_content(form: dict) -> str:
    props = form.get("properties") or {}
    fp = props.get("form")
    if isinstance(fp, dict):
        return fp.get("content") or ""
    if isinstance(fp, str):
        return fp
    return form.get("form") or ""


def easyunit_opts(content: str):
    m = re.search(r"\[select\*? easyunit([\s\S]*?)\]", content, re.I)
    if not m:
        return None, []
    chunk = m.group(0)
    return chunk, re.findall(r'"([^"]+)"', chunk)


def main():
    st, form = call("GET", f"/wp-json/contact-form-7/v1/contact-forms/{FORM_ID}")
    if st != 200 or not isinstance(form, dict):
        raise SystemExit(f"cf7 get failed {st} {form}")
    content = get_content(form)
    chunk, opts = easyunit_opts(content)
    if not chunk:
        raise SystemExit("easyunit not found")
    if any("nilopolis" in o.lower() for o in opts):
        OUT.write_text(json.dumps({"ok": True, "already": True, "opts": opts}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("already has nilopolis", len(opts))
        return

    # Insert before Largo do Machado option if present, else before closing ]
    if '"RJ - Largo do Machado|largomachado"' in chunk:
        new_chunk = chunk.replace(
            '"RJ - Largo do Machado|largomachado"',
            OPTION + ' "RJ - Largo do Machado|largomachado"',
            1,
        )
    else:
        new_chunk = chunk[:-1].rstrip() + " " + OPTION + "]"
    new_content = content.replace(chunk, new_chunk, 1)
    if new_content == content:
        raise SystemExit("content unchanged after replace")

    # CF7 REST accepts top-level "form" string
    attempts = []
    for payload in (
        {"form": new_content},
        {"properties": {"form": new_content}},
        {
            "id": FORM_ID,
            "title": form.get("title"),
            "form": new_content,
            "mail": (form.get("properties") or {}).get("mail"),
            "mail_2": (form.get("properties") or {}).get("mail_2"),
            "messages": (form.get("properties") or {}).get("messages"),
            "additional_settings": (form.get("properties") or {}).get("additional_settings"),
        },
    ):
        st2, resp = call("POST", f"/wp-json/contact-form-7/v1/contact-forms/{FORM_ID}", payload)
        st3, form2 = call("GET", f"/wp-json/contact-form-7/v1/contact-forms/{FORM_ID}")
        content2 = get_content(form2 if isinstance(form2, dict) else {})
        _, opts2 = easyunit_opts(content2)
        ok = any("nilopolis" in o.lower() for o in opts2)
        attempts.append({"post": st2, "ok": ok, "opt_count": len(opts2)})
        if ok:
            OUT.write_text(
                json.dumps({"ok": True, "attempts": attempts, "opts": opts2}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print("OK added nilopolis", attempts)
            return

    # WP REST fallback
    st4, resp4 = call(
        "POST",
        f"/wp-json/wp/v2/wpcf7_contact_form/{FORM_ID}",
        {"form": new_content},
    )
    st5, form5 = call("GET", f"/wp-json/contact-form-7/v1/contact-forms/{FORM_ID}")
    content5 = get_content(form5 if isinstance(form5, dict) else {})
    _, opts5 = easyunit_opts(content5)
    ok5 = any("nilopolis" in o.lower() for o in opts5)
    attempts.append({"wp_v2": st4, "ok": ok5, "opt_count": len(opts5), "resp": str(resp4)[:200]})
    OUT.write_text(
        json.dumps({"ok": ok5, "attempts": attempts, "opts": opts5}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"ok": ok5, "attempts": attempts}, ensure_ascii=False, indent=2))
    if not ok5:
        raise SystemExit("failed to persist nilopolis in easyunit")


if __name__ == "__main__":
    main()
