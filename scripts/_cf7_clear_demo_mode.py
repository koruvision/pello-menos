# -*- coding: utf-8 -*-
"""Desliga demo_mode do CF7 #1831 na loja (causa Beatriz: processa e não conclui)."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "loja.env"


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return e


def call(method, path, payload=None):
    e = env()
    base = e["PM_LOJA_URL"].rstrip("/")
    auth = base64.b64encode(f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()).decode()
    data = None if payload is None else json.dumps(payload).encode()
    headers = {
        "Authorization": "Basic " + auth,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "pm-cf7-demo",
    }
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode()
            return r.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode()
        try:
            return err.code, json.loads(body)
        except json.JSONDecodeError:
            return err.code, {"raw": body[:800]}


def add_settings(data):
    return (data.get("properties") or {}).get("additional_settings")


def main():
    st, data = call("GET", "/wp-json/contact-form-7/v1/contact-forms/1831")
    print("before", add_settings(data))

    # Prefer clear entirely (no demo_mode line). Fallback: explicit off.
    st, saved = call(
        "POST",
        "/wp-json/contact-form-7/v1/contact-forms/1831",
        {"additional_settings": ""},
    )
    print("cleared_response", st, add_settings(saved))
    st, data = call("GET", "/wp-json/contact-form-7/v1/contact-forms/1831")
    after = add_settings(data)
    print("after_clear_get", after)

    content = ""
    if isinstance(after, dict):
        content = str(after.get("content") or "")
        settings = after.get("settings") or []
    else:
        settings = []

    still_on = "demo_mode: on" in content or any(
        isinstance(row, list) and len(row) >= 2 and row[0] == "demo_mode" and row[1] is True
        for row in settings
    )
    if still_on:
        st, saved = call(
            "POST",
            "/wp-json/contact-form-7/v1/contact-forms/1831",
            {"additional_settings": "demo_mode: off"},
        )
        print("force_off_response", st, add_settings(saved))
        st, data = call("GET", "/wp-json/contact-form-7/v1/contact-forms/1831")
        after = add_settings(data)
        print("after_force_get", after)

    content = str((after or {}).get("content") if isinstance(after, dict) else after or "")
    settings = (after or {}).get("settings") if isinstance(after, dict) else []
    on = "demo_mode: on" in content or any(
        isinstance(row, list) and len(row) >= 2 and row[0] == "demo_mode" and row[1] is True
        for row in (settings or [])
    )
    if on:
        raise SystemExit("demo_mode still ON")
    print("CF7_DEMO_MODE_OFF")


if __name__ == "__main__":
    main()
