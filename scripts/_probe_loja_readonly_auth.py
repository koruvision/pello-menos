# -*- coding: utf-8 -*-
"""READ-ONLY auth probe for loja — GET only, no writes."""
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "loja-readonly.env"


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def get(user, password, path):
    cfg = env()
    base = cfg["PM_LOJA_URL"].rstrip("/")
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = urllib.request.Request(
        base + path,
        method="GET",
        headers={
            "Authorization": "Basic " + token,
            "Accept": "application/json",
            "User-Agent": "pm-loja-readonly-probe/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode("utf-8", "replace")
            data = json.loads(body) if body.strip()[:1] in "{[" else body[:200]
            return r.status, data
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:300]


def main():
    cfg = env()
    user = cfg["PM_LOJA_USER"]
    pwd = cfg["PM_LOJA_APP_PASSWORD"]
    pwd_nospace = pwd.replace(" ", "")
    print("loja", cfg["PM_LOJA_URL"], "user", user)
    for label, u, p in (
        ("with_spaces", user, pwd),
        ("no_spaces", user, pwd_nospace),
    ):
        for path in (
            "/wp-json/wp/v2/users/me",
            "/wp-json/wc/v3/products?per_page=1",
            "/wp-json/wc/v3/system_status",
        ):
            st, data = get(u, p, path)
            summary = data if not isinstance(data, dict) else {
                k: data.get(k) for k in ("code", "message", "slug", "name", "id") if k in data
            }
            if isinstance(data, list):
                summary = f"list[{len(data)}]"
            print(label, path, st, summary)


if __name__ == "__main__":
    main()
