# -*- coding: utf-8 -*-
"""Lê ficheiros-chave no OT via Hostinger API e procura Accesstage."""
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
OUT = ROOT / "scripts" / "_hostinger_accesstage_findings.json"
DUMP = ROOT / "scripts" / "_hostinger_ot_dumps"
BASE = "https://developers.hostinger.com"


def env():
    e = {}
    for path in (ENV, OT):
        for line in path.read_text(encoding="utf-8").splitlines():
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
            "User-Agent": "pm-hostinger-read/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body[:500]}
        return err.code, parsed


def list_dir(token, user, domain, directory, max_depth=2):
    return api(
        token,
        f"/api/hosting/v1/accounts/{user}/domains/{domain}/files",
        {"directory": directory, "max_depth": max_depth, "max_items": 2000},
    )


def read_file(token, user, domain, file_path):
    # docs: path is required
    st, body = api(
        token,
        f"/api/hosting/v1/accounts/{user}/domains/{domain}/files/content",
        {"path": file_path},
    )
    if st != 200:
        # try alternate param names
        for key in ("file", "filepath", "file_path"):
            st2, body2 = api(
                token,
                f"/api/hosting/v1/accounts/{user}/domains/{domain}/files/content",
                {key: file_path},
            )
            if st2 == 200:
                return st2, body2
        return st, body
    return st, body


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


def main():
    e = env()
    token = e["PM_HOSTINGER_API_TOKEN"]
    user = e["PM_HOSTINGER_ACCOUNT"]
    domain = e.get("PM_HOSTINGER_DOMAIN") or "pellomenosoficialteste.companygenesis.com.br"
    DUMP.mkdir(parents=True, exist_ok=True)

    report = {"domain": domain, "user": user, "plugin_dirs": [], "reads": [], "keyword_hits": []}

    # top-level plugin directories only
    st, plugins = list_dir(token, user, domain, "wp-content/plugins", max_depth=1)
    print("plugins list", st, plugins.get("total_items") if isinstance(plugins, dict) else plugins)
    for item in (plugins.get("items") if isinstance(plugins, dict) else []) or []:
        if item.get("type") == "directory":
            name = item.get("name") or ""
            report["plugin_dirs"].append(name)
            low = name.lower()
            if any(x in low for x in ("acces", "stage", "pay", "gateway", "pagseguro", "stripe", "cielo", "rede", "getnet", "stone")):
                print("INTERESTING PLUGIN DIR", name)

    print("plugin dirs", len(report["plugin_dirs"]))
    print("all dirs:", ", ".join(sorted(report["plugin_dirs"])[:80]))

    # list themes child + shopwise for includes
    for d in (
        "wp-content/themes/shopwise-child",
        "wp-content/themes/shopwise",
        "wp-content/mu-plugins",
        "wp-content/uploads/pm-home",
    ):
        st, data = list_dir(token, user, domain, d, max_depth=2)
        print("DIR", d, st, data.get("total_items") if isinstance(data, dict) else data)

    files = [
        "wp-content/themes/shopwise-child/functions.php",
        "wp-content/themes/shopwise/functions.php",
        "wp-content/mu-plugins/hostinger-auto-updates.php",
        "wp-content/mu-plugins/hostinger-preview-domain.php",
    ]

    # add shopwise assets that might include payment
    st, shop = list_dir(token, user, domain, "wp-content/themes/shopwise", max_depth=3)
    for item in (shop.get("items") if isinstance(shop, dict) else []) or []:
        path = item.get("path") or ""
        # paths from this listing are relative to shopwise/
        full = f"wp-content/themes/shopwise/{path}".replace("//", "/")
        name = (item.get("name") or path).lower()
        if item.get("type") == "file" and name.endswith((".php", ".js")):
            if any(x in name for x in ("pay", "checkout", "cart", "cf7", "order", "woo", "custom", "ajax")):
                files.append(full)

    # code-snippets stored in DB not files; but look for custom plugin folders
    for name in report["plugin_dirs"]:
        if any(x in name.lower() for x in ("code-snippets", "insert-headers", "header-footer", "wpcode", "my-custom", "pello", "genesis", "company")):
            st, sub = list_dir(token, user, domain, f"wp-content/plugins/{name}", max_depth=2)
            for item in (sub.get("items") if isinstance(sub, dict) else []) or []:
                if item.get("type") == "file" and str(item.get("name") or "").endswith(".php"):
                    rel = item.get("path") or item.get("name")
                    files.append(f"wp-content/plugins/{name}/{rel}".replace(f"{name}/{name}/", f"{name}/"))

    keys = (
        "accesstage",
        "accessstage",
        "Pedido Accesstage",
        "cart-number",
        "securityCode",
        "totalamount",
        "redirectSuccess",
        "removeitemcartpl",
        "wpcf7_mail_sent",
        "wpcf7_before_send_mail",
    )

    seen = set()
    for path in files:
        path = path.replace("\\", "/").replace("//", "/")
        # fix double plugin prefix from relative paths that already include plugin name
        path = re.sub(r"(wp-content/plugins/[^/]+/)\\1", r"\1", path)
        if path in seen:
            continue
        seen.add(path)
        st, body = read_file(token, user, domain, path)
        text = extract_text(body) if st == 200 else ""
        print("READ", path, st, "bytes", len(text) if st == 200 else 0, "err" if st != 200 else "")
        if st != 200:
            report["reads"].append({"path": path, "status": st, "error": body})
            continue
        # dump key files
        if "functions.php" in path or any(k.lower() in text.lower() for k in keys):
            safe = path.replace("/", "__")
            (DUMP / safe).write_text(text, encoding="utf-8")
        hits = [k for k in keys if k.lower() in text.lower()]
        report["reads"].append({"path": path, "status": st, "bytes": len(text), "hits": hits})
        if hits:
            contexts = []
            low = text.lower()
            for k in hits:
                i = low.find(k.lower())
                contexts.append(text[max(0, i - 100) : i + 200])
            report["keyword_hits"].append({"path": path, "hits": hits, "contexts": contexts[:6]})
            print("  HITS", hits)

    # Broader: scan plugin main php files for accesstage string via reading main file only
    for name in sorted(report["plugin_dirs"]):
        main_candidates = [
            f"wp-content/plugins/{name}/{name}.php",
            f"wp-content/plugins/{name}/index.php",
            f"wp-content/plugins/{name}/plugin.php",
        ]
        # common bootstrap names
        if name.startswith("woocommerce"):
            main_candidates.append(f"wp-content/plugins/{name}/{name}.php")
        for path in main_candidates[:1]:
            st, body = read_file(token, user, domain, path)
            if st != 200:
                continue
            text = extract_text(body)
            if "accesstage" in text.lower() or "accessstage" in text.lower() or "pedido accesstage" in text.lower():
                print("PLUGIN HIT", path)
                report["keyword_hits"].append(
                    {
                        "path": path,
                        "hits": ["accesstage"],
                        "contexts": [text[max(0, text.lower().find('acces') - 80) : text.lower().find('acces') + 160]],
                    }
                )
                (DUMP / path.replace("/", "__")).write_text(text, encoding="utf-8")

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT, "keyword_hit_files", len(report["keyword_hits"]))


if __name__ == "__main__":
    main()
