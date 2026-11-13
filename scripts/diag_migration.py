"""Read-only probe of production vs clone after WP-Vivid migration."""

from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path

PROD = "https://loja.pellomenos.com.br"
CLONE = "https://pellomenos.companygenesis.com.br"
OUT = Path(__file__).resolve().parents[1] / "wordpress-loja" / ".secrets" / "diag-migracao.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

CTX = ssl.create_default_context()
UA = {"User-Agent": "pm-diag-readonly/1.0"}


def fetch(url: str, timeout: int = 60) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as response:
            headers = {k.lower(): v for k, v in response.headers.items()}
            return response.status, headers, response.read()
    except urllib.error.HTTPError as error:
        headers = {k.lower(): v for k, v in error.headers.items()} if error.headers else {}
        return error.code, headers, error.read() if error.fp else b""


def summarize_html(label: str, url: str) -> dict:
    status, headers, raw = fetch(url)
    text = raw.decode("utf-8", "replace")
    plugins = sorted(set(re.findall(r"/wp-content/plugins/([^/\"']+)", text)))
    themes = sorted(set(re.findall(r"/wp-content/themes/([^/\"']+)", text)))
    generators = re.findall(r'<meta name="generator" content="([^"]+)"', text, re.I)
    casino = bool(
        re.search(
            r"casino|cruks|jackpot|westace|flash casino|casinospellen",
            text,
            re.I,
        )
    )
    return {
        "label": label,
        "url": url,
        "status": status,
        "bytes": len(raw),
        "server": headers.get("server"),
        "powered": headers.get("x-powered-by"),
        "cache": headers.get("x-hcdn-cache-status") or headers.get("cf-cache-status"),
        "generators": generators,
        "themes": themes,
        "plugins_from_html": plugins,
        "has_pm_home_css": "pm-home/home.css" in text or "/uploads/pm-home/" in text,
        "has_home_fiel_marker": "Home fiel" in text or "data-audience=" in text,
        "has_elementor": "elementor" in text.lower(),
        "has_smartslider": "smartslider" in text.lower() or "n2-ss" in text,
        "has_revslider": "revslider" in text.lower() or "rev_slider" in text,
        "casino_spam": casino,
        "casino_snippets": [
            m.group(0)[:180]
            for m in re.finditer(
                r".{0,40}(?:casino|cruks|jackpot|westace).{0,80}",
                text,
                re.I,
            )
        ][:8],
        "title": (
            re.search(r"<title>(.*?)</title>", text, re.I | re.S).group(1).strip()[:200]
            if re.search(r"<title>(.*?)</title>", text, re.I | re.S)
            else None
        ),
    }


def probe_rest(base: str) -> dict:
    out: dict = {"base": base}
    paths = {
        "wp_v2": "/wp-json/wp/v2/",
        "users": "/wp-json/wp/v2/users?per_page=100&_fields=id,name,slug,link",
        "settings": "/wp-json/wp/v2/settings",
        "plugins_route": "/wp-json/wp/v2/plugins",
        "code_snippets": "/wp-json/code-snippets/v1/snippets",
        "pm_home_bundle": "/wp-json/pm-home/v1/bundle",
        "pages_home": "/wp-json/wp/v2/pages?slug=home&_fields=id,slug,link,modified",
        "page_571": "/wp-json/wp/v2/pages/571?_fields=id,slug,link,modified,status",
        "masculino": "/wp-json/wp/v2/pages?slug=masculino&_fields=id,slug,link,status,modified",
    }
    for key, path in paths.items():
        status, headers, raw = fetch(base + path)
        try:
            body = json.loads(raw.decode("utf-8", "replace"))
        except Exception:
            body = raw[:300].decode("utf-8", "replace")
        entry: dict = {"status": status}
        if key == "users" and isinstance(body, list):
            entry["users"] = [
                {"id": u.get("id"), "slug": u.get("slug"), "name": u.get("name")}
                for u in body
            ]
            entry["has_lsb"] = any(
                (u.get("slug") or "").lower() == "lsb"
                or (u.get("name") or "").lower() == "lsb"
                for u in body
            )
        elif key == "settings" and isinstance(body, dict):
            entry["title"] = body.get("title")
            entry["url"] = body.get("url")
            entry["email"] = body.get("email")
        elif key == "code_snippets" and isinstance(body, list):
            entry["count"] = len(body)
            entry["names"] = [s.get("name") for s in body[:30] if isinstance(s, dict)]
            entry["has_home_fiel"] = any(
                isinstance(s, dict) and "Home fiel" in (s.get("name") or "")
                for s in body
            )
        elif key in {"pages_home", "masculino", "page_571"}:
            entry["body"] = body
        else:
            entry["ok"] = status < 400
            if isinstance(body, str):
                entry["preview"] = body[:160]
            elif isinstance(body, dict):
                entry["keys"] = list(body.keys())[:20]
        out[key] = entry
    for name, path in {
        "pm_home_css": "/wp-content/uploads/pm-home/home.css",
        "pm_home_html": "/wp-content/uploads/pm-home/home.html",
        "pm_home_js": "/wp-content/uploads/pm-home/home.js",
    }.items():
        status, _, _ = fetch(base + path)
        out[name] = {"status": status, "exists": status == 200}
    return out


def main() -> None:
    report = {
        "prod_home": summarize_html("production", PROD + "/"),
        "clone_home": summarize_html("clone", CLONE + "/"),
        "prod_rest": probe_rest(PROD),
        "clone_rest": probe_rest(CLONE),
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)
    prod_users = report["prod_rest"].get("users", {})
    clone_users = report["clone_rest"].get("users", {})
    print("PROD casino_spam", report["prod_home"]["casino_spam"])
    print("PROD pm-home css", report["prod_rest"]["pm_home_css"])
    print("PROD has_lsb", prod_users.get("has_lsb"), "users_status", prod_users.get("status"))
    print("CLONE has_lsb", clone_users.get("has_lsb"), "users_status", clone_users.get("status"))
    print("CLONE home_fiel snippet", report["clone_rest"].get("code_snippets", {}).get("has_home_fiel"))
    print("PROD snippets", report["prod_rest"].get("code_snippets", {}).get("status"))
    print("PROD server", report["prod_home"].get("server"), "CLONE server", report["clone_home"].get("server"))


if __name__ == "__main__":
    main()
