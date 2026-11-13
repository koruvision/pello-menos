# -*- coding: utf-8 -*-
"""Remove 100% o produto teste R$ 1,99 da loja (Woo + front pm-home + bridge)."""
from __future__ import annotations

import base64
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"

NEEDLES = (
    "produto-1-real",
    "produto-r-1",
    "produto-r-199",
    "Produto R$ 1,99",
    "Produto R$ 1",
)


def cfg():
    vals = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip()
    return {
        "url": vals["PM_LOJA_URL"].rstrip("/"),
        "user": vals["PM_LOJA_USER"],
        "password": vals["PM_LOJA_APP_PASSWORD"],
    }


def call(c, method, path, payload=None, raw=None, content_type="application/json", timeout=180):
    data = raw if raw is not None else (
        None if payload is None else json.dumps(payload).encode("utf-8")
    )
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    req = urllib.request.Request(
        c["url"] + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + tok,
            "User-Agent": "pm-purge-199",
            "Content-Type": content_type,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body[:1] in "[{" else body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, (json.loads(body) if body[:1] in "[{" else body[:500])


def find_woo(c):
    found = {}
    for q in ("1.99", "Produto R$", "produto-r-199", "produto-1-real", "produto-r-1"):
        st, rows = call(
            c,
            "GET",
            "/wp-json/wc/v3/products?search="
            + urllib.parse.quote(q)
            + "&per_page=50&status=any",
        )
        if not isinstance(rows, list):
            print("search fail", q, st, rows)
            continue
        for p in rows:
            name = p.get("name") or ""
            slug = p.get("slug") or ""
            price = str(p.get("price") or "")
            if (
                "1,99" in name
                or price == "1.99"
                or "produto-r-199" in slug
                or "produto-1-real" in slug
                or slug.startswith("produto-r-1")
                or name.lower().startswith("produto r$ 1")
            ):
                found[p["id"]] = p
    return found


def trash_woo(c, products):
    for pid, p in products.items():
        print("trash woo", pid, p.get("slug"), p.get("name"), p.get("status"), p.get("price"))
        st, body = call(c, "DELETE", f"/wp-json/wc/v3/products/{pid}?force=true")
        print("  delete", st, body if not isinstance(body, dict) else body.get("id") or body.get("message") or "ok")


def scrub_text(text: str) -> str:
    # drop product cards / links mentioning the test SKU
    # Remove whole product page files handled separately
    for n in NEEDLES:
        if n in text:
            text = text.replace(n, "")
    # leftover "1,99" only if clearly the test product title context already gone
    return text


def scrub_local_files():
    removed = []
    for rel in (
        "products/produto-1-real.html",
        "products/produto-r-1.html",
        "products/produto-r-199.html",
        "media/images/products/produto-1-real.webp",
        "images/products/produto-1-real.webp",
    ):
        path = PM / rel
        if path.is_file():
            path.unlink()
            removed.append(rel)
    print("removed files", removed)

    for name in ("woo-bridge.json", "pages.json", "cart-related.json", "black-nov-campaign.json"):
        path = PM / name
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False

        def drop(obj):
            nonlocal changed
            if isinstance(obj, dict):
                for k in list(obj.keys()):
                    if any(n in str(k) for n in ("produto-1-real", "produto-r-1", "produto-r-199")):
                        obj.pop(k, None)
                        changed = True
                    else:
                        drop(obj[k])
            elif isinstance(obj, list):
                keep = []
                for item in obj:
                    s = json.dumps(item, ensure_ascii=False) if not isinstance(item, str) else item
                    if any(n in s for n in ("produto-1-real", "produto-r-1", "produto-r-199", "Produto R$ 1,99")):
                        changed = True
                        continue
                    drop(item)
                    keep.append(item)
                obj[:] = keep

        drop(data)
        if changed:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("cleaned json", name)

    # scrub HTML cards from home / loja / busca / masculino / products related
    card_re = re.compile(
        r'<article[^>]*(?:produto-1-real|produto-r-199|produto-r-1|Produto R\$ 1,99)[\s\S]*?</article>',
        re.I,
    )
    link_block = re.compile(
        r'<a[^>]+href="[^"]*(?:produto-1-real|produto-r-199|produto-r-1)[^"]*"[\s\S]*?</a>',
        re.I,
    )
    for path in (
        list(PM.glob("*.html"))
        + list(PM.glob("products/*.html"))
        + list(PM.glob("loja/*.html"))
        + list(PM.glob("pages/*.html"))
    ):
        text = path.read_text(encoding="utf-8")
        if not any(n in text for n in NEEDLES):
            continue
        new = card_re.sub("", text)
        new = link_block.sub("", new)
        # pages.json style paths
        new = new.replace("/produto/produto-1-real/", "/")
        new = new.replace("/produto/produto-r-199/", "/")
        new = new.replace("/produto/produto-r-1/", "/")
        for n in NEEDLES:
            new = new.replace(n, "")
        if new != text:
            path.write_text(new, encoding="utf-8")
            print("scrubbed", path.relative_to(PM))


def publish_bundle(c):
    dest = c["url"] + "/wp-content/uploads/pm-home"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in (
            "home.html",
            "masculino.html",
            "loja.html",
            "busca.html",
            "woo-bridge.json",
            "pages.json",
            "cart-related.json",
            "black-nov-campaign.json",
        ):
            path = PM / name
            if not path.is_file():
                continue
            raw = path.read_bytes()
            if name.endswith(".html"):
                raw = path.read_text(encoding="utf-8").replace(CLONE, dest).encode("utf-8")
            z.writestr(name, raw)
            print("zip+", name)
        # empty delete markers aren't supported; overwrite product page with gone notice not needed if removed from pages.json
    req_data = buf.getvalue()
    st, body = call(
        c,
        "POST",
        "/wp-json/pm-home/v1/bundle",
        raw=req_data,
        content_type="application/zip",
        timeout=600,
    )
    print("bundle", st, body)


def verify(c):
    for path in ("/?v=rm199b", "/busca/?q=1%2C99&v=rm199b", "/loja/?v=rm199b"):
        try:
            html = urllib.request.urlopen(
                urllib.request.Request(
                    c["url"] + path,
                    headers={"User-Agent": "x", "Cache-Control": "no-cache"},
                ),
                timeout=60,
            ).read().decode("utf-8", "replace")
        except Exception as e:
            print("verify fail", path, e)
            continue
        hits = [n for n in NEEDLES if n in html] + (["1,99"] if "1,99" in html else [])
        print("live", path, "hits", hits or "none")
    left = find_woo(c)
    print("woo left", {i: (p.get("slug"), p.get("status")) for i, p in left.items()} or "none")


def main():
    c = cfg()
    print("destino", c["url"])
    products = find_woo(c)
    print("found", len(products))
    trash_woo(c, products)
    scrub_local_files()
    publish_bundle(c)
    verify(c)


if __name__ == "__main__":
    main()
