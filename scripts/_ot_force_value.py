# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import re
import urllib.request
from pathlib import Path

OT = Path(__file__).resolve().parents[1] / "projeto-migracao" / ".secrets" / "oficialteste.env"


def env():
    e = {}
    for line in OT.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def main():
    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    req = urllib.request.Request(
        base + "/wp-json/code-snippets/v1/snippets/24",
        headers={"Authorization": "Basic " + auth, "Accept": "application/json"},
    )
    sn = json.loads(urllib.request.urlopen(req, timeout=90).read().decode())
    code = sn["code"]
    for m in re.finditer(r"define\(\s*'PM_BLACK_NOV_FORCE'\s*,\s*'([^']*)'\s*\)", code):
        print("DEFINE", repr(m.group(1)), "at", m.start())
    print("--- head ---")
    print(code[:1400])


if __name__ == "__main__":
    main()
