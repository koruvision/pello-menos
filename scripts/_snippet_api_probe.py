# -*- coding: utf-8 -*-
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path("projeto-migracao/.secrets/oficialteste.env")


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def call(method, path, payload=None):
    cfg = env()
    token = base64.b64encode(
        f"{cfg['PM_OFICIALTESTE_USER']}:{cfg['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        cfg["PM_OFICIALTESTE_URL"].rstrip("/") + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode() or "{}"
            return r.status, json.loads(body) if body.strip().startswith(("{", "[")) else body
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw[:500]
        return e.code, parsed


def main():
    st, rows = call("GET", "/wp-json/code-snippets/v1/snippets")
    print("GET list", st, type(rows).__name__, len(rows) if isinstance(rows, list) else rows)
    if isinstance(rows, list):
        for row in rows:
            print(" ", row.get("id"), row.get("name"), row.get("active"), "code_len", len(row.get("code") or ""))
            code = row.get("code") or ""
            if "checkout-shell" in code:
                for line in code.splitlines():
                    if "checkout-shell" in line:
                        print("   ", line.strip()[:120])
    # try GET id 6
    st6, sn6 = call("GET", "/wp-json/code-snippets/v1/snippets/6")
    print("GET 6", st6, sn6.get("name") if isinstance(sn6, dict) else sn6)
    # try PATCH-like minimal PUT with only code replace if we can read
    if isinstance(sn6, dict) and sn6.get("code"):
        new_code = (
            sn6["code"]
            .replace("checkout-shell.js?v=shell7", "checkout-shell-c10.js?v=c10")
            .replace("checkout-shell.js?v=shell9", "checkout-shell-c10.js?v=c10")
            .replace("checkout-shell.js?v=shell10", "checkout-shell-c10.js?v=c10")
        )
        print("would change", sn6["code"] != new_code, "new has c10", "c10" in new_code)
        payload = {
            "name": sn6.get("name"),
            "code": new_code,
            "scope": sn6.get("scope") or "global",
            "active": True,
        }
        stput, put = call("PUT", "/wp-json/code-snippets/v1/snippets/6", payload)
        print("PUT 6", stput, put if not isinstance(put, dict) else {k: put.get(k) for k in ("id", "code", "message", "data") if k in put or k == "code"})
        if isinstance(put, dict) and put.get("code"):
            print("saved has c10", "checkout-shell-c10" in (put.get("code") or ""))
    # try POST new tiny snippet that only enqueues c10
    tiny = r"""
add_action('wp_enqueue_scripts', function () {
  if (is_admin()) return;
  $path = isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '';
  if (stripos($path, 'finalizar-pagamento') === false && stripos($path, 'finaliza-compra') === false) return;
  $upload = wp_upload_dir();
  $src = $upload['baseurl'] . '/pm-home/checkout-shell-c10.js?v=c10';
  wp_enqueue_script('pm-checkout-shell-c10', $src, array(), null, true);
}, 100);
"""
    stpost, posted = call(
        "POST",
        "/wp-json/code-snippets/v1/snippets",
        {
            "name": "pm-home checkout shell c10",
            "code": tiny,
            "scope": "global",
            "active": True,
            "priority": 20,
        },
    )
    print("POST new", stpost, posted if not isinstance(posted, dict) else {k: posted.get(k) for k in ("id", "name", "active", "message", "code")})


if __name__ == "__main__":
    main()
