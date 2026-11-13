# -*- coding: utf-8 -*-
"""Estudo Hostinger API no OficialTeste: sites, árvore e Accesstage no disco."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "hostinger-ot.env"
OT_ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
OUT = ROOT / "scripts" / "_hostinger_ot_study.json"
BASE = "https://developers.hostinger.com"

KEYS = (
    "accesstage",
    "accessstage",
    "Pedido Accesstage",
    "cart-number",
    "securityCode",
    "totalamount",
    "redirectSuccess",
)


def load_env():
    e = {}
    for path in (ENV, OT_ENV):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def api(token: str, path: str, query: dict | None = None):
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "User-Agent": "pm-hostinger-study/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body[:800]}
        return err.code, parsed


def list_files(token, user, domain, directory="", max_depth=3, max_items=2000):
    return api(
        token,
        f"/api/hosting/v1/accounts/{user}/domains/{domain}/files",
        {
            "directory": directory,
            "max_depth": max_depth,
            "max_items": max_items,
        },
    )


def file_content(token, user, domain, file_path: str):
    return api(
        token,
        f"/api/hosting/v1/accounts/{user}/domains/{domain}/files/content",
        {"file": file_path},
    )


def main():
    e = load_env()
    token = e.get("PM_HOSTINGER_API_TOKEN") or e.get("HOSTINGER_API_TOKEN")
    user = e.get("PM_HOSTINGER_ACCOUNT") or e.get("PM_HOSTINGER_USERNAME")
    domain = e.get("PM_HOSTINGER_DOMAIN") or "pellomenosoficialteste.companygenesis.com.br"
    if not token or not user:
        raise SystemExit("missing token/account in secrets")

    report: dict = {"user": user, "domain": domain, "websites": None, "dirs": {}, "hits": []}

    for probe in (
        "/api/hosting/v1/websites",
        f"/api/hosting/v1/accounts/{user}/websites",
        f"/api/hosting/v1/accounts/{user}/domains",
    ):
        st, body = api(token, probe)
        print("PROBE", probe, st, type(body).__name__, (len(body) if isinstance(body, list) else list(body)[:8] if isinstance(body, dict) else body))
        if st == 200:
            report["websites_probe"] = {"path": probe, "body": body}
            break

    # Root listing
    st, root = list_files(token, user, domain, "", max_depth=2, max_items=500)
    print("ROOT", st, root.get("total_items") if isinstance(root, dict) else root)
    report["dirs"][""] = root if st == 200 else {"status": st, "body": root}

    targets = [
        "wp-content",
        "wp-content/plugins",
        "wp-content/mu-plugins",
        "wp-content/themes",
        "wp-content/themes/shopwise-child",
        "wp-content/themes/shopwise",
        "wp-includes",
    ]
    for d in targets:
        st, data = list_files(token, user, domain, d, max_depth=2, max_items=2000)
        print("DIR", d, st, data.get("total_items") if isinstance(data, dict) else data)
        report["dirs"][d] = data if st == 200 else {"status": st, "body": data}

    # Collect candidate PHP/JS paths from listings
    candidates = []
    for d, data in report["dirs"].items():
        if not isinstance(data, dict):
            continue
        for item in data.get("items") or []:
            name = str(item.get("name") or item.get("path") or "")
            path = str(item.get("path") or ((d + "/" + name).lstrip("/") if d else name))
            low = (name + " " + path).lower()
            if any(k in low for k in ("acces", "stage", "pay", "checkout", "cf7", "gateway")):
                candidates.append(path)
            if path.endswith((".php", ".js")) and any(
                x in low for x in ("function", "custom", "payment", "order", "cart")
            ):
                candidates.append(path)

    # Always read key files
    always = [
        "wp-content/themes/shopwise-child/functions.php",
        "wp-config.php",
    ]
    # Expand mu-plugins / child theme files from listing
    for key in ("wp-content/mu-plugins", "wp-content/themes/shopwise-child", "wp-content/plugins"):
        data = report["dirs"].get(key) or {}
        for item in data.get("items") or []:
            path = str(item.get("path") or "")
            if not path and item.get("name"):
                path = f"{key}/{item['name']}"
            if path.endswith(".php") or path.endswith(".js"):
                candidates.append(path)
            # one more level for plugin dirs with acces in name
            n = str(item.get("name") or "")
            if item.get("type") == "directory" or str(item.get("is_directory") or "").lower() == "true":
                if any(x in n.lower() for x in ("acces", "stage", "pay", "gateway", "pello")):
                    st2, sub = list_files(token, user, domain, f"{key}/{n}", max_depth=3, max_items=500)
                    report["dirs"][f"{key}/{n}"] = sub if st2 == 200 else {"status": st2, "body": sub}
                    for it2 in (sub.get("items") if isinstance(sub, dict) else []) or []:
                        p2 = str(it2.get("path") or f"{key}/{n}/{it2.get('name')}")
                        if p2.endswith((".php", ".js")):
                            candidates.append(p2)

    seen = set()
    read_list = []
    for p in always + candidates:
        p = p.replace("\\", "/").lstrip("/")
        if p in seen:
            continue
        seen.add(p)
        read_list.append(p)

    print("candidates to read", len(read_list))
    for path in read_list[:80]:
        st, body = file_content(token, user, domain, path)
        text = ""
        if isinstance(body, dict):
            text = body.get("content") or body.get("data") or body.get("file_content") or ""
            if isinstance(text, dict):
                text = text.get("content") or json.dumps(text)
        elif isinstance(body, str):
            text = body
        if st != 200:
            print("READ FAIL", path, st, str(body)[:120])
            continue
        text = str(text)
        hits = [k for k in KEYS if k.lower() in text.lower()]
        print("READ", path, "bytes", len(text), "hits", hits)
        if hits or "accesstage" in text.lower():
            # capture contexts
            contexts = []
            low = text.lower()
            for k in hits or ["accesstage"]:
                i = low.find(k.lower())
                if i >= 0:
                    contexts.append(text[max(0, i - 80) : i + 160].replace("\n", " "))
            report["hits"].append(
                {
                    "path": path,
                    "bytes": len(text),
                    "hits": hits,
                    "contexts": contexts[:5],
                }
            )

    # If no hits yet, deep-list plugins folder names
    plugins = report["dirs"].get("wp-content/plugins") or {}
    names = []
    for item in plugins.get("items") or []:
        names.append(item.get("name") or item.get("path"))
    report["plugin_names"] = names
    print("plugin names sample", names[:40], "total", len(names))

    mu = report["dirs"].get("wp-content/mu-plugins") or {}
    report["mu_plugin_names"] = [i.get("name") or i.get("path") for i in (mu.get("items") or [])]
    print("mu-plugins", report["mu_plugin_names"])

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2)[:2_000_000], encoding="utf-8")
    print("wrote", OUT, "hits", len(report["hits"]))


if __name__ == "__main__":
    main()
