# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "oficialteste.env"


def main():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    for sid in [6, 7, 9, 12]:
        req = urllib.request.Request(
            f"{base}/wp-json/code-snippets/v1/snippets/{sid}",
            headers={
                "Authorization": "Basic " + auth,
                "User-Agent": "pm",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            s = json.loads(r.read().decode("utf-8", "replace"))
        print("=" * 60)
        print("SNIP", sid, s.get("name"), "active", s.get("active"), "scope", s.get("scope"))
        print(s.get("code") or "")
        print()


if __name__ == "__main__":
    main()
