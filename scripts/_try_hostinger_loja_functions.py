# -*- coding: utf-8 -*-
"""Tenta ler shopwise-child/functions.php da loja via mesma conta Hostinger OT."""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "hostinger-ot.env"
OUT = ROOT / "projeto-migracao" / ".secrets" / "_accesstage_loja_keys_sanitized.json"
DUMP = ROOT / "scripts" / "_hostinger_loja_dumps"
BASE = "https://developers.hostinger.com"

CANDIDATE_DOMAINS = [
    "loja.pellomenos.com.br",
    "pellomenos.com.br",
    "www.pellomenos.com.br",
]


def env():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def api(token, path, query=None):
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": "pm-hostinger-loja/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body else {})


def extract_text(body):
    if isinstance(body, dict):
        for k in ("content", "data", "file_content", "body", "value"):
            v = body.get(k)
            if isinstance(v, str):
                return v
            if isinstance(v, dict) and "content" in v:
                return str(v["content"])
        return json.dumps(body)
    return str(body)


def parse_keys(src: str, var_name: str) -> dict[str, str]:
    m = re.search(rf"\${re.escape(var_name)}\s*=\s*array\s*\((.*?)\)\s*;", src, flags=re.S | re.I)
    if not m:
        return {}
    out = {}
    for km in re.finditer(r"['\"]([a-z0-9_-]+)['\"]\s*=>\s*['\"]([^'\"]+)['\"]", m.group(1), flags=re.I):
        slug, val = km.group(1).lower(), km.group(2)
        if re.fullmatch(r"[0-9a-f]{32}", val, flags=re.I):
            kind = "hex32"
        elif re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            val,
            flags=re.I,
        ):
            kind = "uuid"
        else:
            kind = f"other:{len(val)}"
        out[slug] = kind
    return out


def main() -> None:
    e = env()
    token = e["PM_HOSTINGER_API_TOKEN"]
    user = e["PM_HOSTINGER_ACCOUNT"]

    import urllib.error

    domains_tried = list(CANDIDATE_DOMAINS)
    # Also try OT domain baseline for sanity
    ot_domain = e.get("PM_HOSTINGER_DOMAIN")
    if ot_domain and ot_domain not in domains_tried:
        domains_tried.append(ot_domain)

    found = None
    for domain in domains_tried:
        path = "wp-content/themes/shopwise-child/functions.php"
        try:
            st, body = api(
                token,
                f"/api/hosting/v1/accounts/{user}/domains/{domain}/files/content",
                {"path": path},
            )
        except urllib.error.HTTPError as err:
            print("ERR", domain, err.code)
            continue
        except Exception as err:
            print("ERR", domain, type(err).__name__, err)
            continue
        text = extract_text(body) if st == 200 else ""
        print("try", domain, st, "bytes", len(text) if st == 200 else 0)
        if st == 200 and "$api" in text and "payment_CF7" in text:
            # Prefer non-OT domain as "loja" if found; keep first loja-like hit
            if domain != ot_domain:
                found = (domain, text)
                break
            if found is None:
                found = (domain, text)

    if not found:
        OUT.write_text(
            json.dumps(
                {
                    "ok": False,
                    "reason": "functions.php da loja nao acessivel via Hostinger nesta conta",
                    "domains_tried": domains_tried,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print("not found; wrote", OUT)
        return

    domain, text = found
    DUMP.mkdir(parents=True, exist_ok=True)
    (DUMP / "shopwise-child__functions.php").write_text(text, encoding="utf-8")
    api_map = parse_keys(text, "api")
    apikey_map = parse_keys(text, "apikey")
    report = {
        "ok": True,
        "domain": domain,
        "bytes": len(text),
        "api_count": len(api_map),
        "apikey_count": len(apikey_map),
        "slugs": sorted(set(api_map) | set(apikey_map)),
        "api_only": sorted(set(api_map) - set(apikey_map)),
        "apikey_only": sorted(set(apikey_map) - set(api_map)),
        "rows": [
            {
                "slug": s,
                "has_api": s in api_map,
                "has_apikey": s in apikey_map,
                "api_kind": api_map.get(s),
                "apikey_kind": apikey_map.get(s),
            }
            for s in sorted(set(api_map) | set(apikey_map))
        ],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("found", domain, "slugs", len(report["slugs"]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
