# -*- coding: utf-8 -*-
"""Remove slug saojoaomeriti dos dumps AccesStage e (se API permitir) do OT Hostinger."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DUMPS = [
    ROOT / "scripts/_hostinger_ot_dumps/shopwise-child__functions.php",
    ROOT / "scripts/_hostinger_ot_dumps/wp-content__themes__shopwise-child__functions.php",
]
ENV = ROOT / "projeto-migracao/.secrets/hostinger-ot.env"
BASE = "https://developers.hostinger.com"
ENTRY = re.compile(
    r"[ \t]*['\"]saojoaomeriti['\"]\s*=>\s*['\"][^'\"]*['\"],?\r?\n",
    re.I,
)


def scrub_text(text: str) -> str:
    return ENTRY.sub("", text)


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def main() -> None:
    for path in DUMPS:
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8")
        new = scrub_text(raw)
        path.write_text(new, encoding="utf-8")
        print(path.name, "removed", raw != new, "left", "saojoaomeriti" in new.lower())

    # Best-effort: rewrite OT live file if Hostinger supports PUT content
    e = env()
    token = e["PM_HOSTINGER_API_TOKEN"]
    user = e["PM_HOSTINGER_ACCOUNT"]
    domain = e.get("PM_HOSTINGER_DOMAIN") or "pellomenosoficialteste.companygenesis.com.br"
    path = "wp-content/themes/shopwise-child/functions.php"
    # read
    url = (
        f"{BASE}/api/hosting/v1/accounts/{user}/domains/{domain}/files/content?"
        + urllib.parse.urlencode({"path": path})
    )
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": "pm-scrub-sjm/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as err:
        print("hostinger read failed", err)
        return

    text = ""
    if isinstance(body, dict):
        for k in ("content", "data", "file_content", "body", "value"):
            v = body.get(k)
            if isinstance(v, str):
                text = v
                break
            if isinstance(v, dict) and isinstance(v.get("content"), str):
                text = v["content"]
                break
    if not text:
        print("no content from hostinger")
        return
    new = scrub_text(text)
    if new == text:
        print("hostinger live already without saojoaomeriti")
        return
    # try PUT/PATCH
    payload = json.dumps({"path": path, "content": new}).encode("utf-8")
    for method in ("PUT", "POST", "PATCH"):
        write_url = f"{BASE}/api/hosting/v1/accounts/{user}/domains/{domain}/files/content"
        wreq = urllib.request.Request(
            write_url,
            data=payload,
            method=method,
            headers={
                "Authorization": "Bearer " + token,
                "User-Agent": "pm-scrub-sjm/1.0",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(wreq, timeout=120) as r:
                print("hostinger write", method, r.status)
                return
        except urllib.error.HTTPError as err:
            print("hostinger write", method, err.code)
        except Exception as err:
            print("hostinger write", method, type(err).__name__, err)


if __name__ == "__main__":
    main()
