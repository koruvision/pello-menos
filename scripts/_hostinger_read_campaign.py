# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "hostinger-ot.env"
OT = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
BASE = "https://developers.hostinger.com"


def env():
    e = {}
    for path in (ENV, OT):
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def read(token, user, domain, file_path):
    url = (
        BASE
        + f"/api/hosting/v1/accounts/{user}/domains/{domain}/files/content?"
        + urllib.parse.urlencode({"path": file_path})
    )
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
            "User-Agent": "pm",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        body = json.loads(r.read().decode())
    text = body.get("content") or ""
    if isinstance(text, dict):
        text = text.get("content") or ""
    return text


def main():
    e = env()
    token, user = e["PM_HOSTINGER_API_TOKEN"], e["PM_HOSTINGER_ACCOUNT"]
    domain = e.get("PM_HOSTINGER_DOMAIN") or "pellomenosoficialteste.companygenesis.com.br"

    campaign = read(token, user, domain, "wp-content/uploads/pm-home/black-nov-campaign.json")
    print("=== black-nov-campaign.json ===")
    print(campaign)

    shell = read(token, user, domain, "wp-content/uploads/pm-home/checkout-shell-c24.js")
    print("\n=== shell markers ===")
    for pat in (
        r"base\s*=\s*\"[^\"]+\"",
        r"campaignPriceForWooId",
        r"catalogIdByWooId",
        r"__PM_BLACK_PHASE__",
        r"pmBlackNov",
        r"c37|c36|c35|c38",
        r"totalamount",
        r"FORCE",
    ):
        hits = re.findall(pat, shell)
        print(pat, "->", hits[:8], "count", len(hits))

    # locate enqueue snippet references in HTML? try reading active theme header or look for snippet file copies
    for p in (
        "wp-content/uploads/pm-home/README.md",
        "wp-content/uploads/pm-home/pm-home-loader.php",
        "wp-content/uploads/pm-home/loader.php",
    ):
        try:
            t = read(token, user, domain, p)
            print("READ", p, len(t))
            print(t[:300])
        except Exception as err:
            print("MISS", p, err)


if __name__ == "__main__":
    main()
