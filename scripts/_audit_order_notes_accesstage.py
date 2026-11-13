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

    def get(path):
        req = urllib.request.Request(
            base + path,
            headers={
                "Authorization": "Basic " + auth,
                "User-Agent": "pm",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode("utf-8", "replace"))

    for oid in (48239, 48238, 48214, 48154):
        print("=" * 50, "ORDER", oid)
        notes = get(f"/wp-json/wc/v3/orders/{oid}/notes?per_page=50")
        for n in notes:
            note = n.get("note") or ""
            print("-", n.get("date_created"), note[:800])
        o = get(f"/wp-json/wc/v3/orders/{oid}")
        meta = {m["key"]: m["value"] for m in o.get("meta_data") or []}
        print("FULL META:")
        for k, v in meta.items():
            vs = str(v)
            if len(vs) > 200:
                vs = vs[:100] + f"…({len(vs)})…" + vs[-60:]
            print(f"  {k}: {vs}")


if __name__ == "__main__":
    main()
